import os
from editor.project import Project, get_current_project, set_current_project


class ProjectService:
    """Application service for project operations."""

    @staticmethod
    def get_current():
        return get_current_project()

    @staticmethod
    def load(path):
        set_current_project(path)
        return get_current_project()

    @staticmethod
    def data_path(*parts):
        p = get_current_project()
        if p:
            return p.data_path(*parts)
        return None

    @staticmethod
    def assets_path():
        p = get_current_project()
        if p:
            return p.assets_path()
        return None

    @staticmethod
    def map_path(map_id):
        p = get_current_project()
        if p:
            return p.map_path(map_id)
        return None


project_service = ProjectService()
