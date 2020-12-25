import cv2
import numpy as np
from tqdm import tqdm

from .voc_helper import (_get_voc_instances_from_xml, _iou)

from ..sa_json_helper import _create_vector_instance
from ....common import write_to_json


def _generate_polygons(object_mask_path):
    segmentation = []

    object_mask = cv2.imread(str(object_mask_path), cv2.IMREAD_GRAYSCALE)

    object_unique_colors = np.unique(object_mask)

    index = 1
    groupId = 0
    for unique_color in object_unique_colors:
        if unique_color in (0, 220):
            continue

        mask = np.zeros_like(object_mask)
        mask[object_mask == unique_color] = 255
        contours, _ = cv2.findContours(
            mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
        )

        segment = []
        if len(contours) > 1:
            for contour in contours:
                segment.append(contour.flatten().tolist())
            groupId = index
            index += 1
        else:
            segment.append(contours[0].flatten().tolist())
            groupId = 0

        segmentation.append((segment, groupId))

    return segmentation


def _generate_instances(polygon_instances, voc_instances):
    instances = []
    for polygon, group_id in polygon_instances:
        ious = []
        if len(polygon) > 1:
            temp = []
            for poly in polygon:
                temp += poly
        else:
            temp = polygon[0]
        bbox_poly = [
            min(temp[::2]),
            min(temp[1::2]),
            max(temp[::2]),
            max(temp[1::2])
        ]
        for _, bbox in voc_instances:
            ious.append(_iou(bbox_poly, bbox))
        ind = np.argmax(ious)
        for poly in polygon:
            instances.append(
                {
                    'className': voc_instances[ind][0],
                    'polygon': poly,
                    'bbox': voc_instances[ind][1],
                    'groupId': group_id
                }
            )
    return instances


def voc_instance_segmentation_to_sa_vector(voc_root, output_dir):
    classes = []
    object_masks_dir = voc_root / 'SegmentationObject'
    annotation_dir = voc_root / "Annotations"

    file_list = object_masks_dir.glob('*')
    for filename in tqdm(file_list):
        polygon_instances = _generate_polygons(object_masks_dir / filename.name)
        voc_instances = _get_voc_instances_from_xml(
            annotation_dir / filename.name
        )
        maped_instances = _generate_instances(polygon_instances, voc_instances)
        sa_loader = []
        for instance in maped_instances:
            sa_obj = _create_vector_instance(
                'polygon', instance["polygon"], {}, [], instance["className"]
            )
            sa_loader.append(sa_obj)

            classes.append(instance["className"])

        file_name = "%s.jpg___objects.json" % filename.stem
        write_to_json(output_dir / file_name, sa_loader)
    return classes


def voc_object_detection_to_sa_vector(voc_root, output_dir):
    classes = []
    annotation_dir = voc_root / "Annotations"
    files_list = annotation_dir.glob('*')
    for filename in tqdm(files_list):
        voc_instances = _get_voc_instances_from_xml(
            annotation_dir / filename.name
        )
        sa_loader = []
        for class_name, bbox in voc_instances:
            classes.append(class_name)

            points = (bbox[0], bbox[1], bbox[2], bbox[3])
            sa_obj = _create_vector_instance('bbox', points, {}, [], class_name)
            sa_loader.append(sa_obj)

        file_name = "%s.jpg___objects.json" % filename.stem
        write_to_json(output_dir / file_name, sa_loader)
    return classes