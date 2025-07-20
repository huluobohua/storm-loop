# Technical Debt Analysis Report
Generated: 2025-07-18 20:06:03

## Executive Summary

**Total Debt Items**: 7605
**Critical Items**: 2066 (27.2%)
**High Priority Items**: 754 (9.9%)

### Debt Distribution by Type
- TODO: 5596
- XXX: 1174
- FIXME: 594
- HACK: 167
- BUG: 74

### Debt Distribution by Category
- quality: 6053
- performance: 825
- security: 617
- architecture: 110

### Priority Distribution
- medium: 4785
- critical: 2066
- high: 754

### Risk Level Distribution
- low: 4785
- blocking: 2066
- medium: 754

## Critical Action Items (Top 10)
1. **tools/debt_cataloger.py:50** - , FIXME, HACK
2. **storm/storm/lib/python3.9/site-packages/dspy/signatures/signature.py:165** - Should we compare the fields?
3. **storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:313** - - any other augassign operators that are missing
4. **storm/storm/lib/python3.9/site-packages/dspy/primitives/python_interpreter.py:356** - - add any other BoolOps missing
5. **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:131** - TODO: What's the right order? Maybe force name-based kwargs!
6. **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:278** - TODO: The merge_dicts stuff above is way too quick and dirty.
7. **storm/storm/lib/python3.9/site-packages/dspy/evaluate/evaluate.py:279** - the display_table can't handle False but can handle 0! Not sure how it works with True exactly, probably fails too.
8. **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:8** - Simplify a lot.
9. **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:9** - Divide Action and Action Input like langchain does for ReAct.
10. **storm/storm/lib/python3.9/site-packages/dspy/predict/react.py:11** - There's a lot of value in having a stopping condition in the LM calls at `\n\nObservation:`

## Files with Highest Debt Concentration
- storm/storm/lib/python3.9/site-packages/torch/testing/_internal/common_methods_invocations.py: 148 items
- storm/storm/lib/python3.9/site-packages/dill/source.py: 75 items
- storm/storm/lib/python3.9/site-packages/dill/_dill.py: 34 items
- storm/storm/lib/python3.9/site-packages/torch/fx/experimental/symbolic_shapes.py: 33 items
- storm/storm/lib/python3.9/site-packages/sympy/integrals/risch.py: 30 items
- storm/storm/lib/python3.9/site-packages/pandas/core/internals/blocks.py: 29 items
- storm/storm/lib/python3.9/site-packages/torch/_prims/__init__.py: 28 items
- storm/storm/lib/python3.9/site-packages/torch/_refs/__init__.py: 28 items
- storm/storm/lib/python3.9/site-packages/torch/ao/ns/fx/n_shadows_utils.py: 26 items
- storm/storm/lib/python3.9/site-packages/regex/test_regex.py: 26 items

## Estimated Total Effort
- Critical items: 150.9 weeks
- High priority: 65.4 weeks
- All items: 532.9 weeks
