import datetime
import logging
import traceback

from pydantic.main import BaseModel

logger = logging.getLogger(__name__)


class HttpRequestLog(BaseModel):
    url: str
    method: str
    body: str | None = None
    startTime: datetime.datetime


class HttpResponseLog(BaseModel):
    status: int
    endTime: datetime.datetime
    totalTime: int


class ErrorInfo(BaseModel):
    function: str
    line: int
    exceptionInfo: str | None = None


class ContextMessageLog(BaseModel):
    dbSession: str | None = None
    httpRequest: HttpRequestLog | None = None
    httpResponse: HttpResponseLog | None = None
    errorInfo: ErrorInfo | None = None


class JsonLog(BaseModel):
    level: str
    timestamp: datetime.datetime
    context: str
    message: str
    contextMessage: ContextMessageLog | dict | None = None


class SafeJsonFormatter(logging.Formatter):
    """
    Json formatter with following schema
    {
        level: str,
        timestamp: Datetime,
        context: str,
        message: str,
        contextMessage: <contextMessage>
    }
    """

    def format(self, record):
        if record.levelname == "ERROR":
            exception_info: str | None = None
            # Check if the error contains exception data
            if record.exc_info:
                exc_type, exc_value, exc_tb = record.exc_info
                exception_info = "".join(
                    traceback.format_exception(exc_type, exc_value, exc_tb)
                )
            record.error_detail = ErrorInfo(
                function=record.funcName,
                line=record.lineno,
                exceptionInfo=exception_info,
            )

        context_message = ContextMessageLog(
            dbSession=getattr(record, "db_session", None),
            httpRequest=getattr(record, "http_request", None),
            httpResponse=getattr(record, "http_response", None),
            errorInfo=getattr(record, "error_detail", None),
        )

        json_log = JsonLog(
            level=record.levelname,
            timestamp=datetime.datetime.fromtimestamp(
                record.created, datetime.timezone.utc
            ),
            context=f"{record.module}.{record.funcName}",
            message=record.getMessage(),
            contextMessage=(
                context_message
                if len(context_message.model_dump(exclude_none=True))
                else None
            ),
        )

        return json_log.model_dump_json(exclude_none=True)
