import os
from typing import Any

from airflow.providers.fab.auth_manager.security_manager.override import FabAirflowSecurityManagerOverride
from flask_appbuilder.security.manager import AUTH_OAUTH

# Cognito integration data
COGNITO_BASE_URL = os.environ["COGNITO_BASE_URL"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
COGNITO_CLIENT_SECRET = os.environ["COGNITO_CLIENT_SECRET"]

# Authentication constants
AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"
AUTH_ROLES_SYNC_AT_LOGIN = False
AUTH_ROLES_MAPPING = {
    "Unity_Viewer": ["User"],
    "Unity_Admin": ["Admin"],
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
        },
    }
]


# Security manager override
class CognitoAuthorizer(FabAirflowSecurityManagerOverride):

    def get_oauth_user_info(self, provider: str, resp: dict[str, Any]) -> dict[str, Any]:

        if provider == "Cognito":
            me = self.appbuilder.sm.oauth_remotes[provider].get("userInfo")
            print(me)
            return {
                "username": "admin",
                "email": "admin@test.airflow.com",
                "first_name": "Admin",
                "last_name": "Admin",
                "role_keys": ["Admin"],
            }


SECURITY_MANAGER_CLASS = CognitoAuthorizer