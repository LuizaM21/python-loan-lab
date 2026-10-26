"""Errors the service raises. The API turns each one into a status code and a JSON body."""

from __future__ import annotations


class LoanLabError(Exception):
    code = "error"
    status = 400

    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


class ValidationError(LoanLabError):
    code, status = "validation_error", 400


class Unauthorized(LoanLabError):
    code, status = "unauthorized", 401


class NotFound(LoanLabError):
    code, status = "not_found", 404


class Conflict(LoanLabError):
    code, status = "conflict", 409
