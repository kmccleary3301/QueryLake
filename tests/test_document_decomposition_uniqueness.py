from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from QueryLake.runtime.document_decomposition import (
    LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT,
    PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT,
    apply_segment_uniqueness_swap,
)


class _Result:
    def __init__(self, rows):
        self._rows = rows

    def one(self):
        return self._rows[0]

    def __iter__(self):
        return iter(self._rows)


class _Session:
    def __init__(self, *, nulls=0, duplicates=None, view_conflicts=None, missing=0, orphans=0, constraints=None):
        self.nulls = nulls
        self.duplicates = duplicates or []
        self.view_conflicts = view_conflicts or []
        self.missing = missing
        self.orphans = orphans
        self.constraints = constraints or [(LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT,)]
        self.exec_calls = []
        self.committed = False

    def exec(self, stmt):
        text = str(stmt)
        self.exec_calls.append(text)
        if 'WHERE segment_view_id IS NULL' in text:
            return _Result([(self.nulls,)])
        if 'HAVING COUNT(*) > 1' in text and 'view_alias' not in text:
            return _Result(self.duplicates)
        if 'HAVING COUNT(*) > 1' in text and 'view_alias' in text:
            return _Result(self.view_conflicts)
        if 'document_id IS NOT NULL AND authority_segment_id IS NULL' in text:
            return _Result([(self.missing,)])
        if 'WHERE c.document_id IS NOT NULL AND c.authority_segment_id IS NOT NULL AND s.id IS NULL' in text:
            return _Result([(self.orphans,)])
        if 'FROM pg_constraint' in text:
            return _Result(self.constraints)
        if 'SELECT COUNT(*) FROM document_segment' in text:
            return _Result([(5,)])
        return _Result([])

    def commit(self):
        self.committed = True


def test_apply_segment_uniqueness_swap_blocks_when_not_ready():
    session = _Session(nulls=2)
    payload = apply_segment_uniqueness_swap(session, dry_run=False)
    assert payload['action'] == 'blocked'
    assert payload['audit']['ready_for_constraint_swap'] is False
    assert session.committed is False


def test_apply_segment_uniqueness_swap_plans_and_applies_when_ready():
    session = _Session(constraints=[(LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT,)])
    plan = apply_segment_uniqueness_swap(session, dry_run=True)
    assert plan['action'] == 'plan_swap'
    assert plan['audit']['ready_for_constraint_swap'] is True
    applied = apply_segment_uniqueness_swap(session, dry_run=False)
    assert applied['action'] == 'applied'
    assert session.committed is True
    rendered = '\n'.join(session.exec_calls)
    assert f'DROP CONSTRAINT IF EXISTS {LEGACY_SEGMENT_UNIQUENESS_CONSTRAINT}' in rendered
    assert f'ADD CONSTRAINT {PROPOSED_SEGMENT_UNIQUENESS_CONSTRAINT}' in rendered
