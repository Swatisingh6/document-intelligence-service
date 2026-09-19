from pydantic import BaseModel, Field


class ErrorDetail(BaseModel):
    code: str = Field(..., json_schema_extra={"example": "UNSUPPORTED_FILE_TYPE"})
    message: str = Field(..., json_schema_extra={"example": "Only PDF, JPG, JPEG and PNG files are supported"})


class ErrorResponse(BaseModel):
    error: ErrorDetail
