import sys, csv, json, ast, argparse
from datetime import datetime, timezone

def parse_tags(tag_list):
    tags = {}
    for t in tag_list or []:
        if "=" not in t:
            continue
        k, v = t.split("=", 1)
        tags[k.strip()] = v.strip()
    return tags

def to_time_ns(ts):
    # ts is epoch seconds float
    try:
        return int(float(ts) * 1_000_000_000)
    except Exception:
        return None

def normalize_fields(d):
    # Convert bool -> int for TSDB friendliness, keep floats/ints as-is
    out = {}
    for k, v in d.items():
        if k in ("Timestamp", "ts"):
            continue
        if isinstance(v, bool):
            out[k] = int(v)
        elif v is None:
            # skip Nones
            continue
        else:
            out[k] = v
    return out

def parse_line(line):
    line = line.strip()
    if not line:
        return None

    # Case A: python dict printed like {'Timestamp': ..., 'ev1_status': False, ...}
    if line.startswith("{") and "'Timestamp'" in line:
        try:
            d = ast.literal_eval(line)
            ts = d.get("Timestamp")
            return float(ts), d
        except Exception:
            return None

    # Case B: JSON printed like {"type":"sensors","data":{...}}
    if line.startswith("{") and '"type"' in line and '"sensors"' in line:
        try:
            j = json.loads(line)
            d = j.get("data") or {}
            ts = d.get("ts")
            return float(ts), d
        except Exception:
            return None

    return None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="sensors.csv")
    ap.add_argument("--jsonl", default="points.jsonl")
    ap.add_argument("--measurement", default="kp_rig")
    ap.add_argument("--tag", action="append", help="tag in k=v form (repeatable)")
    ap.add_argument("--stdout-pass", action="store_true", help="also pass through original lines")
    args = ap.parse_args()

    tags = parse_tags(args.tag)

    csv_f = open(args.csv, "w", newline="", encoding="utf-8")
    jsonl_f = open(args.jsonl, "w", encoding="utf-8")

    writer = None
    header = None

    for raw in sys.stdin:
        if args.stdout_pass:
            sys.stdout.write(raw)
            sys.stdout.flush()

        parsed = parse_line(raw)
        if not parsed:
            continue

        ts, d = parsed
        t_ns = to_time_ns(ts)
        if t_ns is None:
            continue

        # Build CSV row
        if "Timestamp" in d:
            # already has Timestamp key
            row = dict(d)
        else:
            row = dict(d)
            row["Timestamp"] = ts

        # Initialize CSV header on first valid row
        if writer is None:
            # stable-ish column order: Timestamp first, then sorted keys
            keys = list(row.keys())
            keys.remove("Timestamp")
            header = ["Timestamp"] + sorted(keys)
            writer = csv.DictWriter(csv_f, fieldnames=header)
            writer.writeheader()

        # Ensure all columns exist
        for k in header:
            if k not in row:
                row[k] = ""

        writer.writerow(row)
        csv_f.flush()

        # Build TSDB point dict (JSONL)
        point = {
            "measurement": args.measurement,
            "time_ns": t_ns,
            "tags": tags,
            "fields": normalize_fields(d),
        }
        jsonl_f.write(json.dumps(point, ensure_ascii=False) + "\n")
        jsonl_f.flush()

    csv_f.close()
    jsonl_f.close()

if __name__ == "__main__":
    main()
