import io
import os
import uuid
import time
import urllib
import hashlib
import types
import json
import zipfile
import base64
import boto3
import datetime
import random
import string

def encode_internal_id(id):
    str_id = str(id)
    return urllib.parse.quote_plus(str_id, safe='')

def decode_internal_id(encoded_id):
    return urllib.parse.unquote_plus(encoded_id)

def random_id():
    return str(uuid.uuid4())

def random_dynamo_id():
    return dynamo_encode(random_id())

def dynamo_encode(string):
    return str(base64.b32encode(bytes(string, "utf-8"))).replace("=", "v")[2:-1] #To filter b' and '

def dynamo_decode(string):
    return str(base64.b32encode(bytes(string.replace("v", "="), "utf-8")))[2:-1]

def base64_str(string):
    return base64.b64encode(string.encode("ascii")).decode("ascii")

def rev_base64_str(string):
    return base64.b64decode(string.encode("ascii")).decode("ascii")

def convert_recs_for_api(obj, transformf):
    if obj is None:
        return None
    # List of items
    elif isinstance(obj, list):
        api_list = [
            transformf(rec)
            for rec in obj
        ]
        return api_list
    # Single item
    else:
        return transformf(obj)

def current_epoch_time_usec_num():
    return int(time.time() * 1000000)

def current_epoch_time_usec_str():
    return str(current_epoch_time_usec_num())

def current_day():
    return datetime.datetime.today().isoformat()[:10]

def hash_dict(diction):
    return json.dumps(diction, sort_keys=True, default=str)

def remove_falsey_attributes(obj):
    return {k: v for k,v in obj.items() if v}  

def remove_none_attributes(payload):
    """Assumes dict"""
    return {k: v for k, v in payload.items() if not v is None}

def json_loader(item):
    if isinstance(item, str):
        return json.loads(item)
    elif isinstance(item, dict) or (item == None) or isinstance(item, list):
        return item
    else:
        raise Exception('Loader expecting either str or dict')
    
def dict_get_required(obj, key, default=None, valuetype=None, dict_description="dict"):
    value = obj.get(key)
    if value is None:
        if default is not None:
            value = default
        else:
            raise ValueError(f"{key} required in {dict_description}")

    if valuetype and not isinstance(value, valuetype):
        raise ValueError(f"{key} must be {valuetype} but it is {type(value)}")
    
    return value

def flatten(a_list):
    return [item for sublist in a_list for item in sublist]

def lambda_env(key):
    try:
        return os.environ.get(key)
    except Exception as e:
        raise e
