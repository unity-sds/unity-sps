import base64
import json
import logging
import os
from typing import Any

from airflow.providers.fab.auth_manager.security_manager.override import FabAirflowSecurityManagerOverride
from authlib.common.urls import url_decode
from authlib.integrations.base_client.sync_openid import OpenIDMixin
from authlib.oauth2.client import OAuth2Client
from flask_appbuilder.security.manager import AUTH_OAUTH
from tornado.httpclient import HTTPClient, HTTPRequest
from tornado.httputil import url_concat

# Logging
log = logging.getLogger("flask_appbuilder.security.views")

# Cognito integration data
COGNITO_BASE_URL = os.environ["COGNITO_BASE_URL"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
COGNITO_CLIENT_SECRET = os.environ["COGNITO_CLIENT_SECRET"]
COGNITO_USER_POOL_ID = os.environ["COGNITO_USER_POOL_ID"]

# Authentication constants
AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True  # allow users not in the FAB DB
AUTH_USER_REGISTRATION_ROLE = "Admin"  # role given in addition to AUTH_ROLES
AUTH_ROLES_SYNC_AT_LOGIN = True  # replace all user's roles each login
AUTH_ROLES_MAPPING = {  # mapping of Cognito groups to FAB roles
    "Unity_Viewer": "User",
    "Unity_Admin": "Admin",
}

# Cognito provider data
OAUTH_PROVIDERS = [
    {
        "name": "Cognito",
        "icon": "fa-amazon",
        "token_key": "access_token",
        "remote_app": {
            "client_id": COGNITO_CLIENT_ID,
            "client_secret": COGNITO_CLIENT_SECRET,
            "api_base_url": f"{COGNITO_BASE_URL}/",
            "client_kwargs": {"scope": "email openid profile"},
            "access_token_url": f"{COGNITO_BASE_URL}/token",
            "authorize_url": f"{COGNITO_BASE_URL}/authorize",
            "jwks_uri": f"https://cognito-idp.us-west-2.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json",
        },
    }
]


def fetch_token(self, url, body="", headers=None, auth=None, method="POST", state=None, **kwargs):
    """Overridden method to fetch Cognito token data."""

    # Encode client Id and secret
    message = auth.client_id + ":" + auth.client_secret
    message_bytes = message.encode("ascii")
    base64_bytes = base64.b64encode(message_bytes)
    base64_auth = base64_bytes.decode("ascii")

    # Build URL with parameters
    body_dict = dict(url_decode(body))
    params = dict(
        client_id=auth.client_id,
        code=body_dict["code"],
        grant_type="authorization_code",
        redirect_uri=body_dict["redirect_uri"],
    )
    url = url_concat(url, params)
    req = HTTPRequest(
        url,
        method="POST",
        headers={
            "Accept": "application/json",
            "Authorization": "Basic " + base64_auth,
            "Content-Type": "application/x-www-form-urlencoded",
        },
        body="",
    )

    # POST request to Cognito for token data
    http_client = HTTPClient()
    resp = http_client.fetch(req)
    resp_json = json.loads(resp.body.decode("utf8", "replace"))

    return resp_json


def fetch_jwk(self, force=False):
    """Fetch JWK public data."""

    metadata = self.load_server_metadata()
    jwks_uri = metadata.get("jwks_uri")
    log.debug("jwks_uri: %s", jwks_uri)

    req = HTTPRequest(jwks_uri, method="GET")
    http_client = HTTPClient()
    jwks_response = http_client.fetch(req)
    jwks_json = json.loads(jwks_response.body.decode("utf8", "replace"))
    log.debug("jwks_json: %s", jwks_json)
    return jwks_json


def map_roles(roles):
    """Map Cognito roles to Airflow roles."""

    return list(set(AUTH_ROLES_MAPPING.get(role, "Public") for role in roles))


# Security manager override
class CognitoAuthorizer(FabAirflowSecurityManagerOverride):

    def get_oauth_user_info(self, provider: str, resp: dict[str, Any]) -> dict[str, Any]:
        """Override method to login with Cognito specific data."""

        if provider == "Cognito":
            user_info = resp["userinfo"]
            log.debug("user_info: %s", user_info)

            roles = map_roles(user_info["cognito:groups"])
            log.debug("roles: %s", roles)

            return {
                "username": user_info["cognito:username"],
                "email": user_info["email"],
                "role_keys": roles,
            }


# Overrides
SECURITY_MANAGER_CLASS = CognitoAuthorizer
OAuth2Client._fetch_token = fetch_token
OpenIDMixin.fetch_jwk_set = fetch_jwk
