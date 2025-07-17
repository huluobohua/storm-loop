# dspy Legacy Import Migration Plan

## Overview
The `dspy_compatibility_shim.py` is a temporary solution that modifies `sys.modules` to provide backward compatibility for legacy `dspy.dsp.modules` imports. This document outlines the migration plan to eventually remove this shim.

## Current State
- **TGIClient**: ✅ **Already migrated** to use modern `dspy.HFClientTGI`
- **OpenAIModel**: ⚠️ **Partially migrated** - still has abstract method issues
- **TogetherClient**: ❌ **Not migrated** - still uses legacy patterns
- **DeepSeekModel**: ❌ **Not migrated** - still uses legacy patterns  
- **OllamaClient**: ❌ **Not migrated** - still uses legacy patterns

## Migration Strategy

### Phase 1: Immediate (Already Complete)
- [x] **TGIClient modernization** - Now uses `dspy.HFClientTGI` instead of legacy mock
- [x] **Behavioral test coverage** - Ensures functionality during migration
- [x] **Compatibility shim** - Provides bridge during transition

### Phase 2: Short-term (Next 2-4 weeks)
- [ ] **Complete OpenAIModel migration** - Fix abstract method implementation
- [ ] **Migrate TogetherClient** - Replace legacy patterns with modern `dspy.Together`
- [ ] **Migrate DeepSeekModel** - Use modern dspy client patterns
- [ ] **Migrate OllamaClient** - Replace with modern `dspy.OllamaLocal`

### Phase 3: Medium-term (1-2 months)
- [ ] **Remove shim dependencies** - Update all imports to use modern API
- [ ] **Comprehensive testing** - Ensure all functionality works without shim
- [ ] **Performance validation** - Verify no regressions in inference speed/accuracy

### Phase 4: Long-term (2-3 months)
- [ ] **Remove compatibility shim** - Delete `dspy_compatibility_shim.py`
- [ ] **Clean up imports** - Remove all legacy import statements
- [ ] **Documentation update** - Update all references to use modern API

## Technical Implementation Guidelines

### Modern dspy API Mapping
```python
# Legacy Pattern (TO BE REMOVED)
from dspy.dsp.modules.lm import LM
from dspy.dsp.modules.hf import HFModel
from dspy.dsp.modules.hf_client import send_hftgi_request_v01_wrapped

# Modern Pattern (TARGET)
import dspy
model = dspy.HFClientTGI(...)  # Instead of legacy TGI client
model = dspy.OpenAI(...)       # Instead of legacy OpenAI wrapper
model = dspy.Together(...)     # Instead of legacy Together wrapper
```

### Migration Checklist for Each Model Class
- [ ] **Replace legacy inheritance** - Use `dspy.LM` directly
- [ ] **Implement abstract methods** - `basic_request()` and `__call__()`
- [ ] **Use modern client classes** - `dspy.HFClientTGI`, `dspy.OpenAI`, etc.
- [ ] **Add behavioral tests** - Verify functionality works with modern API
- [ ] **Update documentation** - Remove legacy references

## Risk Mitigation
- **Backward compatibility maintained** until all modules migrated
- **Comprehensive test coverage** prevents regressions
- **Gradual migration approach** reduces risk of breaking changes
- **Rollback plan** - Keep shim until 100% confidence in migration

## Success Metrics
- ✅ All model classes use modern dspy API
- ✅ All behavioral tests pass without shim
- ✅ No `sys.modules` modification needed
- ✅ Simplified import statements throughout codebase
- ✅ Improved maintainability and robustness

## Timeline
- **Phase 1**: ✅ Complete (TGIClient modernized)
- **Phase 2**: Target 2-4 weeks
- **Phase 3**: Target 1-2 months  
- **Phase 4**: Target 2-3 months

This migration plan ensures a smooth transition away from the temporary shim solution while maintaining full functionality throughout the process.