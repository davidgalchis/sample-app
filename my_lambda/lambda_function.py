import boto3
import os
import json
import traceback
import json

def lambda_handler(event, context):
    try:
        table_name = lambda_env("table_name")
    
        dynamodb = boto3.client("dynamodb")
    
        response = dynamodb.update_item(
                TableName=table_name,
                Key=add_ddb_meta({"pkey": "dkf"}),
                UpdateExpression = "ADD scoress :val",
                ExpressionAttributeValues = add_ddb_meta({
                    ":val": 1
                    }),
                ReturnValues = "ALL_NEW"
            )
    
        item = remove_ddb_meta(response.get("Attributes")) if response else None
    
        final_response = {
            "statusCode":200,
            "headers": {
                "Access-Control-Allow-Headers" : "Authorization,Content-Type,x-amz-date,x-amzm-header,x-api-key,x-apigateway-header",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "OPTIONS,POST,GET",
                'Content-Type': 'application/json'
            },
            "body": json.dumps({"click_counter": f"{item.get('scoress')}"})
        }
    
        return final_response
    except:
        print(traceback.format_exc())

def add_ddb_meta(obj, skip_this_level=True):
    """Adds ddb meta to an object"""
    if isinstance(obj, dict):
        if skip_this_level:
            return {
                key: add_ddb_meta(value, skip_this_level=False)
                for key, value in obj.items()
            }
        else:
            return {
                "M": add_ddb_meta(obj)
            }
    elif isinstance(obj, (list, tuple)):
        if skip_this_level:
            return [
                add_ddb_meta(item, skip_this_level=False)
                for item in obj
            ]
        else:
            return {
                "L": add_ddb_meta(obj)
            }
    elif isinstance(obj, str):
        return {
            "S": obj
        }
    elif isinstance(obj, bytes):
        return {
            "B": obj
        }
    elif isinstance(obj, bool):
        return {
            "BOOL": obj
        }
    elif isinstance(obj, (int, float)):
        return {
            "N": f"{obj}"
        }
    elif obj is None:
        return {
            "NULL": True
        }
    else:
        raise Exception(f"Type not currently supported for add_ddb_meta: {type(obj)}")

def remove_ddb_meta(obj, skip_this_level=True):
    """Removes ddb meta from object"""
    if isinstance(obj, dict):
        if skip_this_level:
            return {
                key: remove_ddb_meta(value, skip_this_level=False)
                for key, value in obj.items()
            }
        else:
            if len(obj.keys()) != 1:
                raise Exception(f"Improper format: One key expected for ddb meta, but got {len(obj.keys())}: {obj}")

            key = list(obj.keys())[0]
            value = obj[key]

            if key == "NULL":
                return None
            elif key == "N":
                try:
                    return remove_ddb_meta(int(value))
                except ValueError:
                    return remove_ddb_meta(float(value))
            else:
                return remove_ddb_meta(value)
    elif isinstance(obj, list):
        return [remove_ddb_meta(item, skip_this_level=False) for item in obj]
    else:
        return obj

def lambda_env(key):
    try:
        return os.environ.get(key)
    except Exception as e:
        raise e