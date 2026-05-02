---
name: review
description: Auto-review code changes against backend/frontend standards, fix issues, and suggest improvements. Can be triggered manually or automatically on file changes.
allowed-tools: Read, Edit, Grep, Glob, Task
user-invocable: true
---

# Code Review & Auto-Healing Skill

This skill reviews code changes against project standards (backend/frontend skills) and automatically fixes issues.

## What This Skill Does

1. **Detects Changes**: Identifies modified files in the codebase
2. **Reviews Against Standards**: Compares code against backend/frontend skill patterns
3. **Auto-Fixes Issues**: Automatically corrects violations of standards
4. **Suggests Improvements**: Provides recommendations for better code quality
5. **Reports Results**: Summarizes what was fixed and what needs attention

## Usage

### Manual Invocation
```bash
/review                    # Review all changed files
/review path/to/file.py   # Review specific file
/review --backend          # Review only backend files
/review --frontend         # Review only frontend files
```

### Auto-Trigger (via hooks)
Automatically runs when files are saved (configured in settings.json).

## Review Checklist

### Backend Files (Python/FastAPI)
- ✅ SQLModel usage for database models
- ✅ Proper separation: routes → service → repository
- ✅ JWT authentication with `Depends(get_current_user)`
- ✅ Pydantic request/response models
- ✅ HTTPException for errors with status codes
- ✅ Type hints on all functions
- ✅ Docstrings on endpoints
- ✅ Structlog for logging
- ✅ Transaction usage for multi-step operations
- ✅ BCG theme colors in config (#009639, #2D3436)

### Frontend Files (TypeScript/React)
- ✅ TypeScript interfaces for all props
- ✅ FC and memo for components
- ✅ MUI components (not raw HTML)
- ✅ Formik + Yup for forms
- ✅ Redux Toolkit for state management
- ✅ RTK Query for API calls
- ✅ Protected routes with PrivateRoute wrapper
- ✅ JWT token auto-attachment to API calls
- ✅ Proper error handling (401 → redirect to login)
- ✅ BCG theme colors and gradient buttons

## Auto-Fix Capabilities

### Common Fixes
1. **Missing type hints** → Add appropriate types
2. **Missing docstrings** → Generate from code context
3. **Wrong import patterns** → Fix to match skill standards
4. **Missing authentication** → Add `Depends(get_current_user)`
5. **Hardcoded colors** → Replace with theme variables
6. **Raw fetch calls** → Convert to RTK Query
7. **Inline styles** → Convert to `sx` prop or `styled()`
8. **Missing error handling** → Add try/catch with proper status codes
9. **Inconsistent naming** → Fix to match conventions
10. **Missing validation** → Add Yup schema for forms

## Implementation

When invoked, this skill:

1. **Detect changes**
   - If file path provided, review that file
   - Otherwise, check `git status` for modified files
   - Filter by backend (`.py`) or frontend (`.tsx`, `.ts`) files

2. **Load standards**
   - Read backend skill patterns for Python files
   - Read frontend skill patterns for TypeScript files
   - Use patterns as review criteria

3. **Review each file**
   - Read file content
   - Compare against skill standards
   - Identify violations and improvement opportunities

4. **Auto-fix issues**
   - For common violations, apply automatic fixes
   - Use Edit tool to make corrections
   - Track all changes made

5. **Generate suggestions**
   - For complex issues that can't be auto-fixed
   - Provide actionable recommendations
   - Include examples from skills

6. **Report results**
   ```
   📋 Code Review Summary
   ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

   Files Reviewed: 5
   Auto-Fixed Issues: 12
   Suggestions: 3

   ✅ Auto-Fixed
   ─────────────
   • case/app/api/items/routes.py
     - Added missing type hints (3 locations)
     - Added docstring to create_item endpoint
     - Fixed import order

   • case/app/web/src/features/items/ItemForm.tsx
     - Converted inline styles to sx prop
     - Added Yup validation schema
     - Fixed missing displayName

   💡 Suggestions
   ──────────────
   • case/app/api/items/service.py:42
     Consider using transaction() context manager for
     multi-step database operations

   • case/app/web/src/features/items/ItemList.tsx:18
     Consider using RTK Query instead of useEffect + fetch
     for better caching and error handling
   ```

## Configuration

### Auto-Trigger Setup
Add to `~/.claude/settings.json`:

```json
{
  "hooks": {
    "on_file_change": {
      "command": "/review ${file}",
      "debounce_ms": 2000
    }
  }
}
```

### Review Scope
Configure in `.claude/review-config.yaml`:

```yaml
auto_fix:
  enabled: true
  max_fixes_per_file: 10

rules:
  backend:
    - type_hints
    - docstrings
    - authentication
    - error_handling
  frontend:
    - typescript_interfaces
    - component_patterns
    - forms_validation
    - theme_usage

exclude:
  - "*/tests/*"
  - "*/migrations/*"
  - "*.generated.*"
```

## Safety Features

1. **Never breaks working code**
   - Only fixes clear violations
   - Preserves logic and behavior
   - Creates backup before major changes

2. **Conservative auto-fix**
   - Only fixes well-defined patterns
   - Complex issues become suggestions
   - User can approve/reject changes

3. **Detailed reporting**
   - Shows every change made
   - Explains why changes were needed
   - Links to skill documentation

## Examples

### Example 1: Missing Type Hints

**Before:**
```python
def create_item(session, data, user_id):
    return ItemRepository.create(session, data)
```

**After (Auto-Fixed):**
```python
def create_item(
    session: Session,
    data: CreateItemRequest,
    user_id: str
) -> ItemModel:
    """Create a new item."""
    return ItemRepository.create(session, data)
```

### Example 2: Inline Styles to Theme

**Before:**
```typescript
<Box style={{ backgroundColor: '#009639', padding: '16px' }}>
```

**After (Auto-Fixed):**
```typescript
<Box sx={{ bgcolor: 'primary.main', p: 2 }}>
```

### Example 3: Missing Authentication

**Before:**
```python
@router.post("/items")
async def create_item(item: CreateItemRequest, session: Session = Depends(get_session)):
```

**After (Auto-Fixed):**
```python
@router.post("/items")
async def create_item(
    item: CreateItemRequest,
    current_user: UserModel = Depends(get_current_user),
    session: Session = Depends(get_session)
):
```

## Integration with CI/CD

Can be used in pre-commit hooks or CI pipeline:

```bash
# Pre-commit hook
claude /review --auto-fix --fail-on-issues

# CI Pipeline
claude /review --report-format=json > review-report.json
```

## Notes

- Works best when backend/frontend skills are up-to-date
- Can be extended with custom rules
- Integrates with existing git workflow
- Respects .gitignore patterns
