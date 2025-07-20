# Immediate Action Items - Technical Debt

## 🚨 BLOCKING ITEMS - FIX IMMEDIATELY (2066 items)

### tools/debt_cataloger.py:50
- **Type**: TODO
- **Issue**: , FIXME, HACK
- **Effort**: 2-4 hours
- **ID**: e5bd3070056b

### storm/storm/lib/python3.9/site-packages/dspy/signatures/signature.py:165
- **Type**: TODO
- **Issue**: Should we compare the fields?
- **Effort**: 1-2 hours
- **ID**: 2bd61e2a7d8a

### storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:313
- **Type**: TODO
- **Issue**: - any other augassign operators that are missing
- **Effort**: 1-2 hours
- **ID**: 6e638ebb0947

### storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:356
- **Type**: TODO
- **Issue**: - add any other BoolOps missing
- **Effort**: 4-8 hours
- **ID**: 6b9b4b98f65a

### storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:131
- **Type**: FIXME
- **Issue**: TODO: What's the right order? Maybe force name-based kwargs!
- **Effort**: 2-4 hours
- **ID**: 9140fcfd1eed

### storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:278
- **Type**: FIXME
- **Issue**: TODO: The merge_dicts stuff above is way too quick and dirty.
- **Effort**: 2-4 hours
- **ID**: e3f102012878

### storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:279
- **Type**: TODO
- **Issue**: the display_table can't handle False but can handle 0! Not sure how it works with True exactly, probably fails too.
- **Effort**: 2-4 hours
- **ID**: 610a03b451a5

### storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:8
- **Type**: TODO
- **Issue**: Simplify a lot.
- **Effort**: 1-2 hours
- **ID**: 9da6f7877dc7

### storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:9
- **Type**: TODO
- **Issue**: Divide Action and Action Input like langchain does for ReAct.
- **Effort**: 1-2 hours
- **ID**: 0626584728a4

### storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:11
- **Type**: TODO
- **Issue**: There's a lot of value in having a stopping condition in the LM calls at `\n\nObservation:`
- **Effort**: 1-2 hours
- **ID**: 7b3cd0c43081


## 🔒 SECURITY DEBT - HIGH PRIORITY (617 items)

### storm/storm/lib/python3.9/site-packages/dspy/signatures/signature.py:165
- **Type**: TODO
- **Issue**: Should we compare the fields?
- **Effort**: 1-2 hours
- **ID**: 2bd61e2a7d8a

### storm/storm/lib/python3.9/site-packages/dspy/predict/langchain.py:15
- **Type**: TODO
- **Issue**: This class is currently hard to test, because it hardcodes gpt-4 usage:
- **Effort**: 2-4 hours
- **ID**: 14534a6b5d26

### storm/storm/lib/python3.9/site-packages/dspy/predict/langchain.py:80
- **Type**: TODO
- **Issue**: Generate from the template at dspy.Predict(Template2Signature)
- **Effort**: 2-4 hours
- **ID**: caa99dc61878

### storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:194
- **Type**: FIXME
- **Issue**: !
- **Effort**: 2-4 hours
- **ID**: 82210df3742a

### storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:196
- **Type**: TODO
- **Issue**: Look closer into this. It's a bit tricky to reproduce.
- **Effort**: 2-4 hours
- **ID**: 2998f7f3be11

### storm/storm/lib/python3.9/site-packages/dspy/teleprompt/random_search.py:172
- **Type**: TODO
- **Issue**: FIXME: The max number of demos should be determined in part by the LM's tokenizer + max_length.
- **Effort**: 2-4 hours
- **ID**: 31b91e01359a

### storm/storm/lib/python3.9/site-packages/packaging/metadata.py:198
- **Type**: TODO
- **Issue**: The spec doesn't say anything about if the keys should be
- **Effort**: 1-2 hours
- **ID**: 744fe11f48d0

### storm/storm/lib/python3.9/site-packages/aiohttp/helpers.py:249
- **Type**: TODO
- **Issue**: (PY311): username = login or account
- **Effort**: 1-2 hours
- **ID**: 68b55b5d0019

### storm/storm/lib/python3.9/site-packages/aiohttp/helpers.py:255
- **Type**: TODO
- **Issue**: (PY311): Remove this, as password will be empty string
- **Effort**: 1-2 hours
- **ID**: 18942d640a3a

### storm/storm/lib/python3.9/site-packages/tokenizers/tools/visualizer.py:238
- **Type**: TODO
- **Issue**: is this the right name for the data attribute ?
- **Effort**: 1-2 hours
- **ID**: c725dbe041a8


## 🏗️ ARCHITECTURE DEBT - HIGH PRIORITY (93 items)

### storm/storm/lib/python3.9/site-packages/huggingface_hub/commands/delete_cache.py:83
- **Type**: TODO
- **Issue**: refactor this + imports in a unified pattern across codebase
- **Effort**: 8-16 hours
- **ID**: a6b60a225cfa

### storm/storm/lib/python3.9/site-packages/streamlit/runtime/caching/__init__.py:83
- **Type**: TODO
- **Issue**: (lukasmasuch): This is the legacy cache API name which is deprecated
- **Effort**: 4-8 hours
- **ID**: 3844ad3bc9d7

### storm/storm/lib/python3.9/site-packages/sympy/printing/tests/test_repr.py:93
- **Type**: TODO
- **Issue**: more tests
- **Effort**: 1-2 hours
- **ID**: 2e5a7a266c05

### storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1375
- **Type**: FIXME
- **Issue**: Refactor this code and matrix into some tabular environment.
- **Effort**: 8-16 hours
- **ID**: 19454ea24184

### storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1442
- **Type**: FIXME
- **Issue**: refactor Matrix, Piecewise, and this into a tabular environment
- **Effort**: 8-16 hours
- **ID**: 727cabfa7800

### storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1490
- **Type**: FIXME
- **Issue**: refactor Matrix, Piecewise, and this into a tabular environment
- **Effort**: 8-16 hours
- **ID**: 520f478adfd2

### storm/storm/lib/python3.9/site-packages/sympy/functions/elementary/trigonometric.py:1579
- **Type**: TODO
- **Issue**: refactor into TrigonometricFunction common parts of
- **Effort**: 8-16 hours
- **ID**: 190ec54da879

### storm/storm/lib/python3.9/site-packages/sympy/physics/vector/vector.py:735
- **Type**: TODO
- **Issue**: : Circular dependency if imported at top. Should move
- **Effort**: 1-2 hours
- **ID**: dcabfc3e03ce

### storm/storm/lib/python3.9/site-packages/sympy/diffgeom/diffgeom.py:1438
- **Type**: TODO
- **Issue**: the calculation of signatures is slow
- **Effort**: 8-16 hours
- **ID**: e09c8cbb1307

### storm/storm/lib/python3.9/site-packages/sympy/diffgeom/diffgeom.py:1439
- **Type**: TODO
- **Issue**: you do not need all these permutations (neither the prefactor)
- **Effort**: 8-16 hours
- **ID**: 4b436ff8cc01
