---
name: lightrag-upload
description: Upload text documents (txt, md, normal text PDFs) into the local LightRAG knowledge graph. Use when the user says to add/upload/ingest a text document into the rag. NOT for scanned PDFs, images, or chart-heavy docs — use rag-ingest for those.
---

# LightRAG Upload

Server: http://localhost:9623 (NOT the LightRAG default 9621). Server must be UP.

```powershell
$key = (Get-Content F:\____IL_AI\MECH_RAG\lightrag\.env | Select-String '^LIGHTRAG_API_KEY=').Line.Split('=',2)[1].Trim()
curl.exe -s -X POST http://localhost:9623/documents/upload -H "X-API-Key: $key" -F "file=@F:\____IL_AI\MECH_RAG\IN\document.pdf"
```

One curl per file. Processing (chunking, GLM-5.2 entity extraction, bge-m3 embedding via Ollama) runs in the background — minutes per document. Watch it with `docker logs --tail 30 mech_rag-lightrag-1`; track progress via the lightrag-status skill.

**This path does text only.** Lecture slides, figures, and equations come out thin — Kapitel13 yielded 14 chunks here versus 273 via the rag-ingest (MinerU) skill. For anything with diagrams or formulas use rag-ingest instead.

Warn the user that large documents take a while and consume Z.ai tokens.
