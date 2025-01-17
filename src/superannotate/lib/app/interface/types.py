from functools import wraps
from typing import Union

from lib.core.enums import AnnotationStatus
from lib.core.enums import ProjectType
from lib.core.exceptions import AppException
from lib.infrastructure.validators import wrap_error
from pydantic import constr
from pydantic import StrictStr
from pydantic import validate_arguments as pydantic_validate_arguments
from pydantic import ValidationError

NotEmptyStr = constr(strict=True, min_length=1)


class Status(StrictStr):
    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        if cls.curtail_length and len(value) > cls.curtail_length:
            value = value[: cls.curtail_length]
        if value.lower() not in AnnotationStatus.values():
            raise TypeError(
                f"Available statuses is {', '.join(AnnotationStatus.titles())}. "
            )
        return value


class AnnotationType(StrictStr):
    VALID_TYPES = ["bbox", "polygon", "point"]

    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        if value.lower() not in cls.VALID_TYPES:
            raise TypeError(
                f"Available annotation_types are {', '.join(cls.VALID_TYPES)}. "
            )
        return value


class ImageQualityChoices(StrictStr):
    VALID_CHOICES = ["compressed", "original"]

    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        super().validate(value)
        if value.lower() not in cls.VALID_CHOICES:
            raise TypeError(
                f"Image quality available choices are {', '.join(cls.VALID_CHOICES)}."
            )
        return value.lower()


class ProjectTypes(StrictStr):
    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        if value.lower() not in ProjectType.values():
            raise TypeError(
                f"Available annotation_statuses are {', '.join(ProjectType.titles())}. "
            )
        return value


class AnnotationStatuses(StrictStr):
    @classmethod
    def validate(cls, value: Union[str]) -> Union[str]:
        if value.lower() not in AnnotationStatus.values():
            raise TypeError(
                f"Available annotation_statuses are {', '.join(AnnotationStatus.titles())}. "
            )
        return value


def validate_arguments(func):
    @wraps(func)
    def wrapped(*args, **kwargs):
        try:
            return pydantic_validate_arguments(func)(*args, **kwargs)
        except ValidationError as e:
            raise AppException(wrap_error(e))

    return wrapped
