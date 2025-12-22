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

# Auto-register users on first login (only if they have approved Keycloak groups)
# Users without approved groups will be rejected during authentication
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"  # Not used - role determined by Keycloak group mapping

# Role mapping configuration
class CustomSecurityManager(AirflowSecurityManager):
    """
    Custom security manager to map Keycloak groups to Airflow roles.

    IMPORTANT: Users must have at least one approved Keycloak group to access Airflow.
    Users without approved groups will be denied access during authentication.
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
            import json
            import base64

            # Log the OAuth response structure (without sensitive token values)
            log.info(f"OAuth callback from provider: {provider}")
            log.info(f"OAuth response keys: {list(response.keys())}")

            # Get access token
            access_token = response.get("access_token")
            if not access_token:
                log.error(f"No access token in OAuth response. Response keys: {list(response.keys())}")
                log.error(f"Full response (for debugging): {response}")
                return {}

            try:
                # Decode JWT to get user info and groups
                # JWT structure: header.payload.signature
                parts = access_token.split('.')
                if len(parts) != 3:
                    log.error(f"Invalid JWT format. Expected 3 parts, got {len(parts)}")
                    return {}

                payload = parts[1]
                # Add padding if needed
                payload += '=' * (4 - len(payload) % 4)
                decoded = json.loads(base64.urlsafe_b64decode(payload))

                # Log what we received from Keycloak (useful for debugging)
                log.info(f"JWT payload keys: {list(decoded.keys())}")
                log.info(f"Available claims: username={decoded.get('preferred_username')}, email={decoded.get('email')}")
                log.info(f"Groups in token: {decoded.get('groups', [])}")

                # Extract user information (with fallbacks for different claim names)
                username = decoded.get("preferred_username") or decoded.get("username") or decoded.get("sub")
                email = decoded.get("email", f"{username}@example.com")
                first_name = decoded.get("given_name") or decoded.get("first_name") or username
                last_name = decoded.get("family_name") or decoded.get("last_name") or ""

                # Groups might be in different formats depending on Keycloak mapper config
                groups = decoded.get("groups", [])
                if isinstance(groups, str):
                    groups = [groups]

                # Some Keycloak configs put groups in realm_access or resource_access
                if not groups and "realm_access" in decoded:
                    groups = decoded["realm_access"].get("roles", [])
                if not groups and "resource_access" in decoded:
                    client_access = decoded["resource_access"].get(OIDC_CLIENT_ID, {})
                    groups = client_access.get("roles", [])

                user_info = {
                    "username": username,
                    "email": email,
                    "first_name": first_name,
                    "last_name": last_name,
                    "groups": groups,
                }

                log.info(f"Keycloak user login: username={user_info['username']}, email={user_info['email']}, groups={user_info['groups']}")

                # Map groups to roles
                user_info["role_keys"] = self._map_groups_to_roles(user_info["groups"])
                log.info(f"Mapped to Airflow roles: {user_info['role_keys']}")

                return user_info

            except Exception as e:
                log.error(f"Error decoding access token: {e}", exc_info=True)
                log.error(f"Token (first 50 chars): {access_token[:50]}...")
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

        IMPORTANT: Users without any approved Keycloak groups will be rejected.

        Args:
            keycloak_groups: List of Keycloak group names from OIDC token

        Returns:
            List of Airflow role names

        Raises:
            Exception: If user has no approved Keycloak groups (access denied)
        """
        # Keycloak group to Airflow role mapping (from Terraform configuration)
        group_role_mapping = {
%{ for group, roles in keycloak_role_mapping ~}
            '${group}': '${roles[0]}',
%{ endfor ~}
        }

        log.debug(f"Group role mapping: {group_role_mapping}")
        log.debug(f"User's Keycloak groups: {keycloak_groups}")

        # Role priority (higher index = higher priority)
        role_priority = ['Public', 'Viewer', 'User', 'Op', 'Admin']

        # Find highest priority role from user's groups
        highest_role_name = None
        highest_priority = -1

        for group in keycloak_groups:
            # Handle group paths (e.g., "/airflow/admin" or "airflow_admin")
            group_name = group.split('/')[-1]  # Get last part of path

            if group_name in group_role_mapping:
                role_name = group_role_mapping[group_name]
                if role_name in role_priority:
                    priority = role_priority.index(role_name)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_role_name = role_name
                        log.info(f"Group '{group}' maps to role '{role_name}' (priority {priority})")

        # Return the highest priority role
        if highest_role_name:
            return [highest_role_name]
        else:
            # Reject users who don't have any approved Keycloak groups
            log.error(f"Access denied: User has no approved Keycloak groups. User groups: {keycloak_groups}")
            log.error("User must be assigned to one of these Keycloak groups to access Airflow:")
            log.error(f"  Approved groups: {list(group_role_mapping.keys())}")
            raise Exception(
                "Access denied: You are not assigned to any approved Keycloak groups. "
                "Please contact your administrator to request access."
            )

# Set the custom security manager
SECURITY_MANAGER_CLASS = CustomSecurityManager

# Security settings
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None

# Session configuration
PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

log.info("Airflow webserver configured for direct Keycloak OIDC authentication")
log.info(f"Keycloak provider: {OIDC_ISSUER}")
log.info(f"Keycloak client: {OIDC_CLIENT_ID}")
