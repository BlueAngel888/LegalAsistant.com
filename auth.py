import base64
import json
import logging
import os
import re
from threading import Lock
from functools import wraps

import jwt
from flask import g, jsonify, redirect, request, url_for

from clerk_proxy import CLERK_FAPI, CLERK_PROXY_PATH


def _frontend_api():
    key = os.environ.get("CLERK_PUBLISHABLE_KEY", "")
    try:
        encoded = key.split("_", 2)[-1]
        encoded += "=" * (-len(encoded) % 4)
        return base64.urlsafe_b64decode(encoded).decode().rstrip("$")
    except (ValueError, UnicodeDecodeError):
        return ""


CLERK_FRONTEND_API = _frontend_api()
_jwks_clients = {}
_jwks_clients_lock = Lock()


def get_clerk_proxy_host():
    forwarded = request.headers.get("X-Forwarded-Host", "")
    return forwarded.split(",", 1)[0].strip() or request.host.strip()


def publishable_key_from_host(host, fallback_key=""):
    """Python equivalent of @clerk/shared's publishableKeyFromHost."""
    if fallback_key.startswith("pk_test_"):
        return fallback_key
    hostname = re.sub(r":\d+$", "", host.lower()) if host else ""
    if not hostname:
        raise ValueError("Host must not be empty")
    encoded = base64.b64encode(f"clerk.{hostname}$".encode()).decode().rstrip("=")
    return f"pk_live_{encoded}"


def _frontend_api_from_key(key):
    try:
        encoded = key.split("_", 2)[-1]
        encoded += "=" * (-len(encoded) % 4)
        decoded = base64.b64decode(encoded).decode()
        return decoded[:-1] if decoded.endswith("$") else ""
    except (ValueError, UnicodeDecodeError):
        return ""


def _effective_auth_config():
    fallback_key = os.environ.get("CLERK_PUBLISHABLE_KEY", "")
    effective_key = publishable_key_from_host(get_clerk_proxy_host(), fallback_key)
    frontend_api = _frontend_api_from_key(effective_key)
    proxy_url = os.environ.get("CLERK_PROXY_URL", "")
    if proxy_url:
        protocol = request.headers.get("X-Forwarded-Proto", "https").split(",", 1)[0].strip()
        proxy_url = f"{protocol}://{get_clerk_proxy_host()}{CLERK_PROXY_PATH}"
    return effective_key, frontend_api, proxy_url


def _get_jwks_client(frontend_api, proxy_url):
    if not frontend_api:
        return None
    if proxy_url:
        secret_key = os.environ.get("CLERK_SECRET_KEY", "")
        if not secret_key:
            return None
        url = f"{CLERK_FAPI}/.well-known/jwks.json"
        headers = {"Clerk-Proxy-Url": proxy_url, "Clerk-Secret-Key": secret_key}
        cache_key = (url, proxy_url, secret_key)
    else:
        url = f"https://{frontend_api}/.well-known/jwks.json"
        headers = None
        cache_key = (url, "", "")
    with _jwks_clients_lock:
        if cache_key not in _jwks_clients:
            _jwks_clients[cache_key] = jwt.PyJWKClient(url, headers=headers, timeout=10)
        return _jwks_clients[cache_key]


def _verify_clerk_token(token, frontend_api, jwks_client):
    """Verify a Clerk token; split out so tests never depend on app auth patches."""
    try:
        signing_key = jwks_client.get_signing_key_from_jwt(token)
        claims = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            issuer=f"https://{frontend_api}",
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


def get_clerk_user():
    token = request.cookies.get("__session")
    if not token:
        return None

    _, frontend_api, proxy_url = _effective_auth_config()
    jwks_client = _get_jwks_client(frontend_api, proxy_url)
    if not jwks_client:
        return None
    return _verify_clerk_token(token, frontend_api, jwks_client)


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
    effective_key, frontend_api, proxy_url = _effective_auth_config()
    script_base = proxy_url or (f"https://{frontend_api}" if frontend_api else "")
    return {
        "auth_user": g.get("clerk_user"),
        "clerk_frontend_api": frontend_api,
        "clerk_publishable_key": effective_key,
        "clerk_proxy_url": proxy_url,
        "clerk_script_url": (
            f"{script_base}/npm/@clerk/clerk-js@5/dist/clerk.browser.js"
            if script_base
            else ""
        ),
    }