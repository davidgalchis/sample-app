REMAINING_CALLS = {
    "unauth": {
        "api": {
            "v1": {
                "dogs": {"GET": "get_more_dogs"}
            }
        }
    }
}

ACCOUNT_CALLS = {
    "foundation": {
        "api": {
            "v1": {
                "accounts": {"POST": "create_account_and_user"}
            }
        }
    },
    "user": {
       "api": {
            "v1": {
                "account": {
                    ":account_id": {
                        "save": {
                            "POST": "save_dog",
                            "GET": "list_saved_dogs"
                        }
                    }
                },
                "accounts": {"POST": "create_account_and_user"},
                "refresh": {"POST": "refresh_token"},
            }
        }
    }
}



def parse_permission_and_path_args_from_path(logger, path, user_scopes, account_id, method, remove_prefix="/live/"):
    """user_scopes object:
     - account: user
    """

    def recursive_allowed_check(remaining_path, sub_allowed_calls):

        added_values = {}
        allowed = False
        name_of_function_to_call=None
        # If not yet at the last bit of path
        if "/" in remaining_path:
            current_bit, new_remaining_path = remaining_path.split("/", 1)
            # Check if the next bit of path exactly matches a key
            if current_bit in sub_allowed_calls:
                # If there is a dict remaining, you have further you can go
                if isinstance(sub_allowed_calls.get(current_bit), dict):
                    response = recursive_allowed_check(remaining_path=new_remaining_path, sub_allowed_calls=sub_allowed_calls.get(current_bit))
                    # print(f"new_remaining_path: {new_remaining_path} || new_sub: {sub_allowed_calls.get(current_bit)} || current_bit: {current_bit} || sub_allowed_calls: {sub_allowed_calls}")
                    # print(response)
                    # Let any True propagate back up
                    allowed = allowed or response.get("allowed")
                    # Add any new path args to added_values
                    added_values = {**response.get("path_args"), **added_values}
                    # Take note if a function to call has been determined, and propagate it back up
                    name_of_function_to_call = name_of_function_to_call or response.get("name_of_function_to_call")
                # If no dict remaining, but you still have path, it's the end of the line: no match!
                else:
                    pass # Default for allowed is False

            # Set off recursive loop for each wildcard variable
            elif any([a for a in [*sub_allowed_calls] if a.startswith(":")]):
                # print(f"within the wildcard for this sub_allowed_call: {sub_allowed_calls}")
                for k in [*sub_allowed_calls]:
                    # print(k)
                    # print(f"current_bit: {current_bit}")
                    if k.startswith(":"):
                        # Add the new arg that you've found
                        added_values[k[1:]]= current_bit
                        # print(f"added_values: {added_values}")
                        # If there is a dict remaining, you have further you can go, 
                        #   using the reference to the wildcard instead of the value of the variable itself
                        if isinstance(sub_allowed_calls.get(k), dict):
                            response = recursive_allowed_check(remaining_path=new_remaining_path, sub_allowed_calls=sub_allowed_calls.get(k))
                            # print(f"new_remaining_path: {new_remaining_path} || new_sub: {sub_allowed_calls.get(k)} || current_bit: {current_bit} || sub_allowed_calls: {sub_allowed_calls}")
                            # print(response)
                            # Let any True propagate back up
                            allowed = allowed or response.get("allowed")
                            # Add any new path args to added_values
                            added_values = {**response.get("path_args"), **added_values}
                            # Take note if a function to call has been determined, and propagate it back up
                            name_of_function_to_call = name_of_function_to_call or response.get("name_of_function_to_call")
                        # If no dict remaining, but you still have path, it's the end of the line: no match!
                        else:
                            pass # Default for allowed is False
            # If the path doesn't match (there are no more allowed path branches), that's it: game over! No match!
            else:
                pass # Default for allowed is False, Default for name_of_function_to_call is None
        # If at the last bit of path
        else:
            # Check if the final bit of path exactly matches a key
            if remaining_path in sub_allowed_calls:
                
                # Check that the method also matches the allowed methods
                allowed_methods = sub_allowed_calls.get(remaining_path, {})
                # Check if the method given exactly matches an allowed method
                if method in allowed_methods:
                    allowed = True
                    # The value of the key for method should be the right function to call
                    name_of_function_to_call = allowed_methods.get(method)
                # Check if ANY is allowed for the method
                elif "ANY" in allowed_methods:
                    allowed = True
                    # The value of the key for method should be the right function to call
                    name_of_function_to_call = allowed_methods.get("ANY")
                # Got to the end, but the method didn't match. Game over!
                else:
                    pass
                
            # Check if the last one is a wildcard variable
            elif any([a for a in [*sub_allowed_calls] if a.startswith(":")]):
                for k in [*sub_allowed_calls]:
                    if k.startswith(":"):
                        # Add the new arg that you've found
                        added_values[k[1:]] = remaining_path

                        # Check that the method also matches the allowed methods
                        allowed_methods = sub_allowed_calls.get(k, {})
                        # Check if the method given exactly matches an allowed method
                        if method in allowed_methods:
                            allowed = True
                            # The value of the key for method should be the right function to call
                            name_of_function_to_call = allowed_methods.get(method)
                        # Check if ANY is allowed for the method
                        elif "ANY" in allowed_methods:
                            allowed = True
                            # The value of the key for method should be the right function to call
                            name_of_function_to_call = allowed_methods.get("ANY")
                        # Got to the end, but the method didn't match. Game over!
                        else:
                            pass

                        # allowed = True
                        # # The value of the key for final bit should be the right function to call
                        # name_of_function_to_call = sub_allowed_calls.get(k)
            # If the path doesn't match, that's it: game over! No match!
            else:
                pass


        return {
            "allowed":allowed,
            "path_args": added_values,
            "name_of_function_to_call": name_of_function_to_call
        }

    # Remove the undesired prefix, if exists
    formatted_path = path.replace(remove_prefix, "", 1)
    if "/account/" in formatted_path:
        logger.info("Account level call")
        mapping = ACCOUNT_CALLS
        scope = user_scopes.get("account")
    else:
        logger.info("Non-account call")
        mapping = REMAINING_CALLS
        scope = "unauth" if user_scopes.get("unauth") else "foundation"
    logger.info(f"scope={scope}")

    if not scope:
        return {"allowed": False}

    return recursive_allowed_check(
        remaining_path=formatted_path,
        sub_allowed_calls=mapping.get(scope))
