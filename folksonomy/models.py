import re
from datetime import datetime
from typing import List, Optional

from fastapi import FastAPI, status, Response, Depends, Header
from pydantic import BaseModel, ValidationError, field_validator

re_barcode = re.compile(r'[0-9]{1,24}')
re_key = re.compile(r'[a-z0-9_-]+(\:[a-z0-9_-]+)*')


class User(BaseModel):
    """
    User model for authentication and authorization.
    
    Represents the currently authenticated user in the API.
    Used for permission checking and tracking tag ownership.
    
    Attributes:
        user_id: The identifier of the user, or None for unauthenticated requests
    """
    user_id: Optional[str]


class ProductTag(BaseModel):
    """
    Core model representing a product property/tag in the folksonomy system.
    
    Contains a key-value pair associated with a product, along with metadata about
    the tag's ownership, versioning, and editing history.
    
    Used in tag creation, update, retrieval, and deletion operations.
    
    Attributes:
        product: The barcode of the product (digits only)
        k: The property key (must match permitted character pattern)
        v: The property value
        owner: The user_id of the owner ("" for public tags)
        version: Integer version number (starts at 1)
        editor: The user_id of the last editor
        last_edit: Timestamp of the last edit
        comment: Optional comment about the tag
    """
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
    """
    Statistics model for a product's tags/properties.
    
    Used by the /products/stats endpoint to provide a summary of tagging activity
    for each product.
    
    Attributes:
        product: The barcode of the product
        keys: Number of distinct keys/properties for this product
        editors: Number of distinct users who edited the product's tags
        last_edit: Timestamp of the most recent edit for any tag on this product
    """
    product:    str
    keys:       int
    editors:    int
    last_edit:  datetime


class ProductList(BaseModel):
    """
    Simplified product tag model used for product listings.
    
    Used by the /products endpoint to provide a list of products that have
    specific tags/properties.
    
    Attributes:
        product: The barcode of the product
        k: The property key
        v: The property value
    """
    product:    str
    k:          str
    v:          str
    
class KeyStats(BaseModel):
    """
    Statistics model for property keys.
    
    Used by the /keys endpoint to provide information about how frequently
    different keys are used across products in the folksonomy system.
    
    Attributes:
        k: The property key
        count: Number of products using this key
        values: Number of distinct values associated with this key
    """
    k: str 
    count: int  
    values: int  


class HelloResponse(BaseModel):
    """
    Response model for the root endpoint (/).
    
    Contains a welcome message to introduce users to the Folksonomy API.
    
    Attributes:
        message: A string containing the welcome message
    """
    message: str


class TokenResponse(BaseModel):
    """
    Response model for authentication endpoints (/auth and /auth_by_cookie).
    
    Represents the OAuth2 token response returned after successful authentication.
    
    Attributes:
        access_token: The bearer token to be used for authenticated requests
        token_type: The type of token
    """
    access_token: str
    token_type: str


class PingResponse(BaseModel):
    """
    Response model for the health check endpoint (/ping).
    
    Used to verify that the API server is running and can connect to the database.
    
    Attributes:
        ping: A string containing "pong" followed by the current timestamp
    """
    ping: str


class ValueCount(BaseModel):
    """
    Response model for the unique values endpoint (/values/{k}).
    
    Represents a unique value for a given property and the count of products using it.
    
    Attributes:
        v: The property value
        product_count: Number of products that use this value for the specified property
    """
    v: str
    product_count: int