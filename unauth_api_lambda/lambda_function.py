import json
import traceback

from auth import parse_permission_and_path_args_from_path
from dogs import get_more_dogs
from util import remove_none_attributes

from aws_lambda_powertools import Logger

logger = Logger()

def api_get_more_dogs(access_token=None, path_args=None, body=None):
    amount = body.get("amount") or 20
    return get_more_dogs(amount)

all_functions_mapped = {
    "get_more_dogs": api_get_more_dogs
}

@logger.inject_lambda_context
def lambda_handler(event, context):
    headers = event['headers']
    content_type = headers.get("content-type") if headers else None
    path = event['rawPath']
    http_method = event.get("requestContext", {}).get("http", {}).get('method')
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

    user_scopes = {"unauth": True}
    permission_response = parse_permission_and_path_args_from_path(
        logger, path, user_scopes, None, http_method, "/live/"
    )
    logger.debug("permission_response = {}".format(permission_response))

    path_args = permission_response.get("path_args") or {}
    name_of_function_to_call = permission_response.get("name_of_function_to_call")

    if name_of_function_to_call:
        real_function_to_call = all_functions_mapped[name_of_function_to_call]
        qs_params.update(body)
        if qs_params.get("amount"):
            qs_params['amount'] = int(qs_params['amount'])
            
        payload = remove_none_attributes({
            "path_args": path_args,
            "body":qs_params
        })

        try:
            result = real_function_to_call(**payload)
        except Exception as e:
            error_msg = traceback.format_exc()
            logger.error(error_msg)
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
