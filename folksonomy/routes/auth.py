"""Authentication and current user routes."""

import asyncio
import uuid
from typing import Annotated

import aiohttp
from fastapi import APIRouter, Cookie, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from .. import db, settings
from ..models import TokenResponse
from ..utils.auth import CurrentUser, get_user_roles_from_db

router = APIRouter()


def _extract_user_roles(auth_response_data):
    """
    Extract user role information from auth server response
    """
    user_info = auth_response_data.get("user", {})
    is_admin = user_info.get("admin", 0) == 1
    is_moderator = user_info.get("moderator", 0) == 1
    is_user = (
        not is_admin and not is_moderator
    )  # true if both admin and moderator are 0
    return is_admin, is_moderator, is_user


def _get_auth_server(request: Request):
    """
    Get auth server URL from request

    We deduce it by changing part of the request base URL
    according to FOLKSONOMY_PREFIX and AUTH_PREFIX settings
    """
    # For dev purposes, we can use a static auth server with AUTH_SERVER_STATIC
    # which can be specified in local_settings.py
    if hasattr(settings, "AUTH_SERVER_STATIC") and settings.AUTH_SERVER_STATIC:
        return settings.AUTH_SERVER_STATIC
    base_url = f"{request.base_url.scheme}://{request.base_url.netloc}"
    # remove folksonomy prefix and add AUTH prefix
    base_url = base_url.replace(
        settings.FOLKSONOMY_PREFIX or "", settings.AUTH_PREFIX or ""
    )
    return base_url


@router.post("/auth", response_model=TokenResponse, tags=["Authentication"])
async def authentication(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    request: Request,
    response: Response,
):
    """
    Authentication: provide user/password and get a bearer token in return

    - **username**: Open Food Facts user_id (not email)
    - **password**: user password (clear text, but HTTPS encrypted)

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """

    user_id = form_data.username
    password = form_data.password
    token = user_id + "__U" + str(uuid.uuid4())
    auth_url = _get_auth_server(request) + "/cgi/auth.pl"
    print(auth_url)
    auth_data = {"user_id": user_id, "password": password, "body": "1"}
    async with (
        aiohttp.ClientSession() as http_session,
        http_session.post(auth_url, data=auth_data) as resp,
    ):
        status_code = resp.status
        try:
            response_data = await resp.json()
        except (aiohttp.ContentTypeError, ValueError):
            response_data = {}
    if status_code == 200:
        is_admin, is_moderator, is_user = _extract_user_roles(response_data)

        cur, _timing = await db.db_exec(
            """
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use, admin, moderator, "user")
            VALUES (%s, %s, current_timestamp AT TIME ZONE 'GMT', %s, %s, %s);
        """,
            (user_id, user_id, token, is_admin, is_moderator, is_user),
        )
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer", "x-auth-url": auth_url},
        )
    elif status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid auth server: 404",
            headers={"WWW-Authenticate": "Bearer", "x-auth-url": auth_url},
        )
    raise HTTPException(status_code=500, detail="Server error")


@router.post("/auth_by_cookie", response_model=TokenResponse, tags=["Authentication"])
async def authentication_by_cookie(
    request: Request, response: Response, session: str | None = Cookie(None)
):
    """
    Authentication: provide Open Food Facts session cookie and get a bearer token in return

    - **session cookie**: Open Food Facts session cookie

    token is returned, to be used in later requests with usual "Authorization: bearer token" headers
    """
    if not session or session == "":
        raise HTTPException(status_code=422, detail="Missing 'session' cookie")

    try:
        session_data = session.split("&")
        user_id = session_data[session_data.index("user_id") + 1]
        token = user_id + "__U" + str(uuid.uuid4())
    except (ValueError, IndexError):
        raise HTTPException(status_code=422, detail="Malformed 'session' cookie")

    auth_url = _get_auth_server(request) + "/cgi/auth.pl"
    async with (
        aiohttp.ClientSession() as http_session,
        http_session.post(
            auth_url, cookies={"session": session}, data={"body": "1"}
        ) as resp,
    ):
        auth_data = await resp.json()
        status_code = resp.status

    if status_code == 200:
        is_admin, is_moderator, is_user = _extract_user_roles(auth_data)

        cur, _timing = await db.db_exec(
            """
            DELETE FROM auth WHERE user_id = %s;
            INSERT INTO auth (user_id, token, last_use, admin, moderator, "user")
            VALUES (%s, %s, current_timestamp AT TIME ZONE 'GMT', %s, %s, %s);
            """,
            (user_id, user_id, token, is_admin, is_moderator, is_user),
        )
        if cur.rowcount == 1:
            return {"access_token": token, "token_type": "bearer"}
    elif status_code == 403:
        await asyncio.sleep(settings.FAILED_AUTH_WAIT_TIME)  # prevents brute-force
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )
    raise HTTPException(status_code=500, detail="Server error")


@router.get("/user/me")
async def get_user_info(user: CurrentUser):
    """
    Get current user roles (admin, moderator, user)
    """
    if not user or not user.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_roles = await get_user_roles_from_db(user.user_id)

    return {
        "user_id": user.user_id,
        "admin": user_roles["admin"],
        "moderator": user_roles["moderator"],
        "user": user_roles["user"],
    }
