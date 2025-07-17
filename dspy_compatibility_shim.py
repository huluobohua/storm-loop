"""
dspy Compatibility Shim
Provides backward compatibility for legacy dspy.dsp.modules imports
Using modern dspy API with legacy interface mapping
"""

import sys
import types
from typing import Any, Optional, Dict, List
import logging

try:
    import dspy
except ImportError:
    dspy = None


class LegacyLMWrapper:
    """
    Legacy LM class wrapper for backward compatibility
    Maps to modern dspy.clients.LM functionality
    """
    
    def __init__(self, *args, **kwargs):
        if dspy is None:
            raise ImportError("dspy not available")
        
        # Use modern dspy.LM or dspy.clients.LM
        if hasattr(dspy, 'LM'):
            self._modern_lm = dspy.LM
        elif hasattr(dspy.clients, 'LM'):
            self._modern_lm = dspy.clients.LM
        else:
            # Fallback to generic LM if no specific implementation available
            self._modern_lm = dspy.LM
    
    def __call__(self, *args, **kwargs):
        """Delegate calls to modern LM implementation"""
        return self._modern_lm(*args, **kwargs)


class LegacyHFModelWrapper:
    """
    Legacy HFModel class wrapper for backward compatibility
    Maps to modern dspy HuggingFace functionality or LM with HF provider
    """
    
    def __init__(self, *args, **kwargs):
        if dspy is None:
            raise ImportError("dspy not available")
        
        # Try to use modern HF model support
        # In dspy 2.x, HuggingFace models are typically accessed via LM with provider
        if hasattr(dspy, 'LM'):
            self._modern_hf = dspy.LM
        elif hasattr(dspy, 'HuggingFace'):
            self._modern_hf = dspy.HuggingFace
        else:
            # Fallback to generic LM
            self._modern_hf = dspy.LM
    
    def __call__(self, *args, **kwargs):
        """Delegate calls to modern HF implementation"""
        # If using LM, may need to specify HuggingFace provider
        if 'model' in kwargs and not kwargs.get('provider'):
            kwargs['provider'] = 'huggingface'
        return self._modern_hf(*args, **kwargs)


def mock_send_hftgi_request_v01_wrapped(*args, **kwargs):
    """
    Mock implementation of legacy send_hftgi_request_v01_wrapped
    Provides compatibility for code that depends on this function
    """
    logging.warning(
        "Using mock implementation of send_hftgi_request_v01_wrapped. "
        "Consider migrating to modern dspy API."
    )
    
    # Return a mock response structure
    return {
        "choices": [{"text": "Mock response for compatibility"}],
        "usage": {"total_tokens": 10}
    }


def install_dspy_compatibility_shim():
    """
    Install compatibility shim for legacy dspy.dsp.modules imports
    Creates mock modules that map to modern dspy functionality
    """
    
    # Create mock module structure
    modules_mod = types.ModuleType("dspy.dsp.modules")
    lm_mod = types.ModuleType("dspy.dsp.modules.lm")
    hf_mod = types.ModuleType("dspy.dsp.modules.hf")
    hf_client_mod = types.ModuleType("dspy.dsp.modules.hf_client")
    
    # Add legacy classes/functions with modern implementations
    lm_mod.LM = LegacyLMWrapper()
    hf_mod.HFModel = LegacyHFModelWrapper()
    hf_client_mod.send_hftgi_request_v01_wrapped = mock_send_hftgi_request_v01_wrapped
    
    # Also add direct dspy.dsp.LM and dspy.dsp.HFModel aliases
    if dspy is not None:
        dsp_mod = getattr(dspy, 'dsp', None)
        if dsp_mod is None:
            dsp_mod = types.ModuleType("dspy.dsp")
            dspy.dsp = dsp_mod
        
        # Add modern LM class aliases to dspy.dsp namespace
        dsp_mod.LM = dspy.LM if hasattr(dspy, 'LM') else dspy.clients.LM
        dsp_mod.HFModel = dspy.LM if hasattr(dspy, 'LM') else dspy.clients.LM
    
    # Install modules in sys.modules
    sys.modules["dspy.dsp.modules"] = modules_mod
    sys.modules["dspy.dsp.modules.lm"] = lm_mod
    sys.modules["dspy.dsp.modules.hf"] = hf_mod
    sys.modules["dspy.dsp.modules.hf_client"] = hf_client_mod
    
    logging.info("dspy compatibility shim installed for legacy imports")


def uninstall_dspy_compatibility_shim():
    """
    Remove compatibility shim modules from sys.modules
    Useful for testing and cleanup
    """
    modules_to_remove = [
        "dspy.dsp.modules",
        "dspy.dsp.modules.lm",
        "dspy.dsp.modules.hf",
        "dspy.dsp.modules.hf_client"
    ]
    
    for module_name in modules_to_remove:
        if module_name in sys.modules:
            del sys.modules[module_name]
    
    logging.info("dspy compatibility shim uninstalled")


# Auto-install shim when module is imported
if dspy is not None:
    install_dspy_compatibility_shim()
else:
    logging.warning("dspy not available, compatibility shim not installed")