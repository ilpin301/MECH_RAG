---
name: il-aufgabe
description: Use when the user wants an Aufgabe (engineering-mechanics exercise) from a PDF worked out in German, or an analogous practice problem generated from one. Triggers on "Aufgabe 4.4", "solve task 2.3", "loese Aufgabe", "make me a similar task", "Beispielaufgabe", RAG_Solver_Promt.md, RAG_Test_Promt.md.
---

# il-aufgabe

Two-part workflow over `IN\*.pdf` into `OUT\`. Part 1 = full teaching solution. Part 2 = a new analogous problem plus its short solution. Every produced file is **German**; chat language is whatever the user is using.

## 1. Ask first, never assume

Use AskUserQuestion before any other work:

| Ask | Note |
|---|---|
| Task number(s) | e.g. `4.4`, or several at once |
| Source file | default candidate `IN\Aufgabensammlung.pdf`; list `IN\` if the user is unsure |
| Which parts | solution only / new task only / both (default: both) |

If the user already supplied all of it in their message, skip the question and state what you took as given.

## 2. Stages and model choice

Pick the cheapest tier that can do the step.

| # | Stage | Runs as | Why |
|---|---|---|---|
| 1 | Extract task text + render the figure page | `python extract_task.py` | Deterministic, no model at all |
| 2 | Read the figure, resolve the geometry | **main thread (strongest model)** | Vision + dimension chains; highest error source. Never delegate. |
| 3a | Locate lecture context and any existing answer | `python rag_ask.py "..."` | HTTP call, no model tokens |
| 3b | Formula-sheet rows + chapter notation (after the shapes are known) | `python rag_ask.py "..."` | HTTP call, no model tokens |
| 4 | Solve + verify | **main thread (strongest model)** | Physics. Never delegate. |
| 4b | Numeric cross-check of the result | `python fem_check.py model.json` | Independent of the hand algebra; no model tokens |
| 5 | Design the analogous problem | **main thread (strongest model)** | Originality and difficulty matching |
| 6 | Write the files (md + svg) | subagent, `model: sonnet` | Verbatim transcription; also keeps edit diffs out of the user's chat |
| 7 | Validate | `python validate_output.py` + Grep | Deterministic |

Never hand a whole PDF to a subagent. Stage 1 has already reduced it to `task.txt` plus one PNG — pass those paths, not the source.

The scripts need `pymupdf` and `numpy` on whichever `python` is on PATH; `README.md` in this folder covers installing the skill on a fresh machine.

Cache: stage 1 writes into a scratch dir. Re-running a later stage must not re-parse the PDF.

## 3. Geometry — where this workflow actually fails

Read the rendered `page_NN.png` yourself, and before solving:

- **Resolve every dimension chain.** A dimension line split into `a` and `a/2` means the member is `3a/2`, not `a`. Write the total out explicitly.
- **Cross-check against pixels.** Measure the drawing; the length ratio must match your reading. A mismatch means you misread it.
- **Record the reading** in the output under `### Hinweis zur Auslegung der Skizze` whenever a length came from a drawing rather than from the text.
- Check what the intermediate dimension tick lines up with — usually a support point or the end of a load. That is why the chain is split.

## 4. RAG — four targeted queries, never a general one

A generic "explain the Einheitslastsatz" query burns a minute and changes nothing — you already know the method. Query the corpus for what you **cannot** know from the method alone: this course's own formula sheet, its notation, and its worked examples. Use `rag_ask.py`; it handles the API key, the port and the local proxy bypass.

**Before solving** (straight after stage 1, with `task.txt` in hand):

```powershell
python .claude\skills\il-aufgabe\rag_ask.py "<erster Satz der Aufgabenstellung woertlich> — Welche Abschnitte und Beispiele im Skript behandeln genau diese Aufgabenstellung?"
python .claude\skills\il-aufgabe\rag_ask.py "Enthaelt die Aufgabensammlung oder das Skript eine Loesung, ein Ergebnis oder einen Loesungsweg zu Aufgabe <n.n>?"
```

The second is the cheapest independent second opinion available. If the corpus already holds an answer and it disagrees with yours, find out why **before** writing anything.

**After the `M₀` and `M̄₁` shapes are fixed, before writing the files:**

```powershell
python .claude\skills\il-aufgabe\rag_ask.py "Formelsammlung Koppeltafel/Integraltafel: gib die Zeilen fuer <die tatsaechlich vorkommenden Kombinationen, z.B. Rechteck x Dreieck, quadratische Parabel x Dreieck> woertlich wieder, mit Koeffizient, Symbolik und Bezeichnungen."
python .claude\skills\il-aufgabe\rag_ask.py "Welche Vorzeichen- und Schnittufer-Konvention sowie welche Notation verwendet <Kapitel n> fuer <Thema>?"
```

The timing is the point: you can only ask for the **right** table rows once you know which diagram shapes actually occur. Ask earlier and you get the whole table back — a general query again.

Carry the formula-sheet symbols and the chapter's convention into the solution document. A correct result written in notation the student has never seen is worth less than it should be.

**RAG output is a lead, not an authority.** It is LLM-generated over the corpus and has already returned a compatibility equation in different bookkeeping from the one used here. Never take a number, a coefficient or a sign from it without the independent check from stage 4b.

## 5. Solve

Method is fixed by the source material: **Prinzip der virtuellen Kraefte** (Einheitslastsatz), tension-side convention, Koppeltafel. Document skeleton, Koppeltafel rows and SVG conventions: `reference\templates.md`.

Every result gets a back-substitution check in a `## Verifikation` section. A "choose `EA` / `A` so that the force takes value `V`" sub-question is the strongest check available — it must land on the given value **exactly**. If it does not, the stage-2 geometry reading is wrong. Go back and re-read the figure; do not fudge the algebra.

**Always run the numeric cross-check**, whether or not the task supplies such a sub-question — many do not. Write a small JSON model and run `fem_check.py`; it re-derives the support reactions by finite elements, sharing no step with the hand calculation, so it catches sign errors, a misread support type and a wrong dimension chain in one shot. Put the comparison in the `## Verifikation` section as a table of numeric vs. analytic. Cross-check the **new** problem too, before writing it — an analogous task with inconsistent numbers is worse than none.

Two structural traps that are not obvious from the Koppeltafel alone:

- **T-joints.** The "tension side runs continuously around the corner" rule only holds for a corner made of **two** members. At a joint with **three** member ends the moment jumps, and continuity is replaced by node equilibrium: the three member-end moments sum to zero. Fix one cut-face side per member, state it in the document, and use the node sum as the correctness probe.
- **Triangular loads.** Their bending moment is a *mix* of quadratic and cubic terms, not any single row of the Koppeltafel. Integrate directly. See `reference\templates.md`.

## 6. Output contract

`<n-n>` = the task number with a hyphen, e.g. `4-4`.

```
OUT\Aufgabe <n-n>.md            full teaching solution (German)
OUT\<n-n>--Beispielaufgabe.md   new analogous problem: statement + sketch ONLY
OUT\<n-n>--Loesung.md           its concise solution
OUT\svg\<n-n>\*.svg             every illustration
```

- SVGs are **separate files**, never inline in the markdown. Link relative to the `.md`: `![System 1](svg/4-4/System1.svg)` — forward slashes in the link.
- Every SVG: a white background `<rect>` as the first element, black or high-contrast strokes and text.
- `--Beispielaufgabe.md` carries no hints, no intermediate values and no answer.

## 7. Validate before reporting done

```powershell
python .claude\skills\il-aufgabe\validate_output.py 4-4 --out OUT
```

Exit code 0 is required. It checks that the files exist, the required headings are present, every image link resolves, and every SVG parses as XML with a white background rect.

## Common mistakes

| Mistake | Fix |
|---|---|
| Assuming the source file or the task number | Ask. Always. |
| Working from the PDF text layer only | The geometry lives in the drawing. Render it and look. |
| Taking the first number on a dimension line as the length | Sum the chain. |
| Delegating the physics to a cheap subagent | Wrong answers come back confidently worded. Stages 2, 4 and 5 stay on the strongest model. |
| Writing the output files from the main thread | Edit diffs flood the user's chat. Delegate stage 6. |
| Inline `<svg>` inside markdown | Obsidian's sanitizer is unreliable for it. Separate files. |
| Putting SVGs flat in `OUT\` | They go in `OUT\svg\<n-n>\`. |
| Reporting done without running the validator | Broken links and unparseable SVGs fail silently. |
| Writing the files in English | Files are German. The chat language is a separate question. |
| Asking the RAG a general method question | You already know the method. Ask for the formula sheet rows, the chapter notation and any existing answer — §4. |
