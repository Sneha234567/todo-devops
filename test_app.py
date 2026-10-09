import pytest
from app import create_app


@pytest.fixture
def client(tmp_path):
    app = create_app(str(tmp_path / "test.db"))
    app.config["TESTING"] = True
    return app.test_client()


def test_health(client):
    assert client.get("/health").get_json() == {"status": "ok"}


def test_home_page_loads(client):
    r = client.get("/")
    assert r.status_code == 200
    assert b"My To-Do List" in r.data


def test_add_task(client):
    client.post("/add", data={"title": "Learn Jenkins"})
    assert b"Learn Jenkins" in client.get("/").data


def test_empty_task_is_ignored(client):
    client.post("/add", data={"title": "   "})
    assert b"No tasks yet" in client.get("/").data


def test_toggle_and_delete(client):
    client.post("/add", data={"title": "Task A"})
    client.post("/done/1")
    assert b'class="done"' in client.get("/").data
    client.post("/delete/1")
    assert b"Task A" not in client.get("/").data
