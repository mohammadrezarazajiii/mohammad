from flask import Flask, request, redirect, url_for, session, render_template_string
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = "change-this-secret-key"
DATABASE = "money_manager.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.execute("""
        CREATE TABLE IF NOT EXISTS savings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            amount REAL NOT NULL,
            description TEXT,
            date TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()
    conn.close()


LOGIN_PAGE = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ورود</title>
<style>
body{font-family:Tahoma;background:#111827;color:white;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:#1f2937;padding:30px;width:320px;border-radius:15px}
input,button{width:100%;box-sizing:border-box;padding:12px;margin-top:10px;border:0;border-radius:8px}
button{background:#2563eb;color:white}
a{color:#60a5fa}.error{color:#f87171}
</style>
</head>
<body>
<div class="box">
<h2>ورود به حساب</h2>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post">
<input name="username" placeholder="نام کاربری" required>
<input type="password" name="password" placeholder="رمز عبور" required>
<button>ورود</button>
</form>
<p>حساب ندارید؟ <a href="/register">ثبت نام</a></p>
</div>
</body>
</html>
"""


REGISTER_PAGE = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>ثبت نام</title>
<style>
body{font-family:Tahoma;background:#111827;color:white;display:flex;justify-content:center;align-items:center;min-height:100vh}
.box{background:#1f2937;padding:30px;width:320px;border-radius:15px}
input,button{width:100%;box-sizing:border-box;padding:12px;margin-top:10px;border:0;border-radius:8px}
button{background:#16a34a;color:white}
a{color:#60a5fa}.error{color:#f87171}
</style>
</head>
<body>
<div class="box">
<h2>ساخت حساب</h2>
{% if error %}<p class="error">{{ error }}</p>{% endif %}
<form method="post">
<input name="username" placeholder="نام کاربری" required>
<input type="password" name="password" placeholder="رمز عبور" required>
<button>ساخت حساب</button>
</form>
<p><a href="/login">بازگشت به ورود</a></p>
</div>
</body>
</html>
"""


DASHBOARD_PAGE = """
<!doctype html>
<html lang="fa" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>مدیریت مالی</title>
<style>
body{font-family:Tahoma;background:#0f172a;color:white;margin:0}
.container{max-width:1000px;margin:auto;padding:20px}
.header{display:flex;justify-content:space-between;align-items:center}
.logout{background:#dc2626;color:white;padding:10px 15px;border-radius:8px;text-decoration:none}
.cards{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:15px;margin-top:20px}
.card,.box{background:#1e293b;padding:20px;border-radius:15px}
.cards p{font-size:20px}
.income{color:#4ade80}.expense{color:#f87171}.saving{color:#60a5fa}.balance{color:#facc15}
.forms{display:grid;grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:20px;margin-top:25px}
input,select,button{width:100%;box-sizing:border-box;padding:11px;margin-top:8px;border:0;border-radius:8px}
button{background:#2563eb;color:white}
table{width:100%;margin-top:20px;border-collapse:collapse;background:#1e293b}
th,td{padding:10px;border-bottom:1px solid #334155;text-align:center}
.delete{color:#f87171}
</style>
</head>
<body>
<div class="container">
<div class="header"><h1>مدیریت مالی</h1><a class="logout" href="/logout">خروج</a></div>
<p>کاربر: <strong>{{ username }}</strong></p>

<div class="cards">
<div class="card"><h3>کل درآمد</h3><p class="income">{{ "{:,.0f}".format(total_income) }}</p></div>
<div class="card"><h3>کل هزینه</h3><p class="expense">{{ "{:,.0f}".format(total_expense) }}</p></div>
<div class="card"><h3>کل پس‌انداز</h3><p class="saving">{{ "{:,.0f}".format(total_saving) }}</p></div>
<div class="card"><h3>موجودی</h3><p class="balance">{{ "{:,.0f}".format(balance) }}</p></div>
</div>

<div class="forms">
<div class="box">
<h2>ثبت درآمد / هزینه</h2>
<form method="post" action="/add_transaction">
<select name="type">
<option value="income">درآمد</option>
<option value="expense">هزینه</option>
</select>
<input type="number" name="amount" placeholder="مبلغ" min="1" required>
<input name="description" placeholder="توضیحات">
<button>ثبت</button>
</form>
</div>

<div class="box">
<h2>ثبت پس‌انداز</h2>
<form method="post" action="/add_saving">
<input type="number" name="amount" placeholder="مبلغ پس‌انداز" min="1" required>
<input name="description" placeholder="توضیحات">
<button>ثبت پس‌انداز</button>
</form>
</div>
</div>

<h2>تراکنش‌ها</h2>
<table>
<tr><th>نوع</th><th>مبلغ</th><th>توضیحات</th><th>تاریخ</th><th>حذف</th></tr>
{% for item in transactions %}
<tr>
<td>{% if item["type"]=="income" %}<span class="income">درآمد</span>{% else %}<span class="expense">هزینه</span>{% endif %}</td>
<td>{{ "{:,.0f}".format(item["amount"]) }}</td>
<td>{{ item["description"] or "-" }}</td>
<td>{{ item["date"] }}</td>
<td><a class="delete" href="/delete_transaction/{{ item['id'] }}">حذف</a></td>
</tr>
{% endfor %}
</table>

<h2>پس‌اندازها</h2>
<table>
<tr><th>مبلغ</th><th>توضیحات</th><th>تاریخ</th><th>حذف</th></tr>
{% for item in savings %}
<tr>
<td>{{ "{:,.0f}".format(item["amount"]) }}</td>
<td>{{ item["description"] or "-" }}</td>
<td>{{ item["date"] }}</td>
<td><a class="delete" href="/delete_saving/{{ item['id'] }}">حذف</a></td>
</tr>
{% endfor %}
</table>
</div>
</body>
</html>
"""


@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username = ?", (username,)
        ).fetchone()
        conn.close()

        if user and check_password_hash(user["password"], password):
            session["user_id"] = user["id"]
            session["username"] = user["username"]
            return redirect(url_for("dashboard"))

        return render_template_string(
            LOGIN_PAGE, error="نام کاربری یا رمز عبور اشتباه است."
        )

    return render_template_string(LOGIN_PAGE, error=None)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"].strip()
        password = request.form["password"]

        if len(username) < 3:
            return render_template_string(
                REGISTER_PAGE, error="نام کاربری حداقل ۳ حرف باشد."
            )

        if len(password) < 4:
            return render_template_string(
                REGISTER_PAGE, error="رمز عبور حداقل ۴ کاراکتر باشد."
            )

        conn = get_db()
        try:
            conn.execute(
                "INSERT INTO users (username, password) VALUES (?, ?)",
                (username, generate_password_hash(password))
            )
            conn.commit()
        except sqlite3.IntegrityError:
            conn.close()
            return render_template_string(
                REGISTER_PAGE, error="این نام کاربری قبلاً استفاده شده است."
            )
        conn.close()
        return redirect(url_for("login"))

    return render_template_string(REGISTER_PAGE, error=None)


@app.route("/dashboard")
def dashboard():
    if "user_id" not in session:
        return redirect(url_for("login"))

    user_id = session["user_id"]
    conn = get_db()

    total_income = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='income'",
        (user_id,)
    ).fetchone()[0]

    total_expense = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM transactions WHERE user_id=? AND type='expense'",
        (user_id,)
    ).fetchone()[0]

    total_saving = conn.execute(
        "SELECT COALESCE(SUM(amount),0) FROM savings WHERE user_id=?",
        (user_id,)
    ).fetchone()[0]

    transactions = conn.execute(
        "SELECT * FROM transactions WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchall()

    savings = conn.execute(
        "SELECT * FROM savings WHERE user_id=? ORDER BY id DESC",
        (user_id,)
    ).fetchall()

    conn.close()

    return render_template_string(
        DASHBOARD_PAGE,
        username=session["username"],
        total_income=total_income,
        total_expense=total_expense,
        total_saving=total_saving,
        balance=total_income - total_expense - total_saving,
        transactions=transactions,
        savings=savings
    )


@app.route("/add_transaction", methods=["POST"])
def add_transaction():
    if "user_id" not in session:
        return redirect(url_for("login"))

    transaction_type = request.form["type"]
    amount = float(request.form["amount"])
    description = request.form.get("description", "")

    if transaction_type not in ("income", "expense") or amount <= 0:
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute(
        """INSERT INTO transactions
        (user_id, type, amount, description)
        VALUES (?, ?, ?, ?)""",
        (session["user_id"], transaction_type, amount, description)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/add_saving", methods=["POST"])
def add_saving():
    if "user_id" not in session:
        return redirect(url_for("login"))

    amount = float(request.form["amount"])
    description = request.form.get("description", "")

    if amount <= 0:
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute(
        """INSERT INTO savings
        (user_id, amount, description)
        VALUES (?, ?, ?)""",
        (session["user_id"], amount, description)
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/delete_transaction/<int:item_id>")
def delete_transaction(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM transactions WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/delete_saving/<int:item_id>")
def delete_saving(item_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = get_db()
    conn.execute(
        "DELETE FROM savings WHERE id=? AND user_id=?",
        (item_id, session["user_id"])
    )
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000)
