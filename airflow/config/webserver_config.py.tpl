# Keycloak OIDC Remote User Authentication for Airflow
# Authentication happens at Apache proxy layer via mod_auth_openidc
# Airflow trusts the remote user headers from the internal proxy

import os
import logging
from flask_appbuilder.security.manager import AUTH_REMOTE_USER

log = logging.getLogger(__name__)

# Enable remote user authentication
# Airflow will trust REMOTE_USER header set by the Apache proxy
AUTH_TYPE = AUTH_REMOTE_USER

# Auto-register users on first login
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"  # Default role for new users

# Custom security manager for mapping Keycloak groups to Airflow roles
from airflow.www.security import AirflowSecurityManager

class CustomSecurityManager(AirflowSecurityManager):
    """
    Custom security manager to map Keycloak groups to Airflow roles.

    This class intercepts remote user authentication and maps the user's
    Keycloak groups (from X-Remote-User-Groups header) to Airflow roles.
    """

    def auth_user_remote_user(self, username):
        """
        Authenticate user from REMOTE_USER header and map groups to roles.

        Args:
            username: Username from REMOTE_USER header (set by mod_auth_openidc)

        Returns:
            User object if authentication succeeds, None otherwise
        """
        from flask import request

        # Get user info from OIDC headers set by Apache proxy
        email = request.headers.get('X-Remote-User-Email', f'{username}@example.com')
        full_name = request.headers.get('X-Remote-User-Name', username)
        groups_header = request.headers.get('X-Remote-User-Groups', '')

        # Parse full name
        first_name, last_name = username, ''
        if ' ' in full_name:
            first_name, last_name = full_name.split(' ', 1)

        # Parse Keycloak groups from comma-separated header
        keycloak_groups = [g.strip() for g in groups_header.split(',') if g.strip()]

        log.info(f"Remote user auth: username={username}, email={email}, groups={keycloak_groups}")

        # Find or create user
        user = self.find_user(username=username)

        if not user:
            log.info(f"Creating new user: {username}")
            user = self.add_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=self.find_role(self.auth_user_registration_role)
            )
        else:
            # Update existing user info
            log.info(f"Updating existing user: {username}")
            user.email = email
            user.first_name = first_name
            user.last_name = last_name
            self.update_user(user)

        # Map Keycloak groups to Airflow roles
        airflow_roles = self._map_groups_to_roles(keycloak_groups)

        if airflow_roles:
            log.info(f"Assigning roles to {username}: {[r.name for r in airflow_roles]}")
            user.roles = airflow_roles
            self.update_user(user)
        else:
            # No matching groups - assign default Viewer role
            log.warning(f"No matching Keycloak groups for {username}, assigning default Viewer role")
            default_role = self.find_role('Viewer')
            if default_role:
                user.roles = [default_role]
                self.update_user(user)

        return user

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
            List containing single Airflow role object (highest priority)
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
            role = self.find_role(highest_role_name)
            if role:
                return [role]
            else:
                log.error(f"Role '{highest_role_name}' not found in Airflow database")

        return []

# Set the custom security manager
SECURITY_MANAGER_CLASS = CustomSecurityManager

# Security settings
WTF_CSRF_ENABLED = True
WTF_CSRF_TIME_LIMIT = None  # No time limit for CSRF tokens

# Session configuration (matches OIDC session duration)
PERMANENT_SESSION_LIFETIME = 28800  # 8 hours

# Disable public access (all users must authenticate)
AUTH_ROLE_PUBLIC = None

log.info("Airflow webserver configured for Keycloak OIDC remote user authentication")
