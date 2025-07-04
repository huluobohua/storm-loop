import dspy
import os

try:
    from dspy.predict import Predict
    print(f"dspy.Predict found at: {os.path.dirname(Predict.__module__)}")
except ImportError:
    print("dspy.Predict not found")

try:
    from dspy.primitives import Module
    print(f"dspy.primitives.Module found at: {os.path.dirname(Module.__module__)}")
except ImportError:
    print("dspy.primitives.Module not found")

try:
    from dspy.dsp import LM as dsp_LM
    print(f"dspy.dsp.LM found at: {os.path.dirname(dsp_LM.__module__)}")
except ImportError:
    print("dspy.dsp.LM not found")

try:
    from dspy.dsp import HFModel as dsp_HFModel
    print(f"dspy.dsp.HFModel found at: {os.path.dirname(dsp_HFModel.__module__)}")
except ImportError:
    print("dspy.dsp.HFModel not found")

try:
    from dspy.modules import LM as modules_LM
    print(f"dspy.modules.LM found at: {os.path.dirname(modules_LM.__module__)}")
except ImportError:
    print("dspy.modules.LM not found")

try:
    from dspy.modules import HFModel as modules_HFModel
    print(f"dspy.modules.HFModel found at: {os.path.dirname(modules_HFModel.__module__)}")
except ImportError:
    print("dspy.modules.HFModel not found")