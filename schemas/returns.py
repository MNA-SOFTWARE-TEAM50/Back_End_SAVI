"""
Schemas de Devoluciones con Pydantic
"""
from pydantic import BaseModel, field_validator
from typing import Optional, List
from datetime import datetime


class ReturnItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class ExchangeItem(BaseModel):
    product_id: int
    product_name: str
    quantity: int
    unit_price: float
    subtotal: float


class ReturnCreate(BaseModel):
    sale_id: int
    items_returned: List[ReturnItem]
    items_exchanged: Optional[List[ExchangeItem]] = None
    action: str  # refund | credit_note | exchange
    refund_method: Optional[str] = None  # requerido si action=refund
    reason: Optional[str] = None

    @field_validator('action')
    @classmethod
    def valid_action(cls, v: str):
        allowed = {"refund", "credit_note", "exchange"}
        if v not in allowed:
            raise ValueError("action inválido")
        return v


class Return(BaseModel):
    id: int
    sale_id: int
    user_id: str
    items_returned: List[ReturnItem]
    items_exchanged: Optional[List[ExchangeItem]] = None
    subtotal_refund: float
    tax_refund: float
    total_refund: float
    action: str
    refund_method: Optional[str] = None
    reason: Optional[str] = None
    status: str
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReturnList(BaseModel):
    items: List[Return]
    total: int


class ReturnValidation(BaseModel):
    ok: bool
    reason: Optional[str] = None
    errors: Optional[List[str]] = None
