"""The Flask application factory.

Run it:
    flask --app loanlab.api run --port 5080
"""

from __future__ import annotations

import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from datetime import date
from typing import Any

from flask import Flask, g, jsonify, request
from werkzeug.exceptions import HTTPException

from ..db import IN_MEMORY, make_engine, make_sessionmaker
from ..errors import LoanLabError
from ..events import EventLog, InMemoryEventLog, MongoEventLog
from ..models import Base
from ..seed import seed, seed_demo
from .routes import api

DEFAULTS = {
    "DATABASE_URL": "sqlite:///loanlab.sqlite3",
    "API_KEY": "lab-dev-key",
    "RESET_DATABASE": "1",  # start every run from the two sample loans, like the Dose lab
    "SEED": "1",
    "DEMO_LOANS": "0",  # lesson 07: DEMO_LOANS=3000 adds volume
    "MONGO_URL": "",  # lesson 06: switches the event log to MongoDB
    "LOG_LEVEL": "INFO",
}


def _setting(config: dict[str, Any], name: str) -> Any:
    if name in config:
        return config[name]
    return os.environ.get(name, DEFAULTS[name])


def _flag(value: Any) -> bool:
    return str(value).strip().lower() in {"1", "true", "yes", "on"}


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        line = {
            "ts": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "message": record.getMessage(),
            "requestId": getattr(record, "request_id", None),
            **getattr(record, "fields", {}),
        }
        if record.exc_info:
            line["exception"] = self.formatException(record.exc_info)
        return json.dumps(line, default=str)


def _logger(level: str) -> logging.Logger:
    logger = logging.getLogger("loanlab")
    logger.setLevel(level.upper())
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.propagate = False
    return logger


def _event_log(mongo_url: str) -> EventLog:
    if not mongo_url:
        return InMemoryEventLog()
    from pymongo import MongoClient

    log = MongoEventLog(MongoClient(mongo_url)["loanlab"]["events"])
    log.ensure_indexes()
    return log


def create_app(
    config: dict[str, Any] | None = None,
    *,
    today: Callable[[], date] = date.today,
    events: EventLog | None = None,
) -> Flask:
    config = dict(config or {})
    app = Flask(__name__)
    app.config.update(config)
    app.config["API_KEY"] = _setting(config, "API_KEY")

    logger = _logger(_setting(config, "LOG_LEVEL"))
    database_url = _setting(config, "DATABASE_URL")
    engine = make_engine(database_url)
    if _flag(_setting(config, "RESET_DATABASE")):
        Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)  # production would use Alembic migrations (lesson 04)
    sessions = make_sessionmaker(engine)
    event_log = events if events is not None else _event_log(_setting(config, "MONGO_URL"))

    if _flag(_setting(config, "SEED")):
        with sessions() as session:
            seed(session, event_log)
    demo = int(_setting(config, "DEMO_LOANS") or 0)
    if demo:
        with sessions() as session:
            seed_demo(session, event_log, demo)
    if database_url not in IN_MEMORY:
        # gunicorn --preload builds the app once, then forks workers. Connections must not be
        # shared across processes, so empty the pool: each worker opens its own.
        engine.dispose()

    app.extensions["loanlab.engine"] = engine
    app.extensions["loanlab.sessionmaker"] = sessions
    app.extensions["loanlab.events"] = event_log
    app.extensions["loanlab.today"] = today

    app.register_blueprint(api)

    @app.before_request
    def start():
        g.request_id = request.headers.get("X-Request-ID") or uuid.uuid4().hex
        g.started = time.perf_counter()

    @app.after_request
    def finish(response):
        session = g.pop("db", None)
        if session is not None:
            # Unit of work: one transaction per request. Commit only when the request succeeded.
            if response.status_code < 400:
                session.commit()
            else:
                session.rollback()
            session.close()
        response.headers["X-Request-ID"] = g.request_id
        logger.info(
            "request",
            extra={
                "request_id": g.request_id,
                "fields": {
                    "method": request.method,
                    "path": request.path,
                    "status": response.status_code,
                    "durationMs": round((time.perf_counter() - g.started) * 1000, 2),
                },
            },
        )
        return response

    @app.teardown_request
    def cleanup(_exc):
        session = g.pop("db", None)  # still here only if after_request did not run
        if session is not None:
            session.rollback()
            session.close()

    @app.errorhandler(LoanLabError)
    def handle_lab_error(exc: LoanLabError):
        return jsonify({"code": exc.code, "message": exc.message}), exc.status

    @app.errorhandler(HTTPException)
    def handle_http_error(exc: HTTPException):
        code = (exc.name or "error").lower().replace(" ", "_")
        return jsonify({"code": code, "message": exc.description}), exc.code

    @app.errorhandler(Exception)
    def handle_unexpected(exc: Exception):
        logger.exception("unhandled error", extra={"request_id": g.get("request_id")})
        return jsonify({"code": "internal_error", "message": "Unexpected error."}), 500

    return app
