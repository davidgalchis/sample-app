from util import encode_internal_id, lambda_env

RTYPE_ACCOUNT = "A"
RTYPE_SAVED_DOGS = "SD"

def table_name():
    table_arn =  lambda_env('table_arn')
    return table_arn.split('/')[1]

def calc_account_pkey():
    return f"{RTYPE_ACCOUNT}"

def calc_account_skey(account_id):
    return f"{RTYPE_ACCOUNT}*{encode_internal_id(account_id)}"

def calc_saved_dogs_pkey(account_id):
    return f"{RTYPE_SAVED_DOGS}*{encode_internal_id(account_id)}${RTYPE_ACCOUNT}"

def calc_saved_dogs_skey(saved_dog):
    return f"{RTYPE_SAVED_DOGS}*{encode_internal_id(saved_dog)}"

