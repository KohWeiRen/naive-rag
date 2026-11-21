from authlib.integrations.starlette_client import OAuth, OAuthError
from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import RedirectResponse
from starlette.concurrency import run_in_threadpool

from backend.database.db import get_or_create_google_user
from backend.helper import retrieve_val_from_env

router= APIRouter()
oauth = OAuth()

oauth.register(name="google",
               client_id=retrieve_val_from_env("GOOGLE_CLIENT_ID", ""),
               client_secret=retrieve_val_from_env("GOOGLE_CLIENT_SECRET", ""),
               server_metadata_url="https://accounts.google.com/.well-known/openid-configuration",
               client_kwargs={"scope": "openid email"}
              )

@router.get("/login")
async def login(request: Request):
    callback_url = request.url_for("google_callback")
    return await oauth.google.authorize_redirect(request, callback_url)

@router.get("/auth/callback")
async def google_callback(request: Request):
    try:
        token = await oauth.google.authorize_access_token(request)
    except OAuthError:
        raise HTTPException(400, "Google sign in could not be completed.") from None
    
    google_sub = (token.get("userinfo") or {}).get("sub")
    if not google_sub:
        raise HTTPException(400, "Google did not return a verified account ID.")
    
    user_id = await run_in_threadpool(get_or_create_google_user, google_sub)
    request.session.clear()
    request.session["user_id"] = str(user_id)
    return RedirectResponse("/", status_code=303)

@router.get("/me")
def me(request: Request):
    user_id = request.session.get("user_id")
    if user_id is None:
        raise HTTPException(401, "Sign in first.")
    return {"user_id": user_id}

