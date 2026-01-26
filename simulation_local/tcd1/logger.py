import csv
from typing import Any, Dict, Optional


class CsvLogger:
    def __init__(self, path: str):
        if not path:
            raise ValueError("path must be a non-empty string")
        self._f = open(path, "w", newline="")
        self._fieldnames: list[str] = []
        self._w: Optional[csv.DictWriter] = None
        self._buffer: list[Dict[str, Any]] = []

    def _ensure_writer(self, row: Dict[str, Any]) -> None:
        changed = False
        for k in row.keys():
            if k not in self._fieldnames:
                self._fieldnames.append(k)
                changed = True

        if self._w is None or changed:
            self._f.seek(0)
            self._f.truncate(0)
            self._w = csv.DictWriter(self._f, fieldnames=self._fieldnames)
            self._w.writeheader()
            for r in self._buffer:
                self._w.writerow({k: r.get(k, "") for k in self._fieldnames})
            self._f.flush()

    def log(self, row: Dict[str, Any]) -> None:
        row_copy = dict(row)
        self._buffer.append(row_copy)
        self._ensure_writer(row_copy)
        assert self._w is not None
        self._w.writerow({k: row_copy.get(k, "") for k in self._fieldnames})
        self._f.flush()

    def close(self) -> None:
        try:
            self._f.close()
        except Exception:
            pass