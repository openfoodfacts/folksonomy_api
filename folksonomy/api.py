#! /usr/bin/python3

import contextlib
import os
import logging
from logging.handlers import RotatingFileHandler

from folksonomy.routes import auth, product, stats
from .dependencies import *
from . import db
from fastapi.middleware.cors import CORSMiddleware


description = """
Folksonomy Engine API allows you to add free property/value pairs to Open Food Facts products.

The API use the main following variables:
* **product**: the product number
* **k**: "key", meaning the property or tag
* **v**: "value", the value for a related key

## See also

* [Project page](https://wiki.openfoodfacts.org/Folksonomy_Engine)
* [Folksonomy Engine github repository](https://github.com/openfoodfacts/folksonomy_engine)
* [Documented properties](https://wiki.openfoodfacts.org/Folksonomy/Property)
"""

# Setup FastAPI app lifespan
@contextlib.asynccontextmanager
async def app_lifespan(app: FastAPI):
    async with app_logging():
        try:
            yield
        finally:
            await db.terminate()

app = FastAPI(title="Open Food Facts folksonomy REST API",
    description=description, lifespan=app_lifespan)

# Allow anyone to call the API from their own apps
app.add_middleware(
    CORSMiddleware,
    # FastAPI doc related to allow_origin (to avoid CORS issues):
    # "It's also possible to declare the list as "*" (a "wildcard") to say that all are allowed.
    # But that will only allow certain types of communication, excluding everything that involves
    # credentials: Cookies, Authorization headers like those used with Bearer Tokens, etc.
    # So, for everything to work correctly, it's better to specify explicitly the allowed origins."
    # => Workarround: use allow_origin_regex
    # Source: https://github.com/tiangolo/fastapi/issues/133#issuecomment-646985050
    allow_origin_regex='https?://.*',
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)

# define route for authentication
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


@contextlib.asynccontextmanager
async def app_logging():
    logger = logging.getLogger("uvicorn.access")
    handler = logging.handlers.RotatingFileHandler("api.log",mode="a",maxBytes = 100*1024, backupCount = 3)
    handler.setFormatter(logging.Formatter("%(asctime)s - %(levelname)s - %(message)s"))
    logger.addHandler(handler)
    yield

@app.middleware("http")
async def initialize_transactions(request: Request, call_next):
    """middleware that enclose request processing in a transaction"""
    # eventually log user
    async with db.transaction():
        response = await call_next(request)
        return response


@app.get("/", status_code=status.HTTP_200_OK)
async def hello():
    return {"message": "Hello folksonomy World! Tip: open /docs for documentation"}


# Add routers
app.include_router(auth.router)
app.include_router(stats.router)
app.include_router(product.router)


@app.get("/ping")
async def pong(response: Response):
    """
    Check server health
    """
    cur, timing = await db.db_exec("SELECT current_timestamp AT TIME ZONE 'GMT'", ())
    pong = await cur.fetchone()
    return {"ping": "pong @ %s" % pong[0]}
