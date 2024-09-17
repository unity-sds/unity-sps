import json
import logging
import os

# import jwt
from airflow.www.security import AirflowSecurityManager
from flask_appbuilder.security.manager import AUTH_OAUTH

# Cognito integration data
COGNITO_BASE_URL = os.environ["COGNITO_BASE_URL"]
COGNITO_CLIENT_ID = os.environ["COGNITO_CLIENT_ID"]
COGNITO_CLIENT_SECRET = os.environ["COGNITO_CLIENT_SECRET"]

# COGNITO_URL = os.environ['COGNITO_URL']
# CONSUMER_KEY = os.environ['CONSUMER_KEY']
# SECRET_KEY = os.environ['SECRET_KEY']

# FIXME
# REDIRECT_URI = os.environ['REDIRECT_URI']
REDIRECT_URI = "https://www.cnn.com/"

# FIX<E?
# JWKS_URI = ("https://cognito-idp.%s.amazonaws.com/%s/.well-known/jwks.json"
#             % (os.environ['AWS_REGION'], os.environ['COGNITO_POOL_ID']))

# Authentication constants
AUTH_TYPE = AUTH_OAUTH
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Public"
# AUTH_USER_REGISTRATION_ROLE = "Admin"
AUTH_ROLES_SYNC_AT_LOGIN = True  # Checks roles on every login
AUTH_ROLES_MAPPING = {
    "Unity_Viewer": ["User"],
    "Unity_Admin": ["Admin"],
    # "Viewer": ["User"],
    # "Admin": ["Admin"],
}

# Cognito provider data
# OAUTH_PROVIDERS = [
#     {
#         "name": "Cognito",
#         "icon": "fa-amazon",
#         "token_key": "access_token",
#         "remote_app": {
#             "client_id": COGNITO_CLIENT_ID,
#             "client_secret": COGNITO_CLIENT_SECRET,
#             "api_base_url": f"{COGNITO_BASE_URL}/",
#             "client_kwargs": {"scope": "email openid profile"},
#             "access_token_url": f"{COGNITO_BASE_URL}/token",
#             "authorize_url": f"{COGNITO_BASE_URL}/authorize",
#         },
#     }
# ]

OAUTH_PROVIDERS = [
    {
        "name": "aws_cognito",
        "token_key": "access_token",
        "url": COGNITO_BASE_URL,
        "icon": "fa-amazon",
        "remote_app": {
            "client_id": COGNITO_CLIENT_ID,
            "client_secret": COGNITO_CLIENT_SECRET,
            "base_url": os.path.join(COGNITO_BASE_URL, "oauth2/idpresponse"),
            "api_base_url": COGNITO_BASE_URL,
            "redirect_uri": REDIRECT_URI,
            # 'jwks_uri': JWKS_URI,
            "client_kwargs": {"scope": "email openid profile"},
            "access_token_url": os.path.join(COGNITO_BASE_URL, "oauth2/token"),
            "authorize_url": os.path.join(COGNITO_BASE_URL, "oauth2/authorize"),
        },
    }
]

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(message)s")
logger = logging.getLogger()


class CognitoSecurity(AirflowSecurityManager):
    def oauth_user_info(self, provider, response=None):
        # Q: aws_cognito or Cognito?
        if provider == "aws_cognito" and response:

            logger.debug(response)

            res = self.appbuilder.sm.oauth_remotes[provider].get("oauth2/userInfo")

            if res.raw.status != 200:
                logger.error("Failed to obtain user info: %s", res.data)
                return
            me = json.loads(res._content)
            #
            decoded_token = self._azure_jwt_token_parse(response["id_token"])
            logger.debug(" data: %s", decoded_token)
            return {
                "username": me.get("username"),
                "email": me.get("email"),
                "role_keys": decoded_token.get("cognito:groups", ["Public"]),
            }
        else:
            return {}


# Security manager override
# class CognitoAuthorizer(FabAirflowSecurityManagerOverride):
#
#     def get_oauth_user_info(self, provider: str, resp: dict[str, Any]) -> dict[str, Any]:
#
#         if provider == "Cognito":
#             me = self.appbuilder.sm.oauth_remotes[provider].get("userInfo")
#             print(me)
#             return {
#                 "username": "admin",
#                 "email": "admin@test.airflow.com",
#                 "first_name": "Admin",
#                 "last_name": "Admin",
#                 "role_keys": ["Admin"],
#             }


SECURITY_MANAGER_CLASS = CognitoSecurity
