---
name: rag-ingest
description: Ingest non-text documents (scanned PDFs, images, chart/table-heavy PDFs, office docs) into the LightRAG knowledge graph via RAG-Anything + MinerU. Use when the user wants to add a scanned or image-heavy document to the rag.
---

# RAG-Anything Ingest

Pipeline: MinerU parses the document locally (CPU) → text/images split → GLM-5.2 extracts entities, GLM-4.5V describes images → bge-m3 embeds → merged into the same LightRAG storage the Docker server uses.

```powershell
Set-Location F:\____IL_AI\MECH_RAG\lightrag
$env:NO_PROXY='*'
$env:Path = "F:\____IL_AI\RAG\lightrag\.venv-rag\Scripts;$env:Path"   # raganything checks `mineru --version` on PATH
$env:PYTHONIOENCODING='utf-8'
$env:MINERU_DEVICE_MODE='cuda'
# REQUIRED: stop server first — script writes the same storage files as the container
docker compose stop
& "F:\____IL_AI\RAG\lightrag\.venv-rag\Scripts\python.exe" rag_ingest.py "C:\path\to\document.pdf"
docker compose start
```

Notes:
- First run downloads MinerU models (~a few GB) — slow once, cached after.
- MinerU runs on CPU by default; parsing a big scan takes minutes.
- Multiple files: pass several paths, `rag_ingest.py file1.pdf file2.pdf`.
- Verify afterwards with lightrag-status skill (document should appear PROCESSED).
- If rag_ingest.py is missing, tell the user setup step 5 of F:\____IL_AI\MECH_RAG\INSTALL.md is incomplete.