import asyncio
import inspect
import pytest

@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    marker = pyfuncitem.get_closest_marker("asyncio")
    if marker is not None and inspect.iscoroutinefunction(pyfuncitem.obj):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        funcargs = {name: pyfuncitem.funcargs[name] for name in pyfuncitem._fixtureinfo.argnames}
        loop.run_until_complete(pyfuncitem.obj(**funcargs))
        loop.close()
        return True
    return None

@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test to run with asyncio")
