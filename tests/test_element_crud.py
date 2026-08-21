import os
import json
import tempfile
import shutil
from editor.element_crud import generate_new_id, rename_element_maps


class TestGenerateNewId:
    def test_returns_base_when_empty(self):
        assert generate_new_id("foo", []) == "foo"

    def test_appends_number_when_exists(self):
        assert generate_new_id("foo", ["foo"]) == "foo_1"

    def test_increments_number(self):
        assert generate_new_id("foo", ["foo", "foo_1"]) == "foo_2"

    def test_returns_base_when_no_collision(self):
        assert generate_new_id("bar", ["foo", "baz"]) == "bar"


class TestRenameElementMaps:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def _write_map(self, name, grid):
        data = {"grid": grid}
        with open(os.path.join(self.tmpdir, name), "w", encoding="utf-8") as f:
            json.dump(data, f)

    def _read_map(self, name):
        with open(os.path.join(self.tmpdir, name), "r", encoding="utf-8") as f:
            return json.load(f)

    def test_updates_references(self):
        self._write_map("m1.json", {"0,0": "old_id", "1,0": "other"})
        updated = rename_element_maps("old_id", "new_id", self.tmpdir)
        assert updated == 1
        data = self._read_map("m1.json")
        assert data["grid"]["0,0"] == "new_id"
        assert data["grid"]["1,0"] == "other"

    def test_no_update_when_no_match(self):
        self._write_map("m1.json", {"0,0": "something"})
        updated = rename_element_maps("old_id", "new_id", self.tmpdir)
        assert updated == 0

    def test_ignores_non_json(self):
        with open(os.path.join(self.tmpdir, "readme.txt"), "w") as f:
            f.write("old_id")
        updated = rename_element_maps("old_id", "new_id", self.tmpdir)
        assert updated == 0

    def test_handles_multiple_maps(self):
        self._write_map("m1.json", {"0,0": "old_id"})
        self._write_map("m2.json", {"0,0": "old_id"})
        updated = rename_element_maps("old_id", "new_id", self.tmpdir)
        assert updated == 2
