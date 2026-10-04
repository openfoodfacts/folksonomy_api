"""Shared authentication and authorization dependencies."""

from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer

from .. import db
from ..models import User

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)


async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user and check token validity if present
    """
    if token and "__U" in token:
        cur = db.cursor()
        await cur.execute(
            "UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s",
            (token,),
        )
        if cur.rowcount == 1:
            return User(user_id=token.split("__U", 1)[0])
        else:
            return User(user_id=None)


CurrentUser = Annotated[User, Depends(get_current_user)]


def check_owner_user(user: User, owner, allow_anonymous=False):
    """
    Check authentication depending on current user and 'owner' of the data
    """
    user = user.user_id if user is not None else None
    if user is None and not allow_anonymous:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if owner != "":
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Authentication required for '{owner}'",
                headers={"WWW-Authenticate": "Bearer"},
            )
        if owner != user:
            raise HTTPException(
                status_code=422,
                detail=f"owner should be '{owner}' or '' for public, but '{user}' is authenticated",
            )


async def get_user_roles_from_db(user_id: str):
    """
    Get user roles from the auth table
    """
    cur, _timing = await db.db_exec(
        'SELECT admin, moderator, "user" FROM auth WHERE user_id = %s', (user_id,)
    )
    result = await cur.fetchone()
    if not result:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User roles not found"
        )
    return {"admin": result[0], "moderator": result[1], "user": result[2]}


async def check_moderator_permission(user: User):
    """
    Check if the user has moderator or admin permissions
    """
    if not user or not user.user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user_roles = await get_user_roles_from_db(user.user_id)
    if not (user_roles["admin"] or user_roles["moderator"]):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Moderator or admin privileges required",
        )
    return True
