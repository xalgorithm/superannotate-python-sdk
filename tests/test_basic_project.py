from pathlib import Path
import json

import pytest

import superannotate as sa

sa.init(Path.home() / ".annotateonline" / "config.json")


@pytest.mark.parametrize(
    "project_type,name,description,from_folder", [
        (
            1, "Example Project test", "test vector",
            Path("./tests/sample_project_vector")
        ),
        (
            2, "Example Project test", "test pixel",
            Path("./tests/sample_project_pixel")
        ),
    ]
)
def test_basic_project(project_type, name, description, from_folder, tmpdir):
    tmpdir = Path(tmpdir)
    team = sa.get_default_team()

    projects_found = sa.search_projects(team, name)
    for pr in projects_found:
        sa.delete_project(pr)

    projects_found = sa.search_projects(team, name)
    assert len(projects_found) == 0

    project = sa.create_project(team, name, description, project_type)
    assert project["name"] == name
    assert project["description"] == description
    assert project["type"] == project_type

    projects_found = sa.search_projects(team, name)
    assert len(projects_found) == 1
    assert projects_found[0]["name"] == name

    sa.upload_images_from_folder(project, from_folder, annotation_status=2)

    count_in_folder = len(list(from_folder.glob("*.jpg"))
                         ) + len(list(from_folder.glob("*.png")))
    if project_type == 2:
        count_in_folder -= len(list(from_folder.glob("*___save.png")))
    images = sa.search_images(project)
    assert count_in_folder == len(images)

    old_to_new_classes_conversion = sa.create_classes_from_classes_json(
        project, from_folder / "classes" / "classes.json"
    )
    classes_in_file = json.load(open(from_folder / "classes" / "classes.json"))
    classes_in_project = sa.search_classes(project)
    assert len(classes_in_file) == len(classes_in_project)
    for cl_f in classes_in_file:
        found = False
        for cl_c in classes_in_project:
            if cl_f["name"] == cl_c["name"]:
                found = True
                assert old_to_new_classes_conversion[cl_f["id"]] == cl_c["id"]
                break
        assert found

    sa.upload_annotations_from_folder(
        project, from_folder, old_to_new_classes_conversion
    )

    export = sa.prepare_export(project)

    sa.download_export(export, tmpdir)
    for image in from_folder.glob("*.[jpg|png]"):
        found = False
        for image_in_project in tmpdir.glob("*.jpg"):
            if image.name == image_in_project.name:
                found = True
                break
        assert found, image

    for json_in_folder in from_folder.glob("*.json"):
        found = False
        for json_in_project in tmpdir.glob("*.json"):
            if json_in_folder.name == json_in_project.name:
                found = True
                break
        assert found, json_in_folder
    if project_type == 2:
        for mask_in_folder in from_folder.glob("*___save.png"):
            found = False
            for mask_in_project in tmpdir.glob("*___save.png"):
                if mask_in_folder.name == mask_in_project.name:
                    found = True
                    break
            assert found, mask_in_folder
    sa.delete_project(project)

    projects_found = sa.search_projects(team, name)
    assert len(projects_found) == 0