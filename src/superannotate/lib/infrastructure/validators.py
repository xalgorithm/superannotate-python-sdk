from collections import defaultdict

from lib.core.types import PixelAnnotation
from lib.core.types import VectorAnnotation
from lib.core.validators import BaseAnnotationValidator
from lib.core.validators import BaseValidator
from pydantic import ValidationError


def wrap_error(e: ValidationError) -> str:
    error_messages = defaultdict(list)
    for error in e.errors():
        errors_list = list(error["loc"])
        errors_list[1::2] = [f"[{i}]" for i in errors_list[1::2]]
        errors_list[2::2] = [f".{i}" for i in errors_list[2::2]]
        error_messages["".join(errors_list)].append(error["msg"])
    texts = ["\n"]
    for field, text in error_messages.items():
        texts.append(
            "{} {}{}".format(
                field, " " * (48 - len(field)), f"\n {' ' * 48}".join(text)
            )
        )
    return "\n".join(texts)


class BaseSchemaValidator(BaseValidator):
    MODEL = PixelAnnotation

    @classmethod
    def validate(cls, data: dict):
        cls.MODEL(**data)

    def is_valid(self) -> bool:
        try:
            self.validate(self._data)
        except ValidationError as e:
            self._validation_output = e
        return not bool(self._validation_output)

    def generate_report(self) -> str:
        return wrap_error(self._validation_output)


class PixelValidator(BaseSchemaValidator):
    MODEL = PixelAnnotation


class VectorValidator(BaseSchemaValidator):
    MODEL = VectorAnnotation


class AnnotationValidator(BaseAnnotationValidator):
    @classmethod
    def get_pixel_validator(cls):
        return PixelValidator

    @classmethod
    def get_vector_validator(cls):
        return VectorValidator

    @classmethod
    def get_video_validator(cls):
        raise NotImplementedError