from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.responses import JSONResponse
from typing import Optional
from fastapi.security import OAuth2PasswordBearer
import uuid
import asyncio
import aiohttp
from fastapi import Cookie
from folksonomy import db, settings

router = APIRouter()

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


def get_auth_server(request: Request):
    """
    Get auth server URL from request

    We deduce it by changing part of the request base URL
    according to FOLKSONOMY_PREFIX and AUTH_PREFIX settings
    """
    # For dev purposes, we can use a static auth server with AUTH_SERVER_STATIC
    # which can be specified in local_settings.py
    if hasattr(settings, 'AUTH_SERVER_STATIC') and settings.AUTH_SERVER_STATIC:
        return settings.AUTH_SERVER_STATIC
    base_url = f"{request.base_url.scheme}://{request.base_url.netloc}"
    # remove folksonomy prefix and add AUTH prefix
    base_url = base_url.replace(
        settings.FOLKSONOMY_PREFIX or "", settings.AUTH_PREFIX or "")
    return base_url


@router.post("/auth")
async def authentication(request: Request, response: Response, form_data: OAuth2PasswordRequestForm = Depends()):
    """
    Authentication: provide user/password and get a bearer token in return

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    user_id = form_data.username
    password = form_data.password
    token = user_id+'__U'+str(uuid.uuid4())
    auth_url = get_auth_server(request) + "/cgi/auth.pl"
    auth_data = {'user_id': user_id, 'password': password}
    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(auth_url, data=auth_data) as resp:
            status_code = resp.status
    if status_code == 200:
        cur, timing = await db.db_exec("""
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
        """, (user_id, user_id, token))
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        # prevents brute-force
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={
                "WWW-Authenticate": "Bearer",
                "x-auth-url": auth_url
            },
        )
    elif status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth server: 404",
            headers={
                "WWW-Authenticate": "Bearer",
                "x-auth-url": auth_url
            },
        )
    raise HTTPException(
        status_code=500, detail="Server error")


@router.post("/auth_by_cookie")
async def authentication(request: Request, response: Response, session: Optional[str] = Cookie(None)):
    """
    Authentication: provide Open Food Facts session cookie and get a bearer token in return

    - **session cookie**: Open Food Facts session cookie

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """
    if not session or session == '':
        raise HTTPException(
            status_code=422, detail="Missing 'session' cookie")

    try:
        session_data = session.split('&')
        user_id = session_data[session_data.index('user_id') + 1]
        token = user_id + '__U' + str(uuid.uuid4())
    except:
        raise HTTPException(
            status_code=422, detail="Malformed 'session' cookie")

    auth_url = get_auth_server(request) + "/cgi/auth.pl"
    async with aiohttp.ClientSession() as http_session:
        async with http_session.post(auth_url, cookies={'session': session}) as resp:
            status_code = resp.status

    if status_code == 200:
        cur, timing = await db.db_exec(
            """
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use) VALUES (%s,%s,current_timestamp AT TIME ZONE 'GMT');
            """,
            (user_id, user_id, token)
        )
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        # prevents brute-force
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(
        status_code=500, detail="Server error")
