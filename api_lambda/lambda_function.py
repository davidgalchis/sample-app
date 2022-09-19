import json
import traceback
import datetime

from dogs import get_more_dogs, save_dog, list_saved_dogs
from account import create_account_and_user, refresh_account_token, get_jwt_public_keys, is_access_token_valid
from util import remove_none_attributes, random_id, dict_get_required, current_day, lambda_env


user_pool_id = lambda_env("user_pool_id")
region = lambda_env("AWS_REGION")
jwt_keys = get_jwt_public_keys(user_pool_id, region)


def api_refresh_token(access_token=None, path_args=None, body=None):
    user_pool_id = lambda_env("user_pool_id")
    app_client_id = lambda_env("app_client_id")
    app_client_secret = lambda_env("app_client_secret")
    refresh_token = dict_get_required(path_args or {}, "refresh_token", valuetype=str)

    claims = is_access_token_valid(access_token, jwt_keys, app_client_id, user_pool_id, region)
    username = dict_get_required(claims or {}, "username", valuetype=str)

    return refresh_account_token(user_pool_id, app_client_id, app_client_secret, refresh_token, username)

def api_create_account_and_user(access_token=None, path_args=None, body=None):
    user_pool_id = lambda_env("user_pool_id")
    app_client_id = lambda_env("app_client_id")
    app_client_secret = lambda_env("app_client_secret")
    name = dict_get_required(path_args or {}, "name", valuetype=str)
    username = dict_get_required(path_args or {}, "username", valuetype=str)
    email = dict_get_required(path_args or {}, "email", valuetype=str)
    password = dict_get_required(path_args or {}, "password", valuetype=str)
    return create_account_and_user(user_pool_id, app_client_id, app_client_secret, name, username, email, password)

def api_get_more_dogs(access_token=None, path_args=None, body=None):
    amount = body.get("amount") or 20
    return get_more_dogs(amount)

def api_save_dog(access_token=None, path_args=None, body=None):
    account_id = dict_get_required(path_args or {}, "account_id", valuetype=str)
    dog_url = dict_get_required(body or {}, "dog_url", valuetype=str)
    return save_dog(account_id, dog_url)

def api_list_saved_dogs(access_token=None, path_args=None, body=None):
    account_id = dict_get_required(path_args or {}, "account_id", valuetype=str)
    cursor = body.get("cursor")
    amount = body.get("amount") or 20
    
    dogs, next_cursor = list_saved_dogs(account_id, amount, cursor)

    return {
        "dogs": dogs,
        "cursor": next_cursor
    }
    
all_functions_mapped = {
    "get_more_dogs":api_get_more_dogs,
    "save_dog":api_save_dog,
    "list_saved_dogs":api_list_saved_dogs,
    "create_account_and_user":api_create_account_and_user,
    "refresh_token": api_refresh_token
}

def lambda_handler(event, context):
    print(event)
    headers = event['headers']
    content_type = headers.get("content-type") if headers else None
    path = event['rawPath']
    http_method = event.get("requestContext", {}).get("http", {}).get('method')
    name_of_function_to_call = event.get("requestContext", {}).get("authorizer",{}).get("lambda",{}).get("name_of_function_to_call")
    path_args = event.get("requestContext", {}).get("authorizer",{}).get("lambda",{}).get("path_args") or {}
    account_id = event.get("requestContext", {}).get("authorizer",{}).get("lambda",{}).get("account_id")
    access_token = headers.get("authorization", "").replace("Bearer ", "")
    bodystr = event.get('body')
    qs_params = event.get("queryStringParameters") or {}

    # Is this just an options call?
    if http_method == "OPTIONS":
        response = {
            "statusCode": 200,
            "body": json.dumps({"exists":True})
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

    # Try to load the body
    if bodystr:
        try:
            body = json.loads(bodystr) or {}
        except Exception as ex:
            response = {
                "statusCode": 400,
                "body": str(ex)
            }
            return response
    else:
        body = {}

    if name_of_function_to_call:
        print(f"Calling {name_of_function_to_call}")
        real_function_to_call = all_functions_mapped[name_of_function_to_call]
        qs_params.update(body)
        if qs_params.get("amount"):
            qs_params['amount'] = int(qs_params['amount'])
            
        payload = remove_none_attributes({
            "access_token": access_token,
            "path_args": path_args,
            "body":qs_params
        })

        try:
            result = real_function_to_call(**payload)
        except Exception as e:
            error_msg = traceback.format_exc()
            print(error_msg)
            response = {
                "statusCode":400,
                "body":json.dumps({
                    "error": str(e)
                })
            }
            return response
        response = {
            "statusCode":200,
            "body":json.dumps(result)
        }
        return response

    response = {
        "statusCode":200,
        "body":json.dumps("Your call wasn't a valid call!")
    }

    return response
