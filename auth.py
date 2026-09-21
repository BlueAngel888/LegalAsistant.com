import base64
import json
import logging
import os
from functools import wraps

import jwt
from flask import g, jsonify, redirect, request, url_for


def _frontend_api():
    key = os.environ.get("CLERK_PUBLISHABLE_KEY", "")
    try:
        encoded = key.split("_", 2)[-1]
        encoded += "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded).decode().rstrip("$")
    except (ValueError, UnicodeDecodeError):
        return ""


CLERK_FRONTEND_API = _frontend_api()
_jwks_client = (
    jwt.PyJWKClient(f"https://{CLERK_FRONTEND_API}/.well-known/jwks.json")
    if CLERK_FRONTEND_API
    else None
)


def get_clerk_user():
    token = request.cookies.get("__session")
    if not token or not _jwks_client:
        return None

    try:
        signing_key = _jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            options={"verify_aud": False},
        )
        return {
            "id": claims["sub"],
            "session_id": claims.get("sid"),
            "email": claims.get("email"),
        }
    except (jwt.PyJWTError, KeyError, ValueError) as exc:
        logging.info("Clerk session verification failed: %s", exc)
        return None


def load_auth_context():
    g.clerk_user = get_clerk_user()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if g.get("clerk_user"):
            return view(*args, **kwargs)

        if request.is_json or request.path.startswith("/legal-chat"):
            return jsonify({"error": "Authentication required"}), 401

        next_url = request.full_path if request.query_string else request.path
        return redirect(url_for("sign_in", next=next_url))

    return wrapped


def clerk_template_context():
    return {
        "auth_user": g.get("clerk_user"),
        "clerk_frontend_api": CLERK_FRONTEND_API,
        "clerk_publishable_key": os.environ.get("CLERK_PUBLISHABLE_KEY", ""),
        "clerk_proxy_url": os.environ.get("CLERK_PROXY_URL", ""),
    }