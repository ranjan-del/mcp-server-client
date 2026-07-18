"""Tests for the database tool: insert, query and injection-safety."""

from server.tools.database import RecordsDB


def test_insert_and_query_all():
    db = RecordsDB()  # in-memory
    id1 = db.insert("fruit", "apple")
    id2 = db.insert("fruit", "banana")
    id3 = db.insert("veg", "carrot")
    assert [id1, id2, id3] == [1, 2, 3]

    rows = db.query()
    assert len(rows) == 3
    assert rows[0] == {"id": 1, "category": "fruit", "content": "apple"}


def test_query_by_category():
    db = RecordsDB()
    db.insert("fruit", "apple")
    db.insert("veg", "carrot")
    fruit = db.query("fruit")
    assert len(fruit) == 1
    assert fruit[0]["content"] == "apple"


def test_count():
    db = RecordsDB()
    assert db.count() == 0
    db.insert("a", "1")
    db.insert("a", "2")
    assert db.count() == 2


def test_parameterized_query_is_injection_safe():
    db = RecordsDB()
    db.insert("fruit", "apple")
    # A malicious "category" must be treated as a literal string, not SQL. If it
    # were interpolated, the table would be dropped; instead we just get 0 rows.
    malicious = "fruit'; DROP TABLE records; --"
    assert db.query(malicious) == []
    # Table still intact and original row still present.
    assert db.count() == 1
