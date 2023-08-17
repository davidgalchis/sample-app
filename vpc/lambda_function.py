import boto3
import botocore
# import jsonschema
import json
import traceback
import zipfile
import os

from botocore.exceptions import ClientError

from extutil import remove_none_attributes, account_context, ExtensionHandler, ext, \
    current_epoch_time_usec_num, component_safe_name, lambda_env, random_id, \
    handle_common_errors

eh = ExtensionHandler()

# Import your clients
s3 = boto3.client("s3")

"""
eh calls
    eh.add_op() call MUST be made for the function to execute! Adds functions to the execution queue.
    eh.add_props() is used to add useful bits of information that can be used by this component or other components to integrate with this.
    eh.add_links() is used to add useful links to the console, the deployed infrastructure, the logs, etc that pertain to this component.
    eh.retry_error(a_unique_id_for_the_error(if you don't want it to fail out after 6 tries), progress=65, callback_sec=8)
        This is how to wait and try again
        Only set callback seconds for a wait, not an error
        @ext() runs the function if its operation is present and there isn't already a retry declared
    eh.add_log() is how logs are passed to the front-end
    eh.perm_error() is how you permanently fail the component deployment and send a useful message to the front-end
    eh.finish() just finishes the deployment and sends back message and progress
    *RARE*
    eh.add_state() takes a dictionary, merges existing with new
        This is specifically if CloudKommand doesn't need to store it for later. Thrown away at the end of the deployment.
        Preserved across retries, but not across deployments.
There are three elements of state preserved across retries:
    - eh.props
    - eh.links 
    - eh.state 
Wrap all operations you want to run with the following:
    @ext(handler=eh, op="your_operation_name")
Progress only needs to be explicitly reported on 1) a retry 2) an error. Finishing auto-sets progress to 100. 
"""

def lambda_handler(event, context):
    try:
        # All relevant data is generally in the event, excepting the region and account number
        print(f"event = {event}")
        region = account_context(context)['region']
        account_number = account_context(context)['number']

        # This copies the operations, props, links, retry data, and remaining operations that are sent from CloudKommand. 
        # Just always include this.
        eh.capture_event(event)

        # These are other important values you will almost always use
        prev_state = event.get("prev_state") or {}
        project_code = event.get("project_code")
        repo_id = event.get("repo_id")
        cdef = event.get("component_def")
        cname = event.get("component_name")
        
        # Generate or read from component definition the identifier / name of the component here 
        bucket_name = eh.props.get("name") or cdef.get("name") or component_safe_name(project_code, repo_id, cname, no_underscores=True, no_uppercase=True, max_chars=63)

        # you pull in whatever arguments you care about
        """
        # Some examples. S3 doesn't really need any because each attribute is a separate call. 
        auto_verified_attributes = cdef.get("auto_verified_attributes") or ["email"]
        alias_attributes = cdef.get("alias_attributes") or ["preferred_username", "phone_number", "email"]
        username_attributes = cdef.get("username_attributes") or None
        """
        

        ### DECLARE STARTING POINT
        pass_back_data = event.get("pass_back_data", {}) # pass_back_data only exists if this is a RETRY
        # If a RETRY, then don't set starting point
        if pass_back_data:
            pass # If pass_back_data exists, then eh has already loaded in all relevant RETRY information.
        # If NOT retrying, and we are instead upserting, then we start with the GET STATE call
        elif event.get("op") == "upsert":
            eh.add_op("get_bucket")
        # If NOT retrying, and we are instead deleting, then we start with the DELETE call 
        #   (sometimes you start with GET STATE if you need to make a call for the identifier)
        elif event.get("op") == "delete":
            eh.add_op("delete_bucket")

        # The ordering of call declarations should generally be in the following order
        # GET STATE
        # CREATE
        # UPDATE
        # DELETE
        # GENERATE PROPS
        
        ### The section below DECLARES all of the calls that can be made. 
        ### The eh.add_op() function MUST be called for actual execution of any of the functions. 

        ### GET STATE
        get_bucket(bucket_name, cdef, region, prev_state)

        ### CREATE CALL(S) (occasionally multiple)
        create_bucket(bucket_name, cdef, region)
        
        ### UPDATE CALLS (common to have multiple)
        # You want ONE function per boto3 update call, so that retries come back to the EXACT same spot. 
        set_public_access_block(bucket_name, cdef)
        delete_public_access_block(bucket_name)
        set_bucket_policy(bucket_name, cdef)
        delete_bucket_policy(bucket_name)
        set_versioning(bucket_name, cdef)
        set_cors(bucket_name, cdef)
        delete_cors(bucket_name)
        set_tags(bucket_name)
        remove_all_tags(bucket_name)
        put_bucket_website(bucket_name, cdef)
        delete_bucket_website(bucket_name)

        ### DELETE CALL(S)
        delete_bucket(bucket_name)

        ### GENERATE PROPS (sometimes can be done in get/create)

        # IMPORTANT! ALWAYS include this. Sends back appropriate data to CloudKommand.
        return eh.finish()

    # You want this. Leave it.
    except Exception as e:
        msg = traceback.format_exc()
        print(msg)
        eh.add_log("Unexpected Error", {"error": msg}, is_error=True)
        eh.declare_return(200, 0, error_code=str(e))
        return eh.finish()

# This is just an application-specific helper function.
def format_tags(tags_dict):
    return [{"Key": k, "Value": v} for k,v in tags_dict.items()]

### GET STATE
# ALWAYS put the ext decorator on ALL calls that are referenced above
# This is ONLY called when this operation is slated to occur.
# GENERALLY, this function will make a bunch of eh.add_op() calls which determine what actions will be executed.
#   The eh.add_op() call MUST be made for the function to execute!
# eh.add_props() is used to add useful bits of information that can be used by this component or other components to integrate with this.
# eh.add_links() is used to add useful links to the console, the deployed infrastructure, the logs, etc that pertain to this component.
@ext(handler=eh, op="get_bucket")
def get_bucket(bucket_name, cdef, region, prev_state):
    s3 = boto3.client("s3")

    if prev_state and prev_state.get("props") and prev_state.get("props").get("name"):
        prev_bucket_name = prev_state.get("props").get("name")
        if bucket_name != prev_bucket_name:
            eh.perm_error("Cannot Change Bucket Name", progress=0)
            return None
    
    try:
        s3_resource = boto3.resource("s3")
        response = s3_resource.meta.client.head_bucket(Bucket=bucket_name)
        if response:
            print(response)
            eh.add_props({"region": response['ResponseMetadata']['HTTPHeaders']['x-amz-bucket-region']})
    except ClientError as e:
        if int(e.response['Error']['Code']) == 404:
            eh.add_log("Bucket Does Not Exist", {"name": bucket_name})
            eh.add_op("create_bucket")
            return 0
        else:
            print(str(e))
            eh.add_log("Get Bucket Error", {"error": str(e)}, is_error=True)
            eh.retry_error("Get Bucket Error", 30)
            return 0

    try:
        response = s3.get_bucket_versioning(Bucket=bucket_name)
        eh.add_log("Got Bucket Versioning", response)
        versioning = not ((not response.get("Status")) or (response.get("Status") == "Suspended"))
        want_versioning = bool(cdef.get("versioning"))
        if versioning != want_versioning:
            eh.add_op("set_versioning", want_versioning)

        eh.add_props({
            "name": bucket_name,
            "arn":gen_bucket_arn(bucket_name),
        })

        if prev_state and prev_state.get("props") and prev_state.get("props").get("region"):
            eh.add_props({
                "region": prev_state.get("props").get("region")
            })

        eh.add_links({"Bucket": gen_bucket_link(bucket_name)})
        eh.add_op("set_bucket_acl")

        if cdef.get("block_public_access") or cdef.get("public_access_block"):
            eh.add_op("set_public_access_block")
        else:
            eh.add_op("delete_public_access_block")

        if cdef.get("bucket_policy"):
            eh.add_op("set_bucket_policy")
        else:
            eh.add_op("delete_bucket_policy")

        if cdef.get("CORS"):
            eh.add_op("set_cors")
        else:
            eh.add_op("delete_cors")

        if cdef.get("tags"):
            eh.add_op("set_tags", cdef['tags'])
        else:
            eh.add_op("remove_all_tags")

        if cdef.get("website_configuration"):
            eh.add_op("put_bucket_website")
        else:
            eh.add_op("delete_bucket_website")

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "NoSuchBucket":
            eh.add_log("Bucket Does Not Exist", {"bucket_name": bucket_name})
            eh.add_op("create_bucket")
            return None
        else:
            print(str(e))
            eh.retry_error("Get Bucket Versioning Error", 30)
            eh.add_log("Get Bucket Versioning Error", {"error": str(e)}, is_error=True)
            return None
            

@ext(handler=eh, op="create_bucket")
def create_bucket(bucket_name, cdef, region):
    s3 = boto3.client("s3")

    print(f"region = {region}")
    params = remove_none_attributes({
        "ACL": cdef.get("ACL"),
        "Bucket": bucket_name,
        "CreateBucketConfiguration": {
            "LocationConstraint": region
        } if not region == "us-east-1" else None
    })

    try:
        location_response = s3.create_bucket(**params)
        eh.add_log("Bucket Created", location_response)
        if cdef.get("public_read") or cdef.get("acl"):
            eh.add_op("set_bucket_acl")

        if cdef.get("block_public_access") or cdef.get("public_access_block"):
            eh.add_op("set_public_access_block")

        if cdef.get("bucket_policy"):
            eh.add_op("set_bucket_policy")

        if cdef.get("versioning"):
            eh.add_op("set_versioning")

        if cdef.get("CORS"):
            eh.add_op("set_cors")

        if cdef.get("tags"):
            eh.add_op("set_tags", cdef['tags'])

        if cdef.get("website_configuration"):
            eh.add_op("put_bucket_website")

        eh.add_props({
            "name": bucket_name,
            "arn": gen_bucket_arn(bucket_name),
            "region": region
        })

        eh.add_links({"Bucket": gen_bucket_link(bucket_name)})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
        else:
            print(str(e))
            eh.retry_error("Create Error", 0)
            eh.add_log("Create Error", {"error": str(e)}, is_error=True)


@ext(handler=eh, op="set_bucket_acl")
def set_bucket_acl(bucket_name, cdef):
    s3 = boto3.client("s3")

    if cdef.get("public_read") == True:
        params = {
            "GrantRead": "uri=http://acs.amazonaws.com/groups/global/AllUsers"
        }

    elif cdef.get("acl"):
        params = cdef.get("acl") or {}

    else:
        params = {"ACL": "private"}

    params['Bucket'] = bucket_name
    try:
        _ = s3.put_bucket_acl(**params)
        eh.add_log("Managed ACL", params)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Public ACL Error", 7)
            eh.add_log("Put ACL Error", {"error": str(e)}, is_error=True)


@ext(handler=eh, op="set_public_access_block")
def set_public_access_block(bucket_name, cdef):
    s3 = boto3.client("s3")

    if (cdef.get("block_public_access") == True or cdef.get("public_access_block") == True):
        public_access_block = {
            "BlockPublicAcls": True,
            "IgnorePublicAcls": True,
            "BlockPublicPolicy": True,
            "RestrictPublicBuckets": True
        }
    
    else:
        public_access_block = cdef.get("public_access_block")

    try:
        _ = s3.put_public_access_block(Bucket=bucket_name, PublicAccessBlockConfiguration=public_access_block)
        eh.add_log("Put Public Access Block", public_access_block)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Public Access Block Error", 15)
            eh.add_log("Public Access Block Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="delete_public_access_block")
def delete_public_access_block(bucket_name):
    s3 = boto3.client("s3")

    try:
        _ = s3.delete_public_access_block(Bucket=bucket_name)
        eh.add_log("Delete Public Access Block", {"bucket_name": bucket_name})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Public Access Block Error", 15)
            eh.add_log("Public Access Block Error", {"error": str(e)}, is_error=True)


@ext(handler=eh, op="set_bucket_policy")
def set_bucket_policy(bucket_name, cdef):
    s3 = boto3.client("s3")

    bucket_policy = render_bucket_policy(cdef.get("bucket_policy"), bucket_name)
    try:
        response = s3.put_bucket_policy(Bucket=bucket_name, Policy=json.dumps(bucket_policy))
        eh.add_log("Put Bucket Policy", response)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Policy Error", 30)
            eh.add_log("Bucket Policy Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="delete_bucket_policy")
def delete_bucket_policy(bucket_name):
    s3 = boto3.client("s3")

    try:
        response = s3.delete_bucket_policy(Bucket=bucket_name)
        eh.add_log("Delete Bucket Policy", response)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Policy Error", 30)
            eh.add_log("Bucket Policy Error", {"error": str(e)}, is_error=True)


@ext(handler=eh, op="set_versioning")
def set_versioning(bucket_name, cdef):
    s3 = boto3.client("s3")

    versioning = cdef.get("versioning")
    config = {"Status": "Enabled" if versioning else "Suspended"}

    try:
        response = s3.put_bucket_versioning(Bucket=bucket_name, VersioningConfiguration=config)
        _ = response.pop("ResponseMetadata")
        eh.add_log("Put Bucket Versioning", response)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Versioning Error", 50)
            eh.add_log("Bucket Versioning Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="set_cors")
def set_cors(bucket_name, cdef):
    s3 = boto3.client("s3")

    if cdef.get("CORS") == True:
        cors_config = {"CORSRules": [
            {
                'AllowedHeaders': ['*'],
                'AllowedMethods': ['PUT', 'DELETE', 'GET', 'POST', 'HEAD'],
                'AllowedOrigins': ['*'],
                'ExposeHeaders': ['PUT', 'DELETE', 'GET', 'POST', 'HEAD'],
                'MaxAgeSeconds': 3000
            }
        ]}

    else:
        cors_config = cdef.get("CORS")

    try:
        response = s3.put_bucket_cors(Bucket=bucket_name, CORSConfiguration=cors_config)
        eh.add_log("Put Bucket CORS", response)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket CORS Error", 65)
            eh.add_log("Bucket CORS Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="delete_cors")
def delete_cors(bucket_name):
    s3 = boto3.client("s3")

    try:
        response = s3.delete_bucket_cors(Bucket=bucket_name)
        eh.add_log("Delete Bucket CORS", response)

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 0)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket CORS Error", 65)
            eh.add_log("Bucket CORS Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="set_tags")
def set_tags(bucket_name):
    s3 = boto3.client("s3")

    formatted_tags = format_tags(eh.ops['set_tags'])

    try:
        _ = s3.put_bucket_tagging(
            Bucket=bucket_name,
            Tagging={"TagSet": formatted_tags}
        )
        eh.add_log("Tags Set", {"tags": formatted_tags})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in ["ResourceInUseException", "LimitExceededException"]:
            eh.retry_error("Tag Limit", 80)
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Tags Error", 80)
            eh.add_log("Bucket Tags Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="remove_all_tags")
def remove_all_tags(bucket_name):
    s3 = boto3.client("s3")

    try:
        _ = s3.delete_bucket_tagging(Bucket=bucket_name)
        eh.add_log("Tags Deleted", {"bucket_name": bucket_name})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] in ["ResourceInUseException", "LimitExceededException"]:
            eh.retry_error("Tag Limit", 80)
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Tags Error", 80)
            eh.add_log("Bucket Tags Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="put_bucket_website")
def put_bucket_website(bucket_name, cdef):
    s3 = boto3.client("s3")

    website_config = cdef.get("website_configuration")
    print(f"website_config = {website_config}")

    params = remove_none_attributes({
        "ErrorDocument": remove_none_attributes({"Key": website_config.get("error_document")}) or None,
        "IndexDocument": remove_none_attributes({"Suffix": website_config.get("index_document")}) or None,
        "RedirectAllRequests": remove_none_attributes({
            "HostName": website_config.get("redirect_to"),
            "Protocol": website_config.get("redirect_protocol")
        }) or None,
        "RoutingRules": website_config.get("routing_rules")
    })

    print(f"params = {params}")

    try:
        _ = s3.put_bucket_website(
            Bucket=bucket_name,
            WebsiteConfiguration=params
        )
        eh.add_log("Website Config Set", {"config": website_config})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 90)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Website Error", 90)
            eh.add_log("Bucket Website Error", {"error": str(e)}, is_error=True)

@ext(handler=eh, op="delete_bucket_website")
def delete_bucket_website(bucket_name):
    s3 = boto3.client("s3")

    try:
        _ = s3.delete_bucket_website(Bucket=bucket_name)
        eh.add_log("Website Config Deleted", {"bucket_name": bucket_name})

    except botocore.exceptions.ClientError as e:
        if e.response['Error']['Code'] == "BucketAlreadyExists":
            eh.perm_error(f"Bucket {bucket_name} Already Exists", 90)
            eh.add_log("Bucket Already Exists, Exiting", {"error": str(e)}, is_error=True)
            return None
        elif e.response['Error']['Code'] == "BucketAlreadyOwnedByYou":
            eh.add_log("Bucket Already in this Account", {"error": str(e)})
            return None
        else:
            print(str(e))
            eh.retry_error("Bucket Website Error", 90)
            eh.add_log("Bucket Website Error", {"error": str(e)}, is_error=True)


@ext(handler=eh, op="delete_bucket")
def delete_bucket(bucket_name):
    try:
        s3 = boto3.resource('s3')
        s3_bucket = s3.Bucket(bucket_name)
        bucket_versioning = s3.BucketVersioning(bucket_name)
        if bucket_versioning.status == 'Enabled':
            s3_bucket.object_versions.delete()
            eh.add_log("Deleted All Object Versions", {"bucket_name": bucket_name})
        else:
            s3_bucket.objects.all().delete()
            eh.add_log("Deleted All Objects", {"bucket_name": bucket_name})

        s3_bucket.delete()
        eh.add_log("Deleted Bucket", {"bucket_name": bucket_name})

    except botocore.exceptions.ClientError as e:
        print(str(e))
        eh.retry_error(str(e))
        

def gen_bucket_arn(bucket_name):
    return f"arn:aws:s3:::{bucket_name}"

def gen_bucket_link(bucket_name):
    return f"https://s3.console.aws.amazon.com/s3/buckets/{bucket_name}?region=us-east-1&tab=objects"


def render_bucket_policy(policy, bucket_name):
    arn = gen_bucket_arn(bucket_name)
    def update_f(string):
        return string.replace("$SELF$", arn)

    return generic_render_def(policy, update_f)

def generic_render_def(obj, update_f):
    retval = {}
    if isinstance(obj, dict):
        return {k: generic_render_def(v, update_f) for k,v in obj.items()}
    elif isinstance(obj, (set, list, tuple)):
        return [generic_render_def(v, update_f) for v in obj]
    elif isinstance(obj, str):
        return update_f(obj)
    else:
        return obj