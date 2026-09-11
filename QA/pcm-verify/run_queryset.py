"""Run the PCM_RAG verification query set and save answers + retrieved context.

Used twice: once on NanoVectorDBStorage (baseline) and once on Qdrant (after).
Retrieval is NOT LLM-cached, so the `context` capture is a genuine diff of the
vector store. The `answer` capture IS cached, so before the after-run the
mode-prefixed keys must be dropped from kv_store_llm_response_cache.json.

    python run_queryset.py <label>        # e.g. nano | qdrant
"""
import io
import json
import os
import sys
import time
import urllib.request

BASE = os.environ.get("PCM_URL", "http://localhost:9622")
HERE = os.path.dirname(os.path.abspath(__file__))

QUESTIONS = [
    "How does adding a phase change material to a PV panel affect its electrical efficiency, and what temperature drops are reported?",
    "What are the main strategies for enhancing the thermal conductivity of PCMs, and what improvement factors do they achieve?",
    "How are PCMs used in battery thermal management for electric vehicles?",
    "What role do fins play in heat transfer enhancement in PCM latent heat storage, and how does fin geometry matter?",
    "Compare organic and inorganic PCMs: melting range, latent heat, and their practical drawbacks.",
    "What is the cost effectiveness of PCM-integrated building envelopes, and what payback periods are reported?",
    "How does incorporating PCM into mortar or concrete change the thermal inertia and the mechanical strength?",
    "Explain the resistive switching mechanism in chalcogenide phase change memory materials.",
    "What distinguishes Sb2S3 in the context of electromechanical hysteresis and phase change photonics?",
    "What did Wuttig and Yamada identify as the key property contrast that makes phase change materials useful for data storage?",
]


def _api_key():
    """Read LIGHTRAG_API_KEY out of the base's .env; never echoed anywhere."""
    env = os.environ.get("PCM_ENV", r"X:\RAG_MAIN\PCM_RAG\lightrag\.env")
    with io.open(env, encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("LIGHTRAG_API_KEY="):
                return line.split("=", 1)[1].strip()
    return ""


KEY = _api_key()


def post(path, body, timeout=600):
    headers = {"Content-Type": "application/json"}
    if KEY:
        headers["X-API-Key"] = KEY
    r = urllib.request.Request(
        BASE + path, data=json.dumps(body).encode(), method="POST",
        headers=headers,
    )
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    with opener.open(r, timeout=timeout) as resp:
        return json.loads(resp.read())


def main():
    label = sys.argv[1] if len(sys.argv) > 1 else "run"
    out = {"label": label, "base": BASE, "ts": time.time(), "results": []}

    for i, q in enumerate(QUESTIONS, 1):
        rec = {"n": i, "question": q}

        t0 = time.time()
        ctx = post("/query", {"query": q, "mode": "hybrid",
                              "only_need_context": True})
        rec["context_ms"] = round((time.time() - t0) * 1000)
        rec["context"] = ctx.get("response", "")

        t0 = time.time()
        ans = post("/query", {"query": q, "mode": "hybrid"})
        rec["answer_ms"] = round((time.time() - t0) * 1000)
        rec["answer"] = ans.get("response", "")

        out["results"].append(rec)
        print(f"Q{i:2d} ctx={rec['context_ms']:6d}ms ans={rec['answer_ms']:6d}ms "
              f"ctx_len={len(rec['context']):6d} ans_len={len(rec['answer']):5d}",
              flush=True)

    path = os.path.join(HERE, f"queryset_{label}.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)

    ctx_ms = [r["context_ms"] for r in out["results"]]
    ans_ms = [r["answer_ms"] for r in out["results"]]
    print(f"\nsaved {path}")
    print(f"context  median {sorted(ctx_ms)[len(ctx_ms) // 2]} ms   total {sum(ctx_ms)} ms")
    print(f"answer   median {sorted(ans_ms)[len(ans_ms) // 2]} ms   total {sum(ans_ms)} ms")
    return 0


if __name__ == "__main__":
    sys.exit(main())
