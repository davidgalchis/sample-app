import json
from os import access
import re
import boto3
from account import initiate_account_auth, get_account_by_username
from util import lambda_env


def lambda_handler(event, context):

    headers = event['headers']
    content_type = headers.get("content-type") if headers else None
    bodystr = event.get('body')
    http_method = event.get("requestContext").get("http").get("method")

    # Is this just an options call?
    if http_method == "OPTIONS":
        response = {
            "statusCode": 200,
            "body": json.dumps({
                "exists": True
            })
        }
        return response


    # Is this the right content type?
    if content_type != "application/json":
        response = {
            "statusCode": 400,
            "body": json.dumps({
                "error": "Incorrect Content-Type: expected application/json"
            })
        }
        return response

    body = json.loads(bodystr)
    # Get username/password from body
    username = body.get("username")
    password = body.get("password")
    user_pool_id = lambda_env("user_pool_id")
    app_client_id = lambda_env("app_client_id")
    app_client_secret = lambda_env("app_client_secret")
    auth_response = initiate_account_auth(user_pool_id, app_client_id, app_client_secret, username, password)
    print(auth_response)
    auth_details = auth_response.get("AuthenticationResult", {})
    print(auth_details)
    access_token, refresh_token = auth_details.get("AccessToken"), auth_details.get("RefreshToken")
    print(access_token, refresh_token)
    if not access_token:
        response = {
            "statusCode":401,
            "body":json.dumps({"error":"Username and/or password is invalid."})
        }
        return response

    else:
        account_response = get_account_by_username(username)
        response = {
            "statusCode":200,
            "body":json.dumps({"access_token":access_token, "refresh_token": refresh_token, "account_id": account_response.get("account_id")})
        }
        return response
