---
description: "Test a user's happy path and make changes until it is satisfied"
model: "opus"
---

You are responsible for testing a user's path through this application and implementing any fixes to issues you find.

The path that you are testing is located in PATH.md.


# Steps to take

1. Rebuild the app completely and make sure the app and client are running.

2. Use the *playwright-tester* agent to test the app on your specific path.
   - Give this agent detailed instructions on the path / steps to take.
   - Provide the agent detailed expected behavior and specific things you need tested.

The agent will provide back a detailed report, including PASS CRITERIA.

*If PASS CRITERIA performs as expected*:
- Output: <promise>PATH_COMPLETE</promise>

Only output <promise>PATH_COMPLETE</promise> when:
   - The tester has verified that all behavior performs as expected
   
* *IF PASS CRITERIA does not perform as expected*:

# A. Set up an implementation plan to solve the identified problem.
- Create a detailed implementation plan through an interactive, iterative process. You should be skeptical, thorough, and work collaboratively with the user to produce high-quality technical specifications.

## Process Steps

### Step 1: Context Gathering & Initial Analysis

1. **Spawn initial research tasks to gather context on factors driving path failure**:
   Use specialized agents to research in parallel:

   - Use the **codebase-locator** agent to find all files related to the task
   - Use the **codebase-analyzer** agent to understand how the current implementation works

   These agents will:
   - Find relevant source files, configs, and tests
   - Trace data flow and key functions
   - Return detailed explanations with file:line references

2. **Read all files identified by research tasks**:
   - After research tasks complete, read ALL files they identified as relevant
   - Read them FULLY into the main context
   - This ensures you have complete understanding before proceeding

3. **Analyze and verify understanding**:
   - Cross-reference the requirements with actual code
   - Identify any discrepancies or misunderstandings
   - Note assumptions that need verification
   - Determine true scope based on codebase reality

### Step 2: Detailed Plan Writing

2. **Use this template structure to figure out your plan**:

````markdown
# [Feature/Task Name] Implementation Plan

## Overview

[Brief description of what we're implementing and why]

## Current State Analysis

[What exists now, what's missing, key constraints discovered]

## Desired End State

[A Specification of the desired end state after this plan is complete, and how to verify it]

### Key Discoveries:
- [Important finding with file:line reference]
- [Pattern to follow]
- [Constraint to work within]

## What We're NOT Doing

[Explicitly list out-of-scope items to prevent scope creep]

## Implementation Approach

[High-level strategy and reasoning]

## Phase 1: [Descriptive Name]

### Overview
[What this phase accomplishes]

### Changes Required:

#### 1. [Component/File Group]
**File**: `path/to/file.ext`
**Changes**: [Summary of changes]

```[language]
// Specific code to add/modify
```

### Success Criteria:

#### Automated Verification:
- [ ] Integration tests pass: `make test-integration`

---

## Phase 2: [Descriptive Name]

[Similar structure with automated criteria...]

---

## Testing Strategy

### Unit Tests:
- [What to test]
- [Key edge cases]

### Integration Tests:
- [End-to-end scenarios]


## Performance Considerations

[Any performance implications or optimizations needed]

## Migration Notes

[If applicable, how to handle existing data/systems]

## References

- Original ticket: `thoughts/allison/tickets/eng_XXXX.md`
- Related research: `thoughts/shared/research/[relevant].md`
- Similar implementation: `[file:line]`
````

## Important Guidelines for implementation planning

1. **Be Skeptical**:
   - Question vague requirements
   - Identify potential issues early
   - Ask "why" and "what about"
   - Don't assume - verify with code

2. **Be Thorough**:
   - Read all context files COMPLETELY before planning
   - Research actual code patterns using parallel sub-tasks
   - Include specific file paths and line numbers
   - Write measurable success criteria with clear automated vs manual distinction

3. **Be Practical**:
   - Focus on incremental, testable changes
   - Consider migration and rollback
   - Think about edge cases
   - Include "what we're NOT doing"

4. **Track Progress**:
   - Use TodoWrite to track planning tasks
   - Update todos as you complete research
   - Mark planning tasks complete when done

5. **No Open Questions in Final Plan**:
   - Do NOT write the plan with unresolved questions
   - The implementation plan must be complete and actionable
   - Every decision must be made before finalizing the plan

## Verification guidelines

1. **Automated Verification** (can be run by execution agents):
   - Commands that can be run: `pytest`, `lint`, etc.
   - Specific files that should exist
   - Code compilation/type checking
   - Automated test suites


# Step B: Implementing this plan
Now, you need to implement this plan.

## Getting Started
Think about the plan you created:
- Read the plan completely and check for any existing checkmarks (- [x])
- Read the original ticket and all files mentioned in the plan
- **Read files fully** - never use limit/offset parameters, you need complete context
- Think deeply about how the pieces fit together
- Create a todo list to track your progress
- Start implementing if you understand what needs to be done

## Implementation Philosophy

Plans are carefully designed, but reality can be messy. Your job is to:
- Follow the plan's intent while adapting to what you find
- Implement each phase fully before moving to the next
- Verify your work makes sense in the broader codebase context
- Update checkboxes in the plan as you complete sections

When things don't match the plan exactly, think about why and communicate clearly. The plan is your guide, but your judgment matters too.

## Verification Approach

After implementing a phase:
- Run the success criteria checks
- Fix any issues before proceeding
- Update your progress in both the plan and your todos
- Check off completed items in the plan file itself using Edit
- Perform any manual verification yourself (e.g. using Bash or playwright MCP).

## If You Get Stuck

When something isn't working as expected:
- First, make sure you've read and understood all the relevant code
- Consider if the codebase has evolved since the plan was written
- Present the mismatch clearly and ask for guidance

Use sub-tasks sparingly - mainly for targeted debugging or exploring unfamiliar territory.

# After you're done:

- Report to the user the challenges the user path faced, problems identified, and the fix.

