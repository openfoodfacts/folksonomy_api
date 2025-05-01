import re
from datetime import datetime
from typing import Dict, List, Optional

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

class TitleElement(BaseModel):
    """
    The title of a knowledge panel.
    """
    name: str   # Short name of this panel, not including any actual values
    title: str  # Human-readable title shown in the panel 

class TableColumn(BaseModel):
    """
    A column in a TableElement.
    """
    type: str   # Type of value for the values in column
    text: str   # Name of the column

class TableElement(BaseModel):
    """
    Element to display a table in a knowledge panel.
    """
    id: str     # An id for the table
    title: str  # Title of the column
    rows: str   # Values to fill the rows
    columns: List[TableColumn]

class Element(BaseModel):
    """
    Each element object contains one specific element object such as a text element or an image element. For knowledge panels.
    """
    type: str   # The type of the included element object. The type also indicates which field contains the included element object. e.g. if the type is "text", the included element object will be in the "text_element" field.
    table_element: TableElement

class Panel(BaseModel):
    """
    Each knowledge panel contains an optional title and an optional array of elements.
    """
    title_element: TitleElement
    elements: List[Element]

class ProductKnowledgePanels(BaseModel):
    """
    The knowledge panels object is a dictionary of individual panel objects.
    Each key of the dictionary is the id of the panel, and the value is the panel object.

    Apps typically display a number of root panels with known panel ids (e.g. health_card and environment_card). Panels can reference other panels and display them as sub-panels.
    """
    knowledge_panels: Dict[str, Panel]
