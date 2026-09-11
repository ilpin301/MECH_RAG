# MECH_RAG

German-language LightRAG base for technical mechanics (Technische Mechanik 1-3). Sources are
lecture chapters, theory volumes, formula sheets and problem sets, so filenames carry umlauts
(`Stäben`, `Lösung`, `Körpers`) - every path must move through UTF-8, never the ANSI codepage.

## RAG Ingest Rules
- **One SOURCE per ingest run.** If `IN\` has several new files, ingest them one at a time:
  full cycle per source (probe, launch, verify, error-correction pass, cleanup, ledger, memory),
  and only then start the next. Never batch several sources into one list file - a failure then
  cannot be attributed and the delete/re-ingest repair costs minutes per document. Slices of ONE
  source still go in ONE run. A failed or lossy source STOPS the queue; report and wait.
- Always launch ingests via the ragkit launcher, detached, never inline:
  `& $env:RAGKIT_HOME\ingest.ps1 -Root <this base> -ListFile <utf8 list>`. It produces
  `lightrag\LOG\ingest_run.log`, which progress checks depend on, and it owns `docker compose
  stop`/`start` - do not stop the container yourself.
- `-ListFile` is mandatory and always UTF-8. Never pass PDF paths as bare process arguments: the
  German filenames in this base mangle through the ANSI codepage and the ingest silently targets
  the wrong file.
- Delete/wipe `ingest_run.log` ONLY after the run reports `EXITCODE=0`, never before the run starts.
- Probe every PDF before routing: use full image detection (embedded images AND vector figures),
  not just `page.get_images()`. Image-heavy → MinerU/VLM path; text-only → text path.
- Slice PDFs over the MinerU size/page limit before ingest; delete slice PDFs only after all slices
  are confirmed processed.
- Record every ingested SOURCE in `lightrag\INGESTED_SOURCES.txt`, not the slice names. Most of this
  base was ingested as slice families whose names do not resemble the source, so the ledger is the
  only thing stopping a whole 300-page theory volume being ingested a second time.
- Verify every ingest with: doc count delta, graph node delta, vector sanity check, and one targeted
  query.

## This base
- Server `mech_rag-lightrag-1`, port 9623, `COMPOSE_PROJECT_NAME=mech_rag` in `lightrag\.env`.
- The z.ai key is stored as `LLM_BINDING_API_KEY`; the launcher maps it to `ZAI_API_KEY`, which is
  the name `rag_ingest.py` expects.
- `lightrag\` is a shallow clone of hkuds/lightrag with its upstream `.git` renamed to
  `.git-upstream-bak`. Only files this project added are tracked. Do not touch
  `lightrag\CLAUDE.md` - that one is upstream's.
- The store (`lightrag\data\rag_storage\`) is NOT in git. It lives on disk and is backed up to
  Google Drive with `rag_sync.ps1`. Never `git add -A` here.
- **This base lives at `X:\RAG_MAIN\MECH_RAG\` since 2026-09-05** (moved off F:, the
  DRAM-less SSD that corrupted NTFS twice in August). `RAGKIT_HOME` is `X:\RAG_MAIN\RAG`.
  The F: copy still exists as rollback and is STALE - never ingest into it.
- Baseline verified 2026-09-05 directly from the store: 52 documents - 51 `processed` and
  **1 stuck at `handling`** (`Technische Mechanik 1 Theorie-027-051.pdf`, 7 chunks,
  `doc-7d0304f7883e5c11dc4100389a9b3497`), which must be deleted before it is re-ingested.
  4223 chunks; 33405 graph nodes / 139068 edges; `vdb_chunks` 4223, `vdb_entities` 33730,
  `vdb_relationships` 139068; all matrices present, 0 NUL bytes across all 15 store files.
  These numbers are LOWER than the 2026-08-25 figures this file used to record (4472 chunks
  / 34563 nodes / 147166 edges): the 29-Aug BSOD and the 02-Sep hang killed their ingests and
  the store did not keep that work. Trust a fresh count over any recorded baseline after a crash.
  `IN\` holds 54 PDFs plus `Aufgabensammlung_Loesung_Textlayer.md`; 3 of them never reached
  the graph (`Kapitel12_Verzerrungszustand.pdf`, `Technische Mechanik 2 Theorie-7.pdf`,
  `Technische Mechanik 3 Theorie--3.pdf`), so `IN\` is NOT one-doc-per-file any more.
  `FOUND\` holds the original sources, including Technische Mechanik 1 Aufgabenbuch and
  Theorie, which are NOT ingested.
- Standing orphan population, re-measured 2026-09-05 (accepted, not damage): 251 graph edges
  with no relationship vector and 251 relationship vectors with no graph edge, out of 139068
  each - 0.18%, left by entity-merge deletes. This replaces the ~2840 / ~2334 (~1.9%) figures
  recorded on 2026-08-25, which the killed ingests invalidated. Compare against 251 before
  calling an orphan count a finding, and re-measure rather than trusting this line after a crash.
- A BSOD (bugcheck 0x1E) killed the box on 2026-08-25 13:41 during the `Theorie-008-008.pdf` ingest.
  Audited afterwards: no NULs, no truncation, no lost docs - the ingest had finished at 13:36. A
  normal container stop yields Exited (137) here; that is not evidence of an OOM kill.
