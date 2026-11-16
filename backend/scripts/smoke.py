"""接口冒烟：容器内执行 python scripts/smoke.py。

覆盖登录、CSRF 头、首页聚合、待办、日记、食物、记账、档案与增量同步。
"""

import http.cookiejar
import json
import os
import sys
import urllib.error
import urllib.request

BASE = os.getenv("SMOKE_BASE", "http://127.0.0.1:8000")
PASSCODE = os.getenv("ADMIN_PASSWORD", "wb-local-2026")

jar = http.cookiejar.CookieJar()
opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(jar))

results: list[tuple[str, bool, str]] = []


def call(method: str, path: str, body=None, *, xhr: bool = True):
    data = json.dumps(body).encode() if body is not None else None
    request = urllib.request.Request(BASE + path, data=data, method=method)
    request.add_header("Content-Type", "application/json")
    if xhr:
        request.add_header("X-Requested-With", "XMLHttpRequest")
    try:
        with opener.open(request, timeout=15) as response:
            raw = response.read()
            return response.status, json.loads(raw) if raw else {}
    except urllib.error.HTTPError as exc:
        raw = exc.read()
        try:
            return exc.code, json.loads(raw) if raw else {}
        except json.JSONDecodeError:
            return exc.code, {}


def check(name: str, condition: bool, detail: str = "") -> None:
    results.append((name, bool(condition), detail))


def main() -> int:
    status, _ = call("POST", "/api/v1/auth/login", {"passcode": "definitely-wrong"})
    check("错误口令返回 401", status == 401, f"status={status}")

    status, _ = call("POST", "/api/v1/auth/login", {"passcode": PASSCODE}, xhr=False)
    check("缺少 X-Requested-With 被拒", status == 403, f"status={status}")

    status, body = call("POST", "/api/v1/auth/login", {"passcode": PASSCODE})
    check("正确口令登录成功", status == 200 and body.get("ok") is True, f"status={status}")

    status, body = call("GET", "/api/v1/auth/me")
    check("获取当前会话", status == 200 and body.get("owner") == "owner", str(body))

    status, body = call("GET", "/api/v1/dashboard/summary")
    todos = body.get("today_todos", [])
    system_keys = {t["system_key"] for t in todos if t.get("system_key")}
    check("首页聚合可用", status == 200 and "total_assets" in body, f"status={status}")
    check(
        "今日自动生成三条系统待办",
        system_keys == {"finance", "exercise", "diet"},
        f"keys={sorted(system_keys)}",
    )
    check("首页返回农历", bool(body.get("lunar")), str(body.get("lunar")))

    status, body = call("GET", "/api/v1/diaries/today")
    check(
        "日记标题为 ISO 周格式",
        status == 200 and "周" in body.get("title", "") and body.get("title", "").endswith(("一", "二", "三", "四", "五", "六", "日")),
        str(body.get("title")),
    )

    status, body = call("GET", "/api/v1/foods?q=%E7%B1%B3%E9%A5%AD")
    names = [item["name"] for item in body.get("items", [])]
    check("食物搜索命中米饭", status == 200 and "米饭" in names, f"names={names[:3]}")

    status, body = call("GET", "/api/v1/foods?q=mf")
    check(
        "拼音首字母搜索可用",
        status == 200 and any(item["name"] == "米饭" for item in body.get("items", [])),
        f"count={len(body.get('items', []))}",
    )

    status, body = call("GET", "/api/v1/finance/summary")
    check("记账汇总可用", status == 200 and "total_assets" in body, f"status={status}")

    status, body = call("GET", "/api/v1/finance/accounts")
    check("账户列表可用", status == 200 and len(body.get("items", [])) >= 4, f"count={len(body.get('items', []))}")

    status, body = call("GET", "/api/v1/profile")
    masked = body.get("id_card_masked", "")
    check("档案身份证脱敏", status == 200 and "*" in masked, masked)
    check("农历生日换算为公历", body.get("solar_birthday") == "1992-04-01", str(body.get("solar_birthday")))
    check("生肖为猴", body.get("zodiac") == "猴", str(body.get("zodiac")))

    status, body = call("GET", "/api/v1/sync/changes")
    check("增量同步可用", status == 200 and "changes" in body, f"status={status}")

    status, body = call("GET", "/api/v1/health/summary?start=2026-11-01&end=2026-11-30")
    check("健康汇总可用", status == 200 and "diet" in body, f"status={status}")

    status, body = call("GET", "/api/v1/entertainment")
    check("娱乐看板可用", status == 200 and "items" in body, f"status={status}")

    print("\n=== 冒烟结果 ===")
    failed = 0
    for name, ok, detail in results:
        mark = "PASS" if ok else "FAIL"
        if not ok:
            failed += 1
        print(f"[{mark}] {name}" + (f"  -> {detail}" if detail else ""))

    print(f"\n合计 {len(results)} 项，失败 {failed} 项")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
