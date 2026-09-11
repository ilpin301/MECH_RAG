# Prompt for Claude Code

Based on everything discussed in this conversation, create a reusable Claude Code Skill that automates this workflow.

## Goal

The Skill should interactively generate solutions and new tasks from existing ones.

When the Skill starts, it should first ask me:

1. Which task number(s) should be used as the source?
2. Which file contains those tasks?
3. (If needed) Any additional parameters required for generation.

After receiving my answers, the Skill should execute exactly the same workflow we established earlier in this conversation, producing the same quality and output format.

## Requirements

### 1. Interactive workflow

Do not assume inputs.

Always begin by asking for:
- Source file.
- Task number(s).
- Any missing information needed to complete the workflow.

### 2. Reproduce the existing workflow

The Skill should replicate the process previously developed in this conversation, including:
- Reading the selected task(s).
- Creating analogous tasks that test the same concepts.
- Changing the structure, scenario, layout, and numerical values while preserving learning objectives and difficulty.
- Producing all required output files in the same format as before.

### 3. Optimize for cost and speed

Design the Skill to minimize token usage without reducing output quality.

Whenever practical:

- Break the workflow into independent stages.
- Use smaller/cheaper models for simple subtasks such as:
  - parsing,
  - locating tasks,
  - extracting metadata,
  - validation,
  - formatting,
  - file manipulation,
  - simple transformations.
- Reserve the strongest model only for reasoning-intensive tasks such as:
  - designing new problems,
  - preserving pedagogical quality,
  - verifying equivalence of difficulty,
  - ensuring originality.

The orchestration should automatically choose the least expensive model capable of each step.

### 4. Modular architecture

Split the Skill into clearly separated modules/functions wherever possible, for example:

- Input collection
- Task extraction
- Structural analysis
- Problem generation
- Diagram/structure generation
- Solution generation
- Validation
- File writing

Each module should have a single responsibility and well-defined inputs/outputs.

### 5. Efficiency

Avoid:
- repeating large context unnecessarily,
- sending full files between stages if only fragments are needed,
- duplicate parsing,
- duplicate reasoning,
- unnecessary regeneration.

Cache intermediate results whenever possible.

### 6. Validation

Before producing final files, verify that:
- the generated problem is structurally different,
- it assesses the same underlying concepts,
- difficulty is comparable,
- values are internally consistent,
- the solution is correct,
- all required files were produced.

### 7. Deliverables

Generate a complete Claude Code Skill, including:
- the Skill configuration,
- prompts,
- instructions,
- modular workflow,
- recommended model selection for each stage,
- any helper files/templates needed for implementation.

The Skill should be production-ready, easy to maintain, and optimized for both quality and token efficiency.