"""
Patch torch logging to prevent initialization errors in Streamlit
"""
import os
import sys

# Set environment variables early
os.environ["TORCH_LOGS"] = ""
os.environ["PYTORCH_DISABLE_TORCH_FUNCTION_MODE"] = "1"
os.environ["TOKENIZERS_PARALLELISM"] = "false"

def patch_torch_logging():
    """Patch torch logging to prevent initialization errors"""
    try:
        # Import torch._logging before anything else can import torch
        import torch._logging._internal as torch_logging
        
        # Monkey patch the problematic method
        class MockLogState:
            def get_log_level_pairs(self):
                return []
        
        # Replace the log_state with our mock
        torch_logging.log_state = MockLogState()
        
    except ImportError:
        # If torch isn't installed, this is fine
        pass
    except AttributeError:
        # If the internal structure has changed, just continue
        pass

# Apply the patch
patch_torch_logging()