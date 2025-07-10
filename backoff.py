import asyncio

def expo(*args, **kwargs):
    return None

def on_exception(wait, exception, **opts):
    def decorator(func):
        if asyncio.iscoroutinefunction(func):
            async def wrapper(*a, **k):
                return await func(*a, **k)
            return wrapper
        else:
            def wrapper(*a, **k):
                return func(*a, **k)
            return wrapper
    return decorator
