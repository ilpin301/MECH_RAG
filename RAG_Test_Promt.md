```markdown
# Improved Prompt for Claude Code

You are given an existing problem with its structure and solution as a reference.

Your task is to generate a **new, analogous problem** that tests the same concepts but has a **different structure and numerical values**. The new problem should not be a superficial variation—it should require a different setup with other technical structure and given values while maintaining a similar level of difficulty and learning objective.

## Requirements

### File 1: `?-?--Beispielaufgabe.*`
Create a new problem containing only:
- The problem statement.
- A structural sketch/diagram (matching the style of the original, but adapted to the new problem).
- All given values, labels, and necessary information.

Do **not** include:
- Any hints.
- Intermediate calculations.
- The solution.
- The final answer.

### File 2: `?-?--Loesung.*`
Create a concise solution that includes:
- Inermediate calculations
- The essential steps required to solve the problem.
- The final answer.
- Keep the explanation brief and focused (no unnecessary derivations).

## Constraints

- Preserve the original topic, concepts, and approximate difficulty.
- Change the structure, scenario, geometry/layout (if applicable), and numerical values.
- Ensure the problem is internally consistent and fully solvable.
- Use clear, professional formatting consistent with the original files.
- If the original contains a diagram or structural sketch, produce an analogous one for the new problem.

Before writing the files, briefly verify that:
1. The new problem is structurally different from the original.
2. It assesses the same underlying skills.
3. The provided values lead to a valid, unambiguous solution.

Output exactly two files:
1. `?-?--Beispielaufgabe.*`
2. `?-?--Loesung.*` where "?-?--" in pattern takes from corresponding Aufgabe in `RAG_Solver_Promt.md`

Important: svg pict must be on white bg with contrast graphics (lines, texts and so one). Make all results in GERMAN language. don't save tokens. If it doesn't fit in one message, split it into several.
If you can't read or view any of the files I upload due to restrictions, be sure to let me know and suggest a fix (split, zip, csv, etc.).
```
