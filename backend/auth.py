from __future__ import annotations

import base64
import hashlib
import os
import secrets
import time
from dataclasses import dataclass
from hmac import compare_digest
from typing import Any
from urllib.parse import urlencode, urlparse

import httpx
from joserfc import jwt
from joserfc.errors import JoseError
from joserfc.jwk import KeySet
from fastapi import HTTPException, Request, status
from fastapi.responses import RedirectResponse


def _read_bool(name: str, default: bool) -> bool:
    value = os.getenv(name)
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "on"}:
        return True
    if normalized in {"0", "false", "no", "off"}:
        return False
    raise ValueError(f"{name} must be true or false")


@dataclass(frozen=True)
class OIDCSettings:
    enabled: bool
    public_issuer: str
    internal_issuer: str
    client_id: str
    client_secret: str
    session_secret: str
    redirect_uri: str
    post_logout_redirect_uri: str
    required_role: str
    session_max_age: int
    cookie_secure: bool

    @classmethod
    def from_env(cls) -> "OIDCSettings":
        enabled = _read_bool("OIDC_ENABLED", False)
        settings = cls(
            enabled=enabled,
            public_issuer=os.getenv("OIDC_PUBLIC_ISSUER", "").rstrip("/"),
            internal_issuer=os.getenv("OIDC_INTERNAL_ISSUER", "").rstrip("/"),
            client_id=os.getenv("OIDC_CLIENT_ID", ""),
            client_secret=os.getenv("OIDC_CLIENT_SECRET", ""),
            session_secret=(
                os.getenv("OIDC_SESSION_SECRET")
                or "local-only-session-secret-when-oidc-is-disabled"
            ),
            redirect_uri=os.getenv("OIDC_REDIRECT_URI", ""),
            post_logout_redirect_uri=os.getenv(
                "OIDC_POST_LOGOUT_REDIRECT_URI", ""
            ),
            required_role=os.getenv("OIDC_REQUIRED_ROLE", "viewer"),
            session_max_age=int(os.getenv("OIDC_SESSION_MAX_AGE", "43200")),
            cookie_secure=_read_bool("OIDC_COOKIE_SECURE", True),
        )
        settings.validate()
        return settings

    def validate(self) -> None:
        if self.session_max_age <= 0:
            raise ValueError("OIDC_SESSION_MAX_AGE must be greater than zero")
        if not self.enabled:
            return

        required = {
            "OIDC_PUBLIC_ISSUER": self.public_issuer,
            "OIDC_INTERNAL_ISSUER": self.internal_issuer,
            "OIDC_CLIENT_ID": self.client_id,
            "OIDC_CLIENT_SECRET": self.client_secret,
            "OIDC_SESSION_SECRET": self.session_secret,
            "OIDC_REDIRECT_URI": self.redirect_uri,
            "OIDC_POST_LOGOUT_REDIRECT_URI": self.post_logout_redirect_uri,
            "OIDC_REQUIRED_ROLE": self.required_role,
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise ValueError(f"missing OIDC settings: {', '.join(missing)}")
        if len(self.session_secret) < 32:
            raise ValueError("OIDC_SESSION_SECRET must contain at least 32 characters")
        if urlparse(self.public_issuer).scheme != "https":
            raise ValueError("OIDC_PUBLIC_ISSUER must use https")
        if urlparse(self.redirect_uri).scheme != "https":
            raise ValueError("OIDC_REDIRECT_URI must use https")
        if urlparse(self.post_logout_redirect_uri).scheme != "https":
            raise ValueError("OIDC_POST_LOGOUT_REDIRECT_URI must use https")
        if urlparse(self.internal_issuer).scheme not in {"http", "https"}:
            raise ValueError("OIDC_INTERNAL_ISSUER must use http or https")


class OIDCClient:
    def __init__(self, settings: OIDCSettings):
        self.settings = settings

    @property
    def authorization_endpoint(self) -> str:
        return f"{self.settings.public_issuer}/protocol/openid-connect/auth"

    @property
    def token_endpoint(self) -> str:
        return f"{self.settings.internal_issuer}/protocol/openid-connect/token"

    @property
    def jwks_endpoint(self) -> str:
        return f"{self.settings.internal_issuer}/protocol/openid-connect/certs"

    @property
    def logout_endpoint(self) -> str:
        return f"{self.settings.public_issuer}/protocol/openid-connect/logout"

    def start_login(self, request: Request, return_to: str = "/") -> RedirectResponse:
        state = secrets.token_urlsafe(32)
        nonce = secrets.token_urlsafe(32)
        verifier = secrets.token_urlsafe(64)
        challenge = base64.urlsafe_b64encode(
            hashlib.sha256(verifier.encode("ascii")).digest()
        ).rstrip(b"=").decode("ascii")

        request.session.clear()
        request.session["oidc_flow"] = {
            "state": state,
            "nonce": nonce,
            "verifier": verifier,
            "return_to": self._safe_return_path(return_to),
        }
        query = urlencode(
            {
                "client_id": self.settings.client_id,
                "response_type": "code",
                "scope": "openid profile email",
                "redirect_uri": self.settings.redirect_uri,
                "state": state,
                "nonce": nonce,
                "code_challenge": challenge,
                "code_challenge_method": "S256",
            }
        )
        return RedirectResponse(f"{self.authorization_endpoint}?{query}", status_code=302)

    async def finish_login(self, request: Request, code: str, state_value: str) -> str:
        flow = request.session.pop("oidc_flow", None)
        if not isinstance(flow, dict):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Fluxo de login expirado.")
        expected_state = flow.get("state")
        if not isinstance(expected_state, str) or not compare_digest(
            expected_state, state_value
        ):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Estado OIDC inválido.")

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                token_response = await client.post(
                    self.token_endpoint,
                    data={
                        "grant_type": "authorization_code",
                        "code": code,
                        "redirect_uri": self.settings.redirect_uri,
                        "code_verifier": flow["verifier"],
                    },
                    auth=(self.settings.client_id, self.settings.client_secret),
                )
                token_response.raise_for_status()
                tokens = token_response.json()
                jwks_response = await client.get(self.jwks_endpoint)
                jwks_response.raise_for_status()
                jwks = jwks_response.json()
        except (httpx.HTTPError, KeyError, ValueError) as exc:
            raise HTTPException(
                status.HTTP_502_BAD_GATEWAY,
                "Não foi possível concluir o login no provedor de identidade.",
            ) from exc

        id_claims = self._decode_token(tokens.get("id_token"), jwks)
        access_claims = self._decode_token(tokens.get("access_token"), jwks)
        self._validate_id_claims(id_claims, flow.get("nonce"))
        self._validate_access_claims(access_claims)

        roles = access_claims.get("resource_access", {}).get(
            self.settings.client_id, {}
        ).get("roles", [])
        if self.settings.required_role not in roles:
            request.session.clear()
            raise HTTPException(
                status.HTTP_403_FORBIDDEN,
                "Usuário sem permissão para consultar folhas de processo.",
            )

        request.session["user"] = {
            "sub": id_claims["sub"],
            "preferred_username": id_claims.get("preferred_username", ""),
            "name": id_claims.get("name", ""),
            "email": id_claims.get("email", ""),
            "roles": roles,
        }
        request.session["authenticated_at"] = int(time.time())
        return self._safe_return_path(flow.get("return_to", "/"))

    def logout_response(self, request: Request) -> RedirectResponse:
        request.session.clear()
        query = urlencode(
            {
                "client_id": self.settings.client_id,
                "post_logout_redirect_uri": self.settings.post_logout_redirect_uri,
            }
        )
        return RedirectResponse(f"{self.logout_endpoint}?{query}", status_code=302)

    def _decode_token(self, token: Any, jwks: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(token, str) or not token:
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Resposta OIDC inválida.")
        try:
            key_set = KeySet.import_key_set(jwks)
            token_value = jwt.decode(token, key_set, algorithms=["RS256"])
            registry = jwt.JWTClaimsRegistry(leeway=30, exp={"essential": True})
            registry.validate(token_value.claims)
        except (JoseError, TypeError, ValueError) as exc:
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token OIDC inválido.") from exc
        return dict(token_value.claims)

    def _validate_id_claims(self, claims: dict[str, Any], nonce: Any) -> None:
        audience = claims.get("aud", [])
        if isinstance(audience, str):
            audience = [audience]
        valid_nonce = (
            isinstance(nonce, str)
            and isinstance(claims.get("nonce"), str)
            and compare_digest(nonce, claims["nonce"])
        )
        if (
            claims.get("iss") != self.settings.public_issuer
            or self.settings.client_id not in audience
            or not valid_nonce
            or not claims.get("sub")
        ):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "ID token OIDC inválido.")

    def _validate_access_claims(self, claims: dict[str, Any]) -> None:
        if (
            claims.get("iss") != self.settings.public_issuer
            or claims.get("azp") != self.settings.client_id
        ):
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED, "Access token OIDC inválido."
            )

    @staticmethod
    def _safe_return_path(value: Any) -> str:
        if isinstance(value, str) and value.startswith("/") and not value.startswith("//"):
            return value
        return "/"


def session_user(request: Request) -> dict[str, Any] | None:
    user = request.session.get("user")
    authenticated_at = request.session.get("authenticated_at")
    now = time.time()
    if (
        not isinstance(user, dict)
        or type(authenticated_at) is not int
        or authenticated_at > now
        or now - authenticated_at >= request.app.state.oidc_settings.session_max_age
    ):
        request.session.clear()
        return None
    return user


async def require_user(request: Request) -> dict[str, Any]:
    settings: OIDCSettings = request.app.state.oidc_settings
    if not settings.enabled:
        return {"preferred_username": "local", "roles": [settings.required_role]}
    user = session_user(request)
    if user is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Autenticação necessária.")
    if settings.required_role not in user.get("roles", []):
        raise HTTPException(status.HTTP_403_FORBIDDEN, "Permissão insuficiente.")
    return user
