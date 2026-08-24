---
name: lightrag-query
description: Query the local LightRAG knowledge graph (GraphRAG over ingested documents). Use when the user asks a question about their RAG documents, knowledge base, or says "ask the rag", "query lightrag".
---

# LightRAG Query

Server: http://localhost:9623 (NOT the LightRAG default 9621).

```powershell
$key = (Get-Content F:\____IL_AI\MECH_RAG\lightrag\.env | Select-String '^LIGHTRAG_API_KEY=').Line.Split('=',2)[1].Trim()
$h = @{'X-API-Key'=$key; 'Content-Type'='application/json'}
$body = '{"query":"USER QUESTION HERE","mode":"hybrid"}'
(Invoke-RestMethod http://localhost:9623/query -Method Post -Headers $h -Body $body).response
```

Answers can take 30-60s. Raise the tool timeout accordingly.

Modes: `hybrid` (default, best), `local` (entity-focused), `global` (relationship/theme-focused), `naive` (plain vector search), `mix`.

Response JSON has a `response` field with the answer including reference markers. Summarize it for the user and list the cited sources. If the user asks for raw output, show `response` verbatim.

If connection refused: `docker ps --filter name=mech_rag` — container `mech_rag-lightrag-1` must be Up; if not, `docker start mech_rag-lightrag-1`.
