# il-aufgabe — installing on another machine

Everything the skill owns lives in this folder. There is exactly **one**
external dependency at runtime, and it is deliberately not copied in here.

## Contents

| File | Needs | Purpose |
|---|---|---|
| `SKILL.md` | — | the workflow itself |
| `reference/templates.md` | — | document skeletons, Koppeltafel, SVG conventions |
| `extract_task.py` | `pymupdf` | PDF → one task's text + figure PNGs |
| `rag_ask.py` | stdlib only | one targeted LightRAG query |
| `fem_check.py` | `numpy` | independent FE cross-check of a frame |
| `validate_output.py` | stdlib only | files / headings / links / SVG check |

## Install

1. **Place the folder at `<PROJECT>\.claude\skills\il-aufgabe\`.** Any depth
   works — `rag_ask.py` walks upward to find `lightrag\.env` — but keeping it
   project-scoped is what makes the skill appear for this project only.

2. **Two packages**, for whichever `python` is on PATH (not the ingest venv):

   ```powershell
   $env:NO_PROXY='*'; python -m pip install pymupdf numpy
   ```

   The `NO_PROXY` prefix is required on machines with the SOCKS system proxy.

3. **The external dependency: `lightrag\.env`.** `rag_ask.py` reads `PORT` and
   `LIGHTRAG_API_KEY` from it. That file also holds a paid LLM API key and is
   gitignored — leave it in the LightRAG install and never copy it here.

   If your layout differs, point at it explicitly:

   ```powershell
   $env:MECH_RAG_ENV = 'D:\somewhere\lightrag\.env'
   ```

   Or skip the file altogether:

   ```powershell
   $env:MECH_RAG_KEY = '<api key>'
   python rag_ask.py --url http://localhost:9621/query "..."
   ```

4. **The RAG stack itself** — container, Ollama, embeddings, knowledge graph —
   is a separate install. See `INSTALL_NEW_COMPUTER.md` in the project root,
   and its "Optional — porting the existing knowledge graph" section if you are
   copying an existing graph rather than re-ingesting.

## Verify

```powershell
python .claude\skills\il-aufgabe\extract_task.py "IN\Aufgabensammlung.pdf" 4.4 --out .scratch\4-4
python .claude\skills\il-aufgabe\validate_output.py 4-4 --out OUT
python .claude\skills\il-aufgabe\rag_ask.py "Welche Dokumente sind im Wissensgraph enthalten?"
```

The first two need no server; the third proves the RAG side is reachable.
