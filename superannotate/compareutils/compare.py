import sys
from .analyzer import Analyzer
from ..common import SA_CM_COMPARE_ACCURATE, SA_CM_COMPARE_FAST


def compare(gt_path = None, target_path = None):
    analyzer_obj = Analyzer(gt_path, target_path )

    confusion_matrix = analyzer_obj.compare_all()

    return confusion_matrix
