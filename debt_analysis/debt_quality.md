# Quality Debt Report

**Total Items**: 6053

## Items by Priority

### Critical Priority (1268 items)

- **storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:313** - - any other augassign operators that are missing
- **storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:356** - - add any other BoolOps missing
- **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:131** - TODO: What's the right order? Maybe force name-based kwargs!
- **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:278** - TODO: The merge_dicts stuff above is way too quick and dirty.
- **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:279** - the display_table can't handle False but can handle 0! Not sure how it works with True exactly, probably fails too.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:8** - Simplify a lot.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:9** - Divide Action and Action Input like langchain does for ReAct.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:11** - There's a lot of value in having a stopping condition in the LM calls at `\n\nObservation:`
- **storm/storm/lib/python3.9/site-packages/dspy/predict/program_of_thought.py:169** - Don't try to execute the code if it didn't parse
- **storm/storm/lib/python3.9/site-packages/dspy/predict/program_of_thought.py:177** - Don't try to execute the code if it didn't parse
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/random_search.py:14** - This function should take a max_budget and max_teacher_budget. That's in the number of program calls.
- **storm/storm/lib/python3.9/site-packages/dspy/functional/functional.py:135** - Another fun idea is to only (but automatically) do this if the output fails.
- **storm/storm/lib/python3.9/site-packages/dspy/functional/functional.py:138** - Instead of using a language model to create the example, we can also just use a
- **storm/storm/lib/python3.9/site-packages/aiohttp/streams.py:389** - should be `if` instead of `while`
- **storm/storm/lib/python3.9/site-packages/aiohttp/client_proto.py:88** - log this somehow?
- **storm/storm/lib/python3.9/site-packages/lxml_html_clean/clean.py:781** - should the break character be at the end of the
- **storm/storm/lib/python3.9/site-packages/networkx/conftest.py:140** - remove the try-except block when we require numpy >= 2
- **storm/storm/lib/python3.9/site-packages/networkx/drawing/layout.py:876** - Rm csr_array wrapper in favor of spdiags array constructor when available
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/cycles.py:837** - use set for speedup?
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/walks.py:73** - Use matrix_power from scipy.sparse when available

### Medium Priority (4785 items)

- **storm/storm/lib/python3.9/site-packages/typing_extensions.py:659** - so that typing.Generic.__class_getitem__
- **storm/storm/lib/python3.9/site-packages/typing_extensions.py:948** - Use inspect.VALUE here, and make the annotations lazily evaluated
- **storm/storm/lib/python3.9/site-packages/typing_extensions.py:1756** - to get typing._type_check to pass.
- **storm/storm/lib/python3.9/site-packages/typing_extensions.py:1785** - to get typing._type_check to pass in Generic.
- **storm/storm/lib/python3.9/site-packages/typing_extensions.py:3123** - Use inspect.VALUE here, and make the annotations lazily evaluated
- **storm/storm/lib/python3.9/site-packages/dspy/datasets/dataset.py:78** - NOTE: Ideally we use these uuids for dedup internally, for demos and internal train/val splits.
- **storm/storm/lib/python3.9/site-packages/dspy/primitives/assertions.py:319** - warning: might be overwriting a previous _forward method
- **storm/storm/lib/python3.9/site-packages/dspy/primitives/program.py:77** - (Shangyint): This may cause some problems for nested patterns.
- **storm/storm/lib/python3.9/site-packages/dspy/evaluate/metrics.py:1** - This should move internally. Same for passage_match. dspy.metrics.answer_exact_match, dspy.metrics.answer_passage_match
- **storm/storm/lib/python3.9/site-packages/dspy/predict/chain_of_thought_with_hint.py:6** - FIXME: Insert this right before the *first* output field. Also rewrite this to use the new signature system.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/predict.py:141** - get some defaults during init from the context window?
- **storm/storm/lib/python3.9/site-packages/dspy/predict/predict.py:142** - FIXME: Hmm, I guess expected behavior is that contexts can
- **storm/storm/lib/python3.9/site-packages/dspy/predict/chain_of_thought.py:7** - FIXME: Insert this right before the *first* output field. Also rewrite this to use the new signature system.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/chain_of_thought.py:9** - This shouldn't inherit from Predict. It should be a module that has one or two predictors.
- **storm/storm/lib/python3.9/site-packages/dspy/predict/langchain.py:119** - Use template.extract(example, p)
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:13** - metrics should return an object with __bool__ basically, but fine if they're more complex.
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:16** - Switch here from dsp.Example to dspy.Example. Right now, it's okay because it's internal only (predictors).
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:27** - When this bootstraps for another teleprompter like finetune, we want all demos we gather.
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:30** - Add baselines=[...]
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:100** - (shangyint): This is an ugly hack to bind traces of
