# Templates and conventions

## A. Solution document — `OUT\Aufgabe <n-n>.md`

Headings verbatim (the validator greps for them):

```markdown
# Aufgabe <n.n> — <kurzer Titel>

## Problemstellung
(Aufgabe knapp neu formuliert, Geometrie ausgeschrieben.)
### Hinweis zur Auslegung der Skizze
(Nur wenn eine Groesse aus der Zeichnung statt aus dem Text gelesen wurde.)

## Zielsetzung
## Gegeben
## Definitionen und Formeln
## Schritt-fuer-Schritt-Loesung
### Schritt 1 — <was>
(Pro Schritt: *Was* wir tun, *warum*, welche Regel/Formel, Zwischenergebnis.)
## Verifikation
## Endergebnis
## Haeufige Fehler
```

Rules: explain every formula in words before substituting numbers; never shorten a derivation; boxed final results via `$$\boxed{\;...\;}$$`; results table at the end.

## B. New task — `OUT\<n-n>--Beispielaufgabe.md`

Statement, sketch, given values and labels. **Nothing else** — no hints, no partial results, no answer. Sub-questions a)/b)/c) mirroring the original's skill set.

## C. New solution — `OUT\<n-n>--Loesung.md`

Schnittgroessen, the essential steps with intermediate values, `## Probe`, `## Endergebnisse` table. Brief — no full teaching derivation.

The new task must be **structurally** different: change the support layout, the member orientation, the load direction and type, the lengths and the target values. Keep the topic, the assessed concepts and the difficulty. Verify the chosen numbers give an unambiguous, solvable result before writing.

## D. Koppeltafel rows used here

With member length `s`, ordinate `i` from the `M_0` diagram and `k` from the `M_1` diagram:

| `M_0` | `M_1` | `∫ M_0 M_1 ds` |
|---|---|---|
| Rechteck (i) | Rechteck (k) | `s·i·k` |
| Rechteck (i) | Dreieck (k) | `½·s·i·k` |
| Dreieck (i) | Dreieck (k), gleiche Nullstelle | `⅓·s·i·k` |
| quadr. Parabel (i), **Scheitel** at the shared zero | Dreieck (k), gleiche Nullstelle | `¼·s·i·k` |
| quadr. Parabel (i), **symmetric** — zero at both ends, sag `i` at midspan | Dreieck (k) | `⅓·s·i·k` |
| Rechteck (i) | Trapez (k1..k2) | `s·i·(k1+k2)/2` |

**Two different rows share the name "quadratische Parabel".** Most Formelsammlungen use it for the **symmetric** parabola from a uniform load on a supported span — zero at both ends, sag `i` at midspan — giving `⅓`. A cantilever's parabola instead has its **vertex at the edge**, value *and* slope zero at the free end, giving `¼`. Asked for "quadratische Parabel x Dreieck" the RAG quotes the `⅓` row, which is right for its shape and wrong for a cantilever. Always check where the vertex sits before reading off a coefficient, and settle it by direct integration when in doubt — 20 seconds.

Tension-side convention: draw each diagram on the fibre it stretches. Same side for both diagrams gives a positive contribution, opposite sides a negative one. Check continuity around every rigid corner — it is a free correctness probe.

Statically indeterminate with an elastic bar: `δ₁₀ + X·δ₁₁ = 0`, with `δ₁₁ = ∫ M̄₁²/EI ds + N̄₁²·ℓ_bar/EA`. Forgetting the bar term silently computes a rigid bar. For a redundant **support reaction** instead of a bar, the same equation holds with `δ₁₁ = ∫ M̄₁²/EI ds` alone.

**When the table does not apply.** A **triangular (linearly varying) load** produces a moment with a quadratic *and* a cubic term — e.g. `M = q₀(s²/2 − s³/(12l))` for a cantilever with the peak at the free end. No single table row matches it. Integrate directly. The same goes for any diagram that is a sum of two shapes; splitting it into tabulated parts is fine, forcing it into one row is not.

**Two-member corner vs. T-joint.** The tension-side rule above — same side gives a positive contribution — presumes a corner of **two** members, where the tension side runs continuously around it and the moment is continuous. A joint with **three** member ends (a through member plus a branch) behaves differently: the moment **jumps** at the joint, and the tension side may sit on opposite faces of the two collinear segments. There, fix one cut-face convention **per member** and keep it for both `M₀` and `M̄₁`:

| member | computed from | typical variable |
|---|---|---|
| branch | its far end | `s`, from the free/far end |
| through member, side 1 | that side's support | `y` |
| through member, side 2 | that side's support | `u` |

State the table in the solution document. The probe replacing continuity: **the three member-end moments at the joint sum to zero**, in each of the `0` and `1` systems separately. Since the three come from independent free-body cuts, a zero sum is strong evidence all three are right.

**Numeric cross-check.** Run `fem_check.py` (sibling of this file) on every solved frame and on every newly designed one. It re-derives the support reactions by finite elements and shares no algebra with the hand solution, so agreement is genuine evidence. Report it in `## Verifikation` as a numeric-vs-analytic table.

## E. SVG conventions

- Canvas: `<rect width="..." height="..." fill="#ffffff"/>` as the first child.
- `font-family="Georgia, 'Times New Roman', serif"`, symbols `font-style="italic"`.
- Members `stroke-width="6"`, dimension and load lines `1.3`–`1.6`, all `stroke="#000000"`.
- Arrowheads via `<defs><marker>`; define a start-marker variant for two-headed dimension lines.
- Moment diagrams: frame in `#999999`, area filled `fill-opacity="0.25"` — `#1a4fa0` for anything coupling with `M_0`, `#b03030` for a counteracting diagram.
- One file per illustration, in `OUT\svg\<n-n>\`. Names: `System1.svg`, `System2.svg`, `Momente.svg`, `Beispielaufgabe.svg`, `Loesung.svg`.
- Check with `python -c "import xml.etree.ElementTree as ET; ET.parse('f.svg')"` — the validator does this too.
