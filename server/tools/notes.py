"""Notes tool.

MEMORY.md checklist: MCP Server tools -> notes.

A simple **in-memory** notes CRUD store. Unlike the database tool (which shows a
SQLite-backed store), this one keeps notes in a plain dict to demonstrate the
CRUD lifecycle -- Create, Read, Update, Delete -- with the least ceremony. State
lives for the lifetime of the server process only.
"""

from __future__ import annotations

from typing import Dict, List, Optional


class NoteNotFoundError(KeyError):
    """Raised when an operation references a note id that does not exist."""


class NotesStore:
    """An in-memory notes store with monotonically increasing integer ids."""

    def __init__(self) -> None:
        self._notes: Dict[int, str] = {}
        self._next_id = 1

    def create(self, text: str) -> int:
        """Create a note and return its id."""
        if not isinstance(text, str) or not text.strip():
            raise ValueError("note text must be a non-empty string")
        note_id = self._next_id
        self._notes[note_id] = text
        self._next_id += 1
        return note_id

    def read(self, note_id: int) -> str:
        """Return a single note's text, or raise :class:`NoteNotFoundError`."""
        if note_id not in self._notes:
            raise NoteNotFoundError(f"No note with id {note_id}")
        return self._notes[note_id]

    def list(self) -> List[Dict[str, object]]:
        """Return all notes as a list of ``{"id", "text"}`` dicts."""
        return [{"id": nid, "text": text} for nid, text in sorted(self._notes.items())]

    def update(self, note_id: int, text: str) -> None:
        """Replace the text of an existing note."""
        if note_id not in self._notes:
            raise NoteNotFoundError(f"No note with id {note_id}")
        if not isinstance(text, str) or not text.strip():
            raise ValueError("note text must be a non-empty string")
        self._notes[note_id] = text

    def delete(self, note_id: int) -> None:
        """Delete a note by id."""
        if note_id not in self._notes:
            raise NoteNotFoundError(f"No note with id {note_id}")
        del self._notes[note_id]


def register(mcp) -> None:
    """Expose the notes CRUD as MCP tools on the given FastMCP server.

    A single store instance is shared for the server's lifetime so state persists
    across calls within a session.
    """
    store = NotesStore()

    @mcp.tool()
    def notes_create(text: str) -> Dict[str, object]:
        """Create a note. Returns the new note's id and text."""
        note_id = store.create(text)
        return {"id": note_id, "text": text}

    @mcp.tool()
    def notes_list() -> List[Dict[str, object]]:
        """List all notes."""
        return store.list()

    @mcp.tool()
    def notes_read(note_id: int) -> Dict[str, object]:
        """Read a single note by id."""
        return {"id": note_id, "text": store.read(note_id)}

    @mcp.tool()
    def notes_update(note_id: int, text: str) -> Dict[str, object]:
        """Update an existing note's text."""
        store.update(note_id, text)
        return {"id": note_id, "text": text}

    @mcp.tool()
    def notes_delete(note_id: int) -> Dict[str, object]:
        """Delete a note by id."""
        store.delete(note_id)
        return {"deleted": note_id}
