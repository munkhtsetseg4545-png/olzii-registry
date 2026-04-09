"""
Төрийн байгууллагын гишүүдийн бүртгэл
Ажиллуулах: python app.py
Нээх: http://localhost:5000
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3, os
from datetime import date, datetime

app = Flask(__name__)
DB = os.path.join(os.path.dirname(__file__), "members.db")


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


# ── Helpers ──────────────────────────────────────────────────────────────────

def days_until_birthday(bday_str: str) -> int:
    """Төрсөн өдрийг хүртэл хэдэн өдөр үлдсэнийг тооцно."""
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


# ── Routes ────────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


@app.route("/api/members", methods=["GET"])
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
    # Sort upcoming birthdays
    upcoming = sorted([m for m in members if m["days_until"] <= 30], key=lambda x: x["days_until"])
    return jsonify({"members": members, "upcoming": upcoming, "total": len(members)})


@app.route("/api/members", methods=["POST"])
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
def delete_member(mid):
    with get_db() as conn:
        conn.execute("DELETE FROM members WHERE id=?", (mid,))
        conn.commit()
    return jsonify({"ok": True})


@app.route("/api/stats")
def stats():
    today = date.today()
    with get_db() as conn:
        total   = conn.execute("SELECT COUNT(*) FROM members").fetchone()[0]
        rows    = conn.execute("SELECT birthday FROM members").fetchall()
    this_month = sum(1 for r in rows if datetime.strptime(r[0], "%Y-%m-%d").month == today.month)
    soon       = sum(1 for r in rows if days_until_birthday(r[0]) <= 7)
    return jsonify({"total": total, "this_month": this_month, "soon": soon})


if __name__ == "__main__":
    init_db()
    print("\n✅  Сервер эхэллээ →  http://localhost:5000\n")
    app.run(debug=True, port=5000)
