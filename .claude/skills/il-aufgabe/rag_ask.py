#!/usr/bin/env python
"""One targeted question to the local LightRAG knowledge graph.

    python rag_ask.py "Koppeltafel: Zeile fuer quadratische Parabel mal Dreieck"
    python rag_ask.py --mode local "Welche Konvention nutzt Kapitel 15?"
    python rag_ask.py --url http://localhost:9621/query "..."

Port and API key both come from the LightRAG `.env` (PORT, LIGHTRAG_API_KEY),
so nothing here is machine-specific. That file is located by walking up from
this script to the first `lightrag/.env`, which works from any install
location. Override with the MECH_RAG_ENV environment variable, or bypass it
entirely with --url plus MECH_RAG_KEY.

Note the `.env` is NOT read for the host: it stores the container's bind
address (0.0.0.0), which is not a connect address. Always localhost.

The `.env` holds a paid API key and is gitignored. Do not copy it into this
skill folder.

Proxies are bypassed explicitly: the machine's SOCKS system proxy otherwise
breaks urllib.

Answers take 30-90 s. Output is a lead, not an authority -- never take a
number, coefficient or sign from it without an independent check.
"""
import argparse
import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path


def find_env():
    override = os.environ.get("MECH_RAG_ENV")
    if override:
        return Path(override)
    for d in Path(__file__).resolve().parents:
        cand = d / "lightrag" / ".env"
        if cand.is_file():
            return cand
    return None


def read_env(path):
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\s*([A-Z_][A-Z0-9_]*)\s*=\s*(.*)", line)
        if m:
            out[m.group(1)] = m.group(2).strip().strip('"').strip("'")
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("question")
    ap.add_argument("--mode", default="hybrid",
                    choices=["hybrid", "local", "global", "naive", "mix"])
    ap.add_argument("--url", help="override endpoint, e.g. http://localhost:9621/query")
    ap.add_argument("--timeout", type=int, default=300)
    a = ap.parse_args()

    key = os.environ.get("MECH_RAG_KEY", "")
    url = a.url
    if not (url and key):
        envfile = find_env()
        if envfile is None or not envfile.is_file():
            sys.exit("no lightrag/.env found above this script; set MECH_RAG_ENV, "
                     "or pass --url together with MECH_RAG_KEY")
        env = read_env(envfile)
        key = key or env.get("LIGHTRAG_API_KEY", "")
        if not key:
            sys.exit(f"LIGHTRAG_API_KEY missing in {envfile}")
        if not url:
            url = f"http://localhost:{env.get('PORT', '9621')}/query"

    body = json.dumps({"query": a.question, "mode": a.mode}).encode("utf-8")
    req = urllib.request.Request(url, data=body, headers={
        "X-API-Key": key,
        "Content-Type": "application/json; charset=utf-8",
    })
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    try:
        with opener.open(req, timeout=a.timeout) as r:
            print(json.load(r)["response"])
    except urllib.error.URLError as e:
        sys.exit(f"LightRAG unreachable at {url} ({e}). Container up? "
                 "docker start mech_rag-lightrag-1")


if __name__ == "__main__":
    main()
