# Issue #7: Resolve ProfileTemplate Parameter Compatibility

## 📋 **OBJECTIVE**
Standardize ProfileTemplate constructor parameters across the entire codebase to eliminate parameter mismatch errors.

## 🎯 **SCOPE**  
Fix parameter inconsistencies causing TypeError exceptions in Customer and ProfileTemplate instantiation.

## 🔧 **TECHNICAL REQUIREMENTS**

### **ProfileTemplate Parameter Standardization**
**Files**: `src/syfi/patterns/builders.py`, test fixtures
- [ ] **Root Cause Analysis**: 
  - `household_type` vs `category` parameter inconsistency
  - Some code expects `household_type`, others expect `category`
- [ ] **Resolution Strategy**:
  - Choose single parameter name (`category` recommended)
  - Update all ProfileTemplate instantiation calls
  - Add parameter validation/backward compatibility if needed

### **Customer Model Parameter Validation**
**Files**: `src/syfi/patterns/repositories.py`, test files
- [ ] **Root Cause Analysis**:
  - Customer constructor rejects `age` parameter 
  - Tests passing unexpected keyword arguments
- [ ] **Resolution Strategy**:
  - Update Customer model to accept `age` parameter
  - OR update all test calls to use correct parameter names
  - Ensure consistent Customer instantiation patterns

### **Test Fixture Corrections**
**Files**: Multiple test files in `tests/patterns/`
- [ ] Update ProfileTemplate fixtures to use correct parameter names
- [ ] Update Customer instantiation in repository tests
- [ ] Ensure consistent parameter usage across all pattern tests

## 🐛 **SPECIFIC ERRORS TO FIX**

```
TypeError: ProfileTemplate.__init__() got an unexpected keyword argument 'household_type'
TypeError: Customer.__init__() got an unexpected keyword argument 'age'  
```

**Affected Test Files**:
- `tests/patterns/test_strategies.py` (5 failures)
- `tests/patterns/test_repositories.py` (8 failures)
- Related factory and builder tests

## ✅ **ACCEPTANCE CRITERIA**
- [ ] All ProfileTemplate parameter inconsistencies resolved
- [ ] All Customer model parameter errors fixed
- [ ] Parameter usage standardized across codebase
- [ ] ~15 additional tests passing
- [ ] No parameter-related TypeErrors in test suite
- [ ] Backward compatibility maintained where possible

## 📊 **ESTIMATED IMPACT**  
- **Test Pass Rate**: Current → +4% improvement
- **Additional Passing Tests**: ~15
- **Code Quality**: Standardized parameter interfaces

## 🏷️ **LABELS**
`bug` `high-priority` `parameters` `compatibility` `quick-win`

## 📋 **RELATED ISSUES**
- Depends on Issue #6 (some implementations needed first)
- Blocks full patterns module completion