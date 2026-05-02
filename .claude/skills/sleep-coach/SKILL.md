---
name: sleep-coach
description: >
  Nightly personal sleep coach that helps users build an earlier bedtime habit through
  structured coaching conversations. Trigger this skill when the user mentions: running their
  nightly coaching session, sleep coaching, bedtime check-in, early riser coaching, going to
  bed earlier, sleep habit tracking, "coach me", "run my coaching session", or anything
  related to their nightly sleep accountability routine. Also trigger when the user wants to
  review their sleep coaching history, update their bedtime goal, or analyze their sleep
  habit trends. This skill orchestrates the full coaching loop — reading history, conducting
  the session via the `sleep-coach-interviewer` sub-agent, and persisting results.
---

# Sleep Coach — Nightly Bedtime Coaching Session

## What This Skill Does

Runs a structured nightly coaching conversation designed to help the user shift to an
earlier bedtime. Grounded in habit-formation research (implementation intentions,
habit stacking, identity-based change) and motivational interviewing principles
(open questions, affirmations, reflections, summaries — "OARS").

The session follows a loop:

1. **Load context** — read past transcripts and structured data so the coach
   has continuity across sessions.
2. **Conduct the session** — delegate to the `sleep-coach-interviewer`
   sub-agent (in `.claude/agents/`), which runs the interview directly in
   the Claude Code chat.
3. **Persist results** — save the transcript and append structured metrics.

---

## Directory & File Layout

```
coach_logs/          ← transcript logs, one per session
  session_2025-06-01_2200.md
  session_2025-06-02_2215.md
  ...
data.tab             ← tab-delimited structured table (append-only)
```

### data.tab schema

The file uses a **tab-delimited** format. If it does not exist yet, create it with
this header row on first run:

```
date	target_bedtime	actual_bedtime	minutes_from_target	wind_down_started	screen_off_time	sleep_quality_1to5	energy_next_morning_1to5	wins	obstacles	coach_notes
```

Field definitions:
- **date** — ISO date of the session (YYYY-MM-DD)
- **target_bedtime** — the user's current bedtime goal (HH:MM, 24h)
- **actual_bedtime** — when the user actually got into bed last night (HH:MM)
- **minutes_from_target** — signed integer; negative = early, positive = late
- **wind_down_started** — whether the user started a wind-down routine (yes/no)
- **screen_off_time** — when screens were turned off (HH:MM or "N/A")
- **sleep_quality_1to5** — self-rated sleep quality
- **energy_next_morning_1to5** — self-rated next-morning energy (from previous night)
- **wins** — short free-text noting what went well
- **obstacles** — short free-text noting what got in the way
- **coach_notes** — any coaching observations or action items agreed upon

##  Using data_utils.py

The data_utils.py script can help you work with the data.tab more easily.

Here's it's description:

```
Utility script for sleep-coach data management.

Usage:
  python data_utils.py init                     — Create data.tab with headers if missing
  python data_utils.py append <json_string>     — Validate and append a row
  python data_utils.py summary [--days N]       — Print a trend summary (default last 7 days)
  python data_utils.py streak                   — Print current streak info
```

---

## Step-by-Step Procedure

### Step 1 — Load History

1. Check whether `coach_logs/` exists. If not, create it.
2. Check whether `data.tab` exists. If not, create it with the header row above.
3. Read `data.tab` fully. Parse it to understand trends:
   - How many sessions so far?
   - What is the current target bedtime?
   - Trend in actual_bedtime over last 7 sessions (improving / flat / regressing).
   - Recurring obstacles.
   - Best wins to reinforce.
4. Read the **three most recent** transcript files from `coach_logs/` (sorted by
   filename timestamp descending). These give conversational continuity — the
   coach can reference what was discussed previously.
5. Assemble a `session_context` block (plain text) summarising:
   - Session number (total count + 1).
   - Current streak info (consecutive days where actual ≤ target + 15 min).
   - Trend summary.
   - Last session's action items (extracted from the most recent transcript or
     `coach_notes` column).
   - Any milestones approaching (e.g., 7-day streak, first week).

### Step 2 — Invoke the `sleep-coach-interviewer` Sub-Agent

Read the coaching methodology reference before invoking the sub-agent:

```
references/coaching-methodology.md
```

The interview itself is conducted by the **`sleep-coach-interviewer`**
sub-agent (defined in `.claude/agents/sleep-coach-interviewer.md`). It already
contains the full coaching role, conversation structure, tone guidelines, and
output-format spec. Your job here is to launch it with the dynamic session
context.

Invoke it with the `Agent` tool, `subagent_type: "sleep-coach-interviewer"`,
and a prompt containing the dynamic context block below — filled in from
`session_context`:

```
You are conducting tonight's sleep coaching session in the Claude Code chat.

SESSION CONTEXT
- Session #: {session_number}
- Today's date: {YYYY-MM-DD}
- User's current target bedtime: {target_bedtime}
- Streak: {streak_days} consecutive nights within 15 min of target
- Trend (last 7 sessions): {trend_summary}
- Last session action items: {last_action_items}
- Recurring obstacles: {recurring_obstacles}
- Recent wins to reinforce: {recent_wins}

Run the four-phase interview as described in your agent definition. Use the
AskUserQuestion tool for every coach turn — the user is interacting through
Claude Code, not Telegram. When finished, return the transcript and the
[STRUCTURED_DATA] block in the exact format your definition specifies.
```

The sub-agent runs interactively (it asks the user questions via
`AskUserQuestion`) and, when the session is complete, returns a single final
message containing the `[TRANSCRIPT]`, `[SESSION_COMPLETE]`, and
`[STRUCTURED_DATA]` sections. Wait for it to return before continuing.

### Step 3 — Parse the Response

When the sub-agent returns:

1. Look for the `[SESSION_COMPLETE]` marker. Everything before it is the
   conversation transcript.
2. Look for the `[STRUCTURED_DATA]...[/STRUCTURED_DATA]` block. Parse the
   key-value pairs.
3. If the structured block is missing or incomplete, extract what you can
   from the transcript itself and fill in the rest with "N/A".

### Step 4 — Persist Results

#### Save the transcript

Save the full transcript (everything before `[SESSION_COMPLETE]`) to:

```
coach_logs/session_{date}_{HHMM}.md
```

where `{date}` is today's ISO date and `{HHMM}` is the current time (24h).
Add a YAML frontmatter header:

```yaml
---
session_number: {n}
date: {YYYY-MM-DD}
target_bedtime: {HH:MM}
actual_bedtime: {HH:MM}
action_item: "{tonight's action item}"
---
```

#### Append to data.tab

Append one new row to `data.tab` with the parsed structured data. Use tab
delimiters. Make sure the field order matches the header exactly.

Validate before appending:
- The date is not a duplicate of the last row (prevent double-runs).
- Numeric fields are actually numbers.
- Time fields match HH:MM format or are "N/A".

If validation fails, warn the user and still save the transcript — just skip
the data append and note the issue.

### Step 5 — Confirm to User

After persisting, briefly confirm:
- "Session #{n} saved. Tonight's focus: {action_item}. Sleep well!"

Do not re-summarise the whole session — the sub-agent already closed
it out. Keep this terse.

---

## Edge Cases

- **First session ever**: No history to load. The coaching brief should note
  session_number = 1 and instruct the coach to focus Phase 1 on motivation
  and goal-setting (choosing an initial target bedtime) rather than
  reviewing last night.
- **User wants to change their target bedtime**: During the session, if the
  user asks to adjust the target, the coach should discuss it (is it
  realistic? too aggressive?) and if agreed, update the target in the
  structured data for this session onward.
- **User skipped days**: Note the gap in the session context. The coach
  should acknowledge it without judgment ("Welcome back — no guilt, just
  picking up where we left off.").
- **User reports a medical concern**: The coach must flag it, encourage
  professional consultation, and note it in coach_notes. Do not attempt
  to diagnose or treat.

---

## References

For the full coaching methodology, evidence base, and technique library, read:

```
references/coaching-methodology.md
```

Read this file before composing the coaching brief on the first run, or
whenever you need to adapt the approach for a struggling user.
