export interface CorrectionItem {
  id: number
  dataset_id: number
  rule_id: number | null
  rule_name: string
  column_name: string
  severity: string
  severity_label: string
  business_key: string
  key_occurrence: number
  row_index: number
  first_row_index: number
  observed_value: string | null
  expected_expr: string | null
  status: string
  status_label: string
  first_seen_run_id: number | null
  last_seen_run_id: number | null
  fixed_run_id: number | null
  fixed_at: string | null
  created_at: string | null
  updated_at: string | null
}

export interface CorrectionSummary {
  dataset_id: number
  business_key_column: string | null
  total_rows: number
  open_entries: number
  open_bad_rows: number
  usable_rows: number
  fixed_entries: number
  balanced: boolean
  as_of_run_id: number | null
}

// 单个批次对台账的结转快照（后端 rule_runs.correction_json）
export interface RunCorrectionEffect {
  created: number
  still_open: number
  reopened: number
  fixed: number
  open_entries: number
  open_bad_rows: number
  usable_rows: number
  total_rows: number
  balanced: boolean
  business_key_column: string | null
}
