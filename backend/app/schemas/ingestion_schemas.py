"""
Pydantic schemas describing what a valid INCOMING record looks like,
for each of our four data sources. These are distinct from our SQLAlchemy
models (app/models/) — those describe the database's shape; these describe
what we're willing to accept from an external system before it ever
reaches the database.
"""
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator, ValidationError


class CustomerRecordSchema(BaseModel):
    external_id: str
    full_name: str
    email: str | None = None
    region: str | None = None
    acquisition_channel: str | None = None

    @field_validator("external_id")
    @classmethod
    def external_id_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("external_id must not be blank")
        return v

    @field_validator("full_name")
    @classmethod
    def full_name_not_blank(cls, v):
        if not v or not v.strip():
            raise ValueError("full_name must not be blank")
        return v

    @field_validator("email")
    @classmethod
    def email_looks_valid(cls, v):
        if v is not None and v.strip() and "@" not in v:
            raise ValueError("email must contain '@'")
        return v


class ProductRecordSchema(BaseModel):
    external_id: str
    name: str
    category: str | None = None
    unit_price: float

    @field_validator("unit_price")
    @classmethod
    def price_must_be_positive(cls, v):
        if v is None or v <= 0:
            raise ValueError("unit_price must be greater than 0")
        return v


class OrderRecordSchema(BaseModel):
    external_id: str
    customer_external_id: str
    product_external_id: str
    quantity: int
    total_amount: float
    status: str
    region: str | None = None
    channel: str | None = None
    order_date: str

    

    @field_validator("quantity")
    @classmethod
    def quantity_must_be_positive(cls, v):
        if v is None or v <= 0:
            raise ValueError("quantity must be greater than 0")
        return v

    @field_validator("total_amount")
    @classmethod
    def amount_must_be_non_negative(cls, v):
        if v is None or v < 0:
            raise ValueError("total_amount must be >= 0")
        return v

    @field_validator("status")
    @classmethod
    def status_must_be_known(cls, v):
        if v not in {"completed", "cancelled", "refunded"}:
            raise ValueError(f"status '{v}' is not a recognized value")
        return v

    @field_validator("order_date")
    @classmethod
    def order_date_must_parse(cls, v):
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"order_date '{v}' is not a valid ISO datetime")
        return v


class MarketingSpendRecordSchema(BaseModel):
    campaign_external_id: str
    spend_date: str
    amount: float

    @field_validator("amount")
    @classmethod
    def amount_must_be_non_negative(cls, v):
        if v is None or v < 0:
            raise ValueError("amount must be >= 0")
        return v

    @field_validator("spend_date")
    @classmethod
    def spend_date_must_parse(cls, v):
        try:
            datetime.fromisoformat(v)
        except (ValueError, TypeError):
            raise ValueError(f"spend_date '{v}' is not a valid ISO date")
        return v