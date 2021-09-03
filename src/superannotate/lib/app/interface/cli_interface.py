import json
import logging
import os
import sys
import tempfile
import uuid
from typing import Any
from typing import Optional

import lib.core as constances
import pandas as pd
from lib import __file__ as lib_path
from lib.app.helpers import get_annotation_paths
from lib.app.helpers import split_project_path
from lib.app.input_converters.conversion import import_annotation
from lib.app.interface.base_interface import BaseInterfaceFacade
from lib.app.interface.sdk_interface import attach_image_urls_to_project
from lib.app.interface.sdk_interface import attach_video_urls_to_project
from lib.app.interface.sdk_interface import create_folder
from lib.app.interface.sdk_interface import create_project
from lib.app.interface.sdk_interface import upload_images_from_folder_to_project
from lib.app.interface.sdk_interface import upload_videos_from_folder_to_project
from lib.app.serializers import ImageSerializer
from lib.core.entities import ConfigEntity
from lib.infrastructure.controller import Controller
from lib.infrastructure.repositories import ConfigRepository
from tqdm import tqdm


logger = logging.getLogger()
controller = Controller(logger)


class CLIFacade(BaseInterfaceFacade):
    """
    With SuperAnnotate CLI, basic tasks can be accomplished using shell commands:
    superannotatecli <command> <--arg1 val1> <--arg2 val2> [--optional_arg3 val3] [--optional_arg4] ...
    """

    @staticmethod
    def version():
        """
        To show the version of the current SDK installation
        """
        with open(
            f"{os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(lib_path))))}/version.py"
        ) as f:
            version = f.read().rstrip()[15:-1]
            print(version)
        sys.exit(0)

    @staticmethod
    def init():
        """
        To initialize CLI (and SDK) with team token
        """
        repo = ConfigRepository()
        config = repo.get_one(uuid=constances.TOKEN_UUID)
        if config:
            if not input(
                f"File {config} exists. Do you want to overwrite? [y/n] : "
            ).lower() in ("y", "yes"):
                return
        token = input(
            "Input the team SDK token from https://app.superannotate.com/team : "
        )
        config_entity = ConfigEntity(uuid=constances.TOKEN_UUID, value=token)
        repo.insert(config_entity)
        if config:
            print("Configuration file successfully updated.")
        else:
            print("Configuration file successfully created.")
        sys.exit(0)

    def create_project(self, name: str, description: str, type: str):
        """
        To create a new project
        """
        create_project(name, description, type)
        sys.exit(0)

    def create_folder(self, project: str, name: str):
        """
        To create a new folder
        """
        create_folder(project, name)
        sys.exit(0)

    def upload_images(
        self,
        project: str,
        folder: str,
        extensions: str = constances.DEFAULT_IMAGE_EXTENSIONS,
        set_annotation_status: str = constances.AnnotationStatus.NOT_STARTED.name,
        exclude_file_patterns=constances.DEFAULT_FILE_EXCLUDE_PATTERNS,
        recursive_subfolders=False,
        image_quality_in_editor=None,
    ):
        """
        To upload images from folder to project use:

        If optional argument recursive is given then subfolders of <folder_path> are also
         recursively scanned for available images.
        Optional argument extensions accepts comma separated list of image extensions to look for.
        If the argument is not given then value jpg,jpeg,png,tif,tiff,webp,bmp is assumed.
        """
        upload_images_from_folder_to_project(
            project,
            folder_path=folder,
            extensions=extensions,
            annotation_status=set_annotation_status,
            from_s3_bucket=None,
            exclude_file_patterns=exclude_file_patterns,
            recursive_subfolders=recursive_subfolders,
            image_quality_in_editor=image_quality_in_editor,
        )
        sys.exit(0)

    def export_project(
        self,
        project,
        folder,
        include_fuse=False,
        disable_extract_zip_contents=False,
        annotation_statuses=None,
    ):
        project_name, folder_name = split_project_path(project)
        folders = None
        if folder_name:
            folders = [folder_name]
        export_res = self.controller.prepare_export(
            project_name, folders, include_fuse, False, annotation_statuses
        )
        export_name = export_res.data["name"]
        self.controller.download_export(
            project_name=project_name,
            export_name=export_name,
            folder_path=folder,
            extract_zip_contents=not disable_extract_zip_contents,
            to_s3_bucket=False,
        )
        sys.exit(0)

    def upload_preannotations(
        self, project, folder, data_set_name=None, task=None, format=None
    ):
        """
        To upload preannotations from folder to project use
        Optional argument format accepts input annotation format. It can have COCO or SuperAnnotate values.
         If the argument is not given then SuperAnnotate (the native annotation format) is assumed.
        Only when COCO format is specified dataset-name and task arguments are required.
        dataset-name specifies JSON filename (without extension) in <folder_path>.
        task specifies the COCO task for conversion. Please see import_annotation_format for more details.
        The annotation classes will be created during the execution of this command.
        """
        self._upload_annotations(
            project=project,
            folder=folder,
            format=format,
            data_set_name=data_set_name,
            task=task,
            pre=True,
        )
        sys.exit(0)

    def upload_annotations(
        self, project, folder, data_set_name=None, task=None, format=None
    ):
        """
        To upload annotations from folder to project use
        Optional argument format accepts input annotation format. It can have COCO or SuperAnnotate values.
        If the argument is not given then SuperAnnotate (the native annotation format) is assumed.
        Only when COCO format is specified dataset-name and task arguments are required.
        dataset-name specifies JSON filename (without extension) in <folder_path>.
        task specifies the COCO task for conversion. Please see import_annotation_format for more details.
        The annotation classes will be created during the execution of this command.
        """
        self._upload_annotations(
            project=project,
            folder=folder,
            format=format,
            data_set_name=data_set_name,
            task=task,
            pre=False,
        )
        sys.exit(0)

    def _upload_annotations(
        self, project, folder, format, data_set_name, task, pre=True
    ):
        project_name, folder_name = split_project_path(project)
        project = self.controller.get_project_metadata(project_name=project_name).data
        if not format:
            format = "SuperAnnotate"
        if not data_set_name and format == "COCO":
            raise Exception("Data-set name is required")
        elif not data_set_name:
            data_set_name = ""
        if not task:
            task = "object_detection"

        annotations_path = folder
        with tempfile.TemporaryDirectory() as temp_dir:
            if format != "SuperAnnotate":
                import_annotation(
                    input_dir=folder,
                    output_dir=temp_dir,
                    dataset_format=format,
                    dataset_name=data_set_name,
                    project_type=constances.ProjectType.get_name(
                        project["project"].project_type
                    ),
                    task=task,
                )
                annotations_path = temp_dir
            classes_path = f"{annotations_path}/classes/classes.json"
            self.controller.create_annotation_classes(
                project_name=project_name,
                annotation_classes=json.load(open(classes_path)),
            )
            annotation_paths = get_annotation_paths(annotations_path)
            chunk_size = 10
            with tqdm(total=len(annotation_paths)) as progress_bar:
                for i in range(0, len(annotation_paths), chunk_size):
                    response = self.controller.upload_annotations_from_folder(
                        project_name=project["project"].name,
                        folder_name=folder_name,
                        folder_path=annotations_path,
                        annotation_paths=annotation_paths[
                            i : i + chunk_size  # noqa: E203
                        ],
                        is_pre_annotations=pre,
                    )
                    if response.errors:
                        logger.warning(response.errors)
                    progress_bar.update(chunk_size)
        sys.exit(0)

    def attach_image_urls(
        self, project: str, attachments: str, annotation_status: Optional[Any] = None
    ):
        """
        To attach image URLs to project use:
        """

        attach_image_urls_to_project(
            project=project,
            attachments=attachments,
            annotation_status=annotation_status,
        )
        sys.exit(0)

    def attach_video_urls(
        self, project: str, attachments: str, annotation_status: Optional[Any] = None
    ):
        attach_video_urls_to_project(
            project=project,
            attachments=attachments,
            annotation_status=annotation_status,
        )
        sys.exit(0)

    def _attach_urls(
        self, project: str, attachments: str, annotation_status: Optional[Any] = None
    ):
        project_name, folder_name = split_project_path(project)

        image_data = pd.read_csv(attachments, dtype=str)
        image_data = image_data[~image_data["url"].isnull()]
        for ind, _ in image_data[image_data["name"].isnull()].iterrows():
            image_data.at[ind, "name"] = str(uuid.uuid4())

        image_data = pd.DataFrame(image_data, columns=["name", "url"])
        img_names_urls = image_data.rename(columns={"url": "path"}).to_dict(
            orient="records"
        )
        list_of_not_uploaded = []
        duplicate_images = []
        for i in range(0, len(img_names_urls), 500):
            response = self.controller.attach_urls(
                project_name=project_name,
                folder_name=folder_name,
                files=ImageSerializer.deserialize(
                    img_names_urls[i : i + 500]  # noqa: E203
                ),
                annotation_status=annotation_status,
            )
            if response.errors:
                list_of_not_uploaded.append(response.data[0])
                duplicate_images.append(response.data[1])

        list_of_uploaded = [
            image["name"]
            for image in img_names_urls
            if image["name"] not in list_of_not_uploaded
        ]

        return list_of_uploaded, list_of_not_uploaded, duplicate_images

    def upload_videos(
        self,
        project,
        folder,
        target_fps=1,
        recursive=False,
        extensions=constances.DEFAULT_VIDEO_EXTENSIONS,
        set_annotation_status=constances.AnnotationStatus.NOT_STARTED.name,
        start_time=0.0,
        end_time=None,
    ):
        """
        To upload videos from folder to project use
        If optional argument recursive is given then subfolders of <folder_path> are also recursively scanned for available videos.
        Optional argument extensions accepts comma separated list of image extensions to look for.
        If the argument is not given then value mp4,avi,mov,webm,flv,mpg,ogg is assumed.
        target-fps specifies how many frames per second need to extract from the videos (approximate).
        If not specified all frames will be uploaded.
        start-time specifies time (in seconds) from which to start extracting frames, default is 0.0.
        end-time specifies time (in seconds) up to which to extract frames. If it is not specified, then up to end is assumed.
        """

        upload_videos_from_folder_to_project(
            project=project,
            folder_path=folder,
            extensions=extensions,
            exclude_file_patterns=(),
            recursive_subfolders=recursive,
            target_fps=target_fps,
            start_time=start_time,
            end_time=end_time,
            annotation_status=set_annotation_status,
            image_quality_in_editor=None,
        )
        sys.exit(0)
