"""Tests for sedimentary knowledge base."""
import json
import os


class TestKnowledgeBase:
    def test_json_loads_correctly(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        assert "categories" in data
        cats = data["categories"]
        assert len(cats) == 6
        total = sum(len(entries) for entries in cats.values())
        assert total >= 30

    def test_all_entries_have_definition(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        for cat_name, entries in data["categories"].items():
            for entry_name, entry_data in entries.items():
                assert "definition" in entry_data, f"Missing definition in {cat_name}/{entry_name}"
                assert isinstance(entry_data["definition"], str)
                assert len(entry_data["definition"]) > 20

    def test_required_categories_exist(self):
        json_path = os.path.join(
            os.path.dirname(os.path.dirname(__file__)),
            "core_analysis", "data", "sedimentary_knowledge.json"
        )
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        required = ["沉积岩分类", "沉积构造", "成岩作用", "孔隙类型", "常见矿物", "常用术语"]
        for cat in required:
            assert cat in data["categories"], f"Missing category: {cat}"
