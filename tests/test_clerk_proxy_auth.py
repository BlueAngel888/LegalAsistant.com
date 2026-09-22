import base64
from datetime import datetime, timedelta, timezone
from io import BytesIO

import jwt
import requests
from flask import Flask
from cryptography.hazmat.primitives.asymmetric import rsa
from werkzeug.test import Client
from werkzeug.wrappers import Response

import auth
from clerk_proxy import CLERK_FAPI, ClerkProxyMiddleware


class FakeRawHeaders:
    def __init__(self, headers):
        self.headers = headers

    def keys(self):
        return self.headers.keys()

    def getlist(self, name):
        value = self.headers[name]
        return value if isinstance(value, list) else [value]


class FakeUpstream:
    status_code = 200

    def __init__(self):
        self.closed = False
        self.headers = {
            "Content-Type": "application/json",
            "Transfer-Encoding": "chunked",
            "Set-Cookie": ["a=1; Path=/", "b=2; Path=/"],
        }
        self.raw = self
        self.raw.headers = FakeRawHeaders(self.headers)

    def read(self, decode_content=False):
        assert decode_content is False
        return b'{"ok":true}'

    def close(self):
        self.closed = True


class FakeSession:
    def __init__(self):
        self.call = None
        self.last_response = None

    def request(self, **kwargs):
        self.call = kwargs
        self.last_response = FakeUpstream()
        return self.last_response


def test_proxy_preserves_request_and_sets_canonical_headers(monkeypatch):
    monkeypatch.setenv("CLERK_PROXY_URL", "deployment-value")
    monkeypatch.setenv("CLERK_SECRET_KEY", "secret")
    session = FakeSession()
    app = ClerkProxyMiddleware(lambda e, s: (), transport=session)
    client = Client(app, Response)

    response = client.post(
        "/api/__clerk/v1/client?a=one%20two",
        data=b"raw-body",
        content_type="application/octet-stream",
        headers={
            "X-Forwarded-Host": "legalasistant.com, internal.example",
            "X-Forwarded-Proto": "https",
            "X-Forwarded-For": "203.0.113.4, 10.0.0.1",
        },
    )

    assert response.status_code == 200
    assert session.call["url"] == f"{CLERK_FAPI}/v1/client?a=one%20two"
    assert session.call["method"] == "POST"
    assert session.call["data"] == b"raw-body"
    assert session.call["headers"]["Clerk-Proxy-Url"] == "https://legalasistant.com/api/__clerk"
    assert session.call["headers"]["Clerk-Secret-Key"] == "secret"
    assert session.call["headers"]["X-Forwarded-For"] == "203.0.113.4"
    assert response.headers.getlist("Set-Cookie") == ["a=1; Path=/", "b=2; Path=/"]
    assert response.headers["Content-Length"] == str(len(b'{"ok":true}'))
    assert "Transfer-Encoding" not in response.headers
    assert session.last_response.closed is True


def test_default_transport_has_no_shared_cookie_jar(monkeypatch):
    monkeypatch.setenv("CLERK_PROXY_URL", "/api/__clerk")
    monkeypatch.setenv("CLERK_SECRET_KEY", "sk_test_simulated")
    calls = []

    def request(**kwargs):
        calls.append(kwargs)
        return FakeUpstream()

    monkeypatch.setattr(requests, "request", request)
    middleware = ClerkProxyMiddleware(lambda e, s: ())
    assert middleware.transport is requests
    client = Client(middleware, Response)
    client.get("/api/__clerk/v1/client")
    client.get("/api/__clerk/v1/environment")
    assert len(calls) == 2
    assert all("Cookie" not in call["headers"] for call in calls)


def test_get_without_content_length_does_not_read_to_eof(monkeypatch):
    monkeypatch.setenv("CLERK_PROXY_URL", "deployment-value")
    monkeypatch.setenv("CLERK_SECRET_KEY", "secret")
    session = FakeSession()
    app = ClerkProxyMiddleware(lambda e, s: (), transport=session)

    class NeverReadToEof(BytesIO):
        def read(self, size=-1):
            if size == -1:
                raise AssertionError("attempted an unbounded socket read")
            return super().read(size)

    client = Client(app, Response)
    response = client.get(
        "/api/__clerk/v1/environment",
        environ_overrides={"wsgi.input": NeverReadToEof(b""), "CONTENT_LENGTH": ""},
    )
    assert response.status_code == 200
    assert session.call["data"] == b""


def test_publishable_key_from_host_matches_clerk_shared():
    key = auth.publishable_key_from_host("LegalAsistant.COM:443", "pk_live_ignored")
    encoded = base64.b64encode(b"clerk.legalasistant.com$").decode().rstrip("=")
    assert key == f"pk_live_{encoded}"
    assert auth.publishable_key_from_host("localhost", "pk_test_original") == "pk_test_original"


def test_template_context_uses_effective_host_and_proxy(monkeypatch):
    monkeypatch.setenv("CLERK_PROXY_URL", "deployment-value")
    monkeypatch.setenv("CLERK_PUBLISHABLE_KEY", "pk_live_ignored")
    app = Flask(__name__)
    with app.test_request_context(
        "/", headers={"X-Forwarded-Host": "legalasistant.com", "X-Forwarded-Proto": "https"}
    ):
        context = auth.clerk_template_context()

    assert context["clerk_proxy_url"] == "https://legalasistant.com/api/__clerk"
    assert context["clerk_script_url"].startswith(
        "https://legalasistant.com/api/__clerk/npm/@clerk/"
    )
    assert context["clerk_frontend_api"] == "clerk.legalasistant.com"


def test_jwks_client_uses_fixed_upstream_and_canonical_headers(monkeypatch):
    captured = {}
    monkeypatch.setenv("CLERK_SECRET_KEY", "secret")

    class FakeJWKClient:
        def __init__(self, url, **kwargs):
            captured.update(url=url, **kwargs)

    monkeypatch.setattr(auth.jwt, "PyJWKClient", FakeJWKClient)
    auth._jwks_clients.clear()
    auth._get_jwks_client("clerk.legalasistant.com", "https://legalasistant.com/api/__clerk")
    assert captured["url"] == f"{CLERK_FAPI}/.well-known/jwks.json"
    assert captured["headers"]["Clerk-Proxy-Url"] == "https://legalasistant.com/api/__clerk"
    assert "Clerk-Secret-Key" in captured["headers"]


def test_local_jwt_verification_checks_signature_issuer_and_expiry():
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key = private_key.public_key()
    frontend_api = "clerk.legalasistant.com"

    class LocalJWKClient:
        def get_signing_key_from_jwt(self, token):
            return type("SigningKey", (), {"key": public_key})()

    now = datetime.now(timezone.utc)

    def token(**overrides):
        claims = {
            "sub": "user_123",
            "sid": "sess_123",
            "iss": f"https://{frontend_api}",
            "iat": now,
            "exp": now + timedelta(minutes=5),
        }
        claims.update(overrides)
        return jwt.encode(claims, private_key, algorithm="RS256")

    valid = auth._verify_clerk_token(token(), frontend_api, LocalJWKClient())
    assert valid["id"] == "user_123"
    assert valid["session_id"] == "sess_123"
    assert auth._verify_clerk_token(
        token(iss="https://clerk.wrong.example"), frontend_api, LocalJWKClient()
    ) is None
    assert auth._verify_clerk_token(
        token(exp=now - timedelta(seconds=1)), frontend_api, LocalJWKClient()
    ) is None