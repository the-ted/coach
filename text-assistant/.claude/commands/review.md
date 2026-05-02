---
description: Review part of codebase
model: opus
---


I am doing a codebase review. 

The list of modules I need to review is in review/REVIEW.md.

Modules that have not been reviewed are indicated by # TODO.

Pick one module and review it.


# How to do this review

## 1. Goal of this assignment

Your task is to **deeply review** the chosen module area of our codebase and produce a **written report (in Markdown)** that:

1. Identifies **potential sources of technical debt**
2. Flags **deprecated or dead/unused code**
3. Suggests **architectural and design improvements** that would improve:

   * Maintainability
   * Durability (robustness to change over time)
   * Clarity for future developers

> **Important:** You are **not** expected to make any code changes for this assignment. No refactors, no PRs, no renames—only analysis and documentation.

The final deliverable is a single Markdown file that we’ll review together.

---

## 2. Scope

Focus **only** on the selected module.

- Treat the rest of the codebase as **supporting context**
- It’s fine to read outside the module to understand how it’s used, but your findings and recommendations should be focused on the module itself.

---

## 3. Expected Deliverable

Create a Markdown file named:

> `review/MODULE-review-MM-DD-YYYY.md`

The report should follow this structure:

```markdown
# <MODULE> Codebase Review

## 1. Executive Summary
- One-paragraph summary of the module
- Top 3–5 issues you found
- Top 3–5 recommended improvements (high level)

## 2. Context & Understanding
- What <MODULE> does
- Where it lives in the repo (paths, main entry points)
- How it fits into the larger system (upstream/downstream dependencies)
- Key technologies / libraries involved

## 3. Technical Debt Findings
For each issue:
- **ID:** TD-1, TD-2, …
- **Title:** Short description
- **Location(s):** File(s) and line range(s)
- **Type:** e.g. “high complexity”, “duplication”, “missing tests”, “inconsistent patterns”
- **Details:** What you observed
- **Impact:** Why it matters (e.g. maintainability, bug risk, onboarding)
- **Rough Priority:** High / Medium / Low

## 4. Deprecated / Dead / Risky Code
For each item:
- **ID:** DEPR-1, DEPR-2, …
- **Location(s)**
- **Evidence it's deprecated/unused/risky**
- **What might be done (at a high level)**

## 5. Architectural / Design Observations
- Current architecture summary of <MODULE>
- Coupling & cohesion issues
- API / boundary clarity
- Data flow notes
- Error handling & logging approach
- Suggested improvements (with rationale)

## 6. Testing & Observability
- Existing tests related to <MODULE>
- Gaps in test coverage or test quality
- Suggestions for better testing strategy
- Observability: logging, metrics, tracing – what exists, what’s missing

## 7. Suggested Next Steps
- List of concrete next steps (no more than 10)
- Grouped by priority (High / Medium / Low)
- Each linked back to TD- / DEPR- items where relevant

## 8. Open Questions
- Things that were unclear or ambiguous
- Assumptions you had to make
- Areas where you’d like input from the team
```

You don’t have to write a novel, but each section should be **substantive** enough that another developer could read your report and quickly understand `<MODULE>` and its main issues.

---

## 4. How to Approach the Review (Step by Step)

### Step 1 – Get Oriented

1. Find the right set of files pertaining to the module in the repo and:

   * Note the **main directories and files**
   * Identify **entry points** (e.g. main classes, controllers, handlers, commands)

2. Search for:

   * Relevant module name in code, docs, and configs
   * Any mentions of `TODO`, `FIXME`, `HACK`, `legacy`, `deprecated`, etc.

3. Skim any existing documentation or ADRs (architecture decision records), if available.

Capture your understanding in **Section 2: Context & Understanding**.

---

### Step 2 – Map the Module’s Boundaries

Create a simple view (mentally, or as a few bullet lists in your report) of:

* **Inbound dependencies** – Who calls this module?

  * Which services, components, or modules depend on it?

* **Outbound dependencies** – Who does this module call?

  * External services, other internal modules, databases, message queues, etc.

* **Data flow**

  * What data comes in?
  * What data goes out?
  * What major transformations happen?

You don’t need a formal diagram, but if you find it helpful, you can include a small ASCII diagram or describe the flow in bullets.

---

### Step 3 – Inventory the Main Components

Within the module, identify and list:

* Key **classes / components**
* Main **public APIs** (methods, endpoints, commands, events)
* Main **data models** (entities, DTOs, schemas)
* Any **configuration** relevant to this module (feature flags, environment variables, etc.)

You can include these inventories in Section 2 or Section 5 of your report.

---

### Step 4 – Identify Technical Debt

As you read through the code, look for and document:

**1. Complexity hotspots**

* Very large files or functions
* Deeply nested conditionals
* Functions/methods doing “too many things”
* Hard-to-follow control flow or side effects

**2. Duplication and inconsistency**

* similar logic implemented in multiple places
* different patterns used to solve the same problem
* multiple styles of error handling or logging

**3. Weak boundaries**

* Modules reaching deep into each other’s internals
* “God objects” or classes that know/do too much
* Business logic mixed heavily with infrastructure concerns (e.g. HTTP, DB, frameworks)

**4. Fragility and risk**

* Areas with a history of bugs (if commit history or tickets are easy to see)
* Code that’s hard to change without touching many files
* Complex branching logic with no tests

**5. Comments and markers**

* `TODO`, `FIXME`, `HACK`, `WORKAROUND`, etc.
* Comments indicating temporary solutions that became permanent

For each significant issue, create a **Technical Debt** item (Section 3), with:

* A short, descriptive title
* Where it is
* Why it matters
* Rough priority (High / Medium / Low)

---

### Step 5 – Find Deprecated / Dead / Risky Code

Look specifically for:

* **Unused code**

  * Functions/classes that are never referenced
  * Old versions of logic that appear to have been replaced but not removed

* **Deprecated or legacy paths**

  * Comments mentioning “legacy”
  * Old APIs that coexist with newer ones
  * Old feature flags that may no longer be needed
  * Things focused on backwards compatability

* **Versioned or feature-flagged code that may be obsolete**

  * Feature flags that are always true/false
  * Code guarded by flags that appear unused or outdated

When you suspect code is dead or deprecated:

* Capture **where it is**
* Note **why you think it’s unused/deprecated** (e.g., no references found, comment indicates it)
* Flag it in **Section 4: Deprecated / Dead / Risky Code**

You don’t need to prove beyond all doubt that it’s unused—just clearly explain your **evidence and level of confidence**.

---

### Step 6 – Evaluate the Architecture & Design of this module

From what you’ve learned, describe:

1. **How well-defined the boundaries are**

   * Is it clear what the module is responsible for and what it is not?
   * Are responsibilities leaked across modules?

2. **Coupling and cohesion**

   * Is the module tightly coupled to specific implementations (e.g. concrete classes, frameworks)?
   * Do files/classes inside the module group logically, or feel random?

3. **Patterns and abstractions**

   * Are there clear patterns (e.g. service/repository, CQRS, layers) or is it ad hoc?
   * Are abstractions helping or adding unnecessary complexity?

4. **Error handling and logging**

   * Is error handling consistent and helpful?
   * Are logs meaningful for debugging?
   * Are errors swallowed or silenced?

5. **Resilience and durability**

   * How does module behave on partial failures (e.g. downstream service issues)?
   * Is it easy to change or extend behavior without breaking everything?

Summarize these observations and your recommendations in **Section 5: Architectural / Design Observations**.

---

### Step 7 – Look at Testing & Observability

For the module:

1. **Testing**

   * Are there unit tests, integration tests, or end-to-end tests that cover this module?
   * Do tests focus on key behaviors and edge cases?
   * Are tests easy to understand and maintain?

2. **Observability**

   * Is there structured logging?
   * Any metrics, tracing, or dashboards related to this module (if discoverable)?
   * Are errors surfaced in a way that would help debugging?

Add your findings to **Section 6: Testing & Observability**, including any clear gaps and suggestions.

---

### Step 8 – Prioritize and Summarize Recommendations

In **Section 7: Suggested Next Steps**, propose concrete follow-up work, such as:

* “Refactor `X` to reduce method size and clarify responsibilities (TD-3).”
* “Remove unused `LegacyFooService` after confirming no external dependencies (DEPR-1).”
* “Introduce a clear boundary/interface between `<MODULE>` and `<OtherModule>` (TD-5).”
* “Add integration tests for main `<MODULE>` workflows (TD-7).”

Group them by priority (High / Medium / Low) and link them to your TD-/DEPR- items.

---

### Step 9 – Capture Open Questions

Finally, in **Section 8: Open Questions**, note:

* Anything that was unclear or contradictory
* Assumptions you had to make about behavior or intent
* Decisions that seem surprising and worth team discussion

This helps us know where to clarify context for you and where the codebase may need better documentation.

---

## 5. What *Not* to Do

During this assignment, **please DO NOT**:

* Make code changes, open PRs, or commit refactors
* Rename files/classes purely based on your review
* Remove code, even if you’re confident it’s dead
* Change configs or feature flags

All your work should be **read-only analysis** and **written recommendations** in the Markdown file.

---

If anything seems ambiguous while you’re working, note it under **Open Questions** in your report—we can address those together in review.

## FINAL STEP
After you are done with your review, update review/REVIEW.md by changing the status of the module you reviewed from TODO to DONE.
