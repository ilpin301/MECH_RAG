---
name: lightrag-status
description: Check LightRAG server health and list ingested documents with processing status. Use when the user asks what's in the rag, whether ingestion finished, or whether the rag server is running.
---

# LightRAG Status

Server: http://localhost:9623 (NOT the LightRAG default 9621). Container: `mech_rag-lightrag-1`.

```powershell
$key = (Get-Content F:\____IL_AI\MECH_RAG\lightrag\.env | Select-String '^LIGHTRAG_API_KEY=').Line.Split('=',2)[1].Trim()
$h = @{'X-API-Key'=$key}
# Health
Invoke-RestMethod http://localhost:9623/health -Headers $h
# Documents + statuses (PENDING / PROCESSING / PROCESSED / FAILED)
$r = Invoke-RestMethod http://localhost:9623/documents -Headers $h
$r.statuses.PSObject.Properties.Value | ForEach-Object { $_ } | ForEach-Object { "{0,-52} {1,-10} chunks={2}" -f $_.file_path, $_.status, $_.chunks_count }
```

Report to the user: server up/down, document count per status, names of failed docs if any.

If server down:

```powershell
docker start mech_rag-lightrag-1
# or, fresh: Set-Location F:\____IL_AI\MECH_RAG\lightrag ; docker compose up -d
docker logs --tail 50 mech_rag-lightrag-1   # this server logs to stdout only, there is no log file
```

Full API docs: http://localhost:9623/docs

Known: a `dup-*` entry with status `failed` is a duplicate-filename stub from an interrupted run, not a real ingest failure.
