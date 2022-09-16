from util import remove_none_attributes, remove_falsey_attributes, \
    base64_str, rev_base64_str
import boto3
import botocore
import json
import time

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

def remove_ddb_meta_from_list_of_recs(recs):
    return [remove_ddb_meta(rec) for rec in recs]

def get_recs_and_token(table_name, pkey_name, pkey_value, skey_name=None, skey_value=None, amount=20, cursor=None, consistent_read=False, remove_ddb=True, ascending=True, index_name=None, skey_prefix=None):
    """Multi-purpose dynamodb query call that returns recs and token"""
    dynamodb = boto3.client("dynamodb")

    key_condition_expression = "#pkey = :pkey"
    expression_names = {
        "#pkey": pkey_name
    }
    if skey_value:
        expression_names["#skey"] = skey_name

    expression_values = {
        ":pkey": add_ddb_meta(pkey_value)
    }

    if skey_prefix:
        key_condition_expression += " AND begins_with(#skey, :skeyprefix)"
        expression_names["#skey"] = skey_name
        expression_values[":skeyprefix"] = {"S": skey_prefix}

    if skey_name and skey_value:
        key_condition_expression += " AND #skey = :skey"
        expression_values[":skey"] = add_ddb_meta(skey_value)

    if cursor:
        cursor = json.loads(rev_base64_str(cursor))
        
    # if cursor:
    #     print(cursor)
    #     cursor = json.loads(cursor)
    #     print(cursor)
    #     print(type(cursor))

    payload = remove_none_attributes({
        "TableName": table_name,
        "IndexName": index_name,
        "Limit": amount,
        "ConsistentRead": consistent_read,
        "KeyConditionExpression": key_condition_expression,
        "ExpressionAttributeNames": expression_names,
        "ExpressionAttributeValues": expression_values,
        "ScanIndexForward": ascending,
        "ExclusiveStartKey": cursor
    })
    # print(payload)

    response = dynamodb.query(**payload)

    token = (base64_str(json.dumps(response.get('LastEvaluatedKey'))) if response.get('LastEvaluatedKey') else None)

    recs = response.get("Items") if response and response.get("Items") else []

    if remove_ddb:
        recs = remove_ddb_meta_from_list_of_recs(recs)

    return recs, token

def get_rec(table_name, pkey_name, pkey_value, skey_name=None, skey_value=None, consistent_read=False, remove_ddb=True, index_name=None):

    recs, _ = get_recs_and_token(table_name=table_name, pkey_name=pkey_name, pkey_value=pkey_value, skey_name=skey_name,
        skey_value=skey_value, amount=1, consistent_read=consistent_read, remove_ddb=remove_ddb, index_name=index_name)

    rec = recs[0] if recs else None

    return rec

def upsert_rec(table_name, values, pkey_name=None, skey_name=None, condition_expression=None, condition_expression_values=None, return_values="ALL_NEW", remove_attribs=None, remove_ddb=True):

    dynamodb = boto3.client("dynamodb")

    actual_pkey_name = pkey_name or 'pkey'
    actual_skey_name = skey_name or 'skey'
    key_names = [actual_pkey_name, actual_skey_name]
    key = {
        actual_pkey_name: add_ddb_meta(values[actual_pkey_name])
    }
    if actual_skey_name in values.keys():
        key[actual_skey_name] = add_ddb_meta(values[actual_skey_name])

    update_expression = "SET " + ", ".join([f"#{attrib} = :{attrib}" for attrib in values.keys() if attrib not in key_names])
    expression_names = { f"#{attrib}": f"{attrib}" for attrib in values.keys() if attrib not in key_names}
    expression_values = {f":{attrib}": value for attrib, value in add_ddb_meta(values).items() if attrib not in key_names}

    if condition_expression_values:
        for attrib, value in condition_expression_values.items():
            if attrib.startswith(':'):
                expression_values[attrib] = add_ddb_meta(value, skip_this_level=False)
            elif attrib.startswith('#'):
                expression_names[attrib] = value
            else:
                expression_names[f"#{attrib}"] = attrib
                expression_values[f":{attrib}"] = add_ddb_meta(value, skip_this_level=False)

    if remove_attribs and isinstance(remove_attribs, list):
        update_expression += " REMOVE " + ", ".join([f"#{attrib}" for attrib in remove_attribs])
        remove_expression_names = { f"#{attrib}": f"{attrib}" for attrib in remove_attribs if attrib not in key_names}
        expression_names = {**expression_names, **remove_expression_names}

    payload = remove_none_attributes({
        "TableName": table_name,
        "Key": key,
        "ExpressionAttributeValues": expression_values,
        "ExpressionAttributeNames": expression_names,
        "UpdateExpression": update_expression,
        "ConditionExpression": condition_expression,
        "ReturnValues": return_values
    })

    response = dynamodb.update_item(**payload)

    if return_values and remove_ddb:
        return remove_ddb_meta(response.get("Attributes")) if response else None

    return response

#######################################
# DYNAMODB EXCEPTIONS
#
# BackupInUseException
# BackupNotFoundException
# ConditionalCheckFailedException
# ContinuousBackupsUnavailableException
# DuplicateItemException
# ExportConflictException
# ExportNotFoundException
# GlobalTableAlreadyExistsException
# GlobalTableNotFoundException
# IdempotentParameterMismatchException
# IndexNotFoundException
# InternalServerError
# InvalidExportTimeException
# InvalidRestoreTimeException
# ItemCollectionSizeLimitExceededException
# LimitExceededException
# PointInTimeRecoveryUnavailableException
# ProvisionedThroughputExceededException
# ReplicaAlreadyExistsException
# ReplicaNotFoundException
# RequestLimitExceeded
# ResourceInUseException
# ResourceNotFoundException
# TableAlreadyExistsException
# TableInUseException
# TableNotFoundException
# TransactionCanceledException
# TransactionConflictException
# TransactionInProgressException
###########################################

def upsert_rec_robust(table_name, values, pkey_name=None, skey_name=None, condition_expression=None, condition_expression_values=None, return_values="ALL_NEW", remove_attribs=None, remove_ddb=True, num_tries=1):
    if num_tries >= 10:
        raise Exception("qprjo upsert_rec_robust: too many tries")

    dynamodb = boto3.client("dynamodb")

    actual_pkey_name = pkey_name or 'pkey'
    actual_skey_name = skey_name or 'skey'
    key_names = [actual_pkey_name, actual_skey_name]
    key = {
        actual_pkey_name: add_ddb_meta(values[actual_pkey_name])
    }
    if actual_skey_name in values.keys():
        key[actual_skey_name] = add_ddb_meta(values[actual_skey_name])

    update_expression = "SET " + ", ".join([f"#{attrib} = :{attrib}" for attrib in values.keys() if attrib not in key_names])
    expression_names = { f"#{attrib}": f"{attrib}" for attrib in values.keys() if attrib not in key_names}
    expression_values = {f":{attrib}": value for attrib, value in add_ddb_meta(values).items() if attrib not in key_names}

    if condition_expression_values:
        for attrib, value in condition_expression_values.items():
            if attrib.startswith(':'):
                expression_values[attrib] = add_ddb_meta(value, skip_this_level=False)
            elif attrib.startswith('#'):
                expression_names[attrib] = value
            else:
                expression_names[f"#{attrib}"] = attrib
                expression_values[f":{attrib}"] = add_ddb_meta(value, skip_this_level=False)

    if remove_attribs and isinstance(remove_attribs, list):
        update_expression += " REMOVE " + ", ".join([f"#{attrib}" for attrib in remove_attribs])
        remove_expression_names = { f"#{attrib}": f"{attrib}" for attrib in remove_attribs if attrib not in key_names}
        expression_names = {**expression_names, **remove_expression_names}

    payload = remove_none_attributes({
        "TableName": table_name,
        "Key": key,
        "ExpressionAttributeValues": expression_values,
        "ExpressionAttributeNames": expression_names,
        "UpdateExpression": update_expression,
        "ConditionExpression": condition_expression,
        "ReturnValues": return_values
    })

    try:
        response = dynamodb.update_item(**payload)
    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in ["RequestLimitExceeded", "InternalServerError", "TransactionConflictException"]:
            print(f"yosla robust retry with error {str(e)}")
            time.sleep(0.1 * num_tries**2)
            return upsert_rec_robust(table_name, values, pkey_name, skey_name, condition_expression, condition_expression_values, return_values, remove_attribs, remove_ddb, num_tries=num_tries+1)
        else:
            print(f"yoslb error in upsert_rec_robust {str(e)}")
            raise e

    if return_values and remove_ddb:
        return remove_ddb_meta(response.get("Attributes")) if response else None

    return response

def delete_rec(table_name, pkey_value, skey_value=None, pkey_name=None, skey_name=None, condition_expression=None, condition_expression_values=None, remove_ddb=True):
    dynamodb = boto3.client("dynamodb")

    key = {}
    key[pkey_name or "pkey"] = pkey_value
    if not skey_value is None:
        key[skey_name or "skey"] = skey_value

    expression_names = {}
    expression_values = {}
    if condition_expression_values:
        for attrib, value in condition_expression_values.items():
            if attrib.startswith(':'):
                expression_values[attrib] = add_ddb_meta(value, skip_this_level=False)
            elif attrib.startswith('#'):
                expression_names[attrib] = attrib[1:]
            else:
                expression_names[f"#{attrib}"] = attrib
                expression_values[f":{attrib}"] = add_ddb_meta(value, skip_this_level=False)

    payload = remove_falsey_attributes({
        "TableName":table_name,
        "Key":add_ddb_meta(key),
        "ConditionExpression":condition_expression,
        "ExpressionAttributeNames": expression_names,
        "ExpressionAttributeValues": expression_values,
        'ReturnValues':'ALL_OLD'
    })

    response = dynamodb.delete_item(**payload)

    if remove_ddb:
        return remove_ddb_meta(response.get("Attributes")) if response else None
    
    return response

def get_s3_key(table_name, pkey_value, skey_value, s3_obj_id):
    return f"ddb/{table_name}/{pkey_value}/{skey_value or '-'}/{s3_obj_id}.json"

def upsert_rec_with_s3(table_name, values, bucket_name, s3_attrib="s3_attrib", condition_expression=None, condition_expression_values=None, return_values=None, pkey_name=None, skey_name=None, remove_attribs=None, s3_server_side_encryption = True, return_s3_value=False):
    real_pkey_name = pkey_name or 'pkey'
    real_skey_name = skey_name or 'skey'

    pkey_value = values[real_pkey_name]
    use_skey = real_skey_name in values
    real_skey_name = real_skey_name if use_skey else None
    skey_value = values[real_skey_name] if use_skey else None

    table_values = {
        key: value for key, value in values.items() if not key == "s3_attrib"
    }

    s3_value = remove_none_attributes({
        s3_attrib: values.get(s3_attrib)
    })

    s3_obj_id = stable_id(table_name, real_pkey_name, real_skey_name, pkey_value, skey_value)
    s3_key = get_s3_key(table_name, pkey_value, skey_value, s3_obj_id)   

    # need to update s3 if the hashes don't match
    need_update_s3 = bool(s3_value)
    new_s3_hash = stable_id(s3_value) if s3_value else None

    # remove primary key attributes from table_values, see if anything is left
    table_values_content = {**table_values}
    if real_pkey_name in table_values_content:
        del table_values_content[real_pkey_name]
    if use_skey and real_skey_name in table_values_content:
        del table_values_content[real_skey_name]

    # need to update dynamo if we have any content or a new hash
    need_update_dynamo = table_values_content or remove_attribs # either real updates or remove attributes

    if need_update_dynamo:
        table_rec = upsert_rec(table_name, table_values, condition_expression=condition_expression, condition_expression_values=condition_expression_values, return_values=return_values, pkey_name=real_pkey_name, skey_name=real_skey_name, remove_attribs=remove_attribs)
    
    else:
        table_rec = get_rec(table_name, real_pkey_name, pkey_value, real_skey_name, skey_value)

    # Update the bucket
    if need_update_s3:
        s3_client = boto3.client("s3")

        body_bytes = json.dumps(s3_value, indent=2).encode()

        params = remove_none_attributes({
            "Body":body_bytes,
            "Bucket":bucket_name,
            "ContentType":"application/json",
            "Key":s3_key,
            "ServerSideEncryption":"AES256" if s3_server_side_encryption else None
        })

        s3_client.put_object(**params)

        return_rec = {**table_rec, **s3_value}

    elif return_s3_value:
        return_rec = add_s3_value_to_rec(table_rec, table_name, bucket_name, real_pkey_name, real_skey_name)

    else:
        return_rec = table_rec

    return return_rec

def get_rec_with_s3(table_name, bucket_name, pkey_name, pkey_value, skey_name=None, skey_value=None, consistent_read=False, remove_ddb=True, index_name=None):
    rec = get_rec(
        table_name,
        pkey_name, pkey_value, 
        skey_name=skey_name, skey_value=skey_value, index_name=index_name,
        consistent_read=consistent_read, remove_ddb=remove_ddb
    )

    return add_s3_value_to_rec(rec, table_name, bucket_name, pkey_name, skey_name)

#Only works with tables that have pkey_name = "pkey" and skey_name = "skey". Required to work with indexes
def get_recs_and_token_with_s3(table_name, bucket_name, pkey_name, pkey_value, skey_name=None, skey_value=None, amount=20, cursor=None, consistent_read=False, index_name=None, ascending=True):
    """Multi-purpose dynamodb query call that returns recs and token with the s3
    object"""
    dynamodb = boto3.client("dynamodb")

    key_condition_expression = "#pkey = :pkey"
    expression_names = {
        "#pkey": pkey_name
    }
    if skey_value:
        expression_names["#skey"] = skey_name

    expression_values = {
        ":pkey": add_ddb_meta(pkey_value)
    }

    if skey_name and skey_value:
        key_condition_expression += " AND #skey = :skey"
        expression_values[":skey"] = add_ddb_meta(skey_value)

    if cursor:
        cursor = json.loads(cursor)

    payload = remove_none_attributes({
        "TableName": table_name,
        "IndexName": index_name,
        "Limit": amount,
        "ConsistentRead": consistent_read,
        "KeyConditionExpression": key_condition_expression,
        "ExpressionAttributeNames": expression_names,
        "ExpressionAttributeValues": expression_values,
        "ScanIndexForward": ascending,
        "ExclusiveStartKey": cursor
    })

    response = dynamodb.query(**payload)

    token = (json.dumps(response.get('LastEvaluatedKey')) if response.get('LastEvaluatedKey') else None)

    recs = response.get("Items") if response and response.get("Items") else []

    if recs:
        recs = remove_ddb_meta_from_list_of_recs(recs)
        final_recs = [
            add_s3_value_to_rec(rec, table_name, bucket_name, "pkey", "skey") for
            rec in recs
        ]

        return final_recs, token

    else:
        return None, None

def add_s3_value_to_rec(rec, table_name, bucket_name, pkey_name, skey_name=None):
    if rec:        
        pkey_value = rec.get(pkey_name)
        skey_value = rec.get(skey_name) if skey_name else None

        s3_obj_id = stable_id(table_name, pkey_name, skey_name, pkey_value, skey_value)
        # s3_obj_id = rec.get(C_S3_KEY)
        # if s3_obj_id:

        s3_key = get_s3_key(table_name, pkey_value, skey_value, s3_obj_id)

        s3_client = boto3.client('s3')

        try:
            obj = s3_client.get_object(
                Bucket=bucket_name, 
                Key=s3_key
            ) # will raise if not found
        except: # do better exception handling here
            obj = None

        if obj:
            body_bytes = obj.get("Body").read()
            body_json = body_bytes.decode()
            s3_values = json.loads(body_json)

            rec = {**rec, **s3_values}
        else:
            pass # leave rec alone

    return rec