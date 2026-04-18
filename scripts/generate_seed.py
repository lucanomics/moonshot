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

with open("visa_data.json", "r", encoding="utf-8") as f:
    data = json.load(f)

visa_rows = []
for i, v in enumerate(data):
    row = (
        f"  ({q(v['code'])}, {q(v['name'])}, {q(v.get('cat'))}, {q(v.get('period'))}, "
        f"{q(v.get('newReq'))}, {q(v.get('extReq'))}, {q(v.get('faq'))}, "
        f"{q(v.get('dataBadge'))}, {q(v.get('dataDate'))}, "
        f"{jb(v.get('aliases'))}, {i})"
    )
    visa_rows.append(row)

sub_rows = []
for v in data:
    for j, s in enumerate(v.get("subCodes") or []):
        row = (
            f"  ({q(s['code'])}, {q(v['code'])}, {q(s['name'])}, "
            f"{q(s.get('addReq'))}, {q(s.get('note'))}, {jb(s.get('aliases'))}, {j})"
        )
        sub_rows.append(row)

out = "-- Moonshot: visa_data.json seed\n-- migrations/002_seed.sql\n-- 재실행 가능 (TRUNCATE → INSERT)\n\nBEGIN;\n\n"
out += "TRUNCATE visa_sub_codes, visas RESTART IDENTITY CASCADE;\n\n"
out += "INSERT INTO visas\n  (code, name, cat, period, new_req, ext_req, faq, data_badge, data_date, aliases, sort_order)\nVALUES\n"
out += ",\n".join(visa_rows) + ";\n\n"
out += "INSERT INTO visa_sub_codes\n  (code, parent_code, name, add_req, note, aliases, sort_order)\nVALUES\n"
out += ",\n".join(sub_rows) + ";\n\nCOMMIT;\n"

os.makedirs("migrations", exist_ok=True)
with open("migrations/002_seed.sql", "w", encoding="utf-8") as f:
    f.write(out)
print(f"Done: {len(visa_rows)} visas, {len(sub_rows)} sub_codes")
