# Qdrant Migration: Brainstorm / Discovery Notes
Date: 2026-09-09 · Goal: plan the move of LightRAG vector storage from nano-vectordb JSON files to Qdrant, across MECH_RAG and PCM_RAG, on a box with an unfixed RAM byte-lane fault and a no-AVX2 i7-2600K.

## Summary / key decisions
1. **Goal:** all four - cut crash blast radius, free host RAM at ingest, free server RAM / faster queries, room to grow. Full backend cut-over, measured on all four axes.
2. **Scope:** vectors only. Graph and KV stay on NetworkX/JSON; graph storage revisited later on evidence. Accepted: the graphml, the file that actually broke twice, is untouched by this work.
3. **Pilot:** PCM_RAG (verified healthy: 70/70 processed, graphml 0 NULs). MECH_RAG is a separate go, blocked on confirmation that its repair actually ran - as of now it has NOT.
4. **Data move:** copy the stored vectors verbatim (no re-embedding), then re-embed a sample and compare.
5. **Topology:** one Qdrant per base. Service definition shared via the ragkit template; process, port, volume and backup per base.
6. **Storage:** Docker named volume on ext4 in the WSL VHDX, not a bind mount onto X:. Backup via Qdrant's snapshot API.
7. **Old JSONs:** deleted once verification passes. Therefore a verified `rag_sync.ps1 push` beforehand is mandatory - it becomes the only rollback.
8. **Acceptance:** numeric recall@k >= 0.98 vs exact brute force, gating a behavioural before/after comparison on ~10 fixed German questions.
9. **Toolchain in scope:** `check_vectors.py`, `ingest.ps1` + `rag_ingest.py`, `rag_sync.ps1`. Skills deferred.
10. **Machine:** WSL ceiling now 14 GB / 4 GB swap / gradual reclaim, verified. RAM byte-lane fault unfixed and the box is back on the 4-DIMM config that fails; risk explicitly accepted by the user.

## Execution plan (PCM_RAG)
**Step 0 - feasibility gate (blocking).** This CPU is an i7-2600K with `avx sse4_2`, **no AVX2**; that is what killed the faiss option. Start `qdrant/qdrant:v1.19.1`, create a 1024-dim collection, upsert a few hundred points, run a search. Abort the whole plan if it SIGILLs or the search misbehaves. Nothing else starts until this passes.

**Step 1 - baseline + backup.** Record before-numbers (per-doc write volume, host peak RSS, server RSS, query latency). Run the ~10 German questions on nano and save the answers. `rag_sync.ps1 push` and verify the tgz (`tar -tzvf` exit 0, expected member count).

**Step 2 - stand up Qdrant.** Add the pinned `qdrant` service + named volume to PCM's compose, published on 6333. `QDRANT_URL=http://localhost:6333` in `.env` for the host; compose `environment:` overrides the lightrag service to `http://qdrant:6333`. Confirm LightRAG loads `.env` with `override=False` so the real env wins.

**Step 3 - migration script** (`X:\RAG_MAIN\RAG\migrate_nano_to_qdrant.py`, + its test). Streams each `vdb_*.json`, decodes the base64 matrix, upserts `PointStruct(id=compute_mdhash_id_for_qdrant(doc_id, prefix=workspace), vector=row, payload={id, workspace_id, created_at, **meta_fields})` into `lightrag_vdb_{ns}_bge_m3_1024d`. Idempotent, resumable, batched under the 16 MB payload cap. Must stream, not load 1.1 GB at once - that would undo goal 2.

**Step 4 - verify.** Point counts per collection == JSON record counts. Payload spot-check. Re-embed N sampled contents through Ollama and compare cosine. recall@k >= 0.98 vs exact numpy. Then the German query set on Qdrant, compared to the Step 1 answers.

**Step 5 - wire the toolchain.** `rag_ingest.py`: `lightrag_kwargs={"vector_storage": "QdrantVectorDBStorage"}` + `model_name="bge-m3"` on the EmbeddingFunc. `ingest.ps1`: stop only the lightrag service, leave qdrant up. `check_vectors.py`: Qdrant-aware. `rag_sync.ps1`: snapshot export/import + stop both containers.

**Step 6 - prove it end to end.** One real single-document ingest on PCM. Confirm `Flush start:`/`Flush done:` lines appear and the per-document write volume actually dropped. Only then delete the `vdb_*.json` files.

**Step 7 - report.** Before/after numbers on all four goal axes. MECH_RAG stays untouched.


## Established facts (verified this session, not asked)
- Host RAM back to 32 GB: 4x Kingston HX321C11SR/8 @1867, ChannelA/B DIMM0+DIMM1. This is the 4-DIMM config that previously failed. User accepts the risk.
- WSL/Docker ceiling raised and verified: `%USERPROFILE%\.wslconfig` = `memory=14GB`, `swap=4GB`, `autoMemoryReclaim=gradual`. Container reads `MemTotal 14313048 kB`, `SwapTotal 4194304 kB`, `nproc 8`. Was 15.6 GB (default 50%) before the file existed.
- Both containers stopped: `pcm_rag-lightrag-1`, `mech_rag-lightrag-1`. No python running.
- Store sizes now: MECH `vdb_relationships.json` 1195 MB, `vdb_entities.json` 296 MB, `vdb_chunks.json` 44.6 MB, graphml 98 MB (truncated/corrupt). PCM `vdb_relationships.json` 812 MB, `vdb_entities.json` 261 MB, `vdb_chunks.json` 31 MB, graphml 73.9 MB.
- `qdrant/qdrant:latest` = **1.19.1**; image pulled; `./qdrant --version` runs on this CPU (does NOT yet prove SIMD paths are safe - full upsert/search smoke test was NOT run).
- `qdrant_impl.py` collection name = `lightrag_vdb_{namespace}_{model_suffix}`, suffix from `EmbeddingFunc.model_name` + dim, e.g. `bge_m3_1024d`. Empty model_name -> fallback `lightrag_vdb_{namespace}` + warning.
- Point id = `compute_mdhash_id_for_qdrant(doc_id, prefix=effective_workspace)` (sha256 -> UUIDv4 hex). Payload = `{id, workspace_id, created_at, **meta_fields}`.
- `index_done_callback` -> `_flush_pending_vector_ops`: flushes ONLY buffered rows. This is the write-volume win.
- **Trap found:** core `LightRAG` dataclass defaults `vector_storage="NanoVectorDBStorage"`; only the API server reads `LIGHTRAG_VECTOR_STORAGE`. Host-side `rag_ingest.py` uses RAGAnything, so it needs `lightrag_kwargs={"vector_storage": ...}` explicitly - env alone will NOT switch the host ingest.
- **Trap found:** `rag_ingest.py`'s `EmbeddingFunc` sets no `model_name`, so host ingest would target `lightrag_vdb_entities` while the container server targets `lightrag_vdb_entities_bge_m3_1024d`. Two different collections for the same data.
- `check_vectors.py:23` hardcodes the three `vdb_*.json` filenames.
- `rag_sync.ps1` tars only `data/rag_storage`, and stops only `<project>-lightrag-1`.
- No nano->Qdrant migration tool exists upstream; `lightrag/tools/prepare_qdrant_legacy_data.py` is Qdrant->Qdrant only.

## Q&A log
### Q1 - what the migration is buying (success criterion)
- Asked: which outcome, if missed, means it was not worth doing?
- Captured: **all four**, no ranking given.
  1. Cut crash blast radius (~1745 MB -> ~209 MB written per document).
  2. Free host RAM during ingest (vectors leave the host python process).
  3. Free server RAM / faster queries (no ~1.5 GB load at startup; HNSW instead of brute-force numpy over 139k vectors).
  4. Room to grow (MECH_RAG is far from fully ingested; nano's rewrite-everything model does not scale).
- Consequence: this is a full backend cut-over, not a narrow write-volume patch. Success must be measured on all four axes, so the verification plan needs a before/after number for each.
- Flags: none.

### Q2 - order of MECH repair vs migration
- Asked: PCM pilot first, MECH repair first, MECH end-to-end first, or migrate MECH's live vectors out before rolling back?
- Captured: user replied "i`m already do mech rag repair (look at \"base-check-and-repair\" dialog) So do what you deside in this case".
- **Verified against disk instead of trusting: the repair has NOT landed.** `lightrag\data
ag_storage\graph_chunk_entity_relation.graphml` is byte-identical in shape to the 09-08 audit - 98,025,582 bytes, 28,819,566 NULs, 34127 `<node>`, 86106 `<edge`, mtime still 2026-09-08 21:14. `rag_storage.bak` and `rag_storage.PRE_ROLLBACK_20260908_1803` both still present; no `rag_storage.CORRUPT_<ts>` directory exists, which `rollback_store_to_bak.ps1 -Apply` would have created. Conclusion: the other session ran the audit / a dry run, not the apply.
- Decision taken (user delegated it): **PCM_RAG is the pilot.** It is healthy, it is the base whose store nothing else is touching, and it isolates the migration work from whatever the other session does to MECH. MECH migration is scheduled only after its store is actually repaired and verified.
- Flags: MECH_RAG repair -> user / the "base-check-and-repair" session. Must confirm before MECH is migrated. Concurrent writes to MECH's store from two sessions must not happen.

## Open flags (pending input)
- **MECH_RAG repair has not actually run** (verified on disk: graphml still 98,025,582 bytes with 28,819,566 NULs, mtime 2026-09-08 21:14, no `rag_storage.CORRUPT_*` dir) -> user / the "base-check-and-repair" session. Must be settled before MECH is migrated, and no two sessions may write that store at once.
- MECH_RAG Qdrant migration -> blocked on the above plus an explicit go.
- `il-check-rag-base` / `il-rag-ingest` skill updates -> deferred backlog.
- Graph storage decision (Memgraph / Neo4j / Postgres+AGE) -> revisit after the first post-migration ingest produces real numbers.
- `vdb-json-rewrite-is-structural.md` memory still names faiss as the target -> rewrite toward Qdrant once this lands.

### Q3 - how existing vectors reach Qdrant
- Asked: copy the stored vectors, re-ingest from scratch, copy + spot-check, or start empty?
- Captured: **copy the vectors, then re-embed a sample and compare** ("Copy vectors, re-embed only on mismatch").
- Consequences:
  - I must write a nano -> Qdrant migration script; nothing upstream does this. It reads `data` + base64 `matrix` from each `vdb_*.json` and upserts `PointStruct(id=compute_mdhash_id_for_qdrant(doc_id, prefix=workspace), vector=row, payload={id, workspace_id, created_at, **meta_fields})` into `lightrag_vdb_{namespace}_bge_m3_1024d`.
  - No LLM calls, no full re-embed. Embeddings stay byte-identical, so before/after query answers are directly comparable - that doubles as the migration's correctness test.
  - Verification step is part of the script: sample N random rows per store, re-embed their `content` through Ollama bge-m3, compare cosine against the migrated vector, fail loudly on mismatch. Also catches a silently broken Ollama blob (see the norm-0 embedding incident).
  - Open sub-question: `meta_fields` differs per namespace, and nano stores extra keys. The copy must write exactly the keys qdrant_impl would write, or `get_by_id` payload reads break downstream.
- Flags: none.

### Q4 - topology: shared vs per-base Qdrant
- Asked: one Qdrant per base, one shared instance with workspace filtering, or one shared instance with per-base collections?
- User first asked for clarification: "is 3 the same variant like we have now? One main folder RAG from where other rag bases take all needed, but every rag base may have they peculiar properties?"
- Clarification given: no. ragkit shares **code**, not data - each base already owns its container, port, .env, storage dir and Drive snapshot. Option 1 preserves that model (service definition shared via the ragkit template, data and process per base); option 3 shares the physical storage dir and WAL across bases, so RAM-fault corruption during a write would hit every base at once.
- Captured: **Option 1 - one Qdrant per base.**
- Consequences:
  - Each base's `docker-compose.yml` gains a `qdrant` service; the template in `X:\RAG_MAIN\RAG	emplate` is the shared source of that definition.
  - Ports: PCM 6333, MECH 6334 (published to host, because host-side `rag_ingest.py` connects too).
  - `QDRANT_URL` must differ between host and container: `.env` carries the host value (`http://localhost:<port>`), the compose `environment:` block overrides the lightrag service with `http://qdrant:6333`. Requires confirming LightRAG loads .env with `override=False` so the real env wins.
  - **Ingest flow changes.** Qdrant is a server and must stay UP during ingest, but today `ingest.ps1` stops the whole compose project. It must become `docker compose stop lightrag` with `qdrant` left running.
- Flags: none.

### Q5 - where Qdrant's files live
- Asked: bind mount onto X: next to the base, Docker named volume + snapshot API, or named volume + sidecar tar?
- Captured: **named volume inside the WSL VHDX, backed up via Qdrant's snapshot API.**
- Rationale accepted: Qdrant needs a real local filesystem; a WSL2 bind mount of a Windows drive is drvfs/9p, the unsupported class. ext4 in the VHDX gives correct fsync/mmap/locking and is fast.
- Consequences:
  - Volume per base, e.g. `pcm_rag_qdrant`, `mech_rag_qdrant` (docker named volumes, so they survive container recreation but NOT a Docker Desktop "reset to factory defaults" - worth a warning in OPERATING.md).
  - `rag_sync.ps1` must gain a snapshot step: POST the Qdrant snapshot endpoint, pull the snapshot file into the base folder, then tar as today. Restore = untar + upload snapshot back. This replaces "tar a live directory" with a genuinely consistent artifact.
  - The base is no longer entirely on X:; the live vector data is inside the WSL VHDX. The Drive tgz stays the single restore artifact, so this is acceptable, but a bare X: copy of a base is no longer sufficient to move it.
- Flags: none.

### Q6 - scope: vectors only, or graph/KV too
- Asked, with the per-document write budget for MECH_RAG on the table: vdb 1536 MB + graphml 98 MB + 8 kv_store JSONs ~111 MB = ~1745 MB today, ~209 MB after a vectors-only move.
- Captured: **vectors only. The graph is a separate, later decision, made on evidence from a real post-migration ingest.**
- Explicitly noted and accepted: the graphml is 47% of the remaining 209 MB and is the file that the 09-08 BSOD actually truncated. Vectors were never the file that broke. So this migration reduces exposure by 88% of bytes but does NOT remove the specific failure that destroyed the store twice.
- Consequence: after the first successful Qdrant ingest, re-measure and revisit graph storage (Memgraph / Neo4j / Postgres+AGE) as its own piece of work.
- Flags: none.

### Q7 - fate of the old vdb_*.json files
- Asked: leave in place then prune, move out immediately, delete after verification, or keep forever?
- Captured: **delete after verification passes.** Reclaims ~1.1 GB (PCM) / ~1.5 GB (MECH) immediately and leaves no stale copy to confuse a later audit.
- **Mandatory precondition this creates:** deleting them removes the only local rollback, so a fresh `rag_sync.ps1 push` MUST run and be verified (`tar -tzvf` exit 0, expected member count) BEFORE the migration script deletes anything. That Drive tgz becomes the sole pre-migration restore point. Not optional on this box.
- Also noted: the rollback window is narrower than it looks. The instant the first ingest runs against Qdrant, the JSON files are stale, so reverting after that loses that ingest's vectors regardless of whether the files still exist.
- Flags: none.

### Q8 - acceptance bar for retrieval quality
- Context given: nano does exact brute-force cosine; Qdrant is approximate. `qdrant_impl.py` hardcodes `HnswConfigDiff(payload_m=16, m=0)` (global HNSW off, payload-partitioned index on) and passes no `search_params`, so search runs at Qdrant's default ef. Tuning either needs a patch, not an env var.
- Captured: **both, with the numeric gate first.**
  1. Numeric: for N sample query vectors, compute true top-k by exact numpy cosine over the migrated matrix, ask Qdrant for the same top-k, require **recall@k >= 0.98**. Cheap, machine-checkable, catches a badly built index before any LLM spend.
  2. Behavioural: a fixed set of ~10 German questions run against PCM_RAG on nano BEFORE the switch (answers saved), re-run identically on Qdrant after. Bar = substantively the same answers citing the same sources.
- The saved query set becomes the reusable regression suite for the MECH migration later.
- Flags: none.

### Q9 - which toolchain pieces are in scope
- Captured: **in scope** - `check_vectors.py`, `ingest.ps1` + `rag_ingest.py`, `rag_sync.ps1`. **Deferred** - the `il-check-rag-base` and `il-rag-ingest` skills.
- Consequence of the deferral: after the switch those two skills still reason about `vdb_*.json`, orphan-vector counts and the old store layout. Their audits become partly wrong (not dangerous - read-only), so any audit run between now and the skill update must be read with that in mind. Add a warning line to each skill rather than a rewrite, so the staleness is at least visible.
- Flags: skill updates -> deferred backlog item, own task.

### Q10 - how far this work goes with MECH_RAG
- Captured: **stop after PCM_RAG.** MECH is a separate go, gated on the user confirming its store is genuinely repaired and that the "base-check-and-repair" session is finished with it.
- Rationale: avoids two sessions writing the same store, and MECH then runs a procedure already proven once, with the regression query set already built.
- Flags: MECH migration -> blocked on user confirmation of repair + session ownership.

## Verified during planning (PCM_RAG is a sound pilot)
- `kv_store_doc_status.json`: **70 documents, all 70 `processed`.** No stuck doc.
- `graph_chunk_entity_relation.graphml`: 73,871,204 bytes, **0 NUL bytes**, 29986 `<node>`, 93852 `<edge`, closes with `</graphml>`.
- Ollama up on 11434 with `bge-m3:latest`, F16, embedding_length 1024, digest `7907646426...`. Needed for the re-embed spot check.

## Decisions taken without asking (routine, recorded for the record)
- Qdrant image pinned to `qdrant/qdrant:v1.19.1` (`latest` resolved to 1.19.1 today, digest `sha256:12364fe851b9f17356fc88189fc06d1b521262e04659ec7345975b00c9246a10`). No floating `:latest` in a compose file.
- Migration code lives in ragkit (`X:\RAG_MAIN\RAG\`), not in a base, matching the "shared tooling, per-base data" model.
- The migration is **idempotent and resumable**: point ids are a deterministic hash of the doc id, so re-running after a crash re-upserts the same points rather than duplicating. This matters because the box can BSOD mid-migration.
- Ports: PCM 6333, MECH 6334. Volumes: `pcm_rag_qdrant`, `mech_rag_qdrant`.
- One runnable check ships with the migration script (`test_migrate_nano_to_qdrant.py`), per the standing rule that non-trivial logic leaves a check behind.

### Q11 - completeness backstop
- Asked: anything untouched before code gets written?
- Captured: three gaps named - **crash-during-migration handling**, **monitoring during the run**, **git / branch discipline**. Each grilled separately below.

### Q12 - crash-during-migration hardening
- Captured: **resumable + smallest-store-first + count gate.** No checkpoint file, no staging collection, no wipe-and-restart policy.
- Concretely: migrate ascending by size - PCM chunks 31 MB, entities 261 MB, relationships 812 MB - and assert `collection point count == JSON record count` after each store before starting the next. Deterministic point ids mean a re-run overwrites rather than duplicates, so recovery from a BSOD is "run the same command again, it converges".
- Rejected and why: a checkpoint file is itself a corruptible write and a wrong offset silently skips real data; alias staging is the strongest guarantee but adds a concept and needs proof that `qdrant_impl`'s direct collection-name reads resolve aliases.
- Flags: none.

### Q13 - telemetry during the work
- Captured: **arm the rig for both Step 3 (migration write) and Step 6 (proving ingest).**
- Mechanics recorded so it is not re-derived: `X:\RAG_MAIN\MECH_RAG\HW_TEST\monitor.ps1` (start / `-Stop`), output to `C:\Dumps\ingest\<stamp>\`, sampler must run under `powershell` 5.1 not pwsh 7.
- Two preconditions: **delete the stale `C:/Dumps/ingest/monitor.pids`** (the machine has rebooted since it was written; `-Stop` against stale PIDs has already killed unrelated processes once), and **record the new 4x8 GB / 1867 config in context.txt** - every prior capture was on 16 GB, so old and new runs are otherwise not comparable.
- The rig also supplies the host-RSS before/after numbers that goal 2 is measured on.
- Flags: none.

### Q14 - git discipline
- Facts checked, not asked: ragkit is on `master`, clean, HEAD `6fe0afb`. PCM_RAG is on `main` with 27 unrelated modified/deleted files. PCM's `lightrag/.env` is **gitignored** (line 15) so no secret is at risk; `lightrag/docker-compose.yml` **is tracked**. ragkit holds the shared source at `template/docker-compose.yml` + `template/env.template`.
- Captured: **feature branch `feat/qdrant-vector-backend` in ragkit**, merged to master only after PCM verifies end to end - same shape as the flush-safety work (`a14bcdc`, `6fe0afb`). **PCM gets one focused commit on `main`** touching only `lightrag/docker-compose.yml`; its 27 unrelated changes stay untouched and uncommitted.
- Flags: none.

## Reconciliation (final pass over the whole file)
- **Q7 vs Step 6 - when the JSONs actually get deleted.** Q7 says "after verification passes"; the plan has verification split across Step 4 (counts, recall, query set) and Step 6 (a real ingest on the new wiring). Deleting after Step 4 would leave no rollback if the *ingest* wiring turns out wrong, which is the failure Step 6 exists to catch. **Resolved: "verification passes" means Steps 4 AND 6 both green.** The files are deleted at the end of Step 6, not before.
- **Q1 goal 2 vs Step 3 implementation.** Goal 2 is "free host RAM during ingest"; a migration script that loads a 812 MB JSON with `json.load` would peak at multiple GB and contradict its own purpose. Step 3 must stream. Called out explicitly in the plan.
- No other contradictions found.

## Additions to the execution plan from Q12-Q14
- **Step 0** is unchanged and still blocking: no-AVX2 feasibility gate on `qdrant/qdrant:v1.19.1`.
- **Step 3** gains: ascending store order (chunks -> entities -> relationships) with a point-count assert between stores; telemetry rig armed around it; stale `C:/Dumps/ingest/monitor.pids` deleted first; new 4x8 GB config noted in `context.txt`.
- **Step 6** gains: telemetry rig armed; JSON deletion happens here, after the ingest verifies, not after Step 4.
- **Git:** ragkit work on `feat/qdrant-vector-backend`, merged after Step 6; PCM gets one commit for `lightrag/docker-compose.yml`.

## STEP 0 RESULT - feasibility gate PASSED (2026-09-09 ~18:15)
Ran `qdrant/qdrant:v1.19.1` on this i7-2600K (`avx sse4_2`, no AVX2), with the exact
config `qdrant_impl.py` uses - 1024-dim cosine, `HnswConfigDiff(m=0, payload_m=16)`,
`workspace_id` keyword index, all searches filtered on it.

```
healthz: healthz check passed | version: 1.19.1
collection created (m=0, payload_m=16), workspace_id indexed
upserted 2000 x 1024 in 3.6s
points_count: 2000 status: green
recall@10 over 50 queries: 1.0000  (175.6 ms/query)
PASS: qdrant runs correctly on this CPU
EXITCODE=0
```
No SIGILL, no panic, no ERROR in the container log; container stayed Up. **Qdrant does runtime
SIMD dispatch - it does not need AVX2, unlike the faiss build that died with exit 132.**

Caveats recorded so they are not over-read later:
- recall 1.0000 at 2000 points says nothing about 139k points. With `m=0` a small segment is
  likely scanned exactly anyway. The real recall gate is Step 4, on real data at real scale.
- 175.6 ms/query at this size is HTTP + JSON serialization of a 1024-float query vector, not
  index time. Goal 3 (faster queries) has **no evidence yet** and needs a real before/after.
- The gate container ran on the container filesystem (Qdrant logged the expected
  "storage might be lost with container re-creation" warning). Torn down after the run.
- One bug in the gate script, not in Qdrant: `/healthz` answers plain text, and the first
  version json-parsed it and looped until timeout. Fixed; noted because the same trap will
  bite any health check written against Qdrant.

## EXECUTION LOG (PCM_RAG)

### Step 1 - baseline + backup: DONE
- **Backup**: Google Drive was not mounted (no J:, no drivefs process, `MECH_RAG_DRIVE` unset). User chose **local only**. Archive at
  `E:\BackUp_NEW\RAG\PCM_RAG
ag_storage_pre_qdrant_20260909.tgz`, 767 MB, taken with the container stopped.
  Verified: `tar -tzvf` exit 0, 16 members, **all 15 files present at exact source size**, full decompress exit 0.
  This is the ONLY pre-migration rollback - there is no off-machine copy.
- **Baseline server RSS**: `pcm_rag-lightrag-1` steady at **1.829-1.839 GiB / 13.65 GiB**.
- **Baseline query set**: 10 questions spanning both clusters of the base (thermal storage / PV / buildings, and
  chalcogenide phase-change memory). Runner: `QA\pcm-verify
un_queryset.py`, results in `queryset_nano.json`.
  10/10 succeeded. **context median 13,806 ms** (total 293 s), **answer median 34,455 ms** (total 321 s).
  Q8 was a 164 s outlier, assumed z.ai latency.
  Two API facts worth keeping: `auth_mode: disabled` still enforces `LIGHTRAG_API_KEY` via `X-API-Key` (a call without it
  is a bare 403), and `only_need_context: true` returns retrieval WITHOUT the answer LLM - retrieval is not LLM-cached,
  so that field is the honest before/after diff. The `answer` field IS cached and needs the mode-prefixed cache keys
  dropped before the after-run, or it will replay the nano answer and fake a pass.

### Store format finding (drives the migration script)
Each `vdb_*.json` record carries BOTH a global float32 `matrix` and a per-record `vector`.
The per-record `vector` is zlib-compressed **float16**, cosine 1.0000 against its own matrix row (max abs diff ~7e-5).
`matrix` is authoritative: unit-norm, 0 non-finite. The float16 copy is used as a free per-row **alignment proof** -
if the matrix were ever offset against the records, every payload would attach to the wrong embedding, and the
migration asserts worst-cosine >= 0.999 over a 200-row sample to catch exactly that.

### Step 0/2/3 artefacts written (ragkit, branch `feat/qdrant-vector-backend`)
- `migrate_nano_to_qdrant.py` - dry-run by default, `--apply` to write. Smallest store first, count gate between stores,
  deterministic point ids so a crashed run is fixed by re-running it.
- `test_migrate_nano_to_qdrant.py` - 6 checks, all passing. The id scheme is asserted against lightrag's OWN
  `compute_mdhash_id_for_qdrant`, and META_FIELDS against the literal `meta_fields=` lines in `lightrag/lightrag.py`,
  so upstream drift fails loudly instead of migrating into unreadable ids.
- `verify_qdrant_recall.py` - recall@k vs exact numpy cosine over the nano matrix. Must run BEFORE the JSONs are deleted.
- `ingest.ps1` - `docker compose stop|start lightrag` instead of the whole project (Qdrant is a server the host ingest
  needs UP), and the "still running" guard scoped to the lightrag service.
- `rag_ingest.py` - `model_name` on the EmbeddingFunc and `lightrag_kwargs={"vector_storage": ...}` from `.env`.
  Both traps found in planning; without either, host ingest and server use different collections with no error.
- `check_vectors.py` - Qdrant branch (collection exists, green, non-empty, sampled vectors finite/non-zero, chunks
  count cross-checked against `kv_store_text_chunks.json`). Nano path re-verified unchanged: exit 0 on PCM.
- `template/docker-compose.yml` + `template/env.template` + `new_base.ps1` - new bases get the qdrant service with a
  per-base `QDRANT_PORT` derived from `PORT`; the `-From` path re-derives it too, since copying a sibling's port
  would put two bases on one host port.
- `PCM_RAG/rag_sync.ps1` - snapshot export on push, restore on pull, tar carries `qdrant_snapshots/`. Parses clean.
  MECH_RAG's own copy still needs the same change when MECH migrates.

### Step 3 - migration run (in progress at time of writing)
Telemetry armed: `C:\Dumps\ingest60909-184057\`, all six files writing, RAM-config note appended to context.txt.
No stale `monitor.pids` existed, so that trap did not apply.
Dry run first: clean, 126,750 records, row-alignment 1.000000 on all three stores.
Apply: chunks 2,912 green; entities and relationships following. Measured **58-59 points/s**, host python steady at
**426 MB RSS**, qdrant container **138 MB and 0.19% CPU** - the bottleneck is client-side JSON serialization of
1024 floats per point, not the server. ETA ~30 min from the entities midpoint.

### Step 3 - migration COMPLETE (exit 0)
| store | records | in qdrant | time |
|---|---|---|---|
| chunks | 2,912 | 2,912 | 52.8 s |
| entities | 29,986 | 29,986 | 518.7 s |
| relationships | 93,852 | 93,852 | 1620.2 s |
| **total** | **126,750** | **126,750** | ~36 min |
All three count gates passed. Steady 58 pts/s throughout; host python peaked ~852 MB RSS.

### Step 4a - numeric gate PASSED (the real one, at real scale)
`verify_qdrant_recall.py --queries 100 --topk 10`, ground truth = exact numpy cosine over the nano matrix:
- chunks **1.0000**, entities **0.9980**, relationships **0.9970**, 0 empty results. Threshold 0.98. Exit 0.
This supersedes the Step 0 gate's meaningless 1.0000 at 2,000 points.

### Step 4b - backend flipped
Order used: stop lightrag (qdrant stays up) -> purge cached answers -> flip `.env` -> `docker compose up -d lightrag`.
Server confirms `vector_storage: QdrantVectorDBStorage`.
`check_vectors.py` in its new Qdrant mode: all three collections green, 512-point samples, 0 non-finite, 0 zero. Exit 0.
`check_ingest_wiring.py` (new): host path resolves to the same three `lightrag_vdb_*_bge_m3_1024d` collections that
exist on the server, no strays. Exit 0. This is what proves the two planning traps are actually closed.

**Memory numbers (goal 3), reported honestly:**
| | before (nano) | after (qdrant) |
|---|---|---|
| lightrag container | 1.839 GiB | 1.015-1.056 GiB |
| qdrant container | - | 567-580 MiB |
| **combined** | **1.839 GiB** | **~1.60 GiB** |
The LightRAG process dropped ~45%, but Qdrant is a new resident cost, so the net saving is ~13%, not 45%.

### METHOD ERROR found and corrected - the first behavioural comparison was invalid
First qdrant run gave retrieval-kept 69.6%, jaccard 0.594, 2/10 identical reference sets - which flatly contradicts
recall@10 of 0.997-1.000 measured on the same data minutes earlier. Cause: **my cache purge was too broad.**
The non-`default:` keys are not all answers - they split into `<mode>:keywords` (12) and `<mode>:query` (12).
`keywords` is the high/low-level keyword list the LLM extracts FROM THE QUESTION, and it is what the retrieval
query is actually built from. Dropping it made the second run re-extract keywords with a non-deterministic LLM, so
the two runs searched with **different terms** - the diff measured keyword drift, not the vector store.
Fix: `purge_query_cache.py` now keeps `default:*` AND `<mode>:keywords`, dropping only `<mode>:query`
(`--drop-keywords` restores the old behaviour). Cache restored from `.bak`, re-purged, query set re-run.
The invalid run is kept as `queryset_qdrant_nokeywordcache.json` rather than deleted.
**This also refines the `lightrag-query-cache-holds-poisoned-answers` memory, which says to drop all mode-prefixed
keys - correct for clearing poison, wrong for any before/after comparison.**

### Step 6 - BLOCKED, no document to ingest
All 37 PDFs in PCM's `IN\` are accounted for in `INGESTED_SOURCES.txt`. The six that a naive name diff flags as
missing are slice families whose source PDF deliberately stays in `IN\` (the ledger lines carry trailing comments,
which is why the first diff missed them). So there is no safe un-ingested document for the proving ingest.
**Consequence: the `vdb_*.json` files are NOT deleted.** Step 6 gates that deletion and Step 6 cannot run.
Options for the user: name a document, or stand up a throwaway base (which would also exercise the new
`new_base.ps1` QDRANT_PORT logic) to prove the ingest path end to end.

### Step 4b - behavioural gate PASSED (after the cache fix)
`compare_querysets.py queryset_nano.json queryset_qdrant.json`:
- **retrieval kept 100.0%, jaccard 1.000 on all 10 questions** - the entity sets are identical.
- identical reference sets 6/10. The other 4 differ in which retrieved sources the LLM chose to cite in a
  regenerated answer; since retrieval is provably identical, that is LLM non-determinism, not the index.
- The ms columns in that table are NOT comparable: nano ran with a cold keyword cache, qdrant with a warm one.

### The 2-second finding (biggest single discovery of the session)
The first search benchmark said Qdrant took 2057 ms/query - and, tellingly, **the same 2057 ms regardless of
collection size**. That is a fixed per-request cost, not search. Cause: `http://localhost:6333` resolves to `::1`
first, docker publishes on `127.0.0.1` only, and the failed IPv6 attempt burns ~2 s.

```
urllib        localhost:6333    median 2237.1 ms
urllib        127.0.0.1:6333    median  178.9 ms
qdrant-client localhost:6333    median 2055.1 ms
qdrant-client 127.0.0.1:6333    median    8.2 ms
```

**It had already cost this session real time:** the migration's steady "58 points/s" was 128 points per request
divided by 2 s. It read as client-side serialization overhead and was reported as such. Every host-side URL is now
`127.0.0.1` (scripts, `.env`, template, rag_sync). Containers are unaffected - they use docker DNS.
Saved as memory [[qdrant-localhost-costs-2s-per-request]].

### Search benchmark, honest version (after the URL fix)
| store | rows | numpy (what nano did) | qdrant | verdict |
|---|---|---|---|---|
| chunks | 2,912 | 0.6 ms | 7.7 ms | slower |
| entities | 29,986 | 5.8 ms | 7.4 ms | par |
| relationships | 93,852 | 17.4 ms | 8.5 ms | **2.04x faster** |

Qdrant is ~7-8 ms flat (HTTP floor); the numpy scan is linear in rows. Crossover ~40k rows.
**Goal 3 is therefore only half met today** - faster on the store that matters, slower on the small ones - but the
gap widens as the base grows, which is goal 4.

## Scorecard against the four goals from Q1
1. **Crash blast radius** - per-document vector writes 1536 MB -> only changed rows. NOT independently measured,
   because Step 6 could not run. The graphml's 73.9 MB rewrite is untouched.
2. **Host RAM at ingest** - migration peaked ~852 MB RSS. A real post-migration ingest has not been measured.
3. **Server RAM / query speed** - RAM 1.84 -> 1.60 GiB combined (lightrag 1.839 -> ~1.03, qdrant +0.57).
   Search 2.04x faster at 93,852 rows, slower below ~40k. Partially met, measured.
4. **Room to grow** - supported by the flat-vs-linear search curve and by writes no longer scaling with base size.

## Final state
- Committed: ragkit `32fdd38` on `feat/qdrant-vector-backend` (NOT merged to master), PCM_RAG `7ce33e5` on `main`.
  PCM's 27 unrelated modified files left untouched.
- Telemetry stopped cleanly (pids verified as typeperf/powershell first, per the stale-pidfile trap).
  `C:\Dumps\ingest60909-184057\`, 3.9 MB of hw sensors. **No WHEA events and no bugcheck** across ~2 h of
  sustained work on the 4-DIMM config - which is not evidence the RAM fault is gone, only that this run missed it.
- Tests green: `test_migrate_nano_to_qdrant.py`, `test_patch_flush_safety.py`, `test_streamed_save.py`,
  `test_zai_backoff.py`, `ragbase.py` self-check.
- **`vdb_*.json` still on disk (1,187 MB).** Deletion is gated on Step 6 and Step 6 has no document.
- Backup: `E:\BackUp_NEW\RAG\PCM_RAGag_storage_pre_qdrant_20260909.tgz` (767 MB, verified). Local only.

---

## STEP 6 RESULT - PASSED (2026-09-09 20:20 -> 21:15, 55 min)

Document chosen by the user: `FOUND\The_Role_of_Aluminium_Nitride_as_Reinforcement_Material_for_Phase_Change_Materials_PCMS.pdf`
(783 KB, 11 pages). Probed before routing: 16 embedded images + 245 vector drawings -> MinerU/VLM path,
under the page limit so no slicing. Staged into `IN\`, launched detached through the ragkit launcher with a
UTF-8 list file. Telemetry rig armed at `C:\Dumps\ingest\20260909-202012`, stopped clean afterwards.

`EXITCODE=0`. Log at `lightrag\LOG\ingest_run.20260909_211534.ok.log` - note the launcher RENAMES the log on
success, which is why a waiter polling `ingest_run.log` for `EXITCODE=` never fires.

### Goal 1 finally measured - per-document write volume
| | pre-migration | this run |
|---|---|---|
| `vdb_chunks.json` | 31 MB | **not written** |
| `vdb_entities.json` | 261 MB | **not written** |
| `vdb_relationships.json` | 812 MB | **not written** |
| graphml | 73.9 MB | 75.7 MB |
| 9 kv_store JSONs | ~70 MB | ~70.6 MB |
| **total** | **~1,251 MB** | **~146 MB (-88%)** |

Evidence: a `stat` of every store file before and after the run; the three `vdb_*.json` do not appear in the
diff at all (mtimes still 10:16-10:17). The log confirms it from the other side -
`Flush done: QdrantVectorDBStorage[...] 0.0 MB` on all three stores, 24 `Flush start:`/`Flush done:` pairs.
The graphml's 75.7 MB rewrite is untouched and is now 52% of the remaining per-document write.

### Correctness gates
| gate | result |
|---|---|
| docs | 70 -> 71, all `processed` |
| graph | 29,986 -> 30,508 nodes; 93,852 -> 96,045 edges; 0 NULs |
| qdrant entities / relationships | 30,508 / 96,045 - exact match to the graph |
| qdrant chunks | 2,912 -> 2,968 |
| multimodal | 52/52 items, 56/56 chunks - no drops |
| `check_vectors.py` | OK, exit 0, 0 nonfinite / 0 zero |
| `check_ingest_wiring.py` | OK, exit 0 - both silent-failure traps still closed |
| `verify_qdrant_recall.py` | exit 0, 0.9920 / 0.9850 / 0.9950 |
| live query | 4,684 chars, 16 AlN mentions, cites the new doc as `[1]` |

Recall is lower than Step 4's 0.9980-1.0000 for a benign reason: the JSONs are stale ground truth and do not
contain the 522 new entities, which now compete for top-10 slots. Still above the 0.98 threshold.

**Four z.ai 429s (code 1302) during extraction, all recovered** - each is preceded by `Retrying request` lines
and extraction continues; `Generated descriptions for 52/52 multimodal items` proves nothing was dropped.
This is the failure mode [[zai-429-drops-multimodal-items]] warns about, checked and clear.

### Gated follow-ups, both executed on the user's explicit go
- **`vdb_*.json` deleted** - 1,104,824,359 bytes reclaimed. Backup re-verified first:
  `tar --force-local -tzf E:\BackUp_NEW\RAG\PCM_RAG\rag_storage_pre_qdrant_20260909.tgz` exits 0, 16 members,
  all three `rag_storage/vdb_*.json` present. **`verify_qdrant_recall.py` no longer works on PCM** - its ground
  truth was those files.
- **ragkit `feat/qdrant-vector-backend` merged to `master`**, fast-forward to `32fdd38`, tree clean,
  `master` ahead of `origin/master` by 1 (NOT pushed). Full suite re-run on master:
  `test_migrate_nano_to_qdrant.py`, `test_patch_flush_safety.py`, `test_streamed_save.py`,
  `test_zai_backoff.py`, `ragbase.py` - all exit 0.
- Source recorded in `lightrag\INGESTED_SOURCES.txt`.

### Scorecard, updated
1. **Crash blast radius** - MET and measured: 1,251 MB -> 146 MB per document (-88%). The graphml is now the
   dominant remaining write at 52%.
2. **Host RAM at ingest** - telemetry captured at `C:\Dumps\ingest\20260909-202012`, not yet analysed.
3. **Server RAM / query speed** - unchanged from Step 4: partially met, measured.
4. **Room to grow** - supported.

**Still open:** graph storage (the graphml rewrite), MECH_RAG's graphml repair and its own migration,
`il-check-rag-base` / `il-rag-ingest` skills still reasoning about `vdb_*.json` and orphan counts,
MECH_RAG's `rag_sync.ps1` snapshot changes, and pushing ragkit `master`.
