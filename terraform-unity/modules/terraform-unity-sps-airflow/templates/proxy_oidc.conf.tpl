# Apache mod_auth_openidc configuration for Keycloak OIDC Authentication
# This configuration is deployed when enable_oidc_auth is true

# OIDC Provider Configuration
OIDCProviderMetadataURL ${keycloak_provider_url}/.well-known/openid-configuration
OIDCClientID ${keycloak_client_id}

# Client secret - retrieved from AWS Parameter Store at runtime by proxy server
# The proxy server must retrieve the secret from: ${keycloak_client_secret_ssm_param}
# and replace this placeholder before Apache loads the config
OIDCClientSecret "REPLACE_WITH_SECRET_FROM_PARAMETER_STORE"

# Redirect URI - must match Keycloak client Valid Redirect URIs setting
%{ if proxy_domain != "" ~}
OIDCRedirectURI https://${proxy_domain}/${project}/${venue}/sps/redirect_uri
%{ else ~}
OIDCRedirectURI https://REPLACE_WITH_PROXY_DOMAIN/${project}/${venue}/sps/redirect_uri
%{ endif ~}

# Crypto passphrase for encrypting session cookies
# Generate at runtime with: openssl rand -base64 32
OIDCCryptoPassphrase "REPLACE_WITH_GENERATED_CRYPTO_PASSPHRASE"

# Session configuration
OIDCSessionInactivityTimeout 3600     # 1 hour of inactivity
OIDCSessionMaxDuration 28800          # 8 hours maximum session

# User identification and claims
OIDCRemoteUserClaim preferred_username
OIDCScope "openid email profile groups"

# Cookie settings
OIDCCookiePath /${project}/${venue}/sps/
OIDCCookieSameSite On

# Airflow UI - Main location with authentication
<Location "/${project}/${venue}/sps/">
  AuthType openid-connect
  Require valid-user

  # Forward OIDC user claims to Airflow as HTTP headers
  # Airflow will use these headers for authentication and authorization
  RequestHeader set X-Remote-User "%%{REMOTE_USER}e"
  RequestHeader set X-Remote-User-Email "%%{OIDC_CLAIM_email}e"
  RequestHeader set X-Remote-User-Groups "%%{OIDC_CLAIM_groups}e"
  RequestHeader set X-Remote-User-Name "%%{OIDC_CLAIM_name}e"

  ProxyPassReverse "/"
</Location>

# Handle nested path redirects
<Location "/${project}/${venue}/sps/${project}/${venue}/sps/home">
  Redirect "/${project}/${venue}/sps/home"
</Location>

# Main proxy pass configuration with authentication
<LocationMatch "^/${project}/${venue}/sps/(.*)$">
  AuthType openid-connect
  Require valid-user

  # Forward OIDC claims to Airflow backend
  RequestHeader set X-Remote-User "%%{REMOTE_USER}e"
  RequestHeader set X-Remote-User-Email "%%{OIDC_CLAIM_email}e"
  RequestHeader set X-Remote-User-Groups "%%{OIDC_CLAIM_groups}e"
  RequestHeader set X-Remote-User-Name "%%{OIDC_CLAIM_name}e"

  # Proxy to internal Airflow NLB
  ProxyPassMatch "http://${airflow_nlb_hostname}:5000/$1" retry=5 disablereuse=On
  ProxyPreserveHost On
  FallbackResource /management/index.html

  # URL rewriting for embedded links
  AddOutputFilterByType INFLATE;SUBSTITUTE;DEFLATE text/html
  Substitute "s|\"/([^\"]*)|\"/${project}/${venue}/sps/$1|q"
</LocationMatch>
