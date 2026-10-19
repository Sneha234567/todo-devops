import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def page(client, url="/"):
    return client.get(url).get_data(as_text=True)


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_home_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"My To-Do List" in r.data


def test_add_task(client):
    client.post("/add", data={"title": "Learn Jenkins"})
    assert "Learn Jenkins" in page(client)


def test_empty_task_is_ignored(client):
    client.post("/add", data={"title": "   "})
    assert "No tasks yet" in page(client)


def test_toggle_and_delete(client):
    client.post("/add", data={"title": "Task A"})
    client.post("/done/1")
    assert "task p-medium done" in page(client)
    client.post("/delete/1")
    assert "Task A" not in page(client)


def test_category_priority_and_due_date(client):
    client.post("/add", data={"title": "Finish report", "category": "Work",
                              "priority": "High", "due_date": "2999-01-31"})
    html = page(client)
    assert "cat-work" in html and "pr-high" in html and "2999-01-31" in html


def test_invalid_values_fall_back_to_defaults(client):
    client.post("/add", data={"title": "Odd", "category": "Nope",
                              "priority": "Urgent", "due_date": "not-a-date"})
    html = page(client)
    assert "cat-personal" in html and "pr-medium" in html and "📅" not in html


def test_overdue_task_is_flagged(client):
    client.post("/add", data={"title": "Old", "due_date": "2000-01-01"})
    assert "overdue" in page(client)


def test_edit_task(client):
    client.post("/add", data={"title": "Draft"})
    client.post("/edit/1", data={"title": "Final", "category": "Study",
                                 "priority": "Low", "due_date": ""})
    html = page(client)
    assert "Final" in html and "cat-study" in html and "pr-low" in html


def test_filters(client):
    client.post("/add", data={"title": "Open one"})
    client.post("/add", data={"title": "Closed one"})
    client.post("/done/2")
    assert "Open one" in page(client, "/?filter=active")
    assert "Closed one" not in page(client, "/?filter=active")
    assert "Closed one" in page(client, "/?filter=completed")
    assert "Open one" not in page(client, "/?filter=completed")


def test_search_and_category_filter(client):
    client.post("/add", data={"title": "Buy milk", "category": "Personal"})
    client.post("/add", data={"title": "Write code", "category": "Work"})
    assert "Buy milk" in page(client, "/?q=milk")
    assert "Write code" not in page(client, "/?q=milk")
    assert "Write code" in page(client, "/?category=Work")
    assert "Buy milk" not in page(client, "/?category=Work")


def test_sort_by_priority(client):
    client.post("/add", data={"title": "LowTask", "priority": "Low"})
    client.post("/add", data={"title": "HighTask", "priority": "High"})
    html = page(client, "/?sort=priority")
    assert html.index("HighTask") < html.index("LowTask")


def test_clear_completed_and_progress(client):
    client.post("/add", data={"title": "A"})
    client.post("/add", data={"title": "B"})
    client.post("/done/1")
    assert "50% complete" in page(client)
    client.post("/clear-completed")
    html = page(client)
    assert "No matching" not in html and "task p-medium done" not in html


def test_html_is_escaped(client):
    client.post("/add", data={"title": "<script>alert(1)</script>"})
    assert "<script>alert(1)</script>" not in page(client)
