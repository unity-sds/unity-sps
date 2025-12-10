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
"""
   User authentication backend
   Referencies
     - https://flask-appbuilder.readthedocs.io/en/latest/_modules/flask_appbuilder/security/manager.html
     - https://github.com/apache/airflow/blob/main/airflow/api/auth/backend/basic_auth.py
"""
from __future__ import annotations
import logging

# Wrap imports that might not be available during Terraform file() reads
try:
    from functools import wraps
    from typing import Any, Callable, TypeVar, cast
    from flask import Response, request
    from flask_appbuilder.const import AUTH_OAUTH, AUTH_LDAP, AUTH_DB
    from flask_login import login_user
    from airflow.utils.airflow_flask_app import get_airflow_app
    from airflow.www.fab_security.sqla.models import User
    import jwt
    import requests
    from base64 import b64decode
    from cryptography.hazmat.primitives import serialization
    IMPORTS_AVAILABLE = True
except ImportError as e:
    logging.warning(f"Some imports not available during config read: {e}")
    IMPORTS_AVAILABLE = False
    # Define minimal fallbacks
    AUTH_OAUTH = None
    AUTH_LDAP = None
    AUTH_DB = None
CLIENT_AUTH: tuple[str, str] | Any | None = None
log = logging.getLogger(__name__)
CLIENT_ID = 'airflow'
OIDC_ISSUER = 'https://dit.kc-test-maap.xyz/realms/MAAP'

def get_keycloak_public_key():
    """Fetch Keycloak public key with error handling"""
    try:
        req = requests.get(OIDC_ISSUER, timeout=5)
        req.raise_for_status()
        key_der_base64 = req.json()["public_key"]
        key_der = b64decode(key_der_base64.encode())
        return serialization.load_der_public_key(key_der)
    except Exception as e:
        log.error(f"Failed to fetch Keycloak public key: {e}")
        return None

def init_app(_):
    """Initializes authentication backend"""
    pass

if IMPORTS_AVAILABLE:
    T = TypeVar("T", bound=Callable)

    def auth_current_user() -> User | None:
        """Authenticate and set current user if Authorization header exists"""

        ab_security_manager = get_airflow_app().appbuilder.sm
        user = None
        if ab_security_manager.auth_type == AUTH_OAUTH:
            auth_header = request.headers.get('Authorization')
            if not auth_header:
                return None

            public_key = get_keycloak_public_key()
            if public_key is None:
                log.error("Cannot authenticate: Keycloak public key unavailable")
                return None

            token = auth_header.replace('Bearer ', '')
            try:
                me = jwt.decode(token, public_key, algorithms=['HS256', 'RS256'], audience=CLIENT_ID)
            except jwt.InvalidTokenError as e:
                log.error(f"Token validation failed: {e}")
                return None

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
            user = ab_security_manager.auth_user_oauth(userinfo)
        else:
            auth = request.authorization
            if auth is None or not auth.username or not auth.password:
                return None
            if ab_security_manager.auth_type == AUTH_LDAP:
                user = ab_security_manager.auth_user_ldap(auth.username, auth.password)
            if ab_security_manager.auth_type == AUTH_DB:
                user = ab_security_manager.auth_user_db(auth.username, auth.password)
            log.info("user: {0}".format(user))
            if user is not None:
                login_user(user, remember=False)
            return user

    def requires_authentication(function: T):
        """Decorator for functions that require authentication"""
        @wraps(function)
        def decorated(*args, **kwargs):
            if auth_current_user() is not None:
                return function(*args, **kwargs)
            else:
                return Response("Unauthorized", 401, {"WWW-Authenticate": "Basic"})

        return cast(T, decorated)
else:
    # Fallback functions when imports are not available
    def auth_current_user():
        return None

    def requires_authentication(function):
        return function
