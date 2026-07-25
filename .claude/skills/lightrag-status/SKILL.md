---
name: lightrag-status
description: Check LightRAG server health and list ingested documents with processing status. Use when the user asks what's in the rag, whether ingestion finished, or whether the rag server is running.
---

# LightRAG Status

Server: http://localhost:9621 — API key header: `X-API-Key: d163d7cc39376b80a18c5bdfc658cec5`

```powershell
# Health
curl.exe -s http://localhost:9621/health -H "X-API-Key: d163d7cc39376b80a18c5bdfc658cec5"
# Documents + statuses (PENDING / PROCESSING / PROCESSED / FAILED)
curl.exe -s http://localhost:9621/documents -H "X-API-Key: d163d7cc39376b80a18c5bdfc658cec5"
```

Report to the user: server up/down, document count per status, names of failed docs if any. If server down: `docker ps`, then `docker compose up -d` in C:\____PETR_AI\MECH_RAG\lightrag. Full API docs: http://localhost:9621/docs