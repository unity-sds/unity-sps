# Keycloak OIDC Authentication for Airflow Implementation Plan

## Overview
Integrate Keycloak OIDC authentication with Airflow using the Apache HTTPD proxy layer with role-based access control (RBAC).

**Architecture:** User → Keycloak (OIDC) → Apache Proxy (mod_auth_openidc) → Internal NLB → Airflow (Remote User Auth + RBAC)

## Prerequisites
- Keycloak instance URL, realm name, client ID, and client secret
- Apache HTTPD proxy with mod_auth_openidc module installed
- Venue proxy IAM role needs Secrets Manager read permissions (coordinate with CS team if needed)

---

## Phase 1: Terraform Infrastructure Changes

### 1.1 Add Keycloak Variables
**File:** `terraform-unity/modules/terraform-unity-sps-airflow/variables.tf`

Add after line 84:
```hcl
variable "keycloak_provider_url" {
  description = "Keycloak OIDC provider URL (e.g., https://keycloak.example.com/realms/unity)"
  type        = string
  default     = ""
}

variable "keycloak_client_id" {
  description = "Keycloak OIDC client ID"
  type        = string
  default     = ""
}

variable "keycloak_client_secret" {
  description = "Keycloak OIDC client secret"
  type        = string
  sensitive   = true
  default     = ""
}

variable "enable_oidc_auth" {
  description = "Enable Keycloak OIDC authentication"
  type        = bool
  default     = false
}

variable "keycloak_role_mapping" {
  description = "Mapping of Keycloak groups to Airflow roles"
  type        = map(list(string))
  default = {
    "airflow-admins"  = ["Admin"]
    "airflow-ops"     = ["Op"]
    "airflow-users"   = ["User"]
    "airflow-viewers" = ["Viewer"]
  }
}
```

### 1.2 Create Secrets Manager Resources
**File:** `terraform-unity/modules/terraform-unity-sps-airflow/main.tf`

Add after line 766 (after existing SSM parameters):
```hcl
# Keycloak client secret in Secrets Manager
resource "aws_secretsmanager_secret" "keycloak_client_secret" {
  count                   = var.enable_oidc_auth ? 1 : 0
  name                    = format(local.resource_name_prefix, "keycloak-client-secret")
  description             = "Keycloak OIDC client secret for Airflow"
  recovery_window_in_days = 7
  tags = merge(local.common_tags, {
    Name      = format(local.resource_name_prefix, "keycloak-client-secret")
    Component = "airflow"
  })
}

resource "aws_secretsmanager_secret_version" "keycloak_client_secret" {
  count         = var.enable_oidc_auth ? 1 : 0
  secret_id     = aws_secretsmanager_secret.keycloak_client_secret[0].id
  secret_string = var.keycloak_client_secret
}

# SSM parameters for Keycloak config
resource "aws_ssm_parameter" "keycloak_config" {
  for_each = var.enable_oidc_auth ? {
    provider_url     = var.keycloak_provider_url
    client_id        = var.keycloak_client_id
    client_secret_arn = try(aws_secretsmanager_secret.keycloak_client_secret[0].arn, "")
  } : {}

  name  = format("/%s", join("/", compact(["unity", var.project, var.venue, "cs", "security", "keycloak", each.key])))
  type  = "String"
  value = each.value
  tags  = merge(local.common_tags, { Component = "airflow" })
}
```

### 1.3 Update Proxy SSM Parameter
**File:** `terraform-unity/modules/terraform-unity-sps-airflow/main.tf`

Replace lines 740-766 (aws_ssm_parameter.unity_proxy_airflow_ui):
```hcl
resource "aws_ssm_parameter" "unity_proxy_airflow_ui" {
  name        = format("/%s", join("/", compact(["unity", var.project, var.venue, "cs", "management", "proxy", "configurations", "015-sps-airflow-ui"])))
  description = "Unity-proxy configuration for Airflow UI with optional OIDC"
  type        = "String"
  value       = var.enable_oidc_auth ? templatefile("${path.module}/templates/proxy_oidc.conf.tpl", {
    project              = var.project
    venue                = var.venue
    airflow_nlb_hostname = data.kubernetes_service.airflow_ingress_internal.status[0].load_balancer[0].ingress[0].hostname
    keycloak_provider_url = var.keycloak_provider_url
    keycloak_client_id    = var.keycloak_client_id
  }) : <<-EOT

    <Location "/${var.project}/${var.venue}/sps/">
      ProxyPassReverse "/"
    </Location>
    <Location "/${var.project}/${var.venue}/sps/${var.project}/${var.venue}/sps/home">
      Redirect "/${var.project}/${var.venue}/sps/home"
    </Location>
    <LocationMatch "^/${var.project}/${var.venue}/sps/(.*)$">
      ProxyPassMatch "http://${data.kubernetes_service.airflow_ingress_internal.status[0].load_balancer[0].ingress[0].hostname}:5000/$1" retry=5 disablereuse=On
      ProxyPreserveHost On
      FallbackResource /management/index.html
      AddOutputFilterByType INFLATE;SUBSTITUTE;DEFLATE text/html
      Substitute "s|\"/([^\"]*)|\"/${var.project}/${var.venue}/sps/$1|q"
    </LocationMatch>

EOT
  tags = merge(local.common_tags, { Component = "SSM" })
}
```

### 1.4 Create Proxy Template File
**File:** `terraform-unity/modules/terraform-unity-sps-airflow/templates/proxy_oidc.conf.tpl` (NEW)

```apache
# Apache mod_auth_openidc configuration for Keycloak
OIDCProviderMetadataURL ${keycloak_provider_url}/.well-known/openid-configuration
OIDCClientID ${keycloak_client_id}
OIDCClientSecret "REPLACE_WITH_SECRET_FROM_SECRETS_MANAGER"
OIDCRedirectURI https://REPLACE_WITH_PROXY_DOMAIN/${project}/${venue}/sps/redirect_uri
OIDCCryptoPassphrase "REPLACE_WITH_GENERATED_PASSPHRASE"

# Session config
OIDCSessionInactivityTimeout 3600
OIDCSessionMaxDuration 28800

# Claims
OIDCRemoteUserClaim preferred_username
OIDCScope "openid email profile groups"

# Cookie settings
OIDCCookiePath /${project}/${venue}/sps/
OIDCCookieSameSite On

<Location "/${project}/${venue}/sps/">
  AuthType openid-connect
  Require valid-user

  # Forward OIDC claims to Airflow
  RequestHeader set X-Remote-User "%{REMOTE_USER}e"
  RequestHeader set X-Remote-User-Email "%{OIDC_CLAIM_email}e"
  RequestHeader set X-Remote-User-Groups "%{OIDC_CLAIM_groups}e"
  RequestHeader set X-Remote-User-Name "%{OIDC_CLAIM_name}e"

  ProxyPassReverse "/"
</Location>

<Location "/${project}/${venue}/sps/${project}/${venue}/sps/home">
  Redirect "/${project}/${venue}/sps/home"
</Location>

<LocationMatch "^/${project}/${venue}/sps/(.*)$">
  AuthType openid-connect
  Require valid-user

  RequestHeader set X-Remote-User "%{REMOTE_USER}e"
  RequestHeader set X-Remote-User-Email "%{OIDC_CLAIM_email}e"
  RequestHeader set X-Remote-User-Groups "%{OIDC_CLAIM_groups}e"
  RequestHeader set X-Remote-User-Name "%{OIDC_CLAIM_name}e"

  ProxyPassMatch "http://${airflow_nlb_hostname}:5000/$1" retry=5 disablereuse=On
  ProxyPreserveHost On
  FallbackResource /management/index.html
  AddOutputFilterByType INFLATE;SUBSTITUTE;DEFLATE text/html
  Substitute "s|\"/([^\"]*)|\"/${project}/${venue}/sps/$1|q"
</LocationMatch>
```

### 1.5 Update tfvars File
**File:** `terraform-unity/tfvars/unity-dev-sps-airflow.tfvars`

Add at end of file:
```hcl
# Keycloak OIDC Configuration
enable_oidc_auth      = false  # Set to true when ready to enable
keycloak_provider_url = "https://keycloak.example.com/realms/unity"  # REPLACE
keycloak_client_id    = "airflow-unity-dev"  # REPLACE
keycloak_client_secret = "your-client-secret"  # REPLACE - keep secret!

keycloak_role_mapping = {
  "airflow-admins"  = ["Admin"]
  "airflow-ops"     = ["Op"]
  "airflow-users"   = ["User"]
  "airflow-viewers" = ["Viewer"]
}
```

---

## Phase 2: Airflow Configuration

### 2.1 Replace Webserver Config
**File:** `airflow/config/webserver_config.py`

Replace entire file with:
```python
# Keycloak OIDC Remote User Authentication
import os
import logging
from flask_appbuilder.security.manager import AUTH_REMOTE_USER

log = logging.getLogger(__name__)

AUTH_TYPE = AUTH_REMOTE_USER
AUTH_USER_REGISTRATION = True
AUTH_USER_REGISTRATION_ROLE = "Viewer"

from airflow.www.security import AirflowSecurityManager

class CustomSecurityManager(AirflowSecurityManager):
    """Map Keycloak groups to Airflow roles"""

    def auth_user_remote_user(self, username):
        from flask import request

        email = request.headers.get('X-Remote-User-Email', f'{username}@example.com')
        full_name = request.headers.get('X-Remote-User-Name', username)
        groups = request.headers.get('X-Remote-User-Groups', '')

        first_name, last_name = username, ''
        if ' ' in full_name:
            first_name, last_name = full_name.split(' ', 1)

        keycloak_groups = [g.strip() for g in groups.split(',') if g.strip()]
        log.info(f"Auth: {username}, groups: {keycloak_groups}")

        user = self.find_user(username=username)
        if not user:
            user = self.add_user(
                username=username,
                first_name=first_name,
                last_name=last_name,
                email=email,
                role=self.find_role(self.auth_user_registration_role)
            )

        # Map groups to roles
        role_mapping = {
            'airflow-admins': 'Admin',
            'airflow-ops': 'Op',
            'airflow-users': 'User',
            'airflow-viewers': 'Viewer',
        }

        role_priority = ['Viewer', 'User', 'Op', 'Admin']
        highest_role = None
        highest_priority = -1

        for group in keycloak_groups:
            if group in role_mapping:
                role_name = role_mapping[group]
                if role_name in role_priority:
                    priority = role_priority.index(role_name)
                    if priority > highest_priority:
                        highest_priority = priority
                        highest_role = role_name

        if highest_role:
            role = self.find_role(highest_role)
            if role:
                user.roles = [role]
                self.update_user(user)
                log.info(f"Assigned role {highest_role} to {username}")

        return user

SECURITY_MANAGER_CLASS = CustomSecurityManager
WTF_CSRF_ENABLED = True
PERMANENT_SESSION_LIFETIME = 28800
AUTH_ROLE_PUBLIC = None

log.info("Airflow configured for OIDC remote user authentication")
```

### 2.2 Update Helm Values
**File:** `airflow/helm/values.tmpl.yaml`

Add after line 374 (in extraEnv section):
```yaml
  - name: AIRFLOW__WEBSERVER__AUTH_TYPE
    value: "AUTH_REMOTE_USER"
  - name: AIRFLOW__WEBSERVER__RBAC
    value: "True"
```

---

## Phase 3: Keycloak Configuration (External)

### 3.1 Create Keycloak Client
In Keycloak admin console:
1. Create new OIDC client: `airflow-{project}-{venue}`
2. Access Type: `confidential`
3. Valid Redirect URIs: `https://{proxy-domain}/{project}/{venue}/sps/*`
4. Client Scopes: Add `groups` scope with Group Membership mapper
5. Save and copy the client secret

### 3.2 Create Keycloak Groups
Create these groups:
- `airflow-admins` - Full admin access
- `airflow-ops` - Operational access
- `airflow-users` - User access
- `airflow-viewers` - Read-only access

### 3.3 Assign Test Users
Add test users to groups for validation.

---

## Phase 4: Proxy Server Configuration

### 4.1 Install mod_auth_openidc
On venue proxy server:
```bash
# Amazon Linux 2
sudo yum install -y mod_auth_openidc

# Verify module
httpd -M | grep auth_openidc
```

### 4.2 Create Secret Retrieval Script
**File:** `/etc/httpd/scripts/update-keycloak-secret.sh` (on proxy server)

```bash
#!/bin/bash
# Retrieve Keycloak client secret and update Apache config

PROJECT="unity"
VENUE="dev"

# Get secret ARN from SSM
SECRET_ARN=$(aws ssm get-parameter \
  --name "/unity/${PROJECT}/${VENUE}/cs/security/keycloak/client_secret_arn" \
  --query 'Parameter.Value' --output text)

# Get actual secret
CLIENT_SECRET=$(aws secretsmanager get-secret-value \
  --secret-id "$SECRET_ARN" \
  --query 'SecretString' --output text)

# Get proxy config from SSM
aws ssm get-parameter \
  --name "/unity/${PROJECT}/${VENUE}/cs/management/proxy/configurations/015-sps-airflow-ui" \
  --query 'Parameter.Value' --output text > /tmp/airflow-oidc.conf

# Replace placeholders
sed -i "s/REPLACE_WITH_SECRET_FROM_SECRETS_MANAGER/${CLIENT_SECRET}/" /tmp/airflow-oidc.conf

# Generate crypto passphrase
CRYPTO_PASS=$(openssl rand -base64 32)
sed -i "s/REPLACE_WITH_GENERATED_PASSPHRASE/${CRYPTO_PASS}/" /tmp/airflow-oidc.conf

# Replace proxy domain (adjust as needed)
sed -i "s/REPLACE_WITH_PROXY_DOMAIN/unity-dev-proxy.example.com/" /tmp/airflow-oidc.conf

# Install config
sudo cp /tmp/airflow-oidc.conf /etc/httpd/conf.d/
sudo systemctl reload httpd

echo "Keycloak configuration updated"
```

### 4.3 Add IAM Permissions
The venue proxy IAM role needs this policy:
```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Action": [
      "secretsmanager:GetSecretValue",
      "secretsmanager:DescribeSecret"
    ],
    "Resource": "arn:aws:secretsmanager:*:*:secret:*-sps-keycloak-client-secret-*"
  }]
}
```

---

## Phase 5: Deployment Steps

### Step 1: Apply Infrastructure (OIDC Disabled)
```bash
cd terraform-unity/
terraform plan -var-file="tfvars/unity-dev-sps-airflow.tfvars"
terraform apply -var-file="tfvars/unity-dev-sps-airflow.tfvars"
```

This creates Secrets Manager secret and SSM parameters but keeps OIDC disabled.

### Step 2: Configure Proxy Server
1. Install mod_auth_openidc on venue proxy
2. Add IAM permissions for Secrets Manager access
3. Run secret retrieval script
4. Verify Apache config loads without errors

### Step 3: Enable OIDC
Update `tfvars/unity-dev-sps-airflow.tfvars`:
```hcl
enable_oidc_auth = true
```

Apply:
```bash
terraform apply -var-file="tfvars/unity-dev-sps-airflow.tfvars"
```

This updates the proxy SSM parameter with OIDC config. Lambda auto-deploys it.

### Step 4: Restart Airflow
```bash
kubectl rollout restart deployment/airflow-webserver -n sps
```

### Step 5: Test Authentication
1. Navigate to `https://{proxy-domain}/{project}/{venue}/sps/`
2. Should redirect to Keycloak login
3. Login with test admin user
4. Verify you're logged into Airflow as Admin

---

## Phase 6: Validation

### Security Tests
- [ ] Verify OIDC redirect works
- [ ] Verify session timeout (8 hours)
- [ ] Verify logout works
- [ ] Test each role (Admin, Op, User, Viewer)
- [ ] Verify role permissions enforce correctly

### Role Mapping Tests
- [ ] Login as airflow-admins member → Admin role
- [ ] Login as airflow-ops member → Op role
- [ ] Login as airflow-users member → User role
- [ ] Login as airflow-viewers member → Viewer role

### Negative Tests
- [ ] User with no groups → Viewer role (default)
- [ ] Invalid Keycloak credentials → Access denied
- [ ] Expired session → Redirect to login

---

## Rollback Plan

If issues occur:

**Quick Disable:**
```bash
# Set enable_oidc_auth = false in tfvars
terraform apply -var-file="tfvars/unity-dev-sps-airflow.tfvars"
```

This reverts proxy to non-OIDC configuration (open access).

**Full Rollback:**
```bash
git checkout HEAD~1 airflow/config/webserver_config.py
terraform apply -var-file="tfvars/unity-dev-sps-airflow.tfvars" \
  -var="enable_oidc_auth=false"
kubectl rollout restart deployment/airflow-webserver -n sps
```

---

## Critical Files

1. **terraform-unity/modules/terraform-unity-sps-airflow/main.tf** (lines 740-790)
   - Add Secrets Manager and SSM resources
   - Update proxy SSM parameter with template

2. **terraform-unity/modules/terraform-unity-sps-airflow/variables.tf** (after line 84)
   - Add Keycloak configuration variables

3. **terraform-unity/modules/terraform-unity-sps-airflow/templates/proxy_oidc.conf.tpl** (NEW)
   - Apache HTTPD OIDC configuration template

4. **airflow/config/webserver_config.py** (replace entire file)
   - Enable remote user auth and RBAC with role mapping

5. **airflow/helm/values.tmpl.yaml** (lines 374+)
   - Add environment variables for remote user auth

6. **terraform-unity/tfvars/unity-dev-sps-airflow.tfvars** (append)
   - Add Keycloak connection details

---

## Security Considerations

1. **Client secret** stored in Secrets Manager (encrypted)
2. **Internal NLB** prevents direct header spoofing
3. **Network isolation** - proxy is only entry point
4. **Defense in depth** - OIDC at proxy + RBAC in Airflow
5. **Least privilege** - Default role is Viewer (read-only)

---

## Post-Implementation

### Documentation Needed
- User guide: How to login with Keycloak
- Admin guide: How to manage groups and roles
- Troubleshooting: Common OIDC issues

### Monitoring
- OIDC authentication success/failure rates
- Session timeout events
- Unauthorized access attempts
- Secrets Manager access logs

### Future Enhancements
- API authentication with OIDC bearer tokens
- DAG-level permissions based on groups
- Audit logging integration
