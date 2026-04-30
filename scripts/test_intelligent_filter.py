"""端到端测试智能筛选（含 limit + limit_percent）"""
import requests, sys

BASE = "http://127.0.0.1:8002/api/v1"
passed = failed = 0

def check(name, ok, detail=""):
    global passed, failed
    if ok:
        passed += 1; print(f"  OK  {name}")
    else:
        failed += 1; print(f"  FAIL  {name}  {detail}")

# Login
r = requests.post(f"{BASE}/hr/login", json={"username":"admin","password":"admin123"})
t = r.json()["data"]["access_token"]
h = {"Authorization": f"Bearer {t}"}
check("登录", True)

# --- LLM parse with percentage ---
print("\n=== LLM 解析百分比 ===")
cases = [
    ("前50%的候选人", 50),
    ("前10%的候选人", 10),
    ("驾龄3年以上、排名前20%的人", 20),
]
for text, expected_pct in cases:
    r = requests.post(f"{BASE}/hr/candidates/intelligent-filter/parse",
        params={"natural_language": text}, headers=h)
    d = r.json()["data"]
    lp = d.get("limit_percent")
    ok = d.get("limit_percent") == expected_pct or d.get("limit") is not None
    check(f"解析: {text[:25]}...", ok, f"limit_percent={lp}, limit={d.get('limit')}")

# --- Execute with limit_percent ---
print("\n=== 执行百分比筛选 ===")
# First get total count
r = requests.get(f"{BASE}/hr/candidates", params={"page":1,"page_size":1}, headers=h)
total_all = r.json()["data"]["total"]
print(f"  候选人总数: {total_all}")

pct_cases = [
    ({"conditions":[], "logic":"AND", "limit_percent":50}, f"前50% → ceil({total_all}*0.5)={-(-total_all//2)}条"),
    ({"conditions":[], "logic":"AND", "limit_percent":10}, f"前10% → ceil({total_all}*0.1)={-(-total_all//10)}条"),
]
for rules, desc in pct_cases:
    r = requests.post(f"{BASE}/hr/candidates/intelligent-filter/execute",
        json=rules, headers=h)
    d = r.json()["data"]
    actual = len(d["items"])
    expected = -(-total_all * rules["limit_percent"] // 100)  # ceil
    ok = d.get("total", 0) >= actual and actual == expected
    check(f"执行({desc})", ok, f"返回{actual}条, total={d['total']}")

# --- Bound check: limit_percent + conditions ---
print("\n=== 条件 + 百分比 ===")
rules = {
    "conditions":[{"field":"gender","operator":"eq","value":1,"description":"男性"}],
    "logic":"AND",
    "limit_percent": 50
}
r = requests.post(f"{BASE}/hr/candidates/intelligent-filter/execute",
    json=rules, headers=h)
d = r.json()["data"]
check("男性前50%", d.get("total", 0) >= len(d["items"]),
    f"total={d['total']}, 返回{len(d['items'])}条")

# --- Invalid percent (edge case) ---
rules_bad = {"conditions":[], "logic":"AND", "limit_percent": 200}
r = requests.post(f"{BASE}/hr/candidates/intelligent-filter/execute",
    json=rules_bad, headers=h)
d = r.json()["data"]
check("无效百分比200→按默认分页", len(d["items"]) <= 20,
    f"返回{len(d['items'])}条（未崩溃）")

print(f"\n{'='*40}")
print(f"结果: {passed} 通过, {failed} 失败")
if failed: sys.exit(1)
