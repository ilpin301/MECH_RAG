---
name: rag-ingest
description: Ingest non-text documents (scanned PDFs, images, chart/table-heavy PDFs, office docs) into the LightRAG knowledge graph via RAG-Anything + MinerU. Use when the user wants to add a scanned or image-heavy document to the rag.
---

# RAG-Anything Ingest

Pipeline: MinerU parses the document locally (GPU/CUDA) → text/images split → GLM-5.2 extracts entities, GLM-4.5V describes images/tables/charts/equations → bge-m3 embeds → merged into the same LightRAG storage the Docker server uses.

## Source folder rule

Ingest files ONLY from `F:\____IL_AI\MECH_RAG\IN\`. If the user points at a file elsewhere, ask them to copy it into `IN\` first.

## Run it

The venv is SHARED across projects and lives at `F:\____IL_AI\RAG\lightrag\.venv-rag` — not inside this project.

```powershell
# 1. put the document paths in the list file, one per line, UTF-8
#    F:\____IL_AI\MECH_RAG\lightrag\ingest_list.txt
# 2. REQUIRED: stop the server — the script writes the same storage files as the container
docker stop mech_rag-lightrag-1
# 3. launch detached (survives session close); the script restarts the container when done
Start-Process pwsh -ArgumentList "-NoProfile","-File","F:\____IL_AI\MECH_RAG\lightrag\ingest_detached.ps1","-ListFile","F:\____IL_AI\MECH_RAG\lightrag\ingest_list.txt" -WindowStyle Hidden
# 4. monitor
Get-Content F:\____IL_AI\MECH_RAG\lightrag\LOG\ingest_run.log -Wait -Tail 20
```

Success = `EXITCODE=0` at the end of the log. `ingest_detached.ps1` sets every required env var itself (see below) and runs `docker compose start` afterwards.

Use `-ListFile`, not bare path arguments: non-ASCII filenames (Stäben, Verzerrungszustand) get mangled through the ANSI codepage when passed as process args.

## Expect it to be slow

On the Quadro P2000 (5 GB) a ~200-page slide deck takes roughly 3.5 hours end to end. Phases in order, each visible in the log:

1. MinerU layout/formula prediction (GPU, ~30 min)
2. text-phase entity extraction (`Chunk N of M extracted`)
3. multimodal chunk generation — GLM-4.5V describing every figure/table/equation, 2 at a time (`Multimodal chunk generation progress: N/M`)
4. entity extraction over those multimodal chunks
5. merge + summary (`LLMmrg:`) and VDB write

Do not poll the log every 20s for hours — set one long-running watcher that greps for `^EXITCODE=`.

## Required environment (already inside ingest_detached.ps1)

- `TIKTOKEN_CACHE_DIR='C:\Users\il720506\AppData\Local\Temp\data-gym-cache'` — without it tiktoken tries to download `o200k_base.tiktoken` from the Azure CDN and TIMES OUT on this SOCKS-proxy machine. Fatal: `LightRAG initialization failed: HTTPSConnectionPool(host='openaipublic.blob.core.windows.net'...)`. Windows temp cleaning wipes this dir — if it's gone, pre-warm it with `python -c "import tiktoken; tiktoken.get_encoding('o200k_base')"` under `NO_PROXY='*'`.
- `NO_PROXY='*'` — bypass the SOCKS system proxy for local and z.ai calls.
- `MINERU_DEVICE_MODE='cuda'`, `PYTHONIOENCODING='utf-8'`.
- `ZAI_API_KEY` — rag_ingest.py requires this name; this project stores the z.ai key in `.env` as `LLM_BINDING_API_KEY`, and the script maps it across.

## rag_ingest.py contains critical patches — DO NOT regenerate the script

Four patches are REQUIRED (raganything 1.3.1 + lightrag-hku 1.5.4 compatibility):
1. `asdict` → `_build_global_config` redirect in `raganything.modalprocessors`
2. `role_llm_funcs` mirrored into the LightRAG instance `__dict__`
3. junk-content filter wrapping `separate_content` in BOTH `raganything.utils` and `raganything.processor` (drops page_number/header/footer — ~38% of multimodal items are junk otherwise)
4. `_VLM_SEMAPHORE = asyncio.Semaphore(2)` — the z.ai coding endpoint has a CONCURRENCY limit (error 1305); do not raise above 2

Any edit must preserve all four. The reference copy is `F:\____IL_AI\PCM_RAG\lightrag\rag_ingest.py`.

## Re-ingesting a document that is already in the RAG

LightRAG rejects a same-filename insert as a duplicate and leaves a `dup-*` FAILED stub instead of replacing anything. Delete the old doc FIRST (server UP):

```powershell
$key = (Get-Content F:\____IL_AI\MECH_RAG\lightrag\.env | Select-String '^LIGHTRAG_API_KEY=').Line.Split('=',2)[1].Trim()
curl.exe -s -X DELETE http://localhost:9623/documents/delete_document -H "X-API-Key: $key" -H "Content-Type: application/json" -d '{"doc_ids":["doc-XXXX"]}'
```

Deletion runs in the background and LLM-rebuilds every entity shared with other documents — takes a minute or two. Wait for the file to disappear from `/documents` before starting the ingest.

## z.ai 429 behavior

`ERROR: OpenAI API Rate Limit Error ... code 1305` = z.ai concurrency limit, NOT a per-minute rate. "OpenAI" here is the openai python client used as transport for z.ai, not OpenAI the service. Occasional 429s are absorbed by retry backoff — normal, ignore. Items logging `RetryError` (retries exhausted) are SKIPPED, leaving graph gaps; re-run later when z.ai load drops.

## Kill/restart is safe and cheap

- Parse cache + text-phase LLM cache persist after each call — re-runs replay them free.
- Multimodal VLM descriptions may NOT hit cache — expect those to re-run.
- **`vdb_*.json` files are only written on a clean `EXITCODE=0` finish.** A killed run can leave them stale or missing → queries return `[no-context]`. Fix: run to clean completion.
- Killed runs leave `dup-*` FAILED stubs and can leave real docs stuck in `handling`. Cleanup with the server STOPPED: fix `"handling"` → `"processed"` and delete `dup-*` entries in `data\rag_storage\kv_store_doc_status.json`; or delete stubs via the API call above.

## Before any ingest

- Ollama must be up: `curl.exe -s http://localhost:11434/api/version`
- Container stopped (step 2 above)
- Verify afterwards with the lightrag-status skill (document should show `processed` with a realistic chunk count), then test one query.
