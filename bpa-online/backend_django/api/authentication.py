from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional

import jwt
from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed

User = get_user_model()


def decode_token(token: str) -> dict:
    try:
        return jwt.decode(
            token,
            settings.JWT_SECRET_KEY,
            algorithms=[settings.JWT_ALGORITHM],
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthenticationFailed("Token expirado") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthenticationFailed("Token invalido") from exc


def encode_token(payload: dict) -> str:
    now = datetime.now(timezone.utc)
    payload = {
        **payload,
        "iat": int(now.timestamp()),
        "exp": int((now.timestamp()) + (settings.JWT_EXPIRE_HOURS * 3600)),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


class JWTAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header: Optional[str] = request.headers.get("Authorization")
        if not auth_header:
            return None
        if not auth_header.lower().startswith("bearer "):
            return None

        token = auth_header.split(" ", 1)[1].strip()
        if not token:
            return None

        payload = decode_token(token)
        user_id = payload.get("user_id")
        if not user_id:
            raise AuthenticationFailed("Token invalido")

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist as exc:
            raise AuthenticationFailed("Usuario nao encontrado") from exc

        if not user.is_active:
            raise AuthenticationFailed("Usuario inativo")

        return (user, payload)
