#!/usr/bin/env python3
"""Renderer fuzz: mutates the example findings JSON and checks the renderer never tracebacks.

Hedef: bozuk girdi temiz bir hata mesajıyla çıkmalı (exit 2), Python traceback'i basmamalı.
Kullanım: python3 tests/fuzz_render.py [tur]
"""
from __future__ import annotations

import copy
import json
import pathlib
import random
import subprocess
import sys
import tempfile

ROOT = pathlib.Path(__file__).resolve().parent.parent
RENDER = ROOT / "argus" / "scripts" / "render_report.py"
BASE = json.loads((ROOT / "argus" / "examples" / "example-output.json").read_text(encoding="utf-8"))

WEIRD = [None, [], {}, 0, -1, 1.5, "", " ", "x" * 5000, "ü" * 500, ["a", "b"], {"k": "v"},
         True, "|pipe|", "line\nbreak", "<script>alert(1)</script>", "—", "\x00", 10**30]


def run(payload: dict, fmt: str) -> tuple[int, str, str]:
    with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as fh:
        json.dump(payload, fh, ensure_ascii=False)
        path = fh.name
    cmd = [sys.executable, str(RENDER), path, "--format", fmt]
    p = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
    pathlib.Path(path).unlink(missing_ok=True)
    return p.returncode, p.stdout, p.stderr


def mutate(node, key_path=""):
    """Rastgele bir düğümü WEIRD değerlerden biriyle değiştirir; (payload, açıklama) döner."""
    data = copy.deepcopy(BASE)
    target = data
    parts = [p for p in key_path.split(".") if p]
    for p in parts[:-1]:
        target = target[int(p)] if isinstance(target, list) else target[p]
    leaf = parts[-1] if parts else None
    if leaf is None:
        return random.choice(WEIRD)
    if isinstance(target, list):
        target[int(leaf)] = random.choice(WEIRD)
    else:
        target[leaf] = random.choice(WEIRD)
    return data


def paths(node, prefix=""):
    out = []
    if isinstance(node, dict):
        for k, v in node.items():
            p = f"{prefix}.{k}" if prefix else k
            out.append(p)
            out += paths(v, p)
    elif isinstance(node, list):
        for i, v in enumerate(node):
            p = f"{prefix}.{i}"
            out.append(p)
            out += paths(v, p)
    return out


def main() -> int:
    rounds = int(sys.argv[1]) if len(sys.argv) > 1 else 120
    all_paths = paths(BASE)
    print(f"fuzz: {rounds} mutasyon, {len(all_paths)} alan")
    tracebacks, clean, ok = [], 0, 0
    for i in range(rounds):
        p = random.choice(all_paths)
        payload = mutate(BASE, p)
        for fmt in ("md", "html"):
            rc, out, err = run(payload, fmt)
            if "Traceback (most recent call last)" in err:
                tracebacks.append((p, fmt, err.strip().splitlines()[-1][:160]))
            elif rc == 0:
                ok += 1
            else:
                clean += 1
    print(f"  temiz hata: {clean} | render edildi: {ok} | traceback: {len(tracebacks)}")
    for p, fmt, last in tracebacks[:15]:
        print(f"  TRACEBACK {fmt:4} alan={p[:50]:52} {last}")
    return 1 if tracebacks else 0


if __name__ == "__main__":
    sys.exit(main())
