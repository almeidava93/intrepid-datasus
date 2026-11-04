"""Local data folder: Parquet partitions plus a manifest of what was fetched.

Layout:
    <root>/pa/competencia=202605/uf=SP/PASP2605a.parquet      (2008 onward)
    <root>/pa_legacy/competencia=200312/uf=SP/PASP0312.parquet  (1994-2007)
    <root>/manifest.json
"""
from __future__ import annotations

import json
import os
import shutil
import time
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path

from .catalog import Era, Partition, era_for

DEFAULT_ROOT = Path("data")


class LockedError(Exception):
    """Another datasus command is writing to the same data folder."""


def default_root() -> Path:
    return Path(os.environ.get("DATASUS_DATA_DIR", DEFAULT_ROOT))


class Store:
    def __init__(self, root: Path):
        self.root = Path(root)
        self.manifest_path = self.root / "manifest.json"
        self.tmp = self.root / ".tmp"

    # ------------------------------------------------------------ paths
    def era_dir(self, era: Era) -> Path:
        return self.root / era.key

    def partition_dir(self, uf: str, comp: int) -> Path:
        return self.era_dir(era_for(comp)) / f"competencia={comp}" / f"uf={uf}"

    # --------------------------------------------------------- manifest
    def manifest(self) -> dict[str, dict]:
        if not self.manifest_path.exists():
            return {}
        return json.loads(self.manifest_path.read_text(encoding="utf-8"))

    def _write_manifest(self, data: dict) -> None:
        self.root.mkdir(parents=True, exist_ok=True)
        tmp = self.manifest_path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(data, indent=1, sort_keys=True), encoding="utf-8")
        os.replace(tmp, self.manifest_path)

    def record(self, p: Partition, rows: int, nbytes: int) -> None:
        data = self.manifest()
        data[p.key] = {
            "uf": p.uf,
            "competencia": p.competencia,
            "files": p.signature(),
            "rows": rows,
            "bytes": nbytes,
            "fetched_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        }
        self._write_manifest(data)

    def forget(self, keys: list[str]) -> None:
        data = self.manifest()
        for k in keys:
            data.pop(k, None)
        self._write_manifest(data)

    def is_current(self, p: Partition) -> bool:
        """True when the local copy was built from exactly the files now on the FTP."""
        entry = self.manifest().get(p.key)
        return bool(entry) and entry["files"] == p.signature() and self.partition_dir(p.uf, p.competencia).is_dir()

    # -------------------------------------------------------- partitions
    def staging_dir(self, p: Partition) -> Path:
        return self.tmp / f"{p.uf}{p.competencia}"

    def publish(self, p: Partition, built: Path) -> int:
        """Replace the partition folder with a freshly built one; returns its size in bytes."""
        final = self.partition_dir(p.uf, p.competencia)
        final.parent.mkdir(parents=True, exist_ok=True)
        old = final.with_name(final.name + ".old")
        if old.exists():
            shutil.rmtree(old)
        if final.exists():
            os.replace(final, old)
        os.replace(built, final)
        if old.exists():
            shutil.rmtree(old, ignore_errors=True)
        return sum(f.stat().st_size for f in final.glob("*.parquet"))

    def remove(self, keys: list[str]) -> int:
        """Delete partitions by manifest key ('SP/202605'); returns bytes freed."""
        freed = 0
        for key in keys:
            uf, comp = key.split("/")
            d = self.partition_dir(uf, int(comp))
            if d.exists():
                freed += sum(f.stat().st_size for f in d.glob("*"))
                shutil.rmtree(d)
                try:  # drop the month folder when it becomes empty
                    d.parent.rmdir()
                except OSError:
                    pass
        self.forget(keys)
        return freed

    # -------------------------------------------------------------- lock
    @contextmanager
    def lock(self):
        """Stop two fetch/remove runs from writing to the same folder at once."""
        self.root.mkdir(parents=True, exist_ok=True)
        path = self.root / ".lock"
        try:
            fd = os.open(path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError:
            age = time.time() - path.stat().st_mtime
            raise LockedError(
                f"{path} exists: another datasus command is using this folder "
                f"(lock is {age / 60:.0f} min old). If none is running, delete that file."
            ) from None
        try:
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
            yield
        finally:
            path.unlink(missing_ok=True)
