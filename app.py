"""
Хүслийн зүй ТББ — Гишүүдийн бүртгэл
Нэвтрэх: admin / admin4545
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, session
import sqlite3, os
from datetime import date, datetime
from functools import wraps

app = Flask(__name__)
app.secret_key = "khusliinzui2026secretkey"
DB = os.path.join(os.path.dirname(__file__), "members.db")

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin4545"


def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    with get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS members (
                id       INTEGER PRIMARY KEY AUTOINCREMENT,
                name     TEXT    NOT NULL,
                phone    TEXT    NOT NULL,
                birthday TEXT    NOT NULL,
                position TEXT,
                dept     TEXT,
                created  TEXT    DEFAULT (date('now'))
            )
        """)
        conn.commit()


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


def days_until_birthday(bday_str):
    try:
        bday = datetime.strptime(bday_str, "%Y-%m-%d").date()
        today = date.today()
        next_bday = bday.replace(year=today.year)
        if next_bday < today:
            next_bday = bday.replace(year=today.year + 1)
        return (next_bday - today).days
    except Exception:
        return 999


def enrich(row):
    d = dict(row)
    d["days_until"] = days_until_birthday(d["birthday"])
    try:
        dt = datetime.strptime(d["birthday"], "%Y-%m-%d")
        mn_months = ["1","2","3","4","5","6","7","8","9","10","11","12"]
        d["bday_display"] = f"{mn_months[dt.month-1]}-р сарын {dt.day}"
    except Exception:
        d["bday_display"] = d["birthday"]
    return d


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("index"))
        else:
            error = "Нэвтрэх нэр эсвэл нууц үг буруу байна"
    return render_template("login.html", error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    return render_template("index.html")


@app.route("/api/members", methods=["GET"])
@login_required
def list_members():
    q = request.args.get("q", "").strip()
    with get_db() as conn:
        if q:
            rows = conn.execute(
                "SELECT * FROM members WHERE name LIKE ? OR phone LIKE ? OR position LIKE ? OR dept LIKE ? ORDER BY name",
                (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%")
            ).fetchall()
        else:
            rows = conn.execute("SELECT * FROM members ORDER BY name").fetchall()
    members = [enrich(r) for r in rows]
    upcoming = sorted([m for m in members if m["days_until"] <= 30], key=lambda x: x["days_until"])
    return jsonify({"members": members, "upcoming": upcoming, "total": len(members)})


@app.route("/api/members", methods=["POST"])
@login_required
def add_member():
    data = request.json
    name     = (data.get("name")     or "").strip()
    phone    = (data.get("phone")    or "").strip()
    birthday = (data.get("birthday") or "").strip()
    position = (data.get("position") or "").strip()
    dept     = (data.get("dept")     or "").strip()
    if not name or not phone or not birthday:
        return jsonify({"error": "Нэр, утас, төрсөн өдөр заавал шаардлагатай"}), 400
    with get_db() as conn:
        cur = conn.execute(
            "INSERT INTO members (name, phone, birthday, position, dept) VALUES (?,?,?,?,?)",
            (name, phone, birthday, position, dept)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM members WHERE id=?", (cur.lastrowid,)).fetchone()
    return jsonify(enrich(row)), 201


@app.route("/api/members/<int:mid>", methods=["PUT"])
@login_required
def update_member(mid):
    data = request.json
    name     = (data.get("name")     or "").strip()
    phone    = (data.get("phone")    or "").strip()
    birthday = (data.get("birthday") or "").strip()
    position = (data.get("position") or "").strip()
    dept     = (data.get("dept")     or "").strip()
    if not name or not phone or not birthday:
        return jsonify({"error": "Нэр, утас, төрсөн өдөр заавал шаардлагатай"}), 400
    with get_db() as conn:
        conn.execute(
            "UPDATE members SET name=?, phone=?, birthday=?, position=?, dept=? WHERE id=?",
            (name, phone, birthday, position, dept, mid)
        )
        conn.commit()
        row = conn.execute("SELECT * FROM members WHERE id=?", (mid,)).fetchone()
    if not row:
        return jsonify({"error": "Олдсонгүй"}), 404
    return jsonify(enrich(row))


@app.route("/api/members/<int:mid>", methods=["DELETE"])
@login_required
def delete_member(mid):
    with get_db() as conn:
        conn.execute("DELETE FROM members WHERE id=?", (mid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/stats")
@login_required
def stats():
    today = date.today()
    with get_db() as conn:
        total = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        rows  = conn.execute("SELECT birthday FROM members").fetchall()
    this_month = sum(1 for r in rows if datetime.strptime(r[0], "%Y-%m-%d").month == today.month)
    soon       = sum(1 for r in rows if days_until_birthday(r[0]) <= 7)
    return jsonify({"total": total, "this_month": this_month, "soon": soon})


@app.route("/register")
def register_page():
    return render_template("register.html")

@app.route("/api/register", methods=["POST"])
def api_register():
    data = request.json
    name     = (data.get("name")     or "").strip()
    phone    = (data.get("phone")    or "").strip()
    birthday = (data.get("birthday") or "").strip()
    position = (data.get("position") or "").strip()
    dept     = (data.get("dept")     or "").strip()
    if not name or not phone or not birthday:
        return jsonify({"error": "Нэр, утас, төрсөн өдөр заавал шаардлагатай"}), 400
    with get_db() as conn:
        conn.execute(
            "INSERT INTO members (name, phone, birthday, position, dept) VALUES (?,?,?,?,?)",
            (name, phone, birthday, position, dept)
        )
        conn.commit()
    return jsonify({"ok": True}), 201
if __name__ == "__main__":
    init_db()
    print("\n✅  Сервер эхэллээ →  http://localhost:5000\n")
    app.run(debug=False, host="0.0.0.0", port=int(os.environ.get("PORT", 5000)))
