from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.database import database_admin_operations, sql_db_tables


class _Result:
    def __init__(self, row):
        self._row = row

    def first(self):
        return self._row


class _DummySession:
    def __init__(self):
        self.rows = []

    def exec(self, stmt):
        return _Result(None)

    def delete(self, row):
        return None

    def add(self, row):
        self.rows.append(row)

    def commit(self):
        return None


class _Padding:
    system_instruction_wrap = "sys"
    context_wrap = "ctx"
    question_wrap = "q"
    response_wrap = "r"


class _Model:
    def __init__(self, system_path=None, source="remote:demo"):
        self.id = "m1"
        self.name = "model"
        self.system_path = system_path
        self.source = source
        self.default_parameters = {}
        self.padding = _Padding()
        self.default_system_instruction = ""


def test_add_models_to_database_falls_back_to_source_when_system_path_missing():
    db = _DummySession()
    database_admin_operations.add_models_to_database(db, [_Model(system_path=None, source="hf/demo")])
    assert len(db.rows) == 1
    assert db.rows[0].path_on_server == "hf/demo"


def test_add_models_to_database_uses_unconfigured_when_path_and_source_missing():
    db = _DummySession()
    database_admin_operations.add_models_to_database(db, [_Model(system_path=None, source=None)])
    assert db.rows[0].path_on_server == "unconfigured"
