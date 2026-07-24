# MECH_RAG

A local GraphRAG knowledge base over German engineering-mechanics textbook chapters
(Elastostatik, Spannungszustand), built on **LightRAG** + **RAG-Anything** + **MinerU**.

Ask it a question in German, get an answer with formulas and citations back to the
source chapter.

## Stack

| Layer | What runs | Where |
|---|---|---|
| Server / Web UI / REST API | LightRAG 1.5.4 | Docker, `http://localhost:9623` |
| Document parsing | RAG-Anything 1.3.1 + MinerU 3.4.2 | host Python 3.13 venv |
| LLM + VLM | GLM-5.2 / GLM-4.5V via the Z.ai Coding Plan | cloud |
| Embeddings | Ollama `bge-m3`, 1024-dim | local |
| Storage | JSON KV + NetworkX graph + NanoVectorDB | `lightrag/data/rag_storage` |

The server and the host ingest script write the **same** storage files, so the
container must be stopped while ingesting.

## Contents

```
INSTALL_NEW_COMPUTER.md      full step-by-step install for a different machine
lightrag/rag_ingest.py       PDF -> knowledge graph (carries two required monkeypatches)
lightrag/ingest_detached.ps1 detached ingest runner, survives the calling session
lightrag/.env.example        configuration template (no secrets)
lightrag/data/rag_storage/   the built knowledge graph
.claude/skills/              Claude Code skills: query / status / upload / ingest
IN/                          source PDFs
```

## Quick start

Prerequisites and the hardware-dependent choices (torch wheel, MinerU backend) are
covered in [INSTALL_NEW_COMPUTER.md](INSTALL_NEW_COMPUTER.md). Short version:

```powershell
git clone --depth 1 https://github.com/hkuds/lightrag lightrag-upstream
# merge this repo's lightrag/ files into the clone, then:
Copy-Item lightrag/.env.example lightrag/.env    # fill in your keys
docker compose up -d
```

Then open `http://localhost:9623` and authenticate with `LIGHTRAG_API_KEY`.

## Ingesting a document

```powershell
Set-Location lightrag
docker compose stop                                    # shared storage, no locking
(Get-ChildItem ..\IN -File -Filter *.pdf).FullName |
    Set-Content -LiteralPath .\ingest_list.txt -Encoding UTF8
.\ingest_detached.ps1 -ListFile .\ingest_list.txt      # writes ingest_run.log
docker compose start
```

Use `-ListFile` rather than passing paths as arguments: a filename such as
`Kapitel10_..._Stäben.pdf` is mangled by the ANSI codepage when it crosses a process
boundary, and the parser then fails with `FileNotFoundError`.

## Hard-won rules

1. Ollama must be running before every ingest, or embeddings fail silently and leave
   the storage dirty.
2. Stop the container while `rag_ingest.py` runs.
3. Never change `EMBEDDING_MODEL` or `EMBEDDING_DIM` after the first ingest — the
   existing vectors become unusable.
4. Keep both monkeypatches in `rag_ingest.py` while `raganything==1.3.1` and
   `lightrag-hku==1.5.4`; they fix two `KeyError: 'role_llm_funcs'` call sites.
5. `RAG_MINERU_BACKEND` defaults to `pipeline`. MinerU's default `hybrid-engine`
   needs far more RAM — it OOM'd on a 34-page PDF with 32 GB.
6. Wipe documents with `DELETE /documents`, not by deleting `data/rag_storage`.

## Current corpus

| Document | Pages | Chunks |
|---|---|---|
| Kapitel10 — Elastostatik: Zug und Druck in Stäben | 23 | 137 |
| Kapitel11 — Spannungszustand | 34 | 175 |

2563 graph labels total.

## Licensing

`rag_ingest.py`, `ingest_detached.ps1`, the skills and the documentation are this
repository's own work. [LightRAG](https://github.com/hkuds/lightrag),
[RAG-Anything](https://github.com/HKUDS/RAG-Anything) and
[MinerU](https://github.com/opendatalab/MinerU) are separate upstream projects under
their own licenses. The PDFs under `IN/` and everything derived from them in
`lightrag/data/` belong to their original authors and are included here for
reference only.
