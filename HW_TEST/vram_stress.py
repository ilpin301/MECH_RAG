"""VRAM integrity + GPU core stress for the Quadro P2000.

Phase MEM  : fill a resident VRAM buffer with a regenerable pattern (idx ^ seed),
             hold it, read it back, count mismatching int32 words.
Phase CORE : heat the core with matmuls while a smaller checked buffer sits in VRAM.

Fill and verify run in chunks so the only large VRAM resident is the buffer under
test - full-size index/expected temporaries would triple the footprint and push the
data out to host RAM, where it is no longer a VRAM test.

Any nonzero mismatch count = VRAM or memory-controller fault.
Uses the RAG venv's torch, no downloads.
"""
import argparse, subprocess, sys, time
import torch

SEEDS = [0x00000000, -1, 0x5A5A5A5A, 0x3C3C3C3C, 0x0F0F0F0F]
CHUNK = 1 << 24  # 16M int32 words = 64 MiB per temporary


def gpu_temp():
    try:
        out = subprocess.run(
            ["nvidia-smi", "--query-gpu=temperature.gpu,memory.used,power.draw",
             "--format=csv,noheader,nounits"],
            capture_output=True, text=True, timeout=15)
        return out.stdout.strip().replace("\n", " | ")
    except Exception as e:
        return f"nvidia-smi failed: {e}"


class Log:
    def __init__(self, path):
        self.f = open(path, "a", encoding="utf-8")

    def __call__(self, msg):
        line = f"{time.strftime('%H:%M:%S')} {msg}"
        print(line, flush=True)
        self.f.write(line + "\n")
        self.f.flush()


def expected_chunk(start, stop, seed):
    idx = torch.arange(start, stop, dtype=torch.int32, device="cuda")
    return idx.bitwise_xor_(torch.tensor(seed, dtype=torch.int32, device="cuda"))


def fill(buf, seed):
    for s in range(0, buf.numel(), CHUNK):
        e = min(s + CHUNK, buf.numel())
        buf[s:e].copy_(expected_chunk(s, e, seed))
    torch.cuda.synchronize()


def check(buf, seed, log, tag):
    bad = 0
    for s in range(0, buf.numel(), CHUNK):
        e = min(s + CHUNK, buf.numel())
        want = expected_chunk(s, e, seed)
        diff = buf[s:e] != want
        n = int(diff.sum().item())
        if n:
            i = int(diff.nonzero()[0].item())
            log(f"!! {tag} seed={seed:#010x} MISMATCH words={n} index={s + i} "
                f"got={int(buf[s + i].item()):#010x} want={int(want[i].item()):#010x}")
            bad += n
    return bad


def phase_mem(gb, seconds, hold, log):
    n = int(gb * (1 << 30)) // 4
    log(f"PHASE MEM: {gb} GiB = {n} int32 words, hold={hold}s, budget={seconds}s")
    buf = torch.empty(n, dtype=torch.int32, device="cuda")
    errors = passes = 0
    end = time.time() + seconds
    while time.time() < end:
        for seed in SEEDS:
            fill(buf, seed)
            errors += check(buf, seed, log, "write")
            if hold:
                time.sleep(hold)
                errors += check(buf, seed, log, "retention")
            passes += 1
        log(f"MEM pass-set {passes} done, errors={errors} | {gpu_temp()}")
    del buf
    torch.cuda.empty_cache()
    return passes, errors


def phase_core(gb, seconds, log):
    n = int(gb * (1 << 30)) // 4
    log(f"PHASE CORE: matmul heat + {gb} GiB checked buffer, budget={seconds}s")
    seed = 0x5A5A5A5A
    buf = torch.empty(n, dtype=torch.int32, device="cuda")
    fill(buf, seed)
    a = torch.randn(2048, 2048, device="cuda")
    b = torch.randn(2048, 2048, device="cuda")
    errors = iters = 0
    end = time.time() + seconds
    last = 0.0
    while time.time() < end:
        for _ in range(50):
            c = a @ b
            a = c / (c.abs().max() + 1e-6)
        torch.cuda.synchronize()
        iters += 50
        if not torch.isfinite(a).all():
            log("!! CORE matmul produced non-finite values")
            errors += 1
            a = torch.randn(2048, 2048, device="cuda")
        errors += check(buf, seed, log, "core-buffer")
        if time.time() - last > 30:
            log(f"CORE iters={iters} errors={errors} | {gpu_temp()}")
            last = time.time()
    return iters, errors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--minutes", type=float, default=30)
    ap.add_argument("--mem-gb", type=float, default=4.0)
    ap.add_argument("--core-gb", type=float, default=1.0)
    ap.add_argument("--hold", type=float, default=2.0, help="retention hold seconds")
    ap.add_argument("--log", default="X:/RAG_MAIN/MECH_RAG/HW_TEST/vram_stress.log")
    args = ap.parse_args()

    log = Log(args.log)
    if not torch.cuda.is_available():
        log("FATAL: no CUDA device")
        sys.exit(2)
    log("=" * 70)
    log(f"START {torch.cuda.get_device_name(0)} torch={torch.__version__} "
        f"cuda={torch.version.cuda} | {gpu_temp()}")

    half = args.minutes * 60 / 2
    p, e1 = phase_mem(args.mem_gb, half, args.hold, log)
    i, e2 = phase_core(args.core_gb, half, log)

    total = e1 + e2
    log(f"RESULT mem_passes={p} mem_errors={e1} core_iters={i} core_errors={e2}")
    log(f"VERDICT {'FAIL' if total else 'PASS'} total_errors={total}")
    log(f"EXITCODE={1 if total else 0}")
    sys.exit(1 if total else 0)


if __name__ == "__main__":
    main()
