"""visa_data.json → migrations/002_seed.sql 생성기
실행: python3 scripts/generate_seed.py
"""
import json
import os


def q(s):
    if s is None:
        return "NULL"
    s = str(s).replace("\\", "\\\\").replace("'", "''").replace("\n", "\\n").replace("\r", "\\r").replace("\t", "\\t")
    return f"E'{s}'"


def jb(v):
    if v is None:
        return "NULL"
    return f"{q(json.dumps(v, ensure_ascii=False))}::jsonb"


root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
with open(os.path.join(root, "visa_data.json"), "r", encoding="utf-8") as f:
    data = json.load(f)

out = [
    "-- Moonshot: visa_data.json seed",
    "-- 자동 생성됨. 재실행 가능(TRUNCATE → INSERT).",
    "",
    "BEGIN;",
    "",
    "TRUNCATE visa_sub_codes, visas RESTART IDENTITY CASCADE;",
    "",
    "INSERT INTO visas",
    "  (code, name, cat, period, new_req, ext_req, faq, data_badge, data_date, aliases, sort_order)",
    "VALUES",
]

visa_rows = [
    f"  ({q(v['code'])}, {q(v['name'])}, {q(v.get('cat'))}, {q(v.get('period'))}, "
    f"{q(v.get('newReq'))}, {q(v.get('extReq'))}, {q(v.get('faq'))}, "
    f"{q(v.get('dataBadge'))}, {q(v.get('dataDate'))}, "
    f"{jb(v.get('aliases'))}, {i})"
    for i, v in enumerate(data)
]
out.append(",\n".join(visa_rows) + ";")
out.append("")

sub_rows = [
    f"  ({q(s['code'])}, {q(v['code'])}, {q(s['name'])}, "
    f"{q(s.get('addReq'))}, {q(s.get('note'))}, {jb(s.get('aliases'))}, {j})"
    for v in data
    for j, s in enumerate(v.get("subCodes") or [])
]
if sub_rows:
    out += [
        "INSERT INTO visa_sub_codes",
        "  (code, parent_code, name, add_req, note, aliases, sort_order)",
        "VALUES",
        ",\n".join(sub_rows) + ";",
        "",
    ]

out.append("COMMIT;")
out.append("")

out_path = os.path.join(root, "migrations", "002_seed.sql")
os.makedirs(os.path.dirname(out_path), exist_ok=True)
with open(out_path, "w", encoding="utf-8") as f:
    f.write("\n".join(out))

print(f"생성 완료: {out_path} ({len(data)} visas, {len(sub_rows)} sub_codes)")
