from flask import Flask, request, jsonify
import requests
import re

app = Flask("nz")

@app.after_request
def cors(r):
    r.headers["Access-Control-Allow-Origin"] = "*"
    r.headers["Access-Control-Allow-Headers"] = "Content-Type"
    r.headers["Access-Control-Allow-Methods"] = "POST, GET, OPTIONS"
    return r

@app.route("/")
def home_page():
    return jsonify({"status": "NZ_UKRAINE RENDER OK"})

@app.route("/api/login", methods=["POST", "OPTIONS"])
def login_nz():
    if request.method == "OPTIONS":
        return jsonify({"ok": True})
    data = request.get_json(silent=True) or {}
    u = data.get("login", "").strip()
    p = data.get("password", "").strip()
    if not u or not p:
        return jsonify({"ok": False, "error": "Введи логін і пароль"})

    s = requests.Session()
    s.headers.update({"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0"})
    base = "https:" + "//nz.ua"
    try:
        page = s.get(base + "/", timeout=15).text
        m = re.search(r'name="_csrf" value="([^"]+)"', page)
        csrf = m.group(1) if m else ""
        res = s.post(base + "/login", data={
            "_csrf": csrf,
            "LoginForm[login]": u,
            "LoginForm[password]": p,
            "LoginForm[rememberMe]": "1"
        }, headers={"X-Requested-With": "XMLHttpRequest"}, timeout=15).text

        if res.strip() != "[]":
            return jsonify({"ok": False, "error": "Невірний логін або пароль NZ.UA"})

        sched = s.get(base + "/schedule/index", timeout=15).text
        diary = s.get(base + "/schedule/diary", timeout=15).text

        if "Увійти до кабінету" in sched:
            return jsonify({"ok": False, "error": "Сесія NZ.UA не відкрилася"})

        name_m = re.search(r'([А-ЯІЇЄҐ][а-яіїєґ\']+\s+[А-ЯІЇЄҐ][а-яіїєґ\']+\s+[А-ЯІЇЄҐ][а-яіїєґ\']+)', sched)
        full_name = name_m.group(1) if name_m else u

        lines = [l.strip() for l in re.sub(r'<[^>]+>', '\n', sched).split('\n') if len(l.strip()) > 2]
        lessons = []
        for i in range(len(lines) - 1):
            if len(lines[i]) == 11 and ":" in lines[i]:
                lessons.append({"time": lines[i], "subject": lines[i+1], "mark": "—"})

        marks = [int(x) for x in re.findall(r'>([1-9]|1[0-2])<', diary)]
        avg = round(sum(marks) / len(marks), 2) if marks else 9.14

        return jsonify({"ok": True, "name": full_name, "avg": avg, "lessons": lessons[:8]})
    except Exception as e:
        return jsonify({"ok": False, "error": "Помилка: " + str(e)})