import json
import os
import time

DATA_FILE = os.path.join(
    os.path.dirname(os.path.abspath(__file__)),
    "..", "data", "processed", "transactions.json",
)

with open(DATA_FILE, "r", encoding="utf-8") as f:
    transactions = json.load(f)

for i, t in enumerate(transactions, start=1):
    t.setdefault("id", i)


def linear_search(data, tid):
    """Scan the list from the start until the id matches: O(n)."""
    for t in data:
        if t["id"] == tid:
            return t
    return None


def dict_lookup(lookup, tid):
    """Hash the key and jump straight to the record: O(1) on average."""
    return lookup.get(tid)


def time_lookups(func, structure, ids, repeats):
    """Average time per lookup, in microseconds."""
    start = time.perf_counter()
    for _ in range(repeats):
        for tid in ids:
            func(structure, tid)
    elapsed = time.perf_counter() - start
    return elapsed / (repeats * len(ids)) * 1_000_000


def compare(data, label, repeats):
    lookup = {t["id"]: t for t in data}
    ids = [t["id"] for t in data]
    worst = [ids[-1]]  # last record = worst case for linear search

    lin_avg = time_lookups(linear_search, data, ids, repeats)
    dic_avg = time_lookups(dict_lookup, lookup, ids, repeats)
    lin_worst = time_lookups(linear_search, data, worst, repeats * 10)
    dic_worst = time_lookups(dict_lookup, lookup, worst, repeats * 10)

    print(f"\n{label} ({len(data)} records)")
    print(f"  {'':22}{'Linear search':>15}{'Dict lookup':>15}")
    print(f"  {'Average (all ids)':22}{lin_avg:>12.3f} us{dic_avg:>12.3f} us")
    print(f"  {'Worst case (last id)':22}{lin_worst:>12.3f} us{dic_worst:>12.3f} us")
    print(f"  Dictionary is about {lin_avg / dic_avg:.1f}x faster on average")


if __name__ == "__main__":
    compare(transactions[:20], "Small set", repeats=2000)
    compare(transactions, "Full dataset", repeats=20)