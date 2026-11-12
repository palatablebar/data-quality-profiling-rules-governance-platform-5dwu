"""CorrectionStatus — backend source of truth, mirrored by frontend/src/constants/correctionStatus.ts."""
from enum import Enum


class CorrectionStatus(str, Enum):
    OPEN = "open"    # 待修正：清单内仍未改好的业务行
    FIXED = "fixed"  # 已修好：修正版重传后不再命中，条目关闭


ALL_CORRECTION_STATUSES = [s.value for s in CorrectionStatus]

CORRECTION_STATUS_LABELS = {
    CorrectionStatus.OPEN.value: "待修正",
    CorrectionStatus.FIXED.value: "已修好",
}
