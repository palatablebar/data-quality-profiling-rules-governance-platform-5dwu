// CorrectionStatus — mirror of backend/app/constants/correction_status.py
export enum CorrectionStatus {
  OPEN = 'open',
  FIXED = 'fixed',
}

export const CORRECTION_STATUS_LABELS: Record<string, string> = {
  [CorrectionStatus.OPEN]: '待修正',
  [CorrectionStatus.FIXED]: '已修好',
}

export const CORRECTION_STATUS_LIST = [CorrectionStatus.OPEN, CorrectionStatus.FIXED]
