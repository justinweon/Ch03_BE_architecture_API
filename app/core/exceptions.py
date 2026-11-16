"""커스텀 예외와 일관된 에러 응답 포맷.

모든 에러 응답은 {"error": {"code": ..., "message": ..., "details": ...}} 형태로 통일한다.
"""
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from starlette.exceptions import HTTPException as StarletteHTTPException


class ErrorBody(BaseModel):
    code: str
    message: str
    details: list | None = None


class ErrorResponse(BaseModel):
    error: ErrorBody


class AppException(Exception):
    status_code = 400
    code = "BAD_REQUEST"

    def __init__(self, message: str):
        self.message = message


class NotFoundError(AppException):
    status_code = 404
    code = "NOT_FOUND"


class ConflictError(AppException):
    status_code = 409
    code = "CONFLICT"


class UnauthorizedError(AppException):
    status_code = 401
    code = "UNAUTHORIZED"


class ForbiddenError(AppException):
    status_code = 403
    code = "FORBIDDEN"


def _response(status_code: int, code: str, message: str, details: list | None = None) -> JSONResponse:
    body = ErrorResponse(error=ErrorBody(code=code, message=message, details=details))
    return JSONResponse(status_code=status_code, content=body.model_dump(exclude_none=True))


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        headers = {"WWW-Authenticate": "Bearer"} if exc.status_code == 401 else None
        response = _response(exc.status_code, exc.code, exc.message)
        if headers:
            response.headers.update(headers)
        return response

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        details = [
            {"field": ".".join(str(p) for p in err["loc"] if p != "body"), "message": err["msg"]}
            for err in exc.errors()
        ]
        return _response(422, "VALIDATION_ERROR", "요청 값이 올바르지 않습니다.", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        return _response(exc.status_code, "HTTP_ERROR", str(exc.detail))

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        return _response(500, "INTERNAL_SERVER_ERROR", "서버 내부 오류가 발생했습니다.")
