class Retrieve:
    def __init__(self, k=3):
        self.k = k
class OpenAI:
    def __init__(self, *args, **kwargs):
        pass
class OllamaLocal:
    def __init__(self, *args, **kwargs):
        pass
class HFClientTGI:
    def __init__(self, *args, **kwargs):
        pass
class dsp:
    class LM:
        pass
    class HFModel:
        pass
    class modules:
        class lm:
            pass
        class hf:
            pass
        class hf_client:
            @staticmethod
            def send_hftgi_request_v01_wrapped(*args, **kwargs):
                return ""

dsp.modules.lm.LM = dsp.LM
dsp.modules.hf.HFModel = dsp.HFModel
