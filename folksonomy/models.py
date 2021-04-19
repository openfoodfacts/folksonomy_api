import re, time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, status, Response, Depends, Header
from pydantic import BaseModel, ValidationError, validator

re_barcode = re.compile(r'[0-9]{1,13}')
re_key = re.compile(r'[a-zA-Z0-9_]+')

class User(BaseModel):
    user_id: str


class ProductTag(BaseModel):
    product:    str
    k:          str
    v:          str
    owner:      str = ""
    version:    int = 1
    editor:     Optional[str]
    last_edit:  Optional[datetime]
    comment:    Optional[str] = ""

    @validator('product')
    def product_check(cls, v):
        if not re.fullmatch(barcode, v):
            raise ValueError('product is limited to 13 digits')
        return v.title()

    @validator('k')
    def key_check(cls, v):
        if v == '':
            raise ValueError('k cannot be empty')
        if not re.fullmatch(re_key, v):
            raise ValueError('k must be alpha-numeric [a-zA-Z0-9_]')
        return v.title()

    @validator('v')
    def value_check(cls, v):
        if v == '':
            raise ValueError('v cannot be empty')
        return v.title()


class ProductStats(BaseModel):
    product:    str
    keys:       int
    editors:    int
    last_edit:  datetime
