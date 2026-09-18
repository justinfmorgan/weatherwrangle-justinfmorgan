import json, sys
from collections import Counter, defaultdict

path = "daily_14.json"
type_counts = defaultdict(Counter)   # path -> Counter(type)
presence = Counter()                  # path -> count of records where present
list_lens = defaultdict(Counter)     # path -> Counter(len)
parse_errors = []
n = 0

def walk(obj, prefix, seen):
    if isinstance(obj, dict):
        for k, v in obj.items():
            p = f"{prefix}.{k}" if prefix else k
            walk(v, p, seen)
    elif isinstance(obj, list):
        list_lens[prefix][len(obj)] += 1
        for item in obj:
            walk(item, prefix + "[]", seen)
    else:
        seen.add(prefix)
        type_counts[prefix][type(obj).__name__] += 1
    if isinstance(obj, (dict, list)):
        seen.add(prefix)
        type_counts[prefix][type(obj).__name__] += 1

with open(path) as f:
    for i, line in enumerate(f, 1):
        try:
            rec = json.loads(line)
        except json.JSONDecodeError as e:
            parse_errors.append((i, str(e)[:80]))
            continue
        n += 1
        seen = set()
        walk(rec, "", seen)
        for p in seen:
            presence[p] += 1

print(f"records parsed: {n}   parse errors: {len(parse_errors)}")
for pe in parse_errors[:10]:
    print("  ", pe)
print()
print(f"{'path':45} {'present/records':>18}  types")
for p in sorted(type_counts):
    tc = dict(type_counts[p])
    print(f"{p:45} {presence[p]:>8}/{n:<8}  {tc}")
print()
print("list length distributions:")
for p, c in list_lens.items():
    print(f"  {p}: {dict(sorted(c.items()))}")
