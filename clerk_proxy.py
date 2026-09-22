"""WSGI proxy for Clerk's production Frontend API."""

import logging
import os
from urllib.parse import quote

import requests
from urllib3.exceptions import HTTPError as Urllib3HTTPError
from werkzeug.wsgi import get_input_stream
from werkzeug.wrappers import Response


CLERK_FAPI = "https://frontend-api.clerk.dev"
CLERK_PROXY_PATH = "/api/__clerk"
_HOP_BY_HOP = {
    "connection",
    "keep-alive",
    "proxy-authenticate",
    "proxy-authorization",
    "te",
    "trailer",
    "transfer-encoding",
    "upgrade",
}


def _first_header(value):
    return value.split(",", 1)[0].strip() if value else ""


def get_clerk_proxy_host_from_environ(environ):
    """Return the original, public host (the leftmost forwarded host)."""
    return (
        _first_header(environ.get("HTTP_X_FORWARDED_HOST", ""))
        or environ.get("HTTP_HOST", "").strip()
        or environ.get("SERVER_NAME", "").strip()
    )


def get_clerk_proxy_url_from_environ(environ):
    protocol = _first_header(environ.get("HTTP_X_FORWARDED_PROTO", "")) or "https"
    return f"{protocol}://{get_clerk_proxy_host_from_environ(environ)}{CLERK_PROXY_PATH}"


def _request_headers(environ, secret_key):
    headers = {}
    for key, value in environ.items():
        if not key.startswith("HTTP_"):
            continue
        name = key[5:].replace("_", "-")
        if name.lower() not in _HOP_BY_HOP and name.lower() != "host":
            headers[name] = value
    if environ.get("CONTENT_TYPE"):
        headers["Content-Type"] = environ["CONTENT_TYPE"]

    headers["Clerk-Proxy-Url"] = get_clerk_proxy_url_from_environ(environ)
    headers["Clerk-Secret-Key"] = secret_key
    client_ip = (
        _first_header(environ.get("HTTP_X_FORWARDED_FOR", ""))
        or environ.get("REMOTE_ADDR", "")
    )
    if client_ip:
        headers["X-Forwarded-For"] = client_ip
    return headers


def _raw_proxy_suffix(environ):
    raw_uri = environ.get("RAW_URI") or environ.get("REQUEST_URI")
    if raw_uri:
        raw_path = raw_uri.split("?", 1)[0]
    else:
        raw_path = quote(environ.get("PATH_INFO", ""), safe="/:@!$&'()*+,;=-._~%")
    suffix = raw_path[len(CLERK_PROXY_PATH):] or "/"
    query = environ.get("QUERY_STRING", "")
    return f"{suffix}?{query}" if query else suffix


def _response_headers(upstream, status, body_length, method):
    headers = []
    raw_headers = upstream.raw.headers
    for name in raw_headers.keys():
        lower = name.lower()
        if lower in _HOP_BY_HOP or lower == "set-cookie":
            continue
        if lower == "content-length":
            if method == "HEAD" or status == 304:
                headers.extend((name, value) for value in raw_headers.getlist(name))
            continue
        for value in raw_headers.getlist(name):
            headers.append((name, value))
    for cookie in raw_headers.getlist("Set-Cookie"):
        headers.append(("Set-Cookie", cookie))
    if method != "HEAD" and status >= 200 and status not in {204, 304}:
        headers.append(("Content-Length", str(body_length)))
    return headers


class ClerkProxyMiddleware:
    """Intercept Clerk's proxy path before Flask parses or authenticates it."""

    def __init__(self, app, transport=None):
        self.app = app
        # The module-level request function has no cookie jar. A shared Session
        # would persist one visitor's Clerk cookies into another visitor's call.
        self.transport = transport or requests

    def __call__(self, environ, start_response):
        path = environ.get("PATH_INFO", "")
        if not (path == CLERK_PROXY_PATH or path.startswith(CLERK_PROXY_PATH + "/")):
            return self.app(environ, start_response)

        secret_key = os.environ.get("CLERK_SECRET_KEY", "")
        if not os.environ.get("CLERK_PROXY_URL") or not secret_key:
            return self.app(environ, start_response)

        # Werkzeug returns an empty safe stream when neither Content-Length nor
        # wsgi.input_terminated is present, instead of reading to EOF and
        # hanging a normal GET on a live WSGI socket.
        body = get_input_stream(environ, safe_fallback=True).read()

        upstream = None
        try:
            upstream = self.transport.request(
                method=environ.get("REQUEST_METHOD", "GET"),
                url=CLERK_FAPI + _raw_proxy_suffix(environ),
                headers=_request_headers(environ, secret_key),
                data=body,
                allow_redirects=False,
                stream=True,
                timeout=(5, 30),
            )
            response_body = upstream.raw.read(decode_content=False)
            status = upstream.status_code
            headers = _response_headers(
                upstream, status, len(response_body), environ.get("REQUEST_METHOD", "GET")
            )
            response = Response(response_body, status=status, headers=headers, direct_passthrough=True)
            return response(environ, start_response)
        except (requests.RequestException, Urllib3HTTPError, OSError) as exc:
            logging.warning("Clerk Frontend API proxy request failed: %s", type(exc).__name__)
            response = Response(b"", status=502, headers={"Content-Length": "0"})
            return response(environ, start_response)
        finally:
            if upstream is not None:
                upstream.close()


def install_clerk_proxy(app):
    """Install the proxy only when the deployment-provided URL is present."""
    if os.environ.get("CLERK_PROXY_URL"):
        app.wsgi_app = ClerkProxyMiddleware(app.wsgi_app)
