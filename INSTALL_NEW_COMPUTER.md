# Install this RAG stack on a different computer

**Audience: Claude Code running on the target machine.** Follow the steps in order. Every step has a verification command — do not continue until it passes. Report the failing output instead of guessing if a check fails.

This is a hardware-adaptive port of `X:\RAG_MAIN\RAG\REPLICATE.md` Scenario B. The source install is Windows 11 + Quadro P2000 (5 GB VRAM) + 32 GB RAM; steps 4 and 8 branch on the target hardware.

---

## What this stack is

- **LightRAG 1.5.4** server in Docker — web UI + REST API, owns the knowledge graph storage (JSON/NetworkX/NanoVectorDB on a bind mount).
- **RAG-Anything 1.3.1 + MinerU 3.4.2** in a host Python venv — parses PDFs (layout, OCR, formulas, tables, figures) and writes into the *same* storage the container uses.
- **LLM/VLM**: GLM-5.2 + GLM-4.5V via the Z.ai Coding Plan (cloud, no local GPU needed).
- **Embeddings**: local Ollama `bge-m3`, 1024-dim.

Consequence of the shared storage: **the container must be stopped while the host ingest script runs.** Queries go through the container; ingest does not.

---

## Step 0 — collect inputs from the user

Ask for these before starting; they cannot be derived:

1. **Z.ai Coding Plan API key** (format `<32 hex>.<16 alnum>`). On the source machine it lives in `X:\RAG_MAIN\MECH_RAG\lightrag\.env` as `LLM_BINDING_API_KEY` / `VLM_LLM_BINDING_API_KEY`, and also in the user-level env var `ZAI_API_KEY`. Never commit it to a repo.
2. **Install folder** on the new machine, e.g. `D:\MECH_RAG` (this doc writes `<ROOT>` for it).
3. **Port** for the web UI (default `9621`; use another only if taken).
4. Whether the machine has an **NVIDIA GPU** (step 4 branches on it).

---

## Step 1 — prerequisites

```powershell
# check what's already there
docker --version
python --version
py -0p                      # list installed Python versions
git --version
ollama --version
nvidia-smi                  # non-zero exit = no NVIDIA GPU, that's OK
```

Install whatever is missing:

- **Docker Desktop** — https://desktop.docker.com (~635 MB). After install, `docker` may not be on PATH until a shell restart; fall back to `& "C:\Program Files\Docker\Docker\resources\bin\docker.exe"`.
- **Python 3.13** — NOT 3.14. PyTorch and MinerU wheels lag the newest release. Verify: `py -3.13 --version`.
- **git**.
- **Ollama** — https://ollama.com/download.

**Corporate-proxy quirk (this org's machines):** the system proxy is SOCKS-only, so `pip` dies with `OSError: Missing dependencies for SOCKS support`. Prefix every network Python command with `$env:NO_PROXY='*'`. Diagnose with `python -c "import urllib.request; print(urllib.request.getproxies())"`.

**Verify:**
```powershell
docker info --format '{{.ServerVersion}}'   # daemon actually running, not just installed
py -3.13 --version
```
Docker Desktop is frequently *not* running after a reboot. Start it and wait 1–2 min before any `docker compose` command.

---

## Step 2 — Ollama + embedding model

```powershell
[Environment]::SetEnvironmentVariable('OLLAMA_HOST','0.0.0.0:11434','User')
# restart Ollama after setting this, otherwise it stays bound to 127.0.0.1
$env:NO_PROXY='*'; ollama pull bge-m3
```

`OLLAMA_HOST=0.0.0.0` is mandatory: the container reaches Ollama via `host.docker.internal`, which cannot connect to a loopback-only listener.

**Verify:**
```powershell
(Invoke-RestMethod http://localhost:11434/api/version).version
(Invoke-RestMethod http://localhost:11434/api/tags).models.name    # must list bge-m3
```

---

## Step 3 — clone LightRAG

```powershell
New-Item -ItemType Directory -Force <ROOT> | Out-Null
$env:NO_PROXY='*'; git clone --depth 1 https://github.com/hkuds/lightrag <ROOT>\lightrag
```

**Verify:** `Test-Path <ROOT>\lightrag\docker-compose.yml` → True.

---

## Step 4 — Python venv (HARDWARE BRANCH)

```powershell
$env:NO_PROXY='*'
py -3.13 -m venv <ROOT>\lightrag\.venv-rag
& <ROOT>\lightrag\.venv-rag\Scripts\pip.exe install raganything "mineru[core]" openai
```

Reference versions that are known to work together: `raganything 1.3.1`, `lightrag-hku 1.5.4`, `mineru 3.4.2`, `openai 2.44.0`, `numpy 2.5.0`, `transformers 4.57.6`.

Then pick **one** torch branch:

**4a — NVIDIA Pascal GPU (GTX 10xx, Quadro P2000/P4000, Titan X Pascal).**
Compute capability 6.1 is dropped by current default wheels; cu126 is mandatory:
```powershell
& <ROOT>\lightrag\.venv-rag\Scripts\pip.exe install torch==2.7.1 torchvision==0.22.1 `
    --index-url https://download.pytorch.org/whl/cu126 --force-reinstall --no-deps
[Environment]::SetEnvironmentVariable('MINERU_DEVICE_MODE','cuda','User')
```

**4b — NVIDIA Turing or newer (RTX 20xx/30xx/40xx/50xx, A-series, T4).**
Default CUDA wheels are fine:
```powershell
& <ROOT>\lightrag\.venv-rag\Scripts\pip.exe install torch torchvision --index-url https://download.pytorch.org/whl/cu126
[Environment]::SetEnvironmentVariable('MINERU_DEVICE_MODE','cuda','User')
```

**4c — no NVIDIA GPU (AMD, Intel, Apple, VM).**
CPU torch; parsing runs maybe 8× slower but works:
```powershell
& <ROOT>\lightrag\.venv-rag\Scripts\pip.exe install torch torchvision
[Environment]::SetEnvironmentVariable('MINERU_DEVICE_MODE','cpu','User')
```

Find the GPU generation with `nvidia-smi --query-gpu=name,memory.total,compute_cap --format=csv`. Compute cap `6.x` → branch 4a, `7.5+` → 4b.

**Verify:**
```powershell
& <ROOT>\lightrag\.venv-rag\Scripts\python.exe -c "import torch;print(torch.__version__, torch.cuda.is_available())"
```
On 4a/4b this must print `True`. `False` on a machine with an NVIDIA GPU means the wrong wheel — reinstall with the other branch. On 4c `False` is expected.

Also confirm the MinerU CLI is reachable, because RAG-Anything shells out to it:
```powershell
$env:Path = "<ROOT>\lightrag\.venv-rag\Scripts;$env:Path"
mineru --version
```

---

## Step 5 — configuration (`.env`)

Create `<ROOT>\lightrag\.env`:

```env
LLM_BINDING=openai
LLM_BINDING_HOST=https://api.z.ai/api/coding/paas/v4
LLM_BINDING_API_KEY=<ZAI KEY FROM STEP 0>
LLM_MODEL=glm-5.3
VLM_PROCESS_ENABLE=true
VLM_LLM_BINDING=openai
VLM_LLM_BINDING_HOST=https://api.z.ai/api/coding/paas/v4
VLM_LLM_BINDING_API_KEY=<ZAI KEY FROM STEP 0>
VLM_LLM_MODEL=glm-4.5v
EMBEDDING_BINDING=ollama
EMBEDDING_BINDING_HOST=http://host.docker.internal:11434
EMBEDDING_MODEL=bge-m3
EMBEDDING_DIM=1024
EMBEDDING_TOKEN_LIMIT=8192
HOST=0.0.0.0
PORT=<PORT FROM STEP 0>
LIGHTRAG_API_KEY=<GENERATE, see below>
WEBUI_TITLE=IL RAG
SUMMARY_LANGUAGE=English
COMPOSE_PROJECT_NAME=<unique name, e.g. mech_rag>
```

Generate the UI/API key:
```powershell
-join ((1..16) | ForEach-Object { '{0:x2}' -f (Get-Random -Max 256) })
```

Also set the key the ingest script reads:
```powershell
[Environment]::SetEnvironmentVariable('ZAI_API_KEY','<ZAI KEY>','User')
```

Notes:
- Embeddings **cannot** come from Z.ai — the Coding Plan exposes no embedding endpoint. That is why Ollama exists in this stack.
- `COMPOSE_PROJECT_NAME` is required if this machine will ever run **more than one** instance: every clone's folder is named `lightrag`, so without it `docker compose up` silently recreates the *other* instance's container.
- `docker-compose.yml` already maps `${PORT:-9621}:9621`, so changing `PORT` in `.env` is enough — do not edit the compose file.
- `SUMMARY_LANGUAGE` controls summarization only; German documents answer in German regardless.

---

## Step 6 — start the server

```powershell
Set-Location <ROOT>\lightrag
docker compose up -d
```

**Verify:**
```powershell
(Invoke-RestMethod http://localhost:<PORT>/health -Headers @{'X-API-Key'='<LIGHTRAG_API_KEY>'}).status
```
Must print `healthy`. The same response echoes the bindings — confirm `llm_model=glm-5.3`, `embedding_binding=ollama`, `embedding_model=bge-m3`.

Open the UI at `http://localhost:<PORT>` and paste `LIGHTRAG_API_KEY` when prompted (`auth_mode` is `disabled` — the API key is the only credential).

---

## Step 7 — ingest scripts

Copy two files from the source install (`X:\RAG_MAIN\MECH_RAG\lightrag\`) into `<ROOT>\lightrag\`:

- **`rag_ingest.py`** — do not rewrite it from scratch. It carries two mandatory monkeypatches for the `raganything 1.3.1` + `lightrag-hku 1.5.4` combination, both fixing `KeyError: 'role_llm_funcs'`:
  1. redirects `raganything.modalprocessors.asdict` to LightRAG's `_build_global_config()`;
  2. wraps `LightRAG._rebuild_role_llm_funcs` so the `role_llm_funcs` property is mirrored into the instance `__dict__` (the batch multimodal path looks it up dict-style).

  Without #1 every modal item fails; without #2 the batch merge silently falls back to sequential processing — a ~2 h run instead of ~10 min. Remove them only when raganything > 1.3.1.

  It also reads `RAG_MINERU_BACKEND` (default `pipeline`) — see step 8.

- **`ingest_detached.ps1`** — runs the ingest in a detached process so it survives the Claude Code session ending, logging to `ingest_run.log` and appending `EXITCODE=<n>` at the end. Fix the two absolute paths at the top (`$venv`, `$log`) for the new machine.

If the venv is local (it is here — step 4 built it inside `<ROOT>`), point `$venv` at `<ROOT>\lightrag\.venv-rag`.

**Verify:**
```powershell
& <ROOT>\lightrag\.venv-rag\Scripts\python.exe -c "import ast;ast.parse(open(r'<ROOT>\lightrag\rag_ingest.py',encoding='utf-8').read());print('syntax OK')"
Select-String -Path <ROOT>\lightrag\rag_ingest.py -Pattern '_rebuild_and_mirror|_full_config_asdict'   # both patches present
```

---

## Step 8 — choose the MinerU parsing backend (HARDWARE BRANCH)

MinerU 3.4.2 defaults to `hybrid-engine`, a local VLM parser. It is accurate on figures but memory-hungry: on a 32 GB / 5 GB-VRAM box a 34-page PDF ballooned past 11 GB RSS and died after 35 minutes with

```
MineruExecutionError: numpy._core._exceptions._ArrayMemoryError:
Unable to allocate 1.76 MiB for an array with shape (160, 960, 3) and data type float32
```

The `pipeline` backend (classic layout + OCR + formula models) parsed the same file in ~5 minutes at ~2.5 GB RSS.

Decision rule:

| Target machine | `RAG_MINERU_BACKEND` |
|---|---|
| < 64 GB RAM, or < 12 GB VRAM, or docs > 25 pages | `pipeline` (default, safe) |
| ≥ 64 GB RAM **and** ≥ 12 GB VRAM, small docs, figure fidelity matters | `hybrid-engine` |

Check the ceiling before deciding — note that if the commit limit equals physical RAM (no pagefile headroom) there is nowhere to spill:
```powershell
$os = Get-CimInstance Win32_OperatingSystem
"RAM GB: " + [math]::Round($os.TotalVisibleMemorySize/1MB,1)
"Commit limit GB: " + [math]::Round($os.TotalVirtualMemorySize/1MB,1)
nvidia-smi --query-gpu=memory.total --format=csv,noheader
```

Override per run with `$env:RAG_MINERU_BACKEND='hybrid-engine'`; leave unset for `pipeline`.

---

## Step 9 — smoke test (text path)

```powershell
$k = @{'X-API-Key'='<LIGHTRAG_API_KEY>';'Content-Type'='application/json'}
$body = @{ text = "Smoke test. The calibration torque for the gearbox assembly is 42 newton-meters."; file_source = "smoke.txt" } | ConvertTo-Json
$r = Invoke-RestMethod -Uri http://localhost:<PORT>/documents/text -Method Post -Headers $k -Body $body
$r.track_id
```

Poll until `processed` (about 20 s on a warm stack):
```powershell
Invoke-RestMethod "http://localhost:<PORT>/documents/track_status/$($r.track_id)" -Headers $k | ForEach-Object { $_.documents[0].status }
```
The path is `/documents/track_status/<id>`. `/track_status/<id>` 404s.

Query it:
```powershell
$q = @{ query = "What is the calibration torque?"; mode = "hybrid" } | ConvertTo-Json
(Invoke-RestMethod -Uri http://localhost:<PORT>/query -Method Post -Headers $k -Body $q).response
```
The answer must contain 42 N·m **and** cite `smoke.txt`. Then clear it:
```powershell
Invoke-RestMethod -Uri http://localhost:<PORT>/documents -Method Delete -Headers $k
```
Use this API, not `Remove-Item` on `data\rag_storage` — host file deletion there is blocked by policy on managed machines.

---

## Step 10 — smoke test (PDF path)

Put one real PDF in `<ROOT>\IN\`, then:

```powershell
Set-Location <ROOT>\lightrag

# Ollama up? MANDATORY — a down Ollama produces silent embedding failures and dirty storage
(Invoke-RestMethod http://localhost:11434/api/version).version

# Container MUST be stopped: host script and container write the same JSON storage
docker compose stop

# UTF-8 path list — do NOT pass non-ASCII filenames as process arguments,
# the ANSI codepage mangles them (Stäben -> St├дben -> FileNotFoundError)
(Get-ChildItem <ROOT>\IN -File -Filter *.pdf).FullName |
    Set-Content -LiteralPath .\ingest_list.txt -Encoding UTF8

Remove-Item .\ingest_run.log -ErrorAction SilentlyContinue
Start-Process powershell -ArgumentList '-NoProfile','-ExecutionPolicy','Bypass','-File',
    '<ROOT>\lightrag\ingest_detached.ps1','-ListFile','<ROOT>\lightrag\ingest_list.txt' -WindowStyle Hidden
```

Wait for `EXITCODE=` to appear in `ingest_run.log`:
```powershell
while (-not (Select-String -Path .\ingest_run.log -Pattern '^EXITCODE=' -Quiet)) { Start-Sleep -Seconds 30 }
(Select-String -Path .\ingest_run.log -Pattern '^EXITCODE=').Line     # want EXITCODE=0
```

**First run downloads MinerU models (a few GB) — one-time, cached in `~\.cache`.**

While waiting, do not read the log tail alone to judge progress: MinerU's tqdm bars are block-buffered through the redirected pipe, so the log can sit unchanged for 20 minutes while work continues. Judge liveness by CPU delta and GPU use instead:
```powershell
$p = Get-Process python | Sort-Object WorkingSet64 -Descending | Select-Object -First 1
$c = $p.CPU; Start-Sleep 30; $p.Refresh(); "CPU delta: $([math]::Round($p.CPU-$c,1))s / 30s"
nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv,noheader
```
CPU delta near zero *and* an idle GPU is a real hang; anything else is normal.

Then restart the server and verify:
```powershell
docker compose start
Invoke-RestMethod http://localhost:<PORT>/documents -Headers $k |
    ForEach-Object { $_.statuses.processed } |
    ForEach-Object { "$($_.file_path) chunks=$($_.chunks_count)" }
```
Finally run a content question through `/query` in `hybrid` mode and confirm the answer cites the PDF.

---

## Hard rules (violating these corrupts storage or wastes hours)

1. **Ollama must be up before every ingest.** Down Ollama = silent embedding failures + dirty storage + burnt GLM tokens.
2. **Stop the container during `rag_ingest.py`.** Shared JSON storage, no locking.
3. **Never change `EMBEDDING_MODEL` or `EMBEDDING_DIM` after the first ingestion.** Existing vectors become incompatible; the only fix is a full re-ingest.
4. **Keep both monkeypatches in `rag_ingest.py`** while `raganything==1.3.1` and `lightrag-hku==1.5.4`.
5. **Prepend `.venv-rag\Scripts` to PATH before ingesting** — RAG-Anything probes the parser via a `mineru --version` subprocess.
6. **Long ingests must run detached**, not as session-bound background jobs — they die with the Claude Code session.
7. **Set `COMPOSE_PROJECT_NAME`** if more than one instance will live on the machine.
8. **Wipe storage via `DELETE /documents`**, not by deleting `data\rag_storage` from the host.
9. **Prefer keeping storage over wiping it.** A wipe also drops the parse cache and LLM cache, so a re-run costs GLM tokens again; entity merge is an upsert, so re-ingesting is safe.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| `OSError: Missing dependencies for SOCKS support` | SOCKS system proxy | `$env:NO_PROXY='*'` before the command, or `pip install pysocks` once |
| `failed to connect to the docker API at npipe:` | Docker Desktop not running | start it, wait 1–2 min |
| `MineruExecutionError ... ArrayMemoryError` | `hybrid-engine` out of RAM | `$env:RAG_MINERU_BACKEND='pipeline'` (step 8) |
| `FileNotFoundError` with garbled filename | non-ASCII path passed as process arg | use `-ListFile` with a UTF-8 list (step 10) |
| `Parser 'mineru' is not properly installed` | venv `Scripts` not on PATH | prepend it (step 4 verify) |
| `KeyError: 'role_llm_funcs'` | monkeypatches missing | restore `rag_ingest.py` from the source install |
| Ingest hangs after all chunks generated | patch #2 missing, sequential fallback | same as above |
| Z.ai HTTP 429 code 1305 | rate limit under 4-way concurrency | normal, the openai client retries |
| `torch.cuda.is_available()` is False on an NVIDIA box | wrong wheel for the GPU generation | redo step 4a/4b |
| Log frozen for 20+ min mid-parse | tqdm block buffering | check CPU delta + GPU, not the log |
| Doc status ledger fills with `failed` entries | killed runs leave stubs | harmless; clear via the document API if it grows |

---

## Optional — porting the existing knowledge graph instead of re-ingesting

Re-ingestion costs GLM tokens and hours. To move an already-built graph, copy `<SOURCE>\lightrag\data\rag_storage\` to `<ROOT>\lightrag\data\rag_storage\` with both containers stopped. This is only valid if the target `.env` keeps the **same** `EMBEDDING_MODEL` and `EMBEDDING_DIM` — otherwise the vectors are unusable. Start the container afterwards and confirm the document list and a query.

---

## Reference: the source install

- Instances on the source machine: `X:\RAG_MAIN\RAG` (port 9621), `X:\RAG_MAIN\PCM_RAG` (9622), `X:\RAG_MAIN\MECH_RAG` (9623).
- Source hardware: Windows 11 Pro, Quadro P2000 5 GB (Pascal, driver 582.16), 32 GB RAM, Python 3.13.13.
- Related docs: `X:\RAG_MAIN\RAG\INSTALL.md` (original as-built), `X:\RAG_MAIN\RAG\REPLICATE.md` (same-machine replication).
