# TDD Example: Building a User Authentication System

## Context
Build a user authentication system with login, password validation, and session management

## Requirements
- Users can log in with username and password
- Passwords must meet complexity requirements (min 8 chars, uppercase, lowercase, number)
- Sessions expire after 30 minutes of inactivity
- Failed login attempts are tracked and limited

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

---

## Example Step 2: Makefile Inspection

```bash
$ cat Makefile
```

Example output analysis:
```makefile
test:
    pytest tests/ -v

lint:
    ruff check src/ tests/

format:
    ruff format src/ tests/
```

**Findings:**
- Test framework: pytest
- Test location: `tests/`
- Implementation location: `src/` (inferred)
- Linter: ruff
- Formatter: ruff format

---

## Example Feature Plan (what Step 3 might produce)

**F1: Basic login validation**
Test cases should verify:
- Successful authentication with valid credentials
- Rejection of invalid username
- Rejection of invalid password
- Appropriate error messages for each failure case

**F2: Password complexity requirements**
Test cases should verify:
- Minimum length enforcement (8+ characters)
- Required character types (uppercase, lowercase, digits)
- Clear validation error messages
- Edge cases (exactly 8 chars, missing one requirement, etc.)

**F3: Session management**
Test cases should verify:
- Session creation on successful login
- Session expiration after timeout period
- Session validation for protected operations

**F4: Rate limiting**
Test cases should verify:
- Account lock mechanism after failed attempts
- Lock duration and unlock behavior
- Attempt counter reset on successful login

Note: During RED phase, the developer has freedom to determine the exact number and structure of tests needed to adequately specify each feature.

---

## Example Commit Sequence

```
# F1: Basic login validation
test(auth): add tests for basic login validation

- Test successful login with valid credentials
- Test failed login with invalid username  
- Test failed login with invalid password

feat(auth): implement basic login validation

# F2: Password complexity
test(auth): add tests for password complexity requirements

- Test minimum length requirement
- Test uppercase letter requirement
- Test lowercase letter requirement
- Test number requirement

feat(auth): implement password complexity validation

# Optional refactoring after F2
refactor(tests): extract password validation test fixtures

Reduced duplication by creating shared invalid_passwords fixture.
All tests still pass.

refactor(auth): extract password validation rules to separate class

Improved separation of concerns by moving validation logic to
PasswordValidator class. All tests still pass.

# F3: Session management
test(auth): add tests for session management

- Test session creation on successful login
- Test session expiration after timeout

feat(auth): implement session management

# ... and so on
```

**Note on refactoring:**
- Test refactoring and implementation refactoring are separate commits
- Each maintains passing tests (no new behavior)
- Different goals per pass are allowed (e.g., DRY in tests, then extract class in implementation)
- Refactoring is optional - only do it when quality issues warrant the effort
