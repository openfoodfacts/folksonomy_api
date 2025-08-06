import re
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, model_validator, field_validator

re_barcode = re.compile(r"[0-9]{1,24}")
re_key = re.compile(r"[a-z0-9_-]+(\:[a-z0-9_-]+)*")


class User(BaseModel):
    user_id: Optional[str]


class ProductTag(BaseModel):
    product: str
    k: str
    v: str
    owner: str = ""
    version: int = 1
    editor: Optional[str] = None
    last_edit: Optional[datetime] = None
    comment: Optional[str] = ""

    @field_validator("product")
    def product_check(cls, v):
        if not v:
            raise ValueError("barcode cannot be empty")
        if not re.fullmatch(re_barcode, v):
            raise ValueError("barcode should contain only digits from 0-9")
        return v

    @field_validator("k")
    def key_check(cls, v):
        if not v:
            raise ValueError("k cannot be empty")
        # strip the key
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("k must be alpha-numeric [a-z0-9_-:]")
        return v

    @field_validator("v")
    def value_check(cls, v):
        if not v:
            raise ValueError("v cannot be empty")
        # strip values
        v = v.strip()
        return v

    @field_validator("version")
    def version_check(cls, version):
        if version < 1:
            raise ValueError("version must be greater or equal to 1")
        return version


class ProductStats(BaseModel):
    product: str
    keys: int
    editors: int
    last_edit: datetime


class ProductList(BaseModel):
    product: str
    k: str
    v: str


class HelloResponse(BaseModel):
    message: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str


class KeyStats(BaseModel):
    k: str
    count: int
    values: int


class ValueCount(BaseModel):
    v: str
    product_count: int


class PingResponse(BaseModel):
    ping: str


class PropertyRenameRequest(BaseModel):
    old_property: str
    new_property: str

    @model_validator(mode="after")
    def check_not_same(self):
        if self.old_property == self.new_property:
            raise ValueError("old_property and new_property should not be the same.")
        return self
    def property_check(cls, v):
        if not v:
            raise ValueError("property cannot be empty")
        # strip the property
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("property must be alpha-numeric [a-z0-9_-:]")
        return v

class PropertyClashCheckRequest(BaseModel):
    old_property: str
    new_property: str

    @model_validator(mode="after")
    def check_not_same(self):
        if self.old_property == self.new_property:
            raise ValueError("old_property and new_property should not be the same.")
        return self
    def property_check(cls, v):
        if not v:
            raise ValueError("property cannot be empty")
        # strip the property
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("property must be alpha-numeric [a-z0-9_-:]")
        return v

class PropertyDeleteRequest(BaseModel):
    property: str

    @field_validator("property")
    def property_check(cls, v):
        if not v:
            raise ValueError("property cannot be empty")
        # strip the property
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("property must be alpha-numeric [a-z0-9_-:]")
        return v


class ValueRenameRequest(BaseModel):
    property: str
    old_value: str
    new_value: str

    @field_validator("property")
    def property_check(cls, v):
        if not v:
            raise ValueError("property cannot be empty")
        # strip the property
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("property must be alpha-numeric [a-z0-9_-:]")
        return v

    @field_validator("old_value", "new_value")
    def value_check(cls, v):
        if not v:
            raise ValueError("value cannot be empty")
        # strip values
        v = v.strip()
        return v


class ValueDeleteRequest(BaseModel):
    property: str
    value: str

    @field_validator("property")
    def property_check(cls, v):
        if not v:
            raise ValueError("property cannot be empty")
        # strip the property
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError("property must be alpha-numeric [a-z0-9_-:]")
        return v

    @field_validator("value")
    def value_check(cls, v):
        if not v:
            raise ValueError("value cannot be empty")
        # strip values
        v = v.strip()
        return v


class PropertyClashCheck(BaseModel):
    products_with_both: int
    products_with_old_only: int
    products_with_new_only: int
    conflicting_products: list
