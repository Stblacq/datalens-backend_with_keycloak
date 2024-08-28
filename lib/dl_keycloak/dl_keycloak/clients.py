import datetime
import logging

import attr
import httpx
import pydantic

LOGGER = logging.getLogger(__name__)

# Existing data models
@attr.s(auto_attribs=True)
class IntrospectResult:
    active: bool
    username: str | None = None
    sub: str | None = None

@attr.s(auto_attribs=True)
class Token:
    access_token: str
    expires_in: int
    request_datetime: datetime.datetime

    @property
    def expiration_datetime(self) -> datetime.datetime:
        return self.request_datetime + datetime.timedelta(seconds=self.expires_in)

class IntrospectPostResponse(pydantic.BaseModel):
    active: bool
    username: str | None = None
    sub: str | None = None

    def to_dataclass(self) -> IntrospectResult:
        return IntrospectResult(
            active=self.active,
            username=self.username,
            sub=self.sub,
        )

class TokenPostResponse(pydantic.BaseModel):
    access_token: str
    token_type: str
    expires_in: int

    def to_dataclass(self) -> Token:
        return Token(
            access_token=self.access_token,
            expires_in=self.expires_in,
            request_datetime=datetime.datetime.now(),
        )

# Base client
@attr.s(auto_attribs=True)
class KeycloakBaseClient:
    _base_client: httpx.Client | httpx.AsyncClient
    _keycloak_client_id: str
    _keycloak_uri: str
    _keycloak_realm_name: str
    _keycloak_secret_key: str
    def _token_endpoint(self) -> str:
        return f"{self._keycloak_uri}/realms/{self._keycloak_realm_name}/protocol/openid-connect/token"

    def _introspect_endpoint(self) -> str:
        return f"{self._keycloak_uri}/realms/{self._keycloak_realm_name}/protocol/openid-connect/token/introspect"

# Synchronous client
@attr.s(auto_attribs=True)
class KeycloakSyncClient(KeycloakBaseClient):
    _base_client: httpx.Client

    def get_token(self) -> Token:
        LOGGER.info("Requesting token from Keycloak")
        response = self._base_client.post(
            self._token_endpoint(),
            data={
                "client_id": self._keycloak_client_id,
                "client_secret": self._keycloak_secret_key,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        token_response = TokenPostResponse(**response.json())
        return token_response.to_dataclass()

    def introspect(self, token: str) -> IntrospectResult:
        LOGGER.info("Introspecting token with Keycloak")
        response = self._base_client.post(
            self._introspect_endpoint(),
            data={
                "token": token,
                "client_id": self._keycloak_client_id,
                "client_secret": self._keycloak_secret_key,
            },
        )
        response.raise_for_status()
        introspect_response = IntrospectPostResponse(**response.json())
        return introspect_response.to_dataclass()

# Asynchronous client
@attr.s(auto_attribs=True)
class KeycloakAsyncClient(KeycloakBaseClient):
    _base_client: httpx.AsyncClient

    async def get_token(self) -> Token:
        LOGGER.info("Requesting token from Keycloak")
        response = await self._base_client.post(
            self._token_endpoint(),
            data={
                "client_id": self._keycloak_client_id,
                "client_secret": self._keycloak_secret_key,
                "grant_type": "client_credentials",
            },
        )
        response.raise_for_status()
        token_response = TokenPostResponse(**response.json())
        return token_response.to_dataclass()

    async def introspect(self, token: str) -> IntrospectResult:
        LOGGER.info("Introspecting token with Keycloak")
        response = await self._base_client.post(
            self._introspect_endpoint(),
            data={
                "token": token,
                "client_id": self._keycloak_client_id,
                "client_secret": self._keycloak_secret_key,
            },
        )
        response.raise_for_status()
        introspect_response = IntrospectPostResponse(**response.json())
        return introspect_response.to_dataclass()

__all__ = [
    "KeycloakAsyncClient",
    "KeycloakSyncClient",
    "Token",
]
