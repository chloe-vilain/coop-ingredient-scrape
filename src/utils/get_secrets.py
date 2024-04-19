import os

def get_secret(method_name, *args):
    secret_fetch_methods = {
        "env_var": get_secret_from_env_var,
        "secrets_manager": get_secret_from_secrets_manager,
    }
    if (method:=secret_fetch_methods.get(method_name)):
        return method(*args)
    else:
        raise ValueError("method must be one of:", secret_fetch_methods.keys())
    
def get_secret_from_env_var(secret_name):
    return os.environ.get(secret_name) 

def get_secret_from_secrets_manager(secret_name, region):
    raise NotImplementedError


