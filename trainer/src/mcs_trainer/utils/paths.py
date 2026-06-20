from __future__ import annotations

import re
from pathlib import Path


def safe_join(base_dir: Path, relative: str) -> Path:
    """Join relative path under base_dir, refusing zip-slip / absolute escapes."""
    base = Path(base_dir).resolve()
    candidate = (base / relative).resolve()
    try:
        candidate.relative_to(base)
    except ValueError as exc:
        raise ValueError(
            f"Unsafe Pfad '{relative}' liegt ausserhalb von '{base}'"
        ) from exc
    return candidate


def resolve_dataset_dir(path: str | Path) -> Path:
    p = Path(path).expanduser().resolve()
    if not p.exists():
        raise FileNotFoundError(f"Dataset-Verzeichnis nicht gefunden: {p}")
    if not p.is_dir():
        raise NotADirectoryError(f"Kein Verzeichnis: {p}")
    return p


def ensure_subdirs(root: Path, names: list[str]) -> dict[str, Path]:
    root = Path(root)
    root.mkdir(parents=True, exist_ok=True)
    out: dict[str, Path] = {}
    for name in names:
        d = root / name
        d.mkdir(parents=True, exist_ok=True)
        out[name] = d
    return out


_SLUG_RE = re.compile(r"[^a-z0-9]+")


def slugify_dataset_id(value: str) -> str:
    s = value.strip().lower()
    s = _SLUG_RE.sub("-", s).strip("-")
    return s or "dataset"
