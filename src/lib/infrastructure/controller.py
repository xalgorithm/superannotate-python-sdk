import copy
import io
from typing import Iterable
from typing import List

from src.lib.core.conditions import Condition
from src.lib.core.conditions import CONDITION_EQ as EQ
from src.lib.core.entities import FolderEntity
from src.lib.core.entities import ImageEntity
from src.lib.core.entities import ImageInfoEntity
from src.lib.core.entities import ProjectEntity
from src.lib.core.exceptions import AppException
from src.lib.core.response import Response
from src.lib.core.usecases import AttachFileUrls
from src.lib.core.usecases import CloneProjectUseCase
from src.lib.core.usecases import CopyImageAnnotationClasses
from src.lib.core.usecases import CreateFolderUseCase
from src.lib.core.usecases import CreateProjectUseCase
from src.lib.core.usecases import DeleteContributorInvitationUseCase
from src.lib.core.usecases import DeleteFolderUseCase
from src.lib.core.usecases import DeleteProjectUseCase
from src.lib.core.usecases import DownloadImageFromPublicUrlUseCase
from src.lib.core.usecases import DownloadImageUseCase
from src.lib.core.usecases import GetFolderUseCase
from src.lib.core.usecases import GetImagesUseCase
from src.lib.core.usecases import GetImageUseCase
from src.lib.core.usecases import GetProjectFoldersUseCase
from src.lib.core.usecases import GetProjectsUseCase
from src.lib.core.usecases import GetTeamUseCase
from src.lib.core.usecases import ImageUploadUseCas
from src.lib.core.usecases import InviteContributorUseCase
from src.lib.core.usecases import PrepareExportUseCase
from src.lib.core.usecases import SearchContributorsUseCase
from src.lib.core.usecases import SearchFolderUseCase
from src.lib.core.usecases import UpdateFolderUseCase
from src.lib.core.usecases import UpdateImageUseCase
from src.lib.core.usecases import UpdateProjectUseCase
from src.lib.core.usecases import UploadImageS3UseCas
from src.lib.infrastructure.repositories import AnnotationClassRepository
from src.lib.infrastructure.repositories import ConfigRepository
from src.lib.infrastructure.repositories import FolderRepository
from src.lib.infrastructure.repositories import ImageRepository
from src.lib.infrastructure.repositories import ProjectRepository
from src.lib.infrastructure.repositories import ProjectSettingsRepository
from src.lib.infrastructure.repositories import S3Repository
from src.lib.infrastructure.repositories import TeamRepository
from src.lib.infrastructure.repositories import WorkflowRepository
from src.lib.infrastructure.services import SuperannotateBackendService


class BaseController:
    def __init__(self, backend_client: SuperannotateBackendService, response: Response):
        self._backend_client = backend_client
        self._s3_upload_auth_data = None
        self._response = response
        self._project = None

    @property
    def response(self):
        return self._response

    @property
    def projects(self):
        return ProjectRepository(self._backend_client)

    @property
    def teams(self):
        return TeamRepository(self._backend_client)

    @property
    def images(self):
        return ImageRepository(self._backend_client)

    @property
    def configs(self):
        return ConfigRepository()

    @property
    def team_id(self) -> int:
        return int(self.configs.get_one("token").value.split("=")[-1])

    def get_auth_data(self, project_id: int, team_id: int, folder_id: int):
        return self._backend_client.get_s3_upload_auth_token(
            team_id, folder_id, project_id
        )

    def get_s3_repository(
        self, team_id: int, project_id: int, folder_id: int, bucket: str = None
    ):
        if not self._s3_upload_auth_data:
            self._s3_upload_auth_data = self.get_auth_data(
                project_id, team_id, folder_id
            )

        return S3Repository(
            self._s3_upload_auth_data["accessKeyId"],
            self._s3_upload_auth_data["secretAccessKey"],
            self._s3_upload_auth_data["sessionToken"],
            self._s3_upload_auth_data["bucket"],
        )

    @property
    def s3_repo(self):
        return S3Repository


class Controller(BaseController):
    def _get_project(self, name: str):
        if not self._project:
            self._project = self.projects.get_all(
                Condition("name", name, EQ) & Condition("team_id", self.team_id, EQ)
            )[0]
        elif self._project.name != name:
            self._project = self.projects.get_all(
                Condition("name", name, EQ) & Condition("team_id", self.team_id, EQ)
            )[0]
        return self._project

    def _get_folder(self, project: ProjectEntity, name: str):
        if not name:
            name = "root"
        folders = FolderRepository(self._backend_client, project)
        return folders.get_one(
            Condition("name", name, EQ)
            & Condition("team_id", self.team_id, EQ)
            & Condition("project_id", project.uuid, EQ)
        )

    def search_project(self, name: str, **kwargs) -> Response:
        condition = Condition("name", name, EQ)
        for key, val in kwargs.items():
            condition = condition & Condition(key, val, EQ)
        use_case = GetProjectsUseCase(
            response=self.response,
            condition=condition,
            projects=self.projects,
            team_id=self.team_id,
        )
        use_case.execute()
        return self.response

    def create_project(
        self,
        name: str,
        description: str,
        project_type: str,
        contributors: Iterable = (),
        settings: Iterable = (),
        annotation_classes: Iterable = (),
        workflows: Iterable = (),
    ) -> Response:
        entity = ProjectEntity(
            name=name,
            description=description,
            project_type=project_type,
            team_id=self.team_id,
        )
        use_case = CreateProjectUseCase(
            response=self.response,
            project=entity,
            projects=self.projects,
            backend_service_provider=self._backend_client,
            settings=[
                ProjectSettingsRepository.dict2entity(setting) for setting in settings
            ],
            workflows=[
                WorkflowRepository.dict2entity(workflow) for workflow in workflows
            ],
            annotation_classes=[
                AnnotationClassRepository.dict2entity(annotation_class)
                for annotation_class in annotation_classes
            ],
            contributors=contributors,
        )
        use_case.execute()
        return self.response

    def delete_project(self, name: str):
        entities = self.projects.get_all(
            Condition("team_id", self.team_id, EQ) & Condition("name", name, EQ)
        )
        if entities and len(entities) == 1:
            use_case = DeleteProjectUseCase(self.response, entities[0], self.projects)
            use_case.execute()
            return self.response
        if entities and len(entities) > 1:
            raise AppException("There are duplicated names.")

    def update_project(self, name: str, project_data: dict) -> Response:
        entities = self.projects.get_all(
            Condition("team_id", self.team_id, EQ) & Condition("name", name, EQ)
        )
        project = entities[0]
        if entities and len(entities) == 1:
            project.name = project_data["name"]
            use_case = UpdateProjectUseCase(self.response, project, self.projects)
            use_case.execute()
            return self.response
        raise AppException("There are duplicated names.")

    def upload_images(
        self,
        project_name: str,
        images: List[ImageInfoEntity],
        annotation_status: str = None,
        image_quality: str = None,
    ):
        project = self._get_project(project_name)
        use_case = ImageUploadUseCas(
            response=self.response,
            project=project,
            project_settings=ProjectSettingsRepository(self._backend_client, project),
            backend_service_provider=self._backend_client,
            images=images,
            annotation_status=annotation_status,
            image_quality=image_quality,
        )
        use_case.execute()
        return self.response

    def upload_image_to_s3(
        self,
        project_name: str,
        image_path: str,  # image path to upload
        image_bytes: io.BytesIO,
        folder_name: str = None,  # project folder path
    ):
        project = self._get_project(project_name)
        folder = self._get_folder(project, folder_name)
        s3_repo = self.get_s3_repository(self.team_id, project.uuid, folder.uuid,)
        use_case = UploadImageS3UseCas(
            response=self.response,
            project=project,
            project_settings=ProjectSettingsRepository(self._backend_client, project),
            image_path=image_path,
            image=image_bytes,
            s3_repo=s3_repo,
            upload_path=self._s3_upload_auth_data["filePath"],
        )
        use_case.execute()
        return self.response

    def clone_project(
        self,
        name: str,
        from_name: str,
        project_description: str,
        copy_annotation_classes=True,
        copy_settings=True,
        copy_workflow=True,
        copy_contributors=False,
    ):
        projects = self.projects.get_all(
            Condition("name", from_name, EQ) & Condition("team_id", self.team_id, EQ)
        )
        if projects:
            project_to_create = copy.copy(projects[0])
            project_to_create.name = name
            project_to_create.description = project_description
            use_case = CloneProjectUseCase(
                self.response,
                project=projects[0],
                project_to_create=project_to_create,
                projects=self.projects,
                settings=ProjectSettingsRepository(self._backend_client, projects[0]),
                workflows=WorkflowRepository(self._backend_client, projects[0]),
                annotation_classes=AnnotationClassRepository(
                    self._backend_client, projects[0]
                ),
                backend_service_provider=self._backend_client,
                include_contributors=copy_contributors,
                include_settings=copy_settings,
                include_workflow=copy_workflow,
                include_annotation_classes=copy_annotation_classes,
            )
            use_case.execute()
        return self.response

    def attach_urls(
        self,
        project_name: str,
        files: List[ImageEntity],
        folder_name: str,
        annotation_status: int = None,
    ):
        project = self._get_project(project_name)
        folder = self._get_folder(project, folder_name)
        auth_data = self.get_auth_data(project.uuid, project.team_id, folder.uuid)

        limit = auth_data["availableImageCount"]
        use_case = AttachFileUrls(
            response=self.response,
            project=project,
            attachments=files,
            limit=limit,
            backend_service_provider=self._backend_client,
            annotation_status=annotation_status,
        )
        use_case.execute()

    def create_folder(self, project: str, folder_name: str):
        projects = ProjectRepository(service=self._backend_client).get_all(
            condition=Condition("name", project, EQ)
            & Condition("team_id", self.team_id, EQ)
        )
        project = projects[0]
        folder = FolderEntity(
            name=folder_name, project_id=project.uuid, team_id=project.team_id
        )
        use_case = CreateFolderUseCase(
            response=self.response, folder=folder, folders=self.folders
        )
        use_case.execute()
        return self.response

    def get_folder(self, project_name: str, folder_name: str):
        project = self._get_project(project_name)
        use_case = GetFolderUseCase(
            response=self.response,
            project=project,
            folders=FolderRepository(self._backend_client, project),
            folder_name=folder_name,
        )
        use_case.execute()
        return self.response

    def search_folder(self, project_name: str, **kwargs):
        condition = None
        if kwargs:
            conditions_iter = iter(kwargs)
            key = next(conditions_iter)
            condition = Condition(key, kwargs[key], EQ)
            for key, val in conditions_iter:
                condition = condition & Condition(key, val, EQ)

        project = self._get_project(project_name)
        use_case = SearchFolderUseCase(
            response=self.response,
            project=project,
            folders=FolderRepository(self._backend_client, project),
            condition=condition,
        )
        use_case.execute()
        return self.response

    def get_project_folders(
        self, project_name: str,
    ):
        project = self._get_project(project_name)
        use_case = GetProjectFoldersUseCase(
            response=self.response,
            project=project,
            folders=FolderRepository(self._backend_client, project),
        )
        use_case.execute()
        return self.response

    def delete_folders(self, project_name: str, folder_names: List[str]):
        project = self._get_project(project_name)
        folders = self.get_project_folders(project_name).data

        use_case = DeleteFolderUseCase(
            response=self.response,
            project=project,
            folders=FolderRepository(self._backend_client, project),
            folders_to_delete=[
                folder for folder in folders if folder.name in folder_names
            ],
        )
        use_case.execute()
        return self.response

    def prepare_export(
        self,
        project: ProjectEntity,
        folders: List[str],
        include_fuse: bool,
        only_pinned: bool,
        annotation_statuses: List[str] = None,
    ):

        use_case = PrepareExportUseCase(
            response=self.response,
            project=project,
            folder_names=folders,
            backend_service_provider=self._backend_client,
            include_fuse=include_fuse,
            only_pinned=only_pinned,
            annotation_statuses=annotation_statuses,
        )
        use_case.execute()

        return self.response

    def get_team(self):
        use_case = GetTeamUseCase(
            response=self.response, teams=self.teams, team_id=self.team_id
        )
        use_case.execute()
        return self.response

    def invite_contributor(self, email: str, is_admin: bool):
        use_case = InviteContributorUseCase(
            response=self.response,
            backend_service_provider=self._backend_client,
            email=email,
            team_id=self.team_id,
            is_admin=is_admin,
        )
        use_case.execute()
        return self.response

    def delete_contributor_invitation(self, email: str):
        team = self.teams.get_one(self.team_id)
        use_case = DeleteContributorInvitationUseCase(
            response=self.response,
            backend_service_provider=self._backend_client,
            email=email,
            team=team,
        )
        use_case.execute()
        return self.response

    def search_team_contributors(self, **kwargs):
        condition = None
        if kwargs:
            conditions_iter = iter(kwargs)
            key = next(conditions_iter)
            condition = Condition(key, kwargs[key], EQ)
            for key, val in conditions_iter:
                condition = condition & Condition(key, val, EQ)

        use_case = SearchContributorsUseCase(
            response=self.response,
            backend_service_provider=self._backend_client,
            team_id=self.team_id,
            condition=condition,
        )
        use_case.execute()
        return self.response

    def search_images(
        self,
        project_name: str,
        folder_path: str = None,
        annotation_status: str = None,
        image_name_prefix: str = None,
    ):
        project = self._get_project(project_name)
        if not folder_path:
            folder = self._get_folder(project, "root")
        else:
            folder = self._get_folder(project, folder_path)
        use_case = GetImagesUseCase(
            response=self.response,
            project=project,
            folder=folder,
            images=self.images,
            annotation_status=annotation_status,
            image_name_prefix=image_name_prefix,
        )
        use_case.execute()
        return self.response

    def _get_image(
        self, project: ProjectEntity, image_name: str, folder_path: str = None,
    ) -> ImageEntity:
        response = Response()
        folder = self._get_folder(project, folder_path)
        use_case = GetImageUseCase(
            response=response,
            project=project,
            folder=folder,
            image_name=image_name,
            images=self.images,
        )
        use_case.execute()
        return response.data

    def get_image(
        self, project_name: str, image_name: str, folder_path: str = None
    ) -> ImageEntity:
        return self._get_image(self._get_project(project_name), image_name, folder_path)

    def update_folder(self, project_name: str, folder_name: str, folder_data: dict):
        project = self._get_project(project_name)
        folder = self._get_folder(project, folder_name)
        for field, value in folder_data.items():
            setattr(folder, field, value)
        use_case = UpdateFolderUseCase(
            response=self.response,
            folders=FolderRepository(self._backend_client, project),
            folder=folder,
        )
        use_case.execute()
        return self.response

    def download_image(
        self,
        project_name: str,
        image_name: str,
        folder_name: str = None,
        image_variant: str = None,
    ):
        project = self._get_project(project_name)
        image = self._get_image(project, image_name, folder_name)
        use_case = DownloadImageUseCase(
            response=self.response,
            image=image,
            backend_service_provider=self._backend_client,
            image_variant=image_variant,
        )
        use_case.execute()
        return self.response

    def copy_image_annotation_classes(
        self, from_project_name: str, to_project_name: str, image_name: str
    ):
        from_project = self._get_project(from_project_name)
        image = self._get_image(from_project, image_name)
        to_project = self._get_project(to_project_name)
        uploaded_image = self._get_image(to_project, image_name)

        use_case = CopyImageAnnotationClasses(
            response=self.response,
            from_project=from_project,
            to_project=to_project,
            from_image=image,
            to_image=uploaded_image,
            from_project_annotation_classes=AnnotationClassRepository(
                self._backend_client, from_project
            ),
            to_project_annotation_classes=AnnotationClassRepository(
                self._backend_client, to_project
            ),
            from_project_s3_repo=self.get_s3_repository(
                image.team_id, image.project_id, image.folder_id
            ),
            to_project_s3_repo=self.get_s3_repository(
                uploaded_image.team_id,
                uploaded_image.project_id,
                uploaded_image.folder_id,
            ),
            backend_service_provider=self._backend_client,
        )
        use_case.execute()

    def update_image(
        self, project_name: str, image_name: str, folder_name: str = None, **kwargs
    ):
        image = self.get_image(
            project_name=project_name, image_name=image_name, folder_path=folder_name
        )
        for item, val in kwargs.items():
            setattr(image, item, val)
        use_case = UpdateImageUseCase(
            response=self.response, image=image, images=self.images
        )
        use_case.execute()

    def download_image_from_public_url(
        self, project_name: str, image_url: str, image_name: str = None
    ):
        response = Response()
        use_case = DownloadImageFromPublicUrlUseCase(
            response=response,
            project=self._get_project(project_name),
            image_url=image_url,
            image_name=image_name,
        )
        use_case.execute()
        return response
