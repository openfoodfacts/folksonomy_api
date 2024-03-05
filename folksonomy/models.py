import re
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, status, Response, Depends, Header
from pydantic import BaseModel, ValidationError, field_validator

re_barcode = re.compile(r'[0-9]{1,24}')
re_key = re.compile(r'[a-z0-9_-]+(\:[a-z0-9_-]+)*')


class User(BaseModel):
    user_id: Optional[str]


class ProductTag(BaseModel):
    product:    str
    k:          str
    v:          str
    owner:      str = ""
    version:    int = 1
    editor:     Optional[str] = None
    last_edit:  Optional[datetime] = None
    comment:    Optional[str] = ""

    @field_validator('product')
    def product_check(cls, v):
        if not v:
            raise ValueError('barcode cannot be empty')
        if not re.fullmatch(re_barcode, v):
            raise ValueError('barcode should contain only digits from 0-9')
        return v

    @field_validator('k')
    def key_check(cls, v):
        if not v:
            raise ValueError('k cannot be empty')
        # strip the key
        v = v.strip()
        if not re.fullmatch(re_key, v):
            raise ValueError('k must be alpha-numeric [a-z0-9_-:]')
        return v

    @field_validator('v')
    def value_check(cls, v):
        if not v:
            raise ValueError('v cannot be empty')
        # strip values
        v = v.strip()
        return v

    @field_validator('version')
    def version_check(cls, version):
        if version < 1:
            raise ValueError('version must be greater or equal to 1')
        return version


class ProductStats(BaseModel):
    product:    str
    keys:       int
    editors:    int
    last_edit:  datetime


class ProductList(BaseModel):
    product:    str
    k:          str
    v:          str
