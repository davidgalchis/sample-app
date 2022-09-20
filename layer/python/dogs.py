from basics import table_name, \
     RTYPE_SAVED_DOGS, calc_saved_dogs_pkey, calc_saved_dogs_skey
from dynamodb import upsert_rec, get_recs_and_token, get_rec, delete_rec, upsert_rec_robust
from util import convert_recs_for_api, random_id, current_epoch_time_usec_str, \
    remove_none_attributes, json_loader, current_epoch_time_usec_num
import botocore
import random
import json
import time
import fastjsonschema
import requests

from datetime import datetime

def convert_dogs_for_api(recs):
    def transform(rec):

        return remove_none_attributes({
            "dog_url": rec.get("dog_url"),
            "created": rec.get("created")
        })

    return convert_recs_for_api(recs, transform)

def get_more_dogs(amount=20):
    r = requests.get(
        f"https://dog.ceo/api/breeds/image/random/{amount}"
    )
    response_text = r.text
    response = json.loads(response_text)
    return convert_dogs_for_api(response.get("message", []))


def list_saved_dogs(account_id, amount=20, cursor=None):
    recs, next_cursor = get_recs_and_token(
        table_name(),
        pkey_name="pkey",
        pkey_value = calc_saved_dogs_pkey(account_id),
        cursor=cursor,
        amount=amount,
        ascending=False
    )

    return convert_dogs_for_api(recs), next_cursor


def save_dog(account_id, dog_url):

    create_time = current_epoch_time_usec_str()

    pkey = calc_saved_dogs_pkey(account_id)
    skey = calc_saved_dogs_skey(dog_url)

    rec_values = {
        "pkey": pkey,
        "skey": skey,
        "rtype": RTYPE_SAVED_DOGS,
        "dog_url": dog_url,
        "account_id": account_id,
        "created": create_time
    }
    payload = remove_none_attributes(rec_values)

    account_response = upsert_rec(
        table_name=table_name(),
        values=payload,
        condition_expression="attribute_not_exists(pkey)",
        return_values="ALL_NEW"
    )

    return convert_dogs_for_api(account_response)
