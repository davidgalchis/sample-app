from user import get_user
from auth import parse_permission_and_path_args_from_path
from aws_lambda_powertools import Logger

logger = Logger()

def not_authorized(message):
    return {
        "isAuthorized":False,
        "message": message,
        "context": {
            "error": message
        }
    }

@logger.inject_lambda_context
def lambda_handler(event, context):
    logger.debug(f"event={event}")
    headers = event['headers']
    content_type = headers.get("content-type") if headers else None
    path = event['rawPath']
    http_method = event.get("requestContext").get("http").get("method")

    # Is this just an options call?
    if http_method == "OPTIONS":
        return not_authorized("OPTIONS")

    # Is this the right content type?
    if content_type != "application/json":
        return not_authorized("Incorrect Content-Type: expected application/json")

    # Do they provide a session token in the authorization header?
    token = headers.get("authorization", "").replace("Bearer ", "")

    account_id = None
    if not token:
        account_id = "public"
        user_scopes = {"foundation": True}
        logger.info("No token, foundation scope")

    else:
        raw_split_path = path.split("/account/")
        # If account_name appears at least once
        if len(raw_split_path) >= 2:
            account_id = raw_split_path[1].split("/",1)[0]
        else:
            account_id = None
        logger.info(f"account_id = {account_id}")

        if account_id:
            logger.info(f"account_id = {account_id}")
            # Get their permissions for the given account
            user_record = get_user(account_id)
            if not user_record:
                return not_authorized("User does not exist")

            user_scopes = user_record.get("user_scopes")
        else:
            logger.info("No account in path, foundation scope")   
            user_scopes = {"foundation": True}


    logger.info(user_scopes)
    permission_response = parse_permission_and_path_args_from_path(
        logger, path, user_scopes, account_id, http_method, "/live/"
        )
    logger.info(permission_response)
    if permission_response.get("allowed"):
        response = {
            "isAuthorized":True,
            "context": {
                # These args should be passed to the api-lambda being called
                "path_args": permission_response.get("path_args"),
                "name_of_function_to_call": permission_response.get("name_of_function_to_call"),
                "account_id": account_id
            }
        }
        return response
    else:
        return not_authorized("Unauthorized")