import src.superannotate as sa
from tests.integration.base import BaseTestCase


class TestProjectRename(BaseTestCase):
    PROJECT_NAME = "TestProjectRename"
    PROJECT_DESCRIPTION = "Desc"
    PROJECT_TYPE = "Vector"
    NEW_PROJECT_NAME = "new"

    def test_project_rename(self):
        sa.rename_project(self.PROJECT_NAME, self.NEW_PROJECT_NAME)
        meta = sa.get_project_metadata(self.NEW_PROJECT_NAME)
        assert meta["name"] == self.NEW_PROJECT_NAME

    def test_rename_with_special_characters(self):
        sa.rename_project(self.PROJECT_NAME, '/ \ : * ? " < > |')
        sa.get_project_metadata("_ _ _ _ _ _ _ _ _")

