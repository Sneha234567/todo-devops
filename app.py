import os
import sqlite3
from contextlib import contextmanager
from datetime import date

from flask import Flask, render_template, request, redirect, url_for

CATEGORIES = ["Personal", "Work", "Study", "Health", "Other"]
PRIORITIES = ["High", "Medium", "Low"]


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "todo.db")

    @contextmanager
    def db():
        conn = sqlite3.connect(app.config["DB_PATH"])
        conn.row_factory = sqlite3.Row
        try:
            yield conn
            conn.commit()
        finally:
            conn.close()

    def init_db():
        with db() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL, "
                "done INTEGER NOT NULL DEFAULT 0, "
                "category TEXT NOT NULL DEFAULT 'Personal', "
                "priority TEXT NOT NULL DEFAULT 'Medium', "
                "due_date TEXT)"
            )
            # Upgrade databases created by the first version of the app
            existing = {r["name"] for r in conn.execute("PRAGMA table_info(tasks)")}
            upgrades = {
                "category": "TEXT NOT NULL DEFAULT 'Personal'",
                "priority": "TEXT NOT NULL DEFAULT 'Medium'",
                "due_date": "TEXT",
            }
            for column, ddl in upgrades.items():
                if column not in existing:
                    conn.execute(f"ALTER TABLE tasks ADD COLUMN {column} {ddl}")

    init_db()

    def clean_fields(form):
        title = form.get("title", "").strip()[:200]
        category = form.get("category", "Personal")
        if category not in CATEGORIES:
            category = "Personal"
        priority = form.get("priority", "Medium")
        if priority not in PRIORITIES:
            priority = "Medium"
        due = form.get("due_date", "").strip()
        try:
            date.fromisoformat(due)
        except ValueError:
            due = None
        return title, category, priority, due

    @app.route("/")
    def index():
        flt = request.args.get("filter", "all")
        category = request.args.get("category", "")
        q = request.args.get("q", "").strip()
        sort = request.args.get("sort", "newest")
        today = date.today().isoformat()

        sql = "SELECT * FROM tasks WHERE 1=1"
        params = []
        if flt == "active":
            sql += " AND done = 0"
        elif flt == "completed":
            sql += " AND done = 1"
        if category in CATEGORIES:
            sql += " AND category = ?"
            params.append(category)
        if q:
            sql += " AND title LIKE ?"
            params.append(f"%{q}%")

        if sort == "priority":
            sql += (" ORDER BY done, CASE priority WHEN 'High' THEN 0 "
                    "WHEN 'Medium' THEN 1 ELSE 2 END, id DESC")
        elif sort == "due":
            sql += " ORDER BY done, due_date IS NULL, due_date, id DESC"
        else:
            sql += " ORDER BY id DESC"

        with db() as conn:
            tasks = conn.execute(sql, params).fetchall()
            total = conn.execute("SELECT COUNT(*) FROM tasks").fetchone()[0]
            done = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE done = 1").fetchone()[0]
            overdue = conn.execute(
                "SELECT COUNT(*) FROM tasks WHERE done = 0 "
                "AND due_date IS NOT NULL AND due_date < ?", (today,)
            ).fetchone()[0]

        percent = int(done * 100 / total) if total else 0
        return render_template(
            "index.html",
            tasks=tasks, total=total, done=done, active=total - done,
            overdue=overdue, percent=percent, today=today,
            flt=flt, category=category, q=q, sort=sort,
            categories=CATEGORIES, priorities=PRIORITIES,
        )

    @app.route("/add", methods=["POST"])
    def add():
        title, category, priority, due = clean_fields(request.form)
        if title:
            with db() as conn:
                conn.execute(
                    "INSERT INTO tasks (title, category, priority, due_date) "
                    "VALUES (?, ?, ?, ?)", (title, category, priority, due))
        return redirect(url_for("index"))

    @app.route("/edit/<int:task_id>", methods=["POST"])
    def edit(task_id):
        title, category, priority, due = clean_fields(request.form)
        if title:
            with db() as conn:
                conn.execute(
                    "UPDATE tasks SET title = ?, category = ?, priority = ?, "
                    "due_date = ? WHERE id = ?",
                    (title, category, priority, due, task_id))
        return redirect(url_for("index"))

    @app.route("/done/<int:task_id>", methods=["POST"])
    def done(task_id):
        with db() as conn:
            conn.execute("UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,))
        return redirect(url_for("index"))

    @app.route("/delete/<int:task_id>", methods=["POST"])
    def delete(task_id):
        with db() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return redirect(url_for("index"))

    @app.route("/clear-completed", methods=["POST"])
    def clear_completed():
        with db() as conn:
            conn.execute("DELETE FROM tasks WHERE done = 1")
        return redirect(url_for("index"))

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
