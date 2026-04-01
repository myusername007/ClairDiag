# ── Session Manager — in-memory state ───────────────────────────────────────
# Stocke les résultats du pipeline entre l'étape 1 (analyze) et l'étape 2 (revaluate).
# Pas de DB — dict en mémoire. Convient pour une instance unique (Railway/Docker).
#
# Clé : session_id (UUID généré côté serveur)
# TTL : 30 minutes (nettoyage automatique)

import uuid
import time
from typing import Optional

_TTL_SECONDS: int = 30 * 60  # 30 minutes

# Structure : session_id → {probs, symptoms, created_at}
_store: dict[str, dict] = {}


def create(probs: dict[str, float], symptoms: list[str]) -> str:
    """Crée une session et retourne le session_id."""
    _cleanup()
    session_id = str(uuid.uuid4())
    _store[session_id] = {
        "probs": dict(probs),
        "symptoms": list(symptoms),
        "created_at": time.time(),
    }
    return session_id


def get(session_id: str) -> Optional[dict]:
    """Retourne les données de session ou None si expirée/inexistante."""
    _cleanup()
    session = _store.get(session_id)
    if session is None:
        return None
    if time.time() - session["created_at"] > _TTL_SECONDS:
        del _store[session_id]
        return None
    return session


def delete(session_id: str) -> None:
    """Supprime une session."""
    _store.pop(session_id, None)


def _cleanup() -> None:
    """Supprime les sessions expirées."""
    now = time.time()
    expired = [sid for sid, s in _store.items() if now - s["created_at"] > _TTL_SECONDS]
    for sid in expired:
        del _store[sid]