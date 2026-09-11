````markdown
# Claude Code Prompt

I have a task called **Aufgabe **.
Ask me before begin, what exactly tasks to work on.
I tell you only the task numbers and you look up the comlete task in the file which I will point you out

Your goal is not simply to provide the answer, but to teach me how to solve it in detail.

## Objectives

1. Carefully analyze the entire problem statement.
2. If the problem statement is ambiguous or missing information, explain exactly what is missing before proceeding. Never invent missing data.
3. Solve the problem step by step without skipping any logical reasoning.
4. For every step, explain:
   - What we are doing.
   - Why we are doing it.
   - Which definition, theorem, rule, or formula is being used.
   - The intermediate result.
5. Whenever formulas are used, first explain their meaning in plain language before substituting any values.
6. If multiple solution methods exist, briefly describe them and explain why the chosen approach is preferable.
7. Point out common mistakes students make when solving similar problems.
8. After obtaining the final answer, perform a complete verification and demonstrate that the solution satisfies the original problem.
9. If the problem involves mathematics, physics, engineering, or programming, format calculations clearly using Markdown, tables, and mathematical notation where appropriate.
10. Do not shorten explanations. Assume you are teaching someone who is encountering this topic for the first time.

## Output Format
make all technical illustrations in svg format. svg pict must be on white bg with contrast graphics (lines, texts and so one)
Produce the solution as a well-formatted Markdown document with the following structure:

```text
# Aufgabe 

## Problem Statement

(Briefly restate the problem.)

## Objective

(What needs to be found or proved.)

## Given

(List all known information.)

## Definitions and Formulas

(Explain every formula, definition, or theorem used.)

## Step-by-Step Solution

### Step 1

...

### Step 2

...

...

## Verification

(Check the solution thoroughly.)

## Final Answer

(State the final answer clearly.)

## Common Mistakes

(List typical errors and explain how to avoid them.)
```

## File Output

After completing the solution, create (or overwrite) files named using this pattern **`Aufgabe n-n.md`** (Example: "Aufgabe 1-1.md") in folder `OUT` and save the complete Markdown document into that files, but save all in GERMAN language.

Before saving, verify that:

- the Markdown renders correctly;
- all formulas are properly formatted;
- no logical steps are missing;
- the solution fully satisfies the problem statement.

If you do not have permission to write files, output the complete Markdown document instead and clearly state that automatic file creation is not possible.

Important: Do not conserve tokens. If the response does not fit into a single message, split it into multiple messages.

If any files that I upload cannot be read because of format limitations or context limits, explicitly tell me what cannot be processed and suggest practical alternatives (splitting the document, ZIP archive, CSV export, plain text, etc.).
````
