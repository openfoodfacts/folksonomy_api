#! /usr/bin/python3

from fastapi import Query, Request, HTTPException, Depends
import contextlib
import os
import logging
from logging.handlers import RotatingFileHandler
from .dependencies import *
from . import db
from . import settings
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Optional
import aiohttp
import uuid
import asyncio
from fastapi.security import OAuth2PasswordBearer
from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
import re
import psycopg2

description = """
Folksonomy Engine API allows you to add free property/value pairs to Open Food Facts products.
[Previous docstring continues...]
"""

# [Previous app setup code remains unchanged until middleware]

@app.middleware("http")
async def initialize_transactions(request: Request, call_next):
    """middleware that enclose request processing in a transaction"""
    async with db.transaction():
        response = await call_next(request)
        return response

# ====== CACHE CONTROL MIDDLEWARE ADDITION ======
@app.middleware("http")
async def add_cache_control(request: Request, call_next):
    """Dynamically set Cache-Control headers based on endpoint"""
    response = await call_next(request)
    
    if request.url.path.startswith(("/tags", "/product", "/values")):
        response.headers["Cache-Control"] = "no-store, max-age=0"
    elif request.url.path in ("/keys", "/products"):
        response.headers["Cache-Control"] = "public, max-age=300"
    
    return response

# [All existing routes remain unchanged until before /ping]

# ====== NEW TAGS ENDPOINTS ======
@app.delete("/tags/{tag_id}", response_model=dict)
async def delete_tag(
    tag_id: int,
    user: User = Depends(get_current_user),
    owner: str = ""
):
    """
    Delete a tag by ID.
    - tag_id: ID of the tag to delete
    - owner: Owner of the tag (empty for public tags)
    """
    check_owner_user(user, owner, allow_anonymous=False)
    
    try:
        cur, timing = await db.db_exec(
            "DELETE FROM folksonomy WHERE id = %s AND owner = %s RETURNING id",
            (tag_id, owner)
        )
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Tag not found")
        return {"message": f"Tag {tag_id} deleted"}
    except psycopg2.Error as e:
        raise HTTPException(status_code=422, detail=str(e))

@app.get("/tags/search", response_model=List[dict])
async def search_tags(
    q: str = "",
    owner: str = "",
    user: User = Depends(get_current_user),
    limit: int = 50
):
    """
    Search tags by keyword.
    - q: Search term (e.g. "plastic")
    - owner: Filter by owner
    - limit: Max results (default 50)
    """
    check_owner_user(user, owner, allow_anonymous=True)
    search_term = f"%{q}%"
    
    cur, timing = await db.db_exec(
        """
        SELECT json_agg(json_build_object(
            'id', id,
            'k', k,
            'v', v
        ))
        FROM folksonomy
        WHERE owner = %s AND (k ILIKE %s OR v ILIKE %s)
        LIMIT %s
        """,
        (owner, search_term, search_term, limit)
    )
    result = await cur.fetchone()
    return result[0] or []

# [Keep existing /ping endpoint at the very end]
@app.get("/ping", response_model=PingResponse)
async def pong(response: Response):
    """Check server health"""
    cur, timing = await db.db_exec("SELECT current_timestamp AT TIME ZONE 'GMT'",())
    pong = await cur.fetchone()
    return {"ping": "pong @ %s" % pong[0]}
