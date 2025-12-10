# Keycloak Direct OIDC Authentication for Airflow
# Airflow authenticates directly with Keycloak (no proxy layer)

import os
import logging
from airflow.www.security import AirflowSecurityManager
from flask_appbuilder.security.manager import AUTH_OAUTH

log = logging.getLogger(__name__)

# Enable OAuth authentication
AUTH_TYPE = AUTH_OAUTH

# Keycloak OIDC Configuration
OIDC_ISSUER = "${keycloak_provider_url}"
OIDC_CLIENT_ID = "${keycloak_client_id}"

# Client secret must be provided via environment variable
# Set AIRFLOW__WEBSERVER__SECRET_KEY in your deployment
OIDC_CLIENT_SECRET = os.getenv("OIDC_CLIENT_SECRET", "CHANGE_ME")

# OAuth provider configuration
OAUTH_PROVIDERS = [
    {
        "name": "keycloak",
        "icon": "fa-key",
        "token_key": "access_token",
        "remote_app": {
            "client_id": OIDC_CLIENT_ID,
            "client_secret": OIDC_CLIENT_SECRET,
            "api_base_url": OIDC_ISSUER,
            "client_kwargs": {
                "scope": "openid email profile groups"
            },
            "access_token_url": f"{OIDC_ISSUER}/protocol/openid-connect/token",
            "authorize_url": f"{OIDC_ISSUER}/protocol/openid-connect/auth",
            "request_token_url": None,
            "server_metadata_url": f"{OIDC_ISSUER}/.well-known/openid-configuration",
        },
    }
]

# Auto-register users on first login
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"  # Default role for new users

# Role mapping configuration
class CustomSecurityManager(AirflowSecurityManager):
    """
    Custom security manager to map Keycloak groups to Airflow roles.
    """

    def oauth_user_info(self, provider, response):
        """
        Get user info from OAuth provider and map groups to roles.

        Args:
            provider: OAuth provider name
            response: OAuth response containing tokens

        Returns:
            Dictionary with user information
        """
        if provider == "keycloak":
            # Get user info from Keycloak
            import requests

            access_token = response.get("access_token")
            if not access_token:
                log.error("No access token in OAuth response")
                return {}

            # Decode the JWT to get user info and groups
            import json
            import base64

            try:
                # JWT structure: header.payload.signature
                payload = access_token.split('.')[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))

                # Extract user information
                user_info = {
                    "username": decoded.get("preferred_username", ""),
                    "email": decoded.get("email", ""),
                    "first_name": decoded.get("given_name", ""),
                    "last_name": decoded.get("family_name", ""),
                    "groups": decoded.get("groups", []),
                }

                log.info(f"Keycloak user login: {user_info['username']}, groups: {user_info['groups']}")

                # Map groups to roles
                user_info["role_keys"] = self._map_groups_to_roles(user_info["groups"])

                return user_info

            except Exception as e:
                log.error(f"Error decoding access token: {e}")
                return {}

        return {}

    def _map_groups_to_roles(self, keycloak_groups):
        """
        Map Keycloak groups to Airflow roles.

        Role mapping (configured via Terraform):
%{ for group, roles in keycloak_role_mapping ~}
        - ${group} → ${join(", ", roles)}
%{ endfor ~}

        Users with multiple groups get the highest priority role.
        Priority: Admin > Op > User > Viewer > Public

        Args:
            keycloak_groups: List of Keycloak group names from OIDC token

        Returns:
            List of Airflow role names
        """
        # Keycloak group to Airflow role mapping (from Terraform configuration)
        group_role_mapping = {
%{ for group, roles in keycloak_role_mapping ~}
            '${group}': '${roles[0]}',
%{ endfor ~}
        }

        # Role priority (higher index = higher priority)
        role_priority = ['Public', 'Viewer', 'User', 'Op', 'Admin']

        # Find highest priority role from user's groups
        highest_role_name = None
        highest_priority = -1

        for group in keycloak_groups:
            if group in group_role_mapping:
                role_name = group_role_mapping[group]
                if role_name in role_priority:
                    priority = role_priority.index(role_name)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_role_name = role_name
                        log.debug(f"Group '{group}' maps to role '{role_name}' (priority {priority})")

        # Return the highest priority role
        if highest_role_name:
            return [highest_role_name]
        else:
            log.warning(f"No matching Keycloak groups, assigning default role")
            return ["Viewer"]

# Set the custom security manager
SECURITY_MANAGER_CLASS = CustomSecurityManager

# Security settings
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Session configuration
PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

log.info("Airflow webserver configured for direct Keycloak OIDC authentication")
