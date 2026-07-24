---
name: lightrag-status
description: Check LightRAG server health and list ingested documents with processing status. Use when the user asks what's in the rag, whether ingestion finished, or whether the rag server is running.
---

# LightRAG Status

Server: http://localhost:9623 — API key header: `X-API-Key: 73547f1f172e1166f2d7434faa109928`

```powershell
# Health
curl.exe -s http://localhost:9623/health -H "X-API-Key: 73547f1f172e1166f2d7434faa109928"
# Documents + statuses (PENDING / PROCESSING / PROCESSED / FAILED)
curl.exe -s http://localhost:9623/documents -H "X-API-Key: 73547f1f172e1166f2d7434faa109928"
```

Report to the user: server up/down, document count per status, names of failed docs if any. If server down: `docker ps`, then `docker compose up -d` in F:\____IL_AI\MECH_RAG\lightrag. Full API docs: http://localhost:9623/docs