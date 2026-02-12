from __future__ import annotations

import sys
from pathlib import Path

BACKEND_PATH = Path(__file__).resolve().parents[2] / "backend"
if str(BACKEND_PATH) not in sys.path:
    sys.path.append(str(BACKEND_PATH))


def get_dbf_manager():
    from services.dbf_manager_service import get_dbf_manager_instance

    return get_dbf_manager_instance()


def get_bpa_database():
    from database import BPADatabase

    return BPADatabase()
