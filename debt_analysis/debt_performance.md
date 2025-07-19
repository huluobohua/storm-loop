# Performance Debt Report

**Total Items**: 825

## Items by Priority

### Critical Priority (164 items)

- **storm/storm/lib/python3.9/site-packages/streamlit/elements/widgets/data_editor.py:334** - (lukasmasuch): we are only adding rows that have a non-None index
- **storm/storm/lib/python3.9/site-packages/sympy/series/tests/test_gruntz.py:138** - This sometimes fails!!!
- **storm/storm/lib/python3.9/site-packages/sympy/core/containers.py:128** - One would expect:
- **storm/storm/lib/python3.9/site-packages/sympy/polys/rootoftools.py:567** - don't sort until you are sure that it is compatible
- **storm/storm/lib/python3.9/site-packages/sympy/polys/matrices/_dfm.py:311** - flint matrices do not support negative indices
- **storm/storm/lib/python3.9/site-packages/sympy/polys/matrices/_dfm.py:312** - They also raise ValueError instead of IndexError
- **storm/storm/lib/python3.9/site-packages/sympy/polys/matrices/_dfm.py:325** - flint matrices do not support negative indices
- **storm/storm/lib/python3.9/site-packages/sympy/polys/matrices/_dfm.py:326** - They also raise ValueError instead of IndexError
- **storm/storm/lib/python3.9/site-packages/sympy/solvers/ode/tests/test_systems.py:2234** - dsolve gives an error in integration:
- **storm/storm/lib/python3.9/site-packages/sympy/solvers/ode/tests/test_systems.py:2260** - Only works with dotprodsimp see
- **storm/storm/lib/python3.9/site-packages/sympy/functions/special/spherical_harmonics.py:179** - Make sure n \in N
- **storm/storm/lib/python3.9/site-packages/sympy/functions/special/hyper.py:543** - should we check convergence conditions?
- **storm/storm/lib/python3.9/site-packages/sympy/functions/elementary/exponential.py:991** - new and probably slow
- **storm/storm/lib/python3.9/site-packages/sympy/simplify/tests/test_hyperexpand.py:757** - This is marked as tooslow and hence skipped in CI. None of the
- **storm/storm/lib/python3.9/site-packages/sympy/diffgeom/diffgeom.py:1611** - This substitution can fail when there are Dummy symbols and the
- **storm/storm/lib/python3.9/site-packages/sympy/matrices/decompositions.py:956** - ``_find_reasonable_pivot`` uses slow zero testing. Blocked by bug #10279
- **storm/storm/lib/python3.9/site-packages/mpmath/functions/orthogonal.py:313** - something else is required here
- **storm/storm/lib/python3.9/site-packages/mpmath/calculus/optimization.py:560** - decide not to use convergence acceleration
- **storm/storm/lib/python3.9/site-packages/fsspec/asyn.py:320** - implement on_error
- **storm/storm/lib/python3.9/site-packages/fsspec/caching.py:130** - not a for loop so we can consolidate blocks later to

### High Priority (661 items)

- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/bootstrap.py:20** - the max_rounds via branch_idx to get past the cache, not just temperature.
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/signature_opt_typed.py:13** - :
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/signature_opt_typed.py:68** - Can we make textwrap default/automatic in all signatures?
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/signature_opt_typed.py:210** - Parallelize this
- **storm/storm/lib/python3.9/site-packages/dspy/teleprompt/signature_opt_typed.py:245** - Parallelize this
- **storm/storm/lib/python3.9/site-packages/aiohttp/streams.py:560** - add async def readuntil
- **storm/storm/lib/python3.9/site-packages/aiohttp/web_urldispatcher.py:620** - cache file content
- **storm/storm/lib/python3.9/site-packages/networkx/conftest.py:94** - The warnings below need to be dealt with, but for now we silence them.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/isolate.py:106** - This can be parallelized.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/efficiency_measures.py:118** - This can be made more efficient by computing all pairs shortest
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/efficiency_measures.py:166** - This summation can be trivially parallelized.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/vitality.py:75** - This can be trivially parallelized.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tournament.py:329** - This is trivially parallelizable.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tournament.py:342** - This is trivially parallelizable.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tournament.py:345** - This is trivially parallelizable.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tournament.py:405** - This is trivially parallelizable.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tree/mst.py:122** - This can be parallelized, both in the outer loop over
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/tree/mst.py:130** - This loop can be parallelized, to an extent (the union
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/isomorphism/ismags.py:292** - graph and subgraph setter methods that invalidate the caches.
- **storm/storm/lib/python3.9/site-packages/networkx/algorithms/isomorphism/ismags.py:293** - allow for precomputed partitions and colors
