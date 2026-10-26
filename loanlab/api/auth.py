"""API key check for endpoints that change data."""

from __future__ import annotations

import functools
import hmac

from flask import current_app, request

from ..errors import Unauthorized


def require_api_key(view):
    @functools.wraps(view)
    def wrapper(*args, **kwargs):
        expected = current_app.config["API_KEY"]
        given = request.headers.get("X-Api-Key")
        # compare_digest takes the same time whether the first or the last character differs
        if given is None or not hmac.compare_digest(given.encode(), expected.encode()):
            raise Unauthorized("A valid X-Api-Key header is required.")
        return view(*args, **kwargs)

    return wrapper
