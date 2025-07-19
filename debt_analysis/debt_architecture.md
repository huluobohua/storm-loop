# Architecture Debt Report

**Total Items**: 110

## Items by Priority

### Critical Priority (17 items)

- **tools/debt_cataloger.py:50** - , FIXME, HACK
- **storm/storm/lib/python3.9/site-packages/torch/_export/serde/serialize.py:2222** - (zhxchen17) blocked on thrift schema refactor
- **storm/storm/lib/python3.9/site-packages/torch/onnx/_internal/exporter.py:1223** - Prevent circular dependency
- **storm/storm/lib/python3.9/site-packages/torch/onnx/_internal/exporter.py:1532** - Import here to prevent circular dependency
- **storm/storm/lib/python3.9/site-packages/torch/onnx/_internal/fx/torch_export_graph_extractor.py:107** - Import here to prevent circular dependency
- **storm/storm/lib/python3.9/site-packages/torch/distributed/_spmd/graph_optimization.py:60** - (@fegin): Support multiple runs of graph optimization
- **storm/storm/lib/python3.9/site-packages/torch/distributed/_spmd/graph_optimization.py:61** - (@fegin): With this design, circular imports will happen when a pass
- **storm/storm/lib/python3.9/site-packages/torch/_inductor/codegen/cpp_wrapper_cpu.py:2332** - not using type_ as the first step of refactoring. Will update this later.
- **storm/storm/lib/python3.9/site-packages/torch/testing/_internal/common_nn.py:2519** - (#50743): figure out the error
- **storm/storm/lib/python3.9/site-packages/torch/testing/_internal/common_methods_invocations.py:17820** - (@kshitij12345): Refactor similar to `mvlgamma` entries.
- **storm/storm/lib/python3.9/site-packages/torch/jit/_shape_functions.py:40** - only assertion error is bound in C++ compilation right now
- **storm/storm/lib/python3.9/site-packages/torch/jit/_shape_functions.py:95** - only assertion error is bound in C++ compilation right now
- **storm/storm/lib/python3.9/site-packages/torch/ao/quantization/fx/quantize_handler.py:146** - remove this class, this is still exposed in torch.ao.quantization
- **storm/storm/lib/python3.9/site-packages/sklearn/utils/tests/test_validation.py:24** - add this estimator into the _mocking module in a further refactoring
- **storm/storm/lib/python3.9/site-packages/pydantic/_internal/_validators.py:125** - strict mode
- **storm/storm/lib/python3.9/site-packages/pandas/io/formats/html.py:337** - Refactor to remove code duplication with code
- **storm/storm/lib/python3.9/site-packages/pandas/io/formats/html.py:370** - Refactor to remove code duplication with code block

### High Priority (93 items)

- **storm/storm/lib/python3.9/site-packages/huggingface_hub/commands/delete_cache.py:83** - refactor this + imports in a unified pattern across codebase
- **storm/storm/lib/python3.9/site-packages/streamlit/runtime/caching/__init__.py:83** - (lukasmasuch): This is the legacy cache API name which is deprecated
- **storm/storm/lib/python3.9/site-packages/sympy/printing/tests/test_repr.py:93** - more tests
- **storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1375** - Refactor this code and matrix into some tabular environment.
- **storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1442** - refactor Matrix, Piecewise, and this into a tabular environment
- **storm/storm/lib/python3.9/site-packages/sympy/printing/pretty/pretty.py:1490** - refactor Matrix, Piecewise, and this into a tabular environment
- **storm/storm/lib/python3.9/site-packages/sympy/functions/elementary/trigonometric.py:1579** - refactor into TrigonometricFunction common parts of
- **storm/storm/lib/python3.9/site-packages/sympy/physics/vector/vector.py:735** - : Circular dependency if imported at top. Should move
- **storm/storm/lib/python3.9/site-packages/sympy/diffgeom/diffgeom.py:1438** - the calculation of signatures is slow
- **storm/storm/lib/python3.9/site-packages/sympy/diffgeom/diffgeom.py:1439** - you do not need all these permutations (neither the prefactor)
- **storm/storm/lib/python3.9/site-packages/pygments/lexers/mips.py:28** - add '*.s' and '*.asm', which will require designing an analyse_text
- **storm/storm/lib/python3.9/site-packages/grpc/_channel.py:1835** - (xuanwn): Refactor this: https://github.com/grpc/grpc/issues/31704
- **storm/storm/lib/python3.9/site-packages/mpmath/calculus/optimization.py:264** - maybe refactoring with function for divided differences
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/aot_autograd.py:591** - refactor the subclass path of run_functionalized_fw_and_collect_metadata
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:935** - refactor trace_joint
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:1729** - figure out how to refactor the backward properly
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:1834** - figure out how to refactor the backward properly
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/runtime_wrappers.py:1863** - figure out how to refactor the backward properly so I can use aot_dispatch_subclass_wrapper() here.
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/dispatch_and_compile_graph.py:84** - replace with AOTDispatchSubclassWrapper once we refactor
- **storm/storm/lib/python3.9/site-packages/torch/_functorch/_aot_autograd/dispatch_and_compile_graph.py:244** - replace with AOTDispatchSubclassWrapper once we refactor
