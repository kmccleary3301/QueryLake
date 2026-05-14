from scripts.document_decomposition_frontier_lane_status import collect_frontier_lane_status


class _Rows(list):
    def all(self):
        return list(self)


class _FakeDB:
    def exec(self, _stmt):
        return _Rows([
            ("default_local_text", 5, 2),
            ("table_native", 0, 0),
            ("semantic_text", 3, 1),
        ])


def test_frontier_lane_status_demotes_absent_materializations():
    payload = collect_frontier_lane_status(_FakeDB())
    lanes = {row["public_view"]: row for row in payload["lanes"]}
    assert lanes["canonical_segment"]["status"] == "materialized"
    assert lanes["semantic_segment"]["status"] == "materialized"
    assert lanes["table"]["status"] == "demoted_absent_materialization"
    assert lanes["table"]["blocker"] == "no_current_segment_view_materialization:table_native"
