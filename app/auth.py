from __future__ import annotations

import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Optional, Tuple

from .data import default_user
from .schemas import TokenPair, User


class TokenStore:
    def __init__(self) -> None:
        self.access_tokens: Dict[str, Tuple[int, datetime]] = {}
        self.refresh_tokens: Dict[str, Tuple[int, datetime]] = {}
        self.expires_in = 24 * 60 * 60
        self.refresh_expires_in = 7 * 24 * 60 * 60

    def _generate_token(self) -> str:
        return secrets.token_urlsafe(32)

    def issue_tokens(self, user: User) -> TokenPair:
        access = self._generate_token()
        refresh = self._generate_token()
        access_exp = datetime.now(timezone.utc) + timedelta(seconds=self.expires_in)
        refresh_exp = datetime.now(timezone.utc) + timedelta(seconds=self.refresh_expires_in)
        self.access_tokens[access] = (user.user_id, access_exp)
        self.refresh_tokens[refresh] = (user.user_id, refresh_exp)
        return TokenPair(
            access_token=access,
            refresh_token=refresh,
            expires_in=self.expires_in,
            user_id=user.user_id,
            openid=user.openid,
        )

    def verify_access(self, token: str) -> Optional[int]:
        record = self.access_tokens.get(token)
        if not record:
            return None
        user_id, expires_at = record
        if expires_at < datetime.now(timezone.utc):
            self.access_tokens.pop(token, None)
            return None
        return user_id

    def refresh(self, refresh_token: str) -> Optional[TokenPair]:
        record = self.refresh_tokens.get(refresh_token)
        if not record:
            return None
        user_id, expires_at = record
        if expires_at < datetime.now(timezone.utc):
            self.refresh_tokens.pop(refresh_token, None)
            return None
        # rotate tokens
        user = default_user if user_id == default_user.user_id else None
        if not user:
            return None
        return self.issue_tokens(user)

    def revoke(self, token: str) -> None:
        self.access_tokens.pop(token, None)


token_store = TokenStore()
