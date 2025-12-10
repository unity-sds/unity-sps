#
# Licensed to the Apache Software Foundation (ASF) under one
# or more contributor license agreements.  See the NOTICE file
# distributed with this work for additional information
# regarding copyright ownership.  The ASF licenses this file
# to you under the Apache License, Version 2.0 (the
# "License"); you may not use this file except in compliance
# with the License.  You may obtain a copy of the License at
#
#   http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing,
# software distributed under the License is distributed on an
# "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY
# KIND, either express or implied.  See the License for the
# specific language governing permissions and limitations
# under the License.
"""Default configuration for the Airflow webserver"""
from __future__ import annotations
import os
import logging

# Wrap imports that might not be available during Terraform file() reads
try:
    import jwt
    import requests
    from base64 import b64decode
    from cryptography.hazmat.primitives import serialization
    from airflow.www.fab_security.manager import AUTH_OAUTH
    from airflow.www.security import AirflowSecurityManager
    from flask_appbuilder import expose
    from flask_appbuilder.security.views import AuthOAuthView
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports not available during config read: {e}")
    IMPORTS_AVAILABLE = False
    # Define minimal fallbacks
    AUTH_OAUTH = None
basedir = os.path.abspath(os.path.dirname(__file__))
log = logging.getLogger(__name__)
APP_THEME = "simplex.css"
# Flask-WTF flag for CSRF
WTF_CSRF_ENABLED = True
# ----------------------------------------------------
# AUTHENTICATION CONFIG
# ----------------------------------------------------
# For details on how to set up each of the following authentication, see
# http://flask-appbuilder.readthedocs.io/en/latest/security.html# authentication-methods
# for details.
AUTH_TYPE = AUTH_OAUTH if IMPORTS_AVAILABLE else None
# Uncomment to setup Full admin role name
# AUTH_ROLE_ADMIN = 'Admin'
# Uncomment and set to desired role to enable access without authentication
# AUTH_ROLE_PUBLIC = 'Viewer'
# Will allow user self registration
AUTH_USER_REGISTRATION = True
# The recaptcha it's automatically enabled for user self registration is active and the keys are necessary
# RECAPTCHA_PRIVATE_KEY = PRIVATE_KEY
# RECAPTCHA_PUBLIC_KEY = PUBLIC_KEY
# Config for Flask-Mail necessary for user self registration
# MAIL_SERVER = 'smtp.gmail.com'
# MAIL_USE_TLS = True
# MAIL_USERNAME = 'yourappemail@gmail.com'
# MAIL_PASSWORD = 'passwordformail'
# MAIL_DEFAULT_SENDER = 'sender@gmail.com'
# The default user self registration role
AUTH_USER_REGISTRATION_ROLE = "Public"
AUTH_ROLES_SYNC_AT_LOGIN = True
AUTH_ROLES_MAPPING = {
  "airflow_admin": ["Admin"],
  "airflow_op": ["Op"],
  "airflow_user": ["User"],
  "airflow_viewer": ["Viewer"],
  "airflow_public": ["Public"],
}
PROVIDER_NAME = 'keycloak'
CLIENT_ID = 'airflow'
CLIENT_SECRET = 'TODO FILL IN'
OIDC_ISSUER = 'https://dit.kc-test-maap.xyz/realms/MAAP'
OIDC_BASE_URL = "{oidc_issuer}/protocol/openid-connect".format(oidc_issuer=OIDC_ISSUER)
OIDC_TOKEN_URL = "{oidc_base_url}/token".format(oidc_base_url=OIDC_BASE_URL)
OIDC_AUTH_URL = "{oidc_base_url}/auth".format(oidc_base_url=OIDC_BASE_URL)
# When using OAuth Auth, uncomment to setup provider(s) info
OAUTH_PROVIDERS = [{
    'name':PROVIDER_NAME,
    'token_key':'access_token',
    'icon':'fa-circle-o',
    'remote_app': {
        'api_base_url':OIDC_BASE_URL,
        'access_token_url':OIDC_TOKEN_URL,
        'authorize_url':OIDC_AUTH_URL,
        'request_token_url': None,
        'client_id': CLIENT_ID,
        'client_secret': CLIENT_SECRET,
        'client_kwargs':{
            'scope': 'email profile'
        },
    }
}]

def get_keycloak_public_key():
    """Fetch Keycloak public key with error handling"""
    if not IMPORTS_AVAILABLE:
        return None
    try:
        req = requests.get(OIDC_ISSUER, timeout=5)
        req.raise_for_status()
        key_der_base64 = req.json()["public_key"]
        key_der = b64decode(key_der_base64.encode())
        return serialization.load_der_public_key(key_der)
    except Exception as e:
        log.error(f"Failed to fetch Keycloak public key: {e}")
        return None

if IMPORTS_AVAILABLE:
    class CustomAuthRemoteUserView(AuthOAuthView):
        @expose("/logout/")
        def logout(self):
            """Delete access token before logging out."""
            return super().logout()

    class CustomSecurityManager(AirflowSecurityManager):
        authoauthview = CustomAuthRemoteUserView

        def oauth_user_info(self, provider, response):
            if provider == PROVIDER_NAME:
                public_key = get_keycloak_public_key()
                if public_key is None:
                    log.error("Cannot authenticate: Keycloak public key unavailable")
                    return {}

                token = response["access_token"]
                try:
                    me = jwt.decode(token, public_key, algorithms=['HS256', 'RS256'], audience=CLIENT_ID)
                except jwt.InvalidTokenError as e:
                    log.error(f"Token validation failed: {e}")
                    return {}
                # sample of resource_access
                # {
                #   "resource_access": { "airflow": { "roles": ["airflow_admin"] }}
                # }
                try:
                    groups = me["resource_access"]["airflow"]["roles"]
                except KeyError:
                    log.warning("No airflow roles found in token, using default")
                    groups = []
                if len(groups) < 1:
                    groups = ["airflow_public"]
                else:
                    groups = [str for str in groups if "airflow" in str]
                userinfo = {
                    "username": me.get("preferred_username"),
                    "email": me.get("email"),
                    "first_name": me.get("given_name"),
                    "last_name": me.get("family_name"),
                    "role_keys": groups,
                }
                log.info("user info: {0}".format(userinfo))
                return userinfo
            else:
                return {}

    SECURITY_MANAGER_CLASS = CustomSecurityManager
else:
    SECURITY_MANAGER_CLASS = None