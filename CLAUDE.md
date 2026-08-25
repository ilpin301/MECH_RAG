# MECH_RAG

German-language LightRAG base for technical mechanics (Technische Mechanik 1-3). Sources are
lecture chapters, theory volumes, formula sheets and problem sets, so filenames carry umlauts
(`Stäben`, `Lösung`, `Körpers`) - every path must move through UTF-8, never the ANSI codepage.

## RAG Ingest Rules
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
- Baseline as of 2026-08-25: 47 documents, all `processed`. `IN\` holds exactly those 47 files.
  `FOUND\` holds the original sources, including Technische Mechanik 1 Aufgabenbuch and Theorie,
  which are NOT ingested.
- The container exited 137 (OOM-killed) on 2026-08-13 and has not run since, so the store may be
  mid-write. It has not been audited - run `il-check-rag-base` before trusting counts.
