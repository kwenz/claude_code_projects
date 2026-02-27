import uuid
from typing import Dict, Any, Optional


_store: Dict[str, Dict[str, Any]] = {}


def create_session() -> str:
    session_id = str(uuid.uuid4())
    _store[session_id] = {
        "sections": [],
        "raw_text": "",
        "file_name": "",
        "analysis": None,
        "enhanced": None,
    }
    return session_id


def get_session(session_id: str) -> Optional[Dict[str, Any]]:
    return _store.get(session_id)


def update_session(session_id: str, **kwargs) -> None:
    if session_id not in _store:
        raise KeyError(f"Session {session_id} not found")
    _store[session_id].update(kwargs)


def delete_session(session_id: str) -> None:
    _store.pop(session_id, None)
