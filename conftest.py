import asyncio
import pytest

# Add asyncio marker for tests

def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test as asyncio")

# Basic event loop fixture
@pytest.fixture
def event_loop():
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()

# Hook to run async tests
@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if pyfuncitem.get_closest_marker("asyncio"):
        loop = pyfuncitem.funcargs.get("event_loop")
        if loop is None:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
        # Only pass function arguments that the test expects
        import inspect

        sig = inspect.signature(pyfuncitem.obj)
        kwargs = {name: pyfuncitem.funcargs[name] for name in sig.parameters}
        loop.run_until_complete(pyfuncitem.obj(**kwargs))
        return True
    
