# Security Debt Report

**Total Items**: 617

## Items by Priority

### Critical Priority (617 items)

- **storm/storm/lib/python3.9/site-packages/dspy/signatures/signature.py:165** - Should we compare the fields?
- **storm/storm/lib/python3.9/site-packages/dspy/predict/langchain.py:15** - This class is currently hard to test, because it hardcodes gpt-4 usage:
- **storm/storm/lib/python3.9/site-packages/dspy/predict/langchain.py:80** - Generate from the template at dspy.Predict(Template2Signature)
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:194** - !
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:196** - Look closer into this. It's a bit tricky to reproduce.
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/random_search.py:172** - FIXME: The max number of demos should be determined in part by the LM's tokenizer + max_length.
- **storm/storm/lib/python3.9/site-packages/packaging/metadata.py:198** - The spec doesn't say anything about if the keys should be
- **storm/storm/lib/python3.9/site-packages/aiohttp/helpers.py:249** - (PY311): username = login or account
- **storm/storm/lib/python3.9/site-packages/aiohttp/helpers.py:255** - (PY311): Remove this, as password will be empty string
- **storm/storm/lib/python3.9/site-packages/tokenizers/tools/visualizer.py:238** - is this the right name for the data attribute ?
- **storm/storm/lib/python3.9/site-packages/tokenizers/tools/visualizer.py:361** - make this a dataclass or named tuple
- **storm/storm/lib/python3.9/site-packages/lxml_html_clean/clean.py:259** - there doesn't really seem like a general way to figure out what
- **storm/storm/lib/python3.9/site-packages/lxml_html_clean/clean.py:264** - not looking at the action currently, because it is more complex
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tree/branchings.py:742** - make this preserve the key.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tree/tests/test_branchings.py:488** - remove with MultiDiGraph_EdgeKey
- **storm/storm/lib/python3.9/site-packages/langsmith/utils.py:511** - Support other modes
- **storm/storm/lib/python3.9/site-packages/dateparser/languages/locale.py:316** - Switch to new split method.
- **storm/storm/lib/python3.9/site-packages/huggingface_hub/hf_api.py:3890** - use to multithread uploads
- **storm/storm/lib/python3.9/site-packages/huggingface_hub/utils/_validators.py:91** - add an argument to opt-out validation for specific argument?
- **storm/storm/lib/python3.9/site-packages/huggingface_hub/utils/_hf_folder.py:30** - deprecate when adapted in transformers/datasets/gradio
