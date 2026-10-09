import os
import sqlite3
from flask import Flask, render_template, request, redirect, url_for


def create_app(db_path=None):
    app = Flask(__name__)
    app.config["DB_PATH"] = db_path or os.environ.get("DB_PATH", "todo.db")

    def get_db():
        conn = sqlite3.connect(app.config["DB_PATH"])
        conn.row_factory = sqlite3.Row
        return conn

    def init_db():
        with get_db() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS tasks ("
                "id INTEGER PRIMARY KEY AUTOINCREMENT, "
                "title TEXT NOT NULL, "
                "done INTEGER NOT NULL DEFAULT 0)"
            )

    init_db()

    @app.route("/")
    def index():
        with get_db() as conn:
            tasks = conn.execute("SELECT * FROM tasks ORDER BY id DESC").fetchall()
        return render_template("index.html", tasks=tasks)

    @app.route("/add", methods=["POST"])
    def add():
        title = request.form.get("title", "").strip()
        if title:
            with get_db() as conn:
                conn.execute("INSERT INTO tasks (title) VALUES (?)", (title,))
        return redirect(url_for("index"))

    @app.route("/done/<int:task_id>", methods=["POST"])
    def done(task_id):
        with get_db() as conn:
            conn.execute(
                "UPDATE tasks SET done = 1 - done WHERE id = ?", (task_id,)
            )
        return redirect(url_for("index"))

    @app.route("/delete/<int:task_id>", methods=["POST"])
    def delete(task_id):
        with get_db() as conn:
            conn.execute("DELETE FROM tasks WHERE id = ?", (task_id,))
        return redirect(url_for("index"))

    @app.route("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
