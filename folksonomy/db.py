import contextlib
import contextvars
import logging


import aiopg # interface with postgresql

# import psycopg2     # interface with postgresql

from . import settings


log = logging.getLogger(__name__)


conn = contextvars.ContextVar("conn")
"""a context variable for database"""
conn.set(None)

cur = contextvars.ContextVar("cur")
"""a context variable for current cursor"""
cur.set(None)


async def connect(**kwargs):
    """Connect database for current local context"""
    global conn
    _conn = await aiopg.create_pool(**kwargs)
    conn.set(_conn)


async def get_conn():
    """Get current database connection, creating it if needed"""
    global conn
    if conn.get() is None:
        await connect(
            dbname=settings.POSTGRES_DATABASE,
            user=settings.POSTGRES_USER,
            password=settings.POSTGRES_PASSWORD,
            host=settings.POSTGRES_HOST,
            async_=True
        )
    return conn.get()


async def cursor():
    """Return current cursor to run SQL"""
    global cur
    if cur.get() is None:
        raise Exception("You must be in a transaction to use cursor")
    return cur.get()


async def close():
    """Close database connection"""
    global conn
    _conn = conn.get()
    if _conn is not Note:
        _conn.close()
        conn.set(None)


@contextlib.asynccontextmanager
async def transaction_ctx(cur):
    """A function handling transaction init / rollback or commit"""
    try:
        yield cur
    except Exception as e:
        await cur.rollback()
        #await conn.execute("ROLLBACK;")
    else:
        await cur.commit()
        #await cur.execute("COMMIT;")


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