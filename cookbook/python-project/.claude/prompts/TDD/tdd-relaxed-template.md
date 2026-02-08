# Relaxed TDD Development Prompt Template

## Context
[Describe the feature/functionality you want to build]

## Requirements
[List specific requirements or acceptance criteria]

## TDD Instructions

Follow feature-driven Test-Driven Development:

### Planning Phase
1. Break down the work into discrete features
2. Each feature should represent ONE logical capability
3. For each feature, describe the test cases needed to fully specify its behavior
4. Number each feature for tracking (F1, F2, F3, etc.)
5. Present the plan for approval before proceeding

Note: The actual number of tests per feature is determined during the RED phase when writing tests. The plan should focus on describing what behaviors need verification.

### Red-Green Cycle (Feature-Based)

For each feature in the plan:

**RED Phase:**
1. Write ALL tests needed to fully specify this feature's behavior
2. Run `make test` to confirm they all fail appropriately
3. Commit with: `test(<scope>): add tests for [feature]`
   - If multiple test cases, list them in the commit body
4. Do NOT write implementation code yet

**GREEN Phase:**  
1. Write code to make ALL the new tests pass
2. Run `make test` to confirm all tests pass
3. (Optional) Run `make lint` and/or `make format` if appropriate
4. Commit with: `feat(<scope>): implement [feature]`
5. Do NOT refactor yet

**REFACTOR Phase (optional, multi-pass):**

Refactoring can occur in one or more passes when code quality issues exist. Each refactor pass must maintain passing tests and add no new behavior.

**Refactor passes alternate between test and implementation:**

*Test Refactoring Pass:*
1. Refactor test code only (improve clarity, reduce duplication, better organization)
2. Run `make test` to confirm all tests still pass
3. Commit with: `refactor(tests): [improvement]`
4. Examples: extract test helpers, parameterize tests, improve test names

*Implementation Refactoring Pass:*
1. Refactor implementation code only (improve design, reduce coupling, clearer naming)
2. Run `make test` to confirm all tests still pass
3. Commit with: `refactor(<scope>): [improvement]`
4. Examples: extract methods, rename variables, simplify logic

**Refactor Requirements (STRICT):**
- ❌ NEVER add new behavior (test scope never changes)
- ❌ NEVER mix test and implementation refactoring in same commit
- ✅ ALWAYS ensure `make test` passes before committing
- ✅ MAY have different goals per pass (e.g., DRY tests, then simplify implementation)
- ✅ MAY skip if code quality is acceptable

### Commit Requirements
- Use conventional commits format: `<type>(<scope>): <summary>`
- test commits = RED phase (may contain multiple test cases)
- feat commits = GREEN phase (implements all tests from previous commit)
- Each commit must be atomic and focused on one feature
- Include AI-assisted provenance in commit body when appropriate

### Cycle Rules (ENFORCE)
- ❌ NEVER write implementation before tests
- ❌ NEVER mix test and implementation in same commit
- ❌ NEVER implement multiple unrelated features in one commit
- ✅ ALWAYS write all tests for a feature before implementing
- ✅ ALWAYS alternate: test(s) → feat → test(s) → feat
- ✅ ALWAYS run `make test` to verify red/green state
- ✅ ALWAYS commit after each phase

### Progress Tracking
After each commit, show:
```
✅ F1: Add user authentication - RED ✓ GREEN ✓
🔄 F2: Password validation - RED (in progress)
⏳ F3: Session management
⏳ F4: Logout functionality
```

## Verification

Use the project's Makefile targets for testing and verification:
- `make test` - Run test suite and verify red/green state
- `make lint` - Check code quality (optional, per feature)
- `make format` - Format code (optional, before commits)

Inspect the Makefile at the start to understand:
- Test framework and location conventions
- File structure patterns
- Any additional verification steps

---

## BEGIN TDD PROCESS

Step 1: Review the context and requirements
Step 2: Inspect Makefile to understand test/verification setup
Step 3: Create the concrete feature plan with comprehensive test case descriptions
Step 4: Wait for approval
Step 5: Execute feature-based red-green cycles
