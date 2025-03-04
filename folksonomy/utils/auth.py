from fastapi import Depends, HTTPException, status

from folksonomy import db
from ..models import User
from fastapi.security import OAuth2PasswordBearer


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Get current user and check token validity if present
    """
    if token and '__U' in token:
        cur = db.cursor()
        await cur.execute(
            "UPDATE auth SET last_use = current_timestamp AT TIME ZONE 'GMT' WHERE token = %s", (
                token,)
        )
        if cur.rowcount == 1:
            return User(user_id=token.split('__U', 1)[0])
        else:
            return User(user_id=None)


def check_owner_user(user: User, owner, allow_anonymous=False):
    """
    Check authentication depending on current user and 'owner' of the data
    """
    user = user.user_id if user is not None else None
    if user is None and allow_anonymous == False:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if owner != '':
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Authentication required for '%s'" % owner,
                headers={"WWW-Authenticate": "Bearer"},
            )
        if owner != user:
            raise HTTPException(
                status_code=422,
                detail="owner should be '%s' or '' for public, but '%s' is authenticated" % (
                    owner, user),
            )
    return
