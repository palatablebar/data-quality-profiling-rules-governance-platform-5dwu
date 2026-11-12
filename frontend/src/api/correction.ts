import http from './http'
import type { CorrectionItem, CorrectionSummary } from '../types/correction'
import type { Dataset } from '../types/dataset'
import type { Page } from '../types/api'

export interface CorrectionFilters {
  status?: string | null
  page?: number
  page_size?: number
}

export async function fetchCorrections(datasetId: number, filters: CorrectionFilters = {}): Promise<Page<CorrectionItem>> {
  const params: Record<string, unknown> = {}
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== null && value !== undefined && value !== '') params[key] = value
  })
  const { data } = await http.get<Page<CorrectionItem>>(`/datasets/${datasetId}/corrections`, { params })
  return data
}

export async function fetchCorrectionSummary(datasetId: number): Promise<CorrectionSummary> {
  const { data } = await http.get<CorrectionSummary>(`/datasets/${datasetId}/corrections/summary`)
  return data
}

export async function updateBusinessKey(datasetId: number, businessKeyColumn: string | null): Promise<Dataset> {
  const { data } = await http.patch<Dataset>(`/datasets/${datasetId}`, { business_key_column: businessKeyColumn })
  return data
}
