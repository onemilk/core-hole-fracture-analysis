"""Tests for ImageRepository"""
import sqlite3
import pytest
from core_analysis.data.database import ProjectManager
from core_analysis.data.image_repository import ImageRepository
from core_analysis.data.models import Category, ImageRecord


@pytest.fixture
def repo(tmp_path):
    db_path = str(tmp_path / "test.db")
    pm = ProjectManager(db_path)
    pm.initialize()
    return ImageRepository(pm)


class TestImageRepository:
    def test_add_category(self, repo):
        cat = Category(name="渤海湾盆地", type="basin")
        cat_id = repo.add_category(cat)
        assert cat_id == 1
        loaded = repo.get_category(cat_id)
        assert loaded.name == "渤海湾盆地"

    def test_add_child_category(self, repo):
        parent = Category(name="渤海湾盆地", type="basin")
        parent_id = repo.add_category(parent)
        child = Category(name="辽河坳陷", parent_id=parent_id, type="block")
        child_id = repo.add_category(child)
        loaded = repo.get_category(child_id)
        assert loaded.parent_id == parent_id

    def test_get_category_tree(self, repo):
        p1 = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        p2 = repo.add_category(Category(name="辽河坳陷", parent_id=p1, type="block"))
        p3 = repo.add_category(Category(name="沙河街组", parent_id=p2, type="structure"))
        repo.add_category(Category(name="J12-3井", parent_id=p3, type="well"))
        tree = repo.get_category_tree()
        assert len(tree) == 1  # top-level only
        assert tree[0].name == "渤海湾盆地"

    def test_add_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img = ImageRecord(
            category_id=cat_id,
            filename="core001.jpg",
            filepath="/data/core001.jpg",
            depth_from=1560.0,
            depth_to=1560.5,
            dpi=300,
            lithology="灰岩"
        )
        img_id = repo.add_image(img)
        assert img_id == 1

    def test_get_images_by_category(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="a.jpg", filepath="/a.jpg"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="b.jpg", filepath="/b.jpg"))
        images = repo.get_images_by_category(cat_id)
        assert len(images) == 2

    def test_search_images(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="J12_core.jpg", filepath="/a.jpg", lithology="灰岩"))
        repo.add_image(ImageRecord(category_id=cat_id, filename="J15_core.jpg", filepath="/b.jpg", lithology="砂岩"))
        results = repo.search_images("灰岩")
        assert len(results) == 1
        assert results[0].filename == "J12_core.jpg"

    def test_update_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img_id = repo.add_image(ImageRecord(category_id=cat_id, filename="old.jpg", filepath="/old.jpg"))
        img = repo.get_image(img_id)
        img.lithology = "白云岩"
        repo.update_image(img)
        updated = repo.get_image(img_id)
        assert updated.lithology == "白云岩"

    def test_delete_image(self, repo):
        cat_id = repo.add_category(Category(name="渤海湾盆地", type="basin"))
        img_id = repo.add_image(ImageRecord(category_id=cat_id, filename="x.jpg", filepath="/x.jpg"))
        repo.delete_image(img_id)
        assert repo.get_image(img_id) is None
