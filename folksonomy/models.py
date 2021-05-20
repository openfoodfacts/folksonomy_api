import re, time
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, status, Response, Depends, Header
from pydantic import BaseModel, ValidationError, validator, root_validator

re_barcode = re.compile(r'[0-9]{1,13}')
re_key = re.compile(r'[a-z0-9_\.]+(\:[a-z0-9_\.]+)*')
re_types = {
    'date': re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}'),
    'timestamp': re.compile(r'[0-9]{4}-[0-9]{2}-[0-9]{2}[T ][0-9]{2}:[0-9]{2}:[0-9]{2}(Z|[+\-][0-9]{4})'),
    'integer': re.compile(r'(\+|\-)[0-9]+'),
    'boolean': re.compile(r'(true|false)'),
    'string': re.compile(r'.*'),
    'float': re.compile(r'(\+|\-)[0-9]+(\.[0-9]+)'),
    'wikidata': re.compile(r'Q[0-9]+'),
    'url': re.compile(r'https?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
    'email': re.compile(r"(^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$)"),
    'iso3166': re.compile(r"^A[^ABCHJKNPVY]|B[^CKPUX]|C[^BEJPQST]|D[EJKMOZ]|E[CEGHRST]|F[IJKMOR]|G[^CJKOVXZ]|H[KMNRTU]|I[DEL-OQ-T]|J[EMOP]|K[EGHIMNPRWYZ]|L[ABCIKR-VY]|M[^BIJ]|N[ACEFGILOPRUZ]|OM|P[AE-HK-NRSTWY]|QA|R[EOSUW]|S[^FPQUW]|T[^ABEIPQSUXY]|U[AGMSYZ]|V[ACEGINU]|WF|WS|YE|YT|Z[AMW]$")
}

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
        if not re.fullmatch(re_barcode, v):
            raise ValueError('product is limited to 13 digits')
        return v

    @validator('k')
    def key_check(cls, k):
        if k == '':
            raise ValueError('k cannot be empty')
        if not re.fullmatch(re_key, k):
            raise ValueError('k must be alpha-numeric [a-z0-9_:]')
        return k

    @validator('v')
    def value_check(cls, v):
        if v == '':
            raise ValueError('v cannot be empty')
        return v

    @validator('version')
    def version_check(cls, version):
        if version < 1:
            raise ValueError('version must greater or equal to 1')
        return version

    @root_validator
    def check_typing(cls, values):
        k,v = values.get('k'), values.get('v')
        type = k.split('.')
        if len(type) > 2:
            raise ValueError(f'"{k}" invalid')
        elif len(type) == 2:
            if not type[1] in re_types:
                raise ValueError(f'"{k}" is an unkown type')
            if not re.fullmatch(re_types[type[1]], v):
                raise ValueError(f'"{v}" invalid as {type[1]}')
        return values


class ProductStats(BaseModel):
    product:    str
    keys:       int
    editors:    int
    last_edit:  datetime
