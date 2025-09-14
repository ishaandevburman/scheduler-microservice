JOB_REGISTRY = {}

def register_job(name: str):
    def decorator(func):
        JOB_REGISTRY[name] = func
        return func
    return decorator