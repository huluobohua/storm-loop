# PRISMA Assistant Restoration Roadmap

## 🎯 **Project Overview**

**Objective**: Restore the complete PRISMA Assistant functionality for systematic review screening within the STORM-Academic ecosystem.

**Key Integration**: Seamlessly integrate with existing VERIFY system while adding specialized systematic review capabilities.

**Timeline**: 2-3 weeks total implementation with 4 distinct phases

---

## 📋 **4-Phase Implementation Plan**

### **Phase 1: Core Engine Restoration** ⚡
**Duration**: 3-4 days | **Priority**: CRITICAL | **Effort**: 8/10

#### **Objectives**
- Restore core PRISMA Assistant engine from commit c911546
- Establish integration with existing VERIFY infrastructure  
- Set up async screening processing
- Validate 80/20 methodology functionality

#### **Technical Tasks**
1. **Archaeological Analysis** (Day 1)
   - [ ] Extract `knowledge_storm/prisma_assistant.py` from commit c911546 (1,191 lines)
   - [ ] Analyze dependencies and interfaces that may have changed
   - [ ] Document breaking changes since original implementation
   - [ ] Create compatibility assessment report

2. **Core Engine Restoration** (Day 2-3)
   - [ ] Restore `PRISMAScreener` interface class
   - [ ] Implement async screening processing infrastructure
   - [ ] Add confidence scoring and 80/20 decision logic
   - [ ] Integration with existing `CitationVerifier` and `AcademicSourceService`

3. **Integration Testing** (Day 4)
   - [ ] Unit tests for core screening logic
   - [ ] Integration tests with VERIFY system components
   - [ ] Performance benchmarking for screening operations
   - [ ] Validation of 80/20 methodology accuracy

#### **Success Criteria**
- [ ] PRISMAScreener can process individual papers with >95% accuracy
- [ ] Achieves 60-70% automation rate (80/20 methodology)
- [ ] Seamless integration with existing verification services
- [ ] Sub-second screening decisions for individual papers

#### **Dependencies**
- Access to commit c911546 for code archaeology
- Existing VERIFY system components (`CitationVerifier`, `AcademicSourceService`)
- Testing framework for validation

---

### **Phase 2: Agent Integration** 🤖
**Duration**: 2-3 days | **Priority**: HIGH | **Effort**: 6/10

#### **Objectives**
- Integrate PRISMA as specialized agent within multi-agent architecture
- Establish agent communication protocols
- Add systematic review workflow orchestration
- Ensure backward compatibility with existing workflows

#### **Technical Tasks**
1. **Agent Architecture** (Day 1)
   - [ ] Create `PRISMAScreenerAgent` class in `knowledge_storm/agents/`
   - [ ] Implement agent interface and communication protocols
   - [ ] Define agent capabilities and responsibilities
   - [ ] Add error handling and fallback mechanisms

2. **Multi-Agent Integration** (Day 2)
   - [ ] Register `PRISMAScreenerAgent` with `AgentCoordinator`
   - [ ] Update `MultiAgentKnowledgeCurationModule` to include PRISMA
   - [ ] Implement agent task distribution and coordination
   - [ ] Add inter-agent communication for hybrid workflows

3. **Workflow Integration** (Day 3)
   - [ ] Create `systematic_review.py` workflow module
   - [ ] Implement hybrid academic + systematic review workflows
   - [ ] Add workflow selection logic based on task type
   - [ ] Ensure existing academic workflows remain unchanged

#### **Success Criteria**
- [ ] PRISMA agent successfully registers and communicates with coordinator
- [ ] Hybrid workflows combining STORM + PRISMA functionality
- [ ] Zero breaking changes to existing academic workflows
- [ ] Proper error handling and agent failure recovery

#### **Dependencies**
- Completed Phase 1 (Core Engine)
- Existing `AgentCoordinator` and multi-agent infrastructure
- `MultiAgentKnowledgeCurationModule` for integration

---

### **Phase 3: CLI Restoration** 💻
**Duration**: 2-3 days | **Priority**: MEDIUM | **Effort**: 5/10

#### **Objectives**
- Restore complete CLI interface for direct PRISMA access
- Implement rich console output and progress tracking
- Add project template generation
- Support multiple output formats

#### **Technical Tasks**
1. **CLI Infrastructure** (Day 1)
   - [ ] Restore CLI command structure from commit c911546
   - [ ] Implement `init` command for project setup
   - [ ] Add rich console output with emojis and progress indicators
   - [ ] Create project template generation system

2. **Screening Commands** (Day 2)
   - [ ] Implement `screen` command for paper screening
   - [ ] Add batch processing capabilities
   - [ ] Implement progress tracking and status reporting
   - [ ] Add confidence threshold configuration

3. **Analytics & Export** (Day 3)
   - [ ] Implement `stats` command for performance analytics
   - [ ] Add `export` command for multiple output formats
   - [ ] Support CSV, JSON, Markdown, and PRISMA flow outputs
   - [ ] Add visualization capabilities for screening results

#### **Success Criteria**
- [ ] Complete CLI functionality restored (init, screen, stats, export)
- [ ] Rich console output with progress indicators
- [ ] Multiple output format support
- [ ] Project template generation working

#### **Dependencies**
- Completed Phase 1 & 2 (Core Engine + Agent Integration)
- CLI framework and dependencies
- Template system for project generation

---

### **Phase 4: Enhanced Integration** 🚀
**Duration**: 2-3 days | **Priority**: MEDIUM | **Effort**: 4/10

#### **Objectives**
- Add PRISMA 2020 checklist automation
- Implement comprehensive testing framework
- Add performance analytics and visualization
- Create documentation and onboarding materials

#### **Technical Tasks**
1. **PRISMA 2020 Compliance** (Day 1)
   - [ ] Implement PRISMA 2020 checklist automation
   - [ ] Add methodology validation and compliance checking
   - [ ] Create systematic review quality assessment
   - [ ] Add reporting for PRISMA compliance status

2. **Testing & Validation** (Day 2)
   - [ ] Comprehensive unit test coverage for all components
   - [ ] Integration tests for end-to-end workflows
   - [ ] Performance benchmarking and optimization
   - [ ] Real-world validation with academic datasets

3. **Documentation & Polish** (Day 3)
   - [ ] User documentation and onboarding guides
   - [ ] API documentation for developers
   - [ ] Performance optimization and code cleanup
   - [ ] Final integration testing and validation

#### **Success Criteria**
- [ ] PRISMA 2020 checklist automation functional
- [ ] >90% test coverage for all PRISMA components
- [ ] Complete user and developer documentation
- [ ] Performance optimized for production use

#### **Dependencies**
- Completed Phases 1-3 (Full PRISMA functionality)
- Testing framework and infrastructure
- Documentation system

---

## 🔗 **Cross-Phase Dependencies**

### **Issue Dependencies**
```
Phase 1 Dependencies:
├── Issue #105: Infrastructure Setup ✅ (COMPLETE)
└── Commit c911546: Historical implementation ✅ (AVAILABLE)

Phase 2 Dependencies:  
├── Phase 1: Core Engine ⏳ (IN PROGRESS)
└── Multi-agent infrastructure ✅ (AVAILABLE)

Phase 3 Dependencies:
├── Phase 1 & 2: Core + Agent ⏳ (PENDING)
└── CLI framework ✅ (AVAILABLE)

Phase 4 Dependencies:
├── Phases 1-3: Complete functionality ⏳ (PENDING)
└── Testing infrastructure ✅ (AVAILABLE)
```

### **GitHub Issues Impact**
- **Issue #142**: PRISMA Assistant Core Restoration (THIS PROJECT)
- **Issue #106**: PRISMA Assistant CLI Implementation (Phase 3)
- **Issue #107**: Testing & Validation (Phase 4)
- **Issue #109**: Package Distribution (Post-Phase 4)

---

## 📊 **Risk Assessment & Mitigation**

### **High Risk Items**
1. **Code Archaeology Complexity** (Phase 1)
   - **Risk**: Original implementation may have breaking dependencies
   - **Mitigation**: Thorough analysis and gradual integration approach

2. **Agent Integration Conflicts** (Phase 2)  
   - **Risk**: PRISMA agent may conflict with existing agents
   - **Mitigation**: Careful interface design and extensive testing

3. **Performance Impact** (All Phases)
   - **Risk**: Adding PRISMA may slow existing workflows
   - **Mitigation**: Lazy loading and optional integration

### **Medium Risk Items**
1. **CLI Dependency Changes** (Phase 3)
   - **Risk**: CLI dependencies may have evolved since original implementation
   - **Mitigation**: Update dependencies and test compatibility

2. **Testing Complexity** (Phase 4)
   - **Risk**: Comprehensive testing may be time-consuming
   - **Mitigation**: Incremental testing throughout all phases

---

## 🎯 **Success Metrics & Validation**

### **Technical Metrics**
- **Screening Accuracy**: >95% consistency with human expert decisions
- **Automation Rate**: 60-70% automated decisions (80/20 methodology)
- **Performance**: Sub-second screening decisions
- **Integration**: Zero breaking changes to existing workflows

### **Quality Metrics**
- **Test Coverage**: >90% for all PRISMA components
- **Code Quality**: Passes all linting and review requirements
- **Documentation**: Complete user and developer guides
- **Security**: Passes security assessment for academic data handling

### **User Acceptance Metrics**
- **CLI Usability**: All commands functional with rich output
- **Agent Integration**: Seamless operation within STORM-Academic
- **PRISMA Compliance**: Full PRISMA 2020 checklist automation
- **Performance**: Acceptable screening speed for production use

---

## 📅 **Timeline Summary**

| Phase | Duration | Cumulative | Critical Path |
|-------|----------|------------|---------------|
| Phase 1: Core Engine | 3-4 days | Day 4 | ✅ Critical |
| Phase 2: Agent Integration | 2-3 days | Day 7 | ✅ Critical |
| Phase 3: CLI Restoration | 2-3 days | Day 10 | ⚠️ Medium |
| Phase 4: Enhanced Integration | 2-3 days | Day 13 | ⚠️ Medium |

**Total Estimated Timeline**: 9-13 days (2-3 weeks)

---

*This roadmap provides a structured approach to restoring PRISMA Assistant while ensuring seamless integration with the existing STORM-Academic and VERIFY systems.*