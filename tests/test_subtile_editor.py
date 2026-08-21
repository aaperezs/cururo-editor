from editor.subtile_editor import update_subtile_z, update_subtile_behavior


class FakeSetSubtile:
    def __init__(self):
        self.calls = []

    def __call__(self, eid, col, row, data):
        self.calls.append((eid, col, row, data))


class TestUpdateSubtileZ:
    def test_valid_z(self):
        fn = FakeSetSubtile()
        assert update_subtile_z("el1", 0, 1, "5", fn) is True
        assert fn.calls == [("el1", 0, 1, {"z": 5})]

    def test_empty_text(self):
        fn = FakeSetSubtile()
        assert update_subtile_z("el1", 0, 1, "", fn) is True
        assert fn.calls == [("el1", 0, 1, {"z": 0})]

    def test_invalid_text(self):
        fn = FakeSetSubtile()
        assert update_subtile_z("el1", 0, 1, "abc", fn) is False
        assert fn.calls == []


class TestUpdateSubtileBehavior:
    def test_sets_behavior(self):
        fn = FakeSetSubtile()
        update_subtile_behavior("el1", 2, 3, "destruible", fn)
        assert fn.calls == [("el1", 2, 3, {"behavior": "destruible"})]
