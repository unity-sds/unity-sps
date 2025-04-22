import argparse
from getpass import getpass

import requests


def fetch_token(username, password, client_id, region):
    url = f"https://cognito-idp.{region}.amazonaws.com"
    payload = {
        "AuthParameters": {"USERNAME": f"{username}", "PASSWORD": f"{password}"},
        "AuthFlow": "USER_PASSWORD_AUTH",
        "ClientId": f"{client_id}",
    }
    # Set headers
    headers = {
        "X-Amz-Target": "AWSCognitoIdentityProviderService.InitiateAuth",
        "Content-Type": "application/x-amz-json-1.1",
    }
    # POST request
    res = requests.post(url, json=payload, headers=headers).json()
    if "AuthenticationResult" in res:
        access_token = res["AuthenticationResult"]["AccessToken"]
        return access_token


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("-u", "--username", type=str, required=True)
    parser.add_argument("-p", "--password", type=str, default="")
    parser.add_argument("-c", "--client_id", type=str, required=True, help="The Cognito Client ID")
    parser.add_argument("-r", "--region", type=str, default="us-west-2")
    args = parser.parse_args()
    if args.password == "":
        args.password = getpass("Cognito password:")
    access_token = fetch_token(args.username, args.password, args.client_id, args.region)
    print(f"Authorization: Bearer {access_token}")
