import asyncio
import contextlib
import contextvars
import logging
import time
import weakref

import aiopg  # interface with postgresql

# import psycopg2     # interface with postgresql
from . import models, settings

log = logging.getLogger(__name__)

conn = weakref.WeakKeyDictionary()
"""associate each event_loop with a connection pool"""

cur = contextvars.ContextVar("cur")
"""a context variable for current cursor"""
cur.set(None)


class NotInTransactionError(Exception):
    """Trying to get cursor outside of a transaction context manager"""


class NotInAsyncIOError(Exception):
    """Trying to use connection outside of asyncio context"""


async def get_conn():
    """Get current database connection, creating it if needed"""
    global conn
    loop = asyncio.get_running_loop()
    if loop is None:
        raise NotInAsyncIOError("This method only works with asyncio")
    _conn = conn.get(loop)
    if _conn is None:
        _conn = await aiopg.create_pool(
            dbname=settings.POSTGRES_DATABASE,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            port=settings.POSTGRES_PORT,
            async_=True,
        )
        conn[loop] = _conn
    return _conn


def cursor():
    """Return current cursor to run SQL"""
    global cur
    if cur.get() is None:
        raise NotInTransactionError("You must be in a transaction to use cursor")
    return cur.get()


async def terminate():
    """Close all database connection"""
    global conn
    loop = asyncio.get_running_loop()
    _conn = conn.get(loop)
    if _conn is not None:
        _conn.terminate()
        del conn[loop]


@contextlib.asynccontextmanager
async def transaction():
    """Context manager creating cursor in a transaction"""
    global cur
    global conn
    try:
        _pool = await get_conn()
        async with _pool.acquire() as _conn:
            async with _conn.cursor() as _cur:
                # begin returns a context manager handling the transaction with rollback on error
                async with _cur.begin():
                    cur.set(_cur)
                    yield _cur
    finally:
        cur.set(None)


async def db_exec(query, params=()):
    """
    Execute postgresql query and collect timing
    """
    t = time.monotonic()
    cur = cursor()
    await cur.execute(query, params)
    return cur, str(round(time.monotonic() - t, 4) * 1000) + "ms"


def create_product_tag_req(product_tag: models.ProductTag):
    """Request and params to create a product tag in database"""
    return (
        """
        INSERT INTO folksonomy (product,k,v,owner,version,editor,comment)
            VALUES (%s,%s,%s,%s,%s,%s,%s)
        """,
        (
            product_tag.product,
            product_tag.k.lower(),
            product_tag.v,
            product_tag.owner,
            product_tag.version,
            product_tag.editor,
            product_tag.comment,
        ),
    )


def update_product_tag_req(product_tag: models.ProductTag):
    """Request and params to update a product tag in database"""
    return (
        """
        UPDATE folksonomy SET v = %s, version = %s, editor = %s, comment = %s
            WHERE product = %s AND owner = %s AND k = %s
        """,
        (
            product_tag.v,
            product_tag.version,
            product_tag.editor,
            product_tag.comment,
            product_tag.product,
            product_tag.owner,
            product_tag.k.lower(),
        ),
    )
