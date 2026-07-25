---
name: lightrag-upload
description: Upload text documents (txt, md, normal text PDFs) into the local LightRAG knowledge graph. Use when the user says to add/upload/ingest a text document into the rag. NOT for scanned PDFs, images, or chart-heavy docs — use rag-ingest for those.
---

# LightRAG Upload

Server: http://localhost:9621 — API key header: `X-API-Key: d163d7cc39376b80a18c5bdfc658cec5`

```powershell
curl.exe -s -X POST http://localhost:9621/documents/upload -H "X-API-Key: d163d7cc39376b80a18c5bdfc658cec5" -F "file=@C:\path\to\document.pdf"
```

For multiple files, run one curl per file. After upload, processing (chunking, entity extraction via GLM, embedding via Ollama bge-m3) runs in the background — can take minutes per document. Check progress with the lightrag-status skill. Warn the user that large documents take a while and consume Z.ai tokens.