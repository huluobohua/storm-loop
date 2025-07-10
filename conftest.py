import asyncio
import pytest


def pytest_configure(config):
    config.addinivalue_line("markers", "asyncio: mark test function to run in event loop")


@pytest.hookimpl(tryfirst=True)
def pytest_pyfunc_call(pyfuncitem):
    if pyfuncitem.get_closest_marker("asyncio"):
        func = pyfuncitem.obj
        argnames = pyfuncitem._fixtureinfo.argnames
        testargs = {name: pyfuncitem.funcargs[name] for name in argnames}
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(func(**testargs))
        return True
    return None
