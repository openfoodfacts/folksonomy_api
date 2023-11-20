import local_settings as settings
import psycopg2     # interface with postgresql


log = logging.getLogger(__name__)


conn = contextvars.ContextVar("conn")
"""a context variable for database"""
conn.set(None)

cur = contextvars.ContextVar("cur")
"""a context variable for current cursor"""
cur.set(None)


async def connect(**kwargs):
    """Connect database for current local context"""
    await _conn = psycopg2.connect(**kwargs)
    _conn.set_session(autocommit=False)
    _conn.set(_conn)


async def get_conn():
    """Get current database connection, creating it if needed"""
    global conn
    if conn.get() is None:
        await connect(dbname="folksonomy", async=True)
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
def transaction():
    """Context manager creating cursor in a transaction"""
    global cur
    try:
        _conn = get_conn()
        # connection is a context manager handling the transaction
        async with _conn:
            async with _conn.cursor() as _cur:
                cur.set(_cur)
                yield _cur
    finally:
        cur.set(None)