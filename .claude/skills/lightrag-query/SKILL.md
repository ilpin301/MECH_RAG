---
name: lightrag-query
description: Query the local LightRAG knowledge graph (GraphRAG over ingested documents). Use when the user asks a question about their RAG documents, knowledge base, or says "ask the rag", "query lightrag".
---

# LightRAG Query

Server: http://localhost:9621 — API key header required: `X-API-Key: d163d7cc39376b80a18c5bdfc658cec5`

Query with PowerShell (write JSON body to a temp file first to avoid quoting issues):

```powershell
$body = '{"query":"USER QUESTION HERE","mode":"hybrid"}'
$tmp = New-TemporaryFile; Set-Content $tmp $body -NoNewline
curl.exe -s http://localhost:9621/query -H "Content-Type: application/json" -H "X-API-Key: d163d7cc39376b80a18c5bdfc658cec5" -d "@$tmp"
```

Modes: `hybrid` (default, best), `local` (entity-focused), `global` (relationship/theme-focused), `naive` (plain vector search), `mix`.

Response JSON has `response` field with the answer including reference markers. Summarize the answer for the user and list the cited sources. If the user asks for raw output, show `response` verbatim.

If connection refused: check `docker ps` — container `rag-lightrag-1` must be Up; if not, `docker compose up -d` in C:\____PETR_AI\MECH_RAG\lightrag.