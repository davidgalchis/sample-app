from basics import calc_account_pkey, calc_account_skey, table_name, \
    RTYPE_ACCOUNT
from dynamodb import upsert_rec, get_recs_and_token, get_rec, delete_rec, upsert_rec_robust
from util import convert_recs_for_api, random_id, current_epoch_time_usec_str, \
    remove_none_attributes, json_loader, current_epoch_time_usec_num
import botocore
import json
import time
import fastjsonschema
import boto3
import jwt
import urllib
import base64
import hashlib
from jose import jwk
import hmac
import hashlib
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


def create_account_and_user(user_pool_id, app_client_id, name, username, password):

    temp_password = random_id()+"aA1!"

    cognito = boto3.client('cognito-idp')

    temp_username = username.split("@")[0]

    create_user_response = cognito.admin_create_user(
        UserPoolId=user_pool_id,
        Username=temp_username,
        TemporaryPassword=temp_password,
        MessageAction='SUPPRESS',
        UserAttributes=[
            {
                'Name': 'name',
                'Value': name
            },
            {
                'Name': 'email',
                'Value': username
            }
        ]
    )

    set_password_response = cognito.admin_set_user_password(
        UserPoolId=user_pool_id,
        Username=temp_username,
        Password=password,
        Permanent=True
    )
    confirm_response = cognito.admin_confirm_sign_up(
        UserPoolId=user_pool_id,
        Username=temp_username
    )
    initiate_auth_response = initiate_account_auth(user_pool_id, app_client_id, username, password)
    create_account_response = create_account(username, name)

    return initiate_auth_response.get("AuthenticationResult")

def get_jwt_public_keys(user_pool_id, region):
    keys_url = f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}/.well-known/jwks.json"

    with urllib.request.urlopen(keys_url) as f:
        response = f.read()
    keys = json.loads(response.decode('utf-8'))['keys']
    return keys
    

def initiate_account_auth(user_pool_id, app_client_id, username, password):
    cognito = boto3.client('cognito-idp')
    initiate_auth_response = cognito.admin_initiate_auth(
        UserPoolId=user_pool_id,
        ClientId=app_client_id,
        AuthFlow='ADMIN_NO_SRP_AUTH',
        AuthParameters={
            "USERNAME": username,
            "PASSWORD": password
        }
    )
    return initiate_auth_response

def is_access_token_valid(access_token, keys, app_client_id, user_pool_id, region):
    """
    Verification requirements
    - Get the public keys
    - Decode the token
    - Verify that the token is not expired.
    - The client_id claim in an access token should match the app client ID that was created in the Amazon Cognito user pool.
    - The issuer (iss) claim should match your user pool. For example, a user pool created in the us-east-1 Region will have the following iss value:
        https://cognito-idp.us-east-1.amazonaws.com/<userpoolID>.
    - Check the token_use claim.
        If you are only accepting the access token in your web API operations, its value must be access
    """

    # get the kid from the headers prior to verification
    headers = jwt.get_unverified_headers(access_token)
    kid = headers['kid']
    # search for the kid in the downloaded public keys
    key_index = -1
    for i in range(len(keys)):
        if kid == keys[i]['kid']:
            key_index = i
            break
    if key_index == -1:
        print('Public key not found in jwks.json')
        return False
    # construct the public key
    public_key = jwk.construct(keys[key_index])
    # get the last two sections of the token,
    # message and signature (encoded in base64)
    message, encoded_signature = str(access_token).rsplit('.', 1)
    # decode the signature
    decoded_signature = base64.b64decode(encoded_signature.encode('utf-8'))
    # verify the signature
    if not public_key.verify(message.encode("utf8"), decoded_signature):
        print('Signature verification failed')
        return False
    print('Signature successfully verified')
    # since we passed the verification, we can now safely
    # use the unverified claims
    claims = jwt.get_unverified_claims(access_token)
    # additionally we can verify the token expiration
    if time.time() > claims['exp']:
        print('Token is expired')
        return False
    # and the Audience (use claims['client_id'] if verifying an access token)
    if claims['client_id'] != app_client_id:
        print('Token was not issued for this audience')
        return False
    # and the issuer (use claims['iss'] if verifying an access token)
    if claims['iss'] != f"https://cognito-idp.{region}.amazonaws.com/{user_pool_id}":
        print('Token was not issued by this user pool')
        return False
    # now we can use the claims
    print(claims)
    return claims

# Function used to calculate SecretHash value for a given client
def calculate_secret_hash(client_id, client_secret, username):
    key = bytes(client_secret, 'utf-8')
    message = bytes(f'{username}{client_id}', 'utf-8')
    return base64.b64encode(hmac.new(key, message, digestmod=hashlib.sha256).digest()).decode()


def refresh_account_token(user_pool_id, app_client_id, app_client_secret, refresh_token, username):
    cognito = boto3.client('cognito-idp')
    refresh_response = cognito.initiate_auth(
            UserPoolId=user_pool_id,
            ClientId=app_client_id,
            AuthFlow='REFRESH_TOKEN_AUTH',
            AuthParameters={
                'REFRESH_TOKEN': refresh_token,
                'SECRET_HASH': calculate_secret_hash(app_client_id, app_client_secret, username)
                # Note that SECRET_HASH is missing from JSDK
                # Note also that DEVICE_KEY is missing from my example
            }
        )
    return refresh_response

