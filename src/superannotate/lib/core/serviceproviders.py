from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Iterable
from typing import List
from typing import Tuple

from lib.core.service_types import ServiceResponse


class SingleInstanceMetaClass(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in SingleInstanceMetaClass._instances:
            SingleInstanceMetaClass._instances[cls] = super().__call__(*args, **kwargs)
        return SingleInstanceMetaClass._instances[cls]

    def get_instance(cls):
        if cls._instances:
            return cls._instances[cls]


class SuerannotateServiceProvider(metaclass=SingleInstanceMetaClass):
    @abstractmethod
    def attach_files(
        self,
        project_id: int,
        folder_id: int,
        team_id: int,
        files: List[Dict],
        annotation_status_code: int,
        upload_state_code: int,
        meta: Dict,
    ):
        raise NotImplementedError

    @abstractmethod
    def get_annotation_classes(
        self, project_id: int, team_id: int, name_prefix: str = None
    ):
        raise NotImplementedError

    @abstractmethod
    def share_project(
        self, project_id: int, team_id: int, user_id: str, user_role: int
    ):
        raise NotImplementedError

    @abstractmethod
    def prepare_export(
        self,
        project_id: int,
        team_id: int,
        folders: List[str],
        annotation_statuses: Iterable[Any],
        include_fuse: bool,
        only_pinned: bool,
    ):
        raise NotImplementedError

    @abstractmethod
    def invite_contributor(self, team_id: int, email: str, user_role: str):
        raise NotImplementedError

    @abstractmethod
    def delete_team_invitation(self, team_id: int, token: str, email: str):
        raise NotImplementedError

    @abstractmethod
    def search_team_contributors(self, team_id: int, query_string: str = None):
        raise NotImplementedError

    @abstractmethod
    def get_project_settings(self, project_id: int, team_id: int):
        raise NotImplementedError

    @abstractmethod
    def set_project_settings(self, project_id: int, team_id: int, data: List):
        raise NotImplementedError

    @abstractmethod
    def get_project_workflows(self, project_id: int, team_id: int):
        raise NotImplementedError

    @abstractmethod
    def list_images(self, query_string):
        raise NotImplementedError

    @abstractmethod
    def get_project(self, uuid: int, team_id: int):
        raise NotImplementedError

    @abstractmethod
    def set_project_workflow(self, project_id: int, team_id: int, data: Dict):
        raise NotImplementedError

    def delete_folders(self, project_id: int, team_id: int, folder_ids: List[int]):
        raise NotImplementedError

    def get_folder(self, query_string: str):
        raise NotImplementedError

    def get_folders(self, query_string: str = None, params: dict = None):
        raise NotImplementedError

    def create_folder(self, project_id: int, team_id: int, folder_name: str):
        raise NotImplementedError

    def update_folder(self, project_id: int, team_id: int, folder_data: dict):
        raise NotImplementedError

    def get_download_token(
        self,
        project_id: int,
        team_id: int,
        folder_id: int,
        image_id: int,
        include_original: int = 1,
    ) -> dict:
        raise NotImplementedError

    def get_upload_token(
        self, project_id: int, team_id: int, folder_id: int, image_id: int,
    ) -> dict:
        raise NotImplementedError

    def update_image(self, image_id: int, team_id: int, project_id: int, data: dict):
        raise NotImplementedError

    def copy_images_between_folders_transaction(
        self,
        team_id: int,
        project_id: int,
        from_folder_id: int,
        to_folder_id: int,
        images: List[str],
        include_annotations: bool = False,
        include_pin: bool = False,
    ) -> int:
        raise NotImplementedError

    def move_images_between_folders(
        self,
        team_id: int,
        project_id: int,
        from_folder_id: int,
        to_folder_id: int,
        images: List[str],
    ) -> List[str]:
        """
        Returns list of moved images.
        """
        raise NotImplementedError

    def get_duplicated_images(
        self, project_id: int, team_id: int, folder_id: int, images: List[str]
    ):
        raise NotImplementedError

    def get_progress(
        self, project_id: int, team_id: int, poll_id: int
    ) -> Tuple[int, int]:
        raise NotImplementedError

    def set_images_statuses_bulk(
        self,
        image_names: List[str],
        team_id: int,
        project_id: int,
        folder_id: int,
        annotation_status: int,
    ):
        raise NotImplementedError

    def delete_images(self, project_id: int, team_id: int, image_ids: List[int]):
        raise NotImplementedError

    def assign_images(
        self,
        team_id: int,
        project_id: int,
        folder_name: str,
        user: str,
        image_names: list,
    ):
        raise NotImplementedError

    def get_bulk_images(
        self, project_id: int, team_id: int, folder_id: int, images: List[str]
    ) -> List[dict]:
        raise NotImplementedError

    def un_assign_folder(
        self, team_id: int, project_id: int, folder_name: str,
    ):
        raise NotImplementedError

    def assign_folder(
        self, team_id: int, project_id: int, folder_name: str, users: list
    ):
        raise NotImplementedError

    def un_assign_images(
        self, team_id: int, project_id: int, folder_name: str, image_names: list,
    ):
        raise NotImplementedError

    def un_share_project(
        self, team_id: int, project_id: int, user_id: str,
    ):
        raise NotImplementedError

    def upload_form_s3(
        self,
        project_id: int,
        team_id: int,
        access_key: str,
        secret_key: str,
        bucket_name: str,
        from_folder_name: str,
        to_folder_id: int,
    ):
        raise NotImplementedError

    def get_upload_status(self, project_id: int, team_id: int, folder_id: int):
        raise NotImplementedError

    def get_exports(self, team_id: int, project_id: int):
        raise NotImplementedError

    def get_export(self, team_id: int, project_id: int, export_id: int):
        raise NotImplementedError

    def get_project_images_count(self, team_id: int, project_id: int):
        raise NotImplementedError

    def get_s3_upload_auth_token(self, team_id: int, folder_id: int, project_id: int):
        raise NotImplementedError

    def delete_annotation_class(
        self, team_id: int, project_id: int, annotation_class_id: int
    ):
        raise NotImplementedError

    def set_annotation_classes(self, team_id: int, project_id: int, data: list):
        raise NotImplementedError

    def set_project_workflow_bulk(self, project_id: int, team_id: int, steps: list):
        raise NotImplementedError

    def set_project_workflow_attributes_bulk(
        self, project_id: int, team_id: int, attributes: list
    ):
        raise NotImplementedError

    def get_pre_annotation_upload_data(
        self, project_id: int, team_id: int, image_ids: List[int], folder_id: int
    ):
        raise NotImplementedError

    def get_annotation_upload_data(
        self, project_id: int, team_id: int, image_ids: List[int], folder_id: int
    ) -> ServiceResponse:
        raise NotImplementedError

    def get_templates(self, team_id: int):
        raise NotImplementedError

    def start_model_training(self, team_id: int, hyper_parameters: dict) -> dict:
        raise NotImplementedError

    def get_model_metrics(self, team_id: int, model_id: int) -> dict:
        raise NotImplementedError

    def get_models(
        self, name: str, team_id: int, project_id: int, model_type: str
    ) -> List:
        raise NotImplementedError

    def bulk_get_folders(self, team_id: int, project_ids: List[int]):
        raise NotImplementedError

    def update_model(self, team_id: int, model_id: int, data: dict):
        raise NotImplementedError

    def delete_model(self, team_id: int, model_id: int):
        raise NotImplementedError

    def stop_model_training(self, team_id: int, model_id: int):
        raise NotImplementedError

    def get_ml_model_download_tokens(
        self, team_id: int, model_id: int
    ) -> ServiceResponse:
        raise NotImplementedError

    def run_segmentation(
        self, team_id: int, project_id: int, model_name: str, image_ids: list
    ):
        raise NotImplementedError

    def run_prediction(
        self, team_id: int, project_id: int, ml_model_id: int, image_ids: list
    ):
        raise NotImplementedError

    def delete_image_annotations(
        self,
        team_id: int,
        project_id: int,
        folder_id: int = None,
        image_names: List[str] = None,
    ) -> dict:
        raise NotImplementedError

    def get_annotations_delete_progress(
        self, team_id: int, project_id: int, poll_id: int
    ):
        raise NotImplementedError

    def get_limitations(
        self, team_id: int, project_id: int, folder_id: int = None
    ) -> ServiceResponse:
        raise NotImplementedError
