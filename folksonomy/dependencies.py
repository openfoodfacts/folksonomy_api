import asyncio
import json
import time
import re
import uuid
from datetime import datetime
from typing import List, Optional
import psycopg2     # interface with postgresql
import aiohttp     # async requests to call OFF for login/password check

# FastAPI
from fastapi import FastAPI, status, Request, Response, Depends, Header, HTTPException, Cookie
from fastapi.responses import JSONResponse
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm

# pydantic: define data schema
from pydantic import BaseModel, ValidationError, validator

# folksonomy imports
from .models import ProductTag, ProductStats, User, ProductList, KeyStats, StatusResponse

