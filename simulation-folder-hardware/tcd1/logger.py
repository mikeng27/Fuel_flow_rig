import csv
from typing import Any, Dict, Optional


class CsvLogger:
    def __init__(self, path: str):
        self._f = open(path, "w", newline="")
        self._fieldnames = []
        self._w: Optional[csv.DictWriter] = None
        self._buffer: list[Dict[str, Any]] = []

    def _ensure_writer(self, row: Dict[str, Any]) -> None:
        changed = False
        for k in row:
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
        self._buffer.append(row)
        self._ensure_writer(row)
        self._w.writerow({k: row.get(k, "") for k in self._fieldnames})
        self._f.flush()

    def close(self) -> None:
        self._f.close()
