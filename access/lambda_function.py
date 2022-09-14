import json


def lambda_handler(event, context):
    """
    Trades an access code for a session token
    """
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
    # Get cognito information from access_code

    # github_code = body.get("github_code")

    # if not github_code:
    #     response = {
    #         "statusCode":401,
    #         "body":json.dumps({"error":"Github code not provided"})
    #     }
    #     return response

    access_token, refresh_token = "", "" #authenticate_with_github2(github_code=github_code)
    if not access_token:
        response = {
            "statusCode":401,
            "body":json.dumps({"error":"Access code invalid"})
        }
        return response

    else:
        response = {
            "statusCode":200,
            "body":json.dumps({"access_token":access_token, "refresh_token": refresh_token})
        }
        return response
