import gc
import json
import sys
import time
import tracemalloc
from pathlib import Path

import matplotlib.pyplot as plt

from astparser import parsestr as ast_parsestr
from parser import parsestr


def gen_json(n: int) -> str:
    node_id = [0]

    def make_node() -> dict:
        i = node_id[0]
        node_id[0] += 1
        node: dict = {
            "id": i,
            "name": f"node_{i}",
            "value": round(i * 1.5, 3),
            "active": i % 2 == 0,
            "meta": {"score": round(-i / 7.0, 4), "created": 1700000000 + i},
        }
        if i % 3 == 0:
            node["tags"] = ["alpha", "beta", "gamma"]
        return node

    def build_tree(count: int) -> dict:
        node = make_node()
        if count <= 1:
            return node
        remaining = count - 1
        branching = min(4, remaining)
        chunk, extra = divmod(remaining, branching)
        children = {}
        for j in range(branching):
            size = chunk + (1 if j < extra else 0)
            children[f"child_{j}"] = build_tree(size)
        node["children"] = children
        return node

    return json.dumps(build_tree(n))


def measure_time(fn, payload, repeats=3):
    best = float("inf")
    for _ in range(repeats):
        gc.collect()
        t0 = time.perf_counter()
        fn(payload)
        t1 = time.perf_counter()
        best = min(best, t1 - t0)
    return best


def measure_memory(fn, payload):
    gc.collect()
    tracemalloc.start()
    fn(payload)
    _, peak = tracemalloc.get_traced_memory()
    tracemalloc.stop()
    return peak


def main():
    sys.setrecursionlimit(10_000)

    sizes = [10, 30, 100, 300, 1000, 3000, 10_000, 30_000]

    bytes_x: list[int] = []
    pstr_t: list[float] = []
    ast_t: list[float] = []
    json_t: list[float] = []
    pstr_m: list[int] = []
    ast_m: list[int] = []
    json_m: list[int] = []

    print(f"{'n':>7} {'bytes':>10} {'parsestr_ms':>12} {'ast_ms':>9} {'json_ms':>9} "
          f"{'parsestr_KB':>13} {'ast_KB':>9} {'json_KB':>9}")
    print("-" * 87)

    for n in sizes:
        payload = gen_json(n)
        n_bytes = len(payload.encode("utf-8"))

        t_p = measure_time(parsestr, payload)
        t_a = measure_time(ast_parsestr, payload)
        t_j = measure_time(json.loads, payload)
        m_p = measure_memory(parsestr, payload)
        m_a = measure_memory(ast_parsestr, payload)
        m_j = measure_memory(json.loads, payload)

        bytes_x.append(n_bytes)
        pstr_t.append(t_p)
        ast_t.append(t_a)
        json_t.append(t_j)
        pstr_m.append(m_p)
        ast_m.append(m_a)
        json_m.append(m_j)

        print(f"{n:>7} {n_bytes:>10} {t_p*1000:>12.2f} {t_a*1000:>9.2f} {t_j*1000:>9.2f} "
              f"{m_p/1024:>13.1f} {m_a/1024:>9.1f} {m_j/1024:>9.1f}")

    fig, (ax_t, ax_m) = plt.subplots(1, 2, figsize=(13, 5))

    ax_t.plot(bytes_x, pstr_t, "o-", label="parsestr (single-phase)")
    ax_t.plot(bytes_x, ast_t, "o-", label="astparser (tokenize + parse + evaluate)")
    ax_t.plot(bytes_x, json_t, "o-", label="json.loads (stdlib, C-backed)")
    ax_t.set_xscale("log")
    ax_t.set_yscale("log")
    ax_t.set_xlabel("Input size (bytes)")
    ax_t.set_ylabel("Parse time (s)")
    ax_t.set_title("Parse time vs input size")
    ax_t.grid(True, which="both", alpha=0.3)
    ax_t.legend()

    ax_m.plot(bytes_x, [m / 1024 for m in pstr_m], "o-", label="parsestr (single-phase)")
    ax_m.plot(bytes_x, [m / 1024 for m in ast_m], "o-", label="astparser (tokenize + parse + evaluate)")
    ax_m.plot(bytes_x, [m / 1024 for m in json_m], "o-", label="json.loads (stdlib, C-backed)")
    ax_m.set_xscale("log")
    ax_m.set_yscale("log")
    ax_m.set_xlabel("Input size (bytes)")
    ax_m.set_ylabel("Peak Python heap (KB)")
    ax_m.set_title("Peak memory vs input size")
    ax_m.grid(True, which="both", alpha=0.3)
    ax_m.legend()

    fig.suptitle("parsestr vs astparser vs json.loads — nested JSON tree of N nodes (branching factor 4)")
    plt.tight_layout()

    out = Path("benchmark.png")
    plt.savefig(out, dpi=120)
    print(f"\nsaved {out}")


if __name__ == "__main__":
    main()
