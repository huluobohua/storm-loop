import importlib.util as _importlib_util
import pathlib as _pathlib
import sys as _sys

def _load_dspy_stub() -> None:
    stub_path = _pathlib.Path(__file__).resolve().parent.parent / 'dspy_stub.py'
    spec = _importlib_util.spec_from_file_location('dspy', stub_path)
    module = _importlib_util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore
    _sys.modules['dspy'] = module
    return module

_temp_stub = None
_force_missing = 'dspy' in _sys.modules and _sys.modules['dspy'] is None
_need_stub = False
try:
    import dspy  # noqa: F401
    if not hasattr(dspy, 'Retrieve'):
        _need_stub = True
except Exception:
    if not _force_missing:
        _need_stub = True
if _need_stub:
    _temp_stub = _load_dspy_stub()

try:
    from .academic_rm import CrossrefRM
except Exception:  # pragma: no cover - optional dependency
    CrossrefRM = None  # type: ignore

if _temp_stub is not None:
    _sys.modules.pop('dspy', None)

try:
    from .multi_agent_knowledge_curation import MultiAgentKnowledgeCurationModule
except Exception:  # pragma: no cover - optional dependency
    MultiAgentKnowledgeCurationModule = None  # type: ignore

__all__ = ["CrossrefRM", "MultiAgentKnowledgeCurationModule"]
