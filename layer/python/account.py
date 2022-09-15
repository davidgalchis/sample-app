from basics import calc_account_pkey, calc_account_skey, table_name, \
    RTYPE_ACCOUNT
from dynamodb import upsert_rec, get_recs_and_token, get_rec, delete_rec, upsert_rec_robust
from util import convert_recs_for_api, random_id, current_epoch_time_usec_str, \
    remove_none_attributes, json_loader, current_epoch_time_usec_num
import botocore
import random
import json
import time
import fastjsonschema
import boto3

from datetime import datetime


def convert_account_for_api(recs):
    def transform(rec):

        return remove_none_attributes({
            "account_id": rec.get("account_id"),
            "displayname": rec.get("displayname"),
            "name": rec.get("name"),
            "email": rec.get("email"),
            "created": rec.get("created"),
            "updated": rec.get("updated")
        })

    return convert_recs_for_api(recs, transform)

def get_account(account_id, consistent_read=False):
    pkey = calc_account_pkey()
    skey = calc_account_skey(account_id)

    rec = get_rec(
        table_name=table_name(),
        pkey_name="pkey",
        pkey_value=pkey,
        skey_name="skey",
        skey_value=skey,
        consistent_read=consistent_read
    )

    return convert_account_for_api(rec)

def create_account(email, name):

    create_time = current_epoch_time_usec_str()

    account_id = random_id() 

    pkey = calc_account_pkey()
    skey = calc_account_skey(account_id=account_id)

    rec_values = {
        "pkey": pkey,
        "skey": skey,
        "displayname": name,
        "email": email,
        "name": name,
        "rtype": RTYPE_ACCOUNT,
        "account_id": account_id,
        "created": create_time,
        "updated": create_time
    }
    payload = remove_none_attributes(rec_values)

    account_response = upsert_rec(
        table_name=table_name(),
        values=payload,
        condition_expression="attribute_not_exists(pkey)",
        return_values="ALL_NEW"
    )

    return convert_account_for_api(account_response)


def create_account_and_user(user_pool_id, username, password):
    """
    Register a user

    aws cognito-idp sign-up --region {your-aws-region} --client-id {your-client-id} --username admin@example.com --password password123

    Confirm user registration

    aws cognito-idp admin-confirm-sign-up --region {your-aws-region} --user-pool-id {your-user-pool-id} --username admin@example.com

    Authenticate (get tokens)

    aws cognito-idp admin-initiate-auth --region {your-aws-region} --cli-input-json file://auth.json
    """
    cognito = boto3.client('cognito-idp')

    create_user_response = cognito.admin_create_user(
        UserPoolId='string',
        Username=username,
        MessageAction='SUPPRESS',
        ClientMetadata={
            'string': 'string'
        }
    )
    response = client.admin_confirm_sign_up(
        UserPoolId='string',
        Username='string',
        ClientMetadata={
            'string': 'string'
        }
    )


    return None

def initiate_account_auth(username, password):
    return None

def refresh_account_token(refresh_token):
    return None