---
description: Post-implementation simplification pass — disentangle complexity, then re-verify against the implementation plan
---

# Simplify

You are tasked with performing a simplification pass on a completed implementation, then re-verifying it against the original plan.

Simplicity is not about aesthetics or brevity. **Simple means "not intertwined."** Complex means things are braided together — complected — so that you cannot reason about one thing without holding others in your head. Your job is to find places where the recent implementation has braided things together unnecessarily, and to disentangle them.

This is primarily a subtractive process. You are not here to add features, redesign, or rewrite. You are here to take working code and reduce the number of things that are intertwined.

This step happens **after** implementation is complete and tests are passing. When finished, you will re-run all automated checks and present manual verification steps from the plan back to the user.

## Getting Started

You will be given a path to an implementation plan markdown file. This plan was used during the implementation phase and contains:

- The phases and specific changes that were made
- Automated success criteria and test commands
- Manual verification steps

When given a plan path:

1. **Read the plan completely.** Understand what was built, why, and how success is measured. Read all files referenced in the plan. Read files fully — never use limit/offset parameters.
2. **Understand the scope of changes from git:**

```
git diff main --stat
git diff main --name-only
git log --oneline main..HEAD
```

If on `main` with no branch, use the most recent commits:

```
git log --oneline -n 10
git diff HEAD~N  # where N covers the implementation commits
```

3. **Read every changed file fully.** Do not skim. You need to understand both what changed and the surrounding context. Cross-reference with the plan to make sure you understand which changes map to which phases.
4. **Create a todo list** to track your simplification candidates.

If no plan path is provided, ask for one. The plan is your map of intent — without it you're guessing at what the implementation was trying to accomplish.

## The Core Question

For every piece of code in the diff, ask: **"How many things do I need to hold in my head to understand this?"**

Humans can juggle only a few things at a time. When things are intertwined, reasoning about them requires holding all the intertwined pieces simultaneously, and the complexity grows combinatorially. The goal is to make each piece of code understandable in isolation.

Focus exclusively on the diff — files and code that were added or modified in the recent implementation. Do not wander into unrelated parts of the codebase.

## Phase 1: Find Complected Code

Look for places where distinct concerns have been braided together. These are ordered roughly by how much damage they do to reasonability:

### State complects everything it touches

State intertwines value and time. Anything that reads or writes shared mutable state becomes coupled to everything else that touches that state — and modules and encapsulation do not mitigate this.

Look for:
- Mutable state that was introduced where a computed value or passed argument would work
- Objects or classes that hold state only to pass it between their own methods — this is just hidden argument passing with temporal coupling
- Variables that are written in one place and read in a distant other, creating invisible wires between code sections

Ask: can this be a value instead? Can it be computed from inputs rather than read from state? Can it be passed as an argument rather than stored and retrieved?

### Objects that complect state, identity, and value

When information gets wrapped in an object with methods, you've braided together what the data *is*, how it *behaves*, and the *specific instance* of it. This is especially wasteful when the "object" is really just information being passed around.

Look for:
- Classes that are essentially data carriers with getters — a plain map, dict, struct, record, or named tuple would be simpler
- Objects created solely to be passed to one other function — this is information dressed up as behavior
- Domain data locked inside class hierarchies when it could be plain data structures that generic functions operate on

Ask: is this an entity with true identity and lifecycle, or is it information? If it's information, leave it as data.

### Methods that complect function and state

A method is a function stapled to a piece of state. Sometimes this coupling is the whole point (the method genuinely operates on the object's identity). Often it's incidental — the function doesn't actually need to be tied to that state.

Look for:
- Methods that don't use `self`/`this` — these are functions that happen to live on an object
- Methods that could take their dependencies as arguments instead of reaching into instance variables
- Static methods or classmethods that exist on a class for namespacing only — a module-level function in the right namespace is simpler

### Inheritance that complects types

Inheritance braids together multiple types into a single chain where changing one affects all others. It makes each type impossible to understand without also understanding its parents and children.

Look for:
- Inheritance hierarchies introduced where composition or a simple interface would work
- Base classes with only one subclass — this is speculative generalization, not useful polymorphism
- Cases where a child overrides most of the parent's behavior — the "is-a" relationship is a lie

### Conditionals that complect the flow of the whole program

Every conditional (switch, if/else chain, pattern match on type) braids together multiple paths. When they dispatch on type or kind, they scatter the logic for one concept across the program.

Look for:
- Switch/match statements on type that could be polymorphic dispatch — one function per type, each understandable independently
- Long if/else chains that mix policy decisions with mechanism — can the rules be expressed as data?
- Conditionals that duplicate knowledge already expressed in the type system

### Syntax and ceremony that complect meaning with noise

Look for:
- Boilerplate that was copy-pasted from elsewhere in the codebase without evaluating whether all of it is needed here
- Overly clever constructs where a straightforward version would be equally concise — do not mistake familiarity for simplicity
- Framework ceremony that could be replaced with plain language constructs

## Phase 2: Disentangle

For each complected piece you've found, the question is: **can I separate the braided concerns without changing what the code does?**

### Separate by removing

- Dead code, unused imports, parameters, and variables
- Defensive checks that can't trigger given actual call sites
- Comments that restate what the code says
- Debug/development logging that shouldn't ship
- Try/catch blocks that re-raise without adding context
- Feature flags or config options with only one possible value

### Separate by inlining

- Functions called exactly once that don't represent a meaningful abstraction boundary
- Variables assigned once and consumed on the next line — these names aren't earning their keep
- Wrapper classes that delegate to a single dependency without adding behavior
- Intermediate transformations that could be a single expression

### Separate by replacing

These are narrow, targeted replacements — not rewrites. The structure stays the same, but a complected construct is swapped for a simpler one:

- Mutable variable → computed value or function argument
- Object that's really just data → plain data structure (map, record, struct, tuple)
- Method that doesn't use instance state → standalone function
- Inheritance with one child → composition or direct implementation
- Imperative loop accumulating state → declarative transformation (map/filter/reduce) if the language idiom supports it
- String building / manual serialization → data structure that a generic function serializes

**Constraint:** only do this when the replacement is a strict disentangling — fewer things braided together afterward. If the replacement introduces a new kind of coupling or requires touching code outside the diff, do not do it.

### Separate by extracting

When one piece of code handles two unrelated concerns:

- Split it into two pieces that each handle one concern
- Make sure each piece can be understood without knowing about the other
- Connect them through arguments, return values, or a queue — not shared state

## Phase 3: Incremental Verification

After each individual simplification, run a quick check to make sure nothing is broken:

```
make check test  # or the project's equivalent
```

If tests fail after a change, **revert it immediately**. A simplification that breaks things was not actually a simplification — it was a misunderstanding of what was intertwined. Do not try to "fix" the tests to accommodate your change.

## Phase 4: Full Verification Against the Plan

Once all simplifications are complete, you must re-verify the **entire implementation** against the plan's success criteria. Simplification can subtly break things that incremental unit tests don't catch — integration behavior, manual workflows, edge cases the plan specifically called out. This phase ensures the implementation still fulfills its original contract.

### Step 1: Re-run all automated checks from the plan

Go back to the plan file and find every automated success criterion and test command across all phases. Run all of them, not just the ones near code you changed. Capture and report results.

```
# Run the project's full check suite
make check test  # or the project's equivalent

# Then run any phase-specific checks from the plan
# e.g. migration checks, lint, type checks, integration tests, etc.
```

If any automated check fails:
- Identify which simplification caused the failure
- Revert that specific simplification
- Re-run the checks to confirm the revert fixed it
- Note in your summary that you reverted and why

### Step 2: Re-verify the plan's success criteria

Walk through every phase of the plan and verify its success criteria still hold:

- Check that the plan's expected files, functions, endpoints, schemas, etc. still exist and work as specified
- If the plan mentions specific behavior (e.g. "API returns 404 for missing resources"), verify it
- If the plan has performance considerations, make sure your simplifications didn't regress them

### Step 3: Pause for manual verification

After all automated verification passes, **stop and present the manual verification steps to the user**. Do not skip this even if you are confident everything works.

Pull the manual verification steps directly from the plan and present them:

```
Simplification Complete — Ready for Manual Verification

All automated checks pass: ✓
- [List each automated check and its result]

Simplifications that were reverted (if any):
- [What was reverted and why]

Please perform the manual verification steps from the plan:
- [List every manual verification step from the plan, across all phases]
- [Include any manual testing steps, UI checks, integration scenarios, etc.]

Let me know if anything doesn't work as expected.
```

Do not mark manual verification items as complete. Only the user can confirm these.

## Presenting Results

The manual verification pause in Phase 4 is your primary output. But before that pause, include a summary of what you changed:

```
Simplification Summary

Disentangled:
- [what was separated and which concerns were braided together]

Removed:
- [what was removed and why it wasn't earning its keep]

Replaced:
- [what was swapped for a simpler construct and why]

Reverted:
- [any simplifications that broke tests, what you tried and why it failed]

Left alone:
- [things you evaluated but decided were actually simple, and why — 
   e.g. "X looks complex but the concerns are genuinely coupled, not incidentally braided"]
```

Then present the Phase 4 verification results and manual verification steps as described above.

The "left alone" and "reverted" sections are important. They show you examined things critically, made judgment calls, and respected the implementation's actual dependencies rather than just your assumptions about them.

## If The Code Is Already Simple

Sometimes implementation produces code that doesn't need simplification. That's a good outcome. But **you must still run the full verification from Phase 4** — this pass is also a chance to catch anything that slipped through implementation.

If you review the diff and find nothing substantively complected, say so:

```
Simplification review complete — no simplification changes needed.

Reviewed N files, M lines changed. The implementation is already simple:
- [brief note on why — e.g. "concerns are well-separated, state is minimal, 
   data is treated as data, each function handles one thing"]

Full verification against plan:
- [List each automated check and its result]

Please perform the manual verification steps from the plan:
- [List every manual verification step from the plan]
```

Do not manufacture changes to justify the pass. An empty simplification diff is a valid result. Simplicity is a prerequisite for reliability — if the code is already simple, declare victory. But still verify.
