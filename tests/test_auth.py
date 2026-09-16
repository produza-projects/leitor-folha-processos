from __future__ import annotations

import time
import base64
import json
from urllib.parse import parse_qs, urlparse
from unittest.mock import patch

import pytest
import httpx
from fastapi import HTTPException
from joserfc import jwt
from joserfc.jwk import RSAKey
from itsdangerous import TimestampSigner

from backend.auth import OIDCClient, OIDCSettings
from backend.main import create_app


def oidc_settings(**overrides) -> OIDCSettings:
    values = {
        "enabled": True,
        "public_issuer": "https://auth-dev.produza.ind.br/realms/produza-dev",
        "internal_issuer": "http://keycloak:8080/realms/produza-dev",
        "client_id": "leitor-folha-processos",
        "client_secret": "client-secret",
        "session_secret": "a" * 64,
        "redirect_uri": "https://fp-dev.produza.ind.br/auth/callback",
        "post_logout_redirect_uri": "https://fp-dev.produza.ind.br/",
        "required_role": "viewer",
        "session_max_age": 43200,
        "cookie_secure": True,
    }
    values.update(overrides)
    return OIDCSettings(**values)


class FakeResponse:
    def __init__(self, payload):
        self.payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self.payload


class FakeHTTPClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        return None

    async def post(self, *args, **kwargs):
        assert kwargs["auth"] == ("leitor-folha-processos", "client-secret")
        assert kwargs["data"]["code_verifier"]
        return FakeResponse({"id_token": "id-token", "access_token": "access-token"})

    async def get(self, *args, **kwargs):
        return FakeResponse({"keys": []})


def test_enabled_settings_reject_short_session_secret():
    settings = oidc_settings(session_secret="short")
    with pytest.raises(ValueError, match="at least 32"):
        settings.validate()


def test_token_validation_requires_rs256_signature_and_expiration():
    oidc = OIDCClient(oidc_settings())
    private_key = RSAKey.generate_key(auto_kid=True)
    jwks = {"keys": [private_key.as_dict()]}
    claims = {"sub": "user-123", "exp": int(time.time()) + 300}
    token = jwt.encode({"alg": "RS256", "kid": private_key.kid}, claims, private_key)

    assert oidc._decode_token(token, jwks)["sub"] == "user-123"

    token_without_exp = jwt.encode(
        {"alg": "RS256", "kid": private_key.kid},
        {"sub": "user-123"},
        private_key,
    )
    with pytest.raises(HTTPException):
        oidc._decode_token(token_without_exp, jwks)


@pytest.fixture
def anyio_backend():
    return "asyncio"


def application_client(application):
    return httpx.AsyncClient(
        transport=httpx.ASGITransport(app=application),
        base_url="https://fp-dev.produza.ind.br",
    )


@pytest.mark.anyio
async def test_health_is_public_and_root_starts_login():
    settings = oidc_settings()
    async with application_client(create_app(settings)) as client:
        assert (await client.get("/healthz")).status_code == 200
        response = await client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


@pytest.mark.anyio
async def test_login_uses_authorization_code_pkce_and_sanitizes_return_path():
    settings = oidc_settings()
    async with application_client(create_app(settings)) as client:
        response = await client.get(
            "/login?return_to=//attacker.example", follow_redirects=False
        )
    assert response.status_code == 302
    location = urlparse(response.headers["location"])
    query = parse_qs(location.query)
    assert f"{location.scheme}://{location.netloc}{location.path}" == (
        "https://auth-dev.produza.ind.br/realms/produza-dev/protocol/openid-connect/auth"
    )
    assert query["response_type"] == ["code"]
    assert query["code_challenge_method"] == ["S256"]
    assert query["redirect_uri"] == ["https://fp-dev.produza.ind.br/auth/callback"]
    assert query["state"][0]
    assert query["nonce"][0]
    assert query["code_challenge"][0]
    cookie = response.headers["set-cookie"].lower()
    assert "httponly" in cookie
    assert "secure" in cookie


@pytest.mark.anyio
async def test_callback_creates_minimal_session_for_viewer():
    settings = oidc_settings()
    oidc = OIDCClient(settings)
    app = create_app(settings, oidc)
    async with application_client(app) as client:
        login = await client.get("/login?return_to=/", follow_redirects=False)
        state = parse_qs(urlparse(login.headers["location"]).query)["state"][0]
        id_claims = {
            "iss": settings.public_issuer,
            "aud": settings.client_id,
            "sub": "user-123",
            "nonce": parse_qs(urlparse(login.headers["location"]).query)["nonce"][0],
            "preferred_username": "usuario.teste",
            "name": "Usuário Teste",
        }
        access_claims = {
            "iss": settings.public_issuer,
            "azp": settings.client_id,
            "resource_access": {settings.client_id: {"roles": ["viewer"]}},
        }

        with (
            patch("backend.auth.httpx.AsyncClient", FakeHTTPClient),
            patch.object(oidc, "_decode_token", side_effect=[id_claims, access_claims]),
        ):
            response = await client.get(
                f"/auth/callback?code=code-123&state={state}",
                follow_redirects=False,
            )

        me = await client.get("/api/me")

    assert response.status_code == 302
    assert response.headers["location"] == "/"
    assert "Max-Age=43200" in response.headers["set-cookie"]
    assert me.status_code == 200
    assert me.json() == {
        "sub": "user-123",
        "preferred_username": "usuario.teste",
        "name": "Usuário Teste",
        "email": "",
        "roles": ["viewer"],
    }


@pytest.mark.anyio
async def test_callback_rejects_user_without_viewer_role():
    settings = oidc_settings()
    oidc = OIDCClient(settings)
    async with application_client(create_app(settings, oidc)) as client:
        login = await client.get("/login", follow_redirects=False)
        query = parse_qs(urlparse(login.headers["location"]).query)
        id_claims = {
            "iss": settings.public_issuer,
            "aud": settings.client_id,
            "sub": "user-123",
            "nonce": query["nonce"][0],
        }
        access_claims = {
            "iss": settings.public_issuer,
            "azp": settings.client_id,
            "resource_access": {settings.client_id: {"roles": []}},
        }

        with (
            patch("backend.auth.httpx.AsyncClient", FakeHTTPClient),
            patch.object(oidc, "_decode_token", side_effect=[id_claims, access_claims]),
        ):
            response = await client.get(
                f"/auth/callback?code=code-123&state={query['state'][0]}"
            )

        me = await client.get("/api/me")

        assert response.status_code == 403
        assert me.status_code == 401


@pytest.mark.anyio
async def test_pdf_route_requires_authentication_before_database_access():
    settings = oidc_settings()
    async with application_client(create_app(settings)) as client:
        assert (await client.get("/buscar/1234567")).status_code == 401


def test_session_duration_default_and_environment_override(monkeypatch):
    monkeypatch.setenv("OIDC_ENABLED", "false")
    monkeypatch.delenv("OIDC_SESSION_MAX_AGE", raising=False)
    assert OIDCSettings.from_env().session_max_age == 43200
    monkeypatch.setenv("OIDC_SESSION_MAX_AGE", "1800")
    assert OIDCSettings.from_env().session_max_age == 1800
    monkeypatch.setenv("OIDC_SESSION_MAX_AGE", "0")
    with pytest.raises(ValueError, match="greater than zero"):
        OIDCSettings.from_env()


def session_cookie(settings, **extra):
    payload = {"user": {"sub": "user-123", "roles": ["viewer"]}, **extra}
    return TimestampSigner(settings.session_secret).sign(
        base64.b64encode(json.dumps(payload).encode())
    ).decode()


@pytest.mark.anyio
@pytest.mark.parametrize("duration", [43200, 1800])
async def test_session_expires_from_login_even_with_recent_cookie(duration):
    settings = oidc_settings(session_max_age=duration)
    logged_in_at = int(time.time())
    async with application_client(create_app(settings)) as client:
        client.cookies.set("fp_session", session_cookie(
            settings, authenticated_at=logged_in_at
        ))
        with patch("backend.auth.time.time", return_value=logged_in_at + duration - 1):
            assert (await client.get("/api/me")).status_code == 200
            assert (await client.get("/", follow_redirects=False)).status_code == 200

        # A cookie reissued near expiration must not extend the login deadline.
        for route, expected_status in [("/api/me", 401), ("/buscar/1234567", 401), ("/", 302)]:
            client.cookies.clear()
            client.cookies.set("fp_session", session_cookie(
                settings, authenticated_at=logged_in_at
            ))
            with patch("backend.auth.time.time", return_value=logged_in_at + duration):
                response = await client.get(route, follow_redirects=False)
            assert response.status_code == expected_status
            if route == "/":
                assert response.headers["location"] == "/login"


@pytest.mark.anyio
@pytest.mark.parametrize("extra", [{}, {"authenticated_at": "invalid"}, {"authenticated_at": 99999999999}])
async def test_legacy_or_invalid_session_requires_login(extra):
    settings = oidc_settings()
    async with application_client(create_app(settings)) as client:
        client.cookies.set("fp_session", session_cookie(settings, **extra))
        assert (await client.get("/api/me")).status_code == 401


@pytest.mark.anyio
async def test_logout_clears_local_session():
    settings = oidc_settings()
    async with application_client(create_app(settings)) as client:
        client.cookies.set("fp_session", session_cookie(
            settings, authenticated_at=int(time.time())
        ), domain="fp-dev.produza.ind.br", path="/")
        response = await client.get("/logout", follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"].startswith(settings.public_issuer)
        assert (await client.get("/api/me")).status_code == 401
