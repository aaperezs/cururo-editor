import os
import json
import tempfile
import shutil
from unittest.mock import patch, MagicMock
from editor.item_crud import (
    create_new_item, clone_item, delete_item_by_id,
    rename_item_with_refs, _update_elementos_refs, _update_stack_refs,
)


class TestCreateNewItem:
    @patch("editor.item_crud.get_all_items", return_value=[])
    @patch("editor.item_crud.create_item")
    def test_creates_with_base_id(self, mock_create, mock_all):
        iid = create_new_item()
        assert iid == "item_nuevo"
        mock_create.assert_called_once_with("item_nuevo")

    @patch("editor.item_crud.get_all_items", return_value=["item_nuevo"])
    @patch("editor.item_crud.create_item")
    def test_appends_number(self, mock_create, mock_all):
        iid = create_new_item()
        assert iid == "item_nuevo_1"


class TestCloneItem:
    @patch("editor.item_crud.get_item", return_value=None)
    def test_returns_none_if_not_found(self, _):
        assert clone_item("nonexistent") is None

    @patch("editor.item_crud.get_item")
    @patch("editor.item_crud.get_all_items", return_value=[])
    @patch("editor.item_crud.set_item")
    def test_clones_with_copia_suffix(self, mock_set, mock_all, mock_get):
        mock_get.return_value = {"nombre": "sword"}
        iid = clone_item("item1")
        assert iid == "item1_copia"
        mock_set.assert_called_once()


class TestDeleteItemById:
    @patch("editor.item_crud.delete_item")
    def test_calls_delete(self, mock_del):
        delete_item_by_id("i1")
        mock_del.assert_called_once_with("i1")


class TestRenameItemWithRefs:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    @patch("editor.item_crud.item_exists", return_value=True)
    def test_returns_zero_if_target_exists(self, _):
        result = rename_item_with_refs("old", "new", None)
        assert result == 0

    @patch("editor.item_crud.item_exists", return_value=False)
    @patch("editor.item_crud.rename_item", return_value=False)
    def test_returns_zero_if_rename_fails(self, _, __):
        result = rename_item_with_refs("old", "new", None)
        assert result == 0

    @patch("editor.item_crud.item_exists", return_value=False)
    @patch("editor.item_crud.rename_item", return_value=True)
    def test_returns_zero_when_no_project(self, _, __):
        result = rename_item_with_refs("old", "new", None)
        assert result == 0


class TestUpdateElementosRefs:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_updates_drop_list_refs(self):
        el_path = os.path.join(self.tmpdir, "elementos.json")
        el_data = {
            "elem1": {
                "properties": {
                    "drops": [
                        {"item": "old_id", "prob": 0.5},
                        {"item": "other", "prob": 0.3},
                    ]
                }
            }
        }
        with open(el_path, "w", encoding="utf-8") as f:
            json.dump(el_data, f)
        project = MagicMock()
        project.data_path.return_value = el_path
        _update_elementos_refs("old_id", "new_id", project)
        with open(el_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        assert result["elem1"]["properties"]["drops"][0]["item"] == "new_id"
        assert result["elem1"]["properties"]["drops"][1]["item"] == "other"

    def test_no_change_when_no_refs(self):
        el_path = os.path.join(self.tmpdir, "elementos.json")
        el_data = {"elem1": {"properties": {"drops": [{"item": "other"}]}}}
        with open(el_path, "w", encoding="utf-8") as f:
            json.dump(el_data, f)
        project = MagicMock()
        project.data_path.return_value = el_path
        _update_elementos_refs("old_id", "new_id", project)
        with open(el_path, "r", encoding="utf-8") as f:
            result = json.load(f)
        assert result["elem1"]["properties"]["drops"][0]["item"] == "other"

    def test_handles_missing_file(self):
        project = MagicMock()
        project.data_path.return_value = os.path.join(self.tmpdir, "nonexistent.json")
        _update_elementos_refs("old", "new", project)


class TestUpdateStackRefs:
    def setup_method(self):
        self.tmpdir = tempfile.mkdtemp()

    def teardown_method(self):
        shutil.rmtree(self.tmpdir)

    def test_updates_give_remove_item_events(self):
        stacks_dir = os.path.join(self.tmpdir, "stacks")
        os.makedirs(stacks_dir)
        stack = {
            "events": [
                {"event": "give_item", "params": {"item_id": "old_id"}},
                {"event": "remove_item", "params": {"item_id": "old_id"}},
                {"event": "dialog", "params": {"text": "hi"}},
            ]
        }
        with open(os.path.join(stacks_dir, "s1.json"), "w", encoding="utf-8") as f:
            json.dump(stack, f)
        project = MagicMock()
        project.data_path.return_value = stacks_dir
        updated = _update_stack_refs("old_id", "new_id", project)
        assert updated == 1
        with open(os.path.join(stacks_dir, "s1.json"), "r", encoding="utf-8") as f:
            result = json.load(f)
        assert result["events"][0]["params"]["item_id"] == "new_id"
        assert result["events"][1]["params"]["item_id"] == "new_id"
        assert result["events"][2]["params"]["text"] == "hi"

    def test_returns_zero_when_no_stacks_dir(self):
        project = MagicMock()
        project.data_path.return_value = os.path.join(self.tmpdir, "nonexistent")
        assert _update_stack_refs("old", "new", project) == 0

    def test_returns_zero_when_no_refs(self):
        stacks_dir = os.path.join(self.tmpdir, "stacks")
        os.makedirs(stacks_dir)
        stack = {"events": [{"event": "dialog", "params": {"text": "hi"}}]}
        with open(os.path.join(stacks_dir, "s1.json"), "w", encoding="utf-8") as f:
            json.dump(stack, f)
        project = MagicMock()
        project.data_path.return_value = stacks_dir
        assert _update_stack_refs("old", "new", project) == 0
