from pydantic import BaseModel, ConfigDict, field_validator
from typing import Optional
from uuid import UUID
from datetime import datetime


class FactorCreate(BaseModel):
    name: str
    display_name: str
    description: Optional[str] = None
    expression: str
    category: str = "custom"
    parameters: dict = {}

    @field_validator("name")
    @classmethod
    def name_valid(cls, v: str) -> str:
        if not v.replace("_", "").isalnum():
            raise ValueError("因子名称只能包含字母、数字和下划线")
        return v


class FactorUpdate(BaseModel):
    display_name: Optional[str] = None
    description: Optional[str] = None
    expression: Optional[str] = None
    parameters: Optional[dict] = None
    is_active: Optional[bool] = None


class FactorResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    user_id: Optional[UUID] = None
    name: str
    display_name: str
    description: Optional[str] = None
    expression: str
    category: str
    parameters: dict
    is_active: bool
    created_at: datetime


class FactorPreviewRequest(BaseModel):
    expression: str
    stock_code: str
    start_date: str
    end_date: str


class FactorAnalysisRequest(BaseModel):
    factor_id: UUID
    stock_codes: list[str]
    start_date: str
    end_date: str
