"""Tests for the notes tool: full CRUD lifecycle."""

import pytest

from server.tools.notes import NoteNotFoundError, NotesStore


def test_create_and_read():
    store = NotesStore()
    nid = store.create("first note")
    assert nid == 1
    assert store.read(1) == "first note"


def test_list_returns_all_sorted():
    store = NotesStore()
    store.create("a")
    store.create("b")
    assert store.list() == [{"id": 1, "text": "a"}, {"id": 2, "text": "b"}]


def test_update():
    store = NotesStore()
    nid = store.create("old")
    store.update(nid, "new")
    assert store.read(nid) == "new"


def test_delete():
    store = NotesStore()
    nid = store.create("temp")
    store.delete(nid)
    assert store.list() == []
    with pytest.raises(NoteNotFoundError):
        store.read(nid)


def test_read_missing_raises():
    store = NotesStore()
    with pytest.raises(NoteNotFoundError):
        store.read(999)


def test_create_rejects_empty():
    store = NotesStore()
    with pytest.raises(ValueError):
        store.create("   ")
