import { defineStore } from 'pinia'
import { fetchCorrectionSummary, fetchCorrections } from '../api/correction'
import type { CorrectionItem, CorrectionSummary } from '../types/correction'

export interface CorrectionFilterState {
  status: string | null
}

interface CorrectionState {
  datasetId: number | null
  items: CorrectionItem[]
  summary: CorrectionSummary | null
  total: number
  page: number
  pages: number
  filters: CorrectionFilterState
  loading: boolean
  error: string
}

export const useCorrectionStore = defineStore('correction', {
  state: (): CorrectionState => ({
    datasetId: null,
    items: [],
    summary: null,
    total: 0,
    page: 1,
    pages: 1,
    filters: { status: null },
    loading: false,
    error: '',
  }),
  actions: {
    async load(datasetId?: number | null, page = 1) {
      const target = datasetId ?? this.datasetId
      if (!target) {
        this.items = []
        this.summary = null
        this.total = 0
        return
      }
      this.datasetId = target
      this.loading = true
      this.error = ''
      try {
        const [list, summary] = await Promise.all([
          fetchCorrections(target, { status: this.filters.status, page, page_size: 50 }),
          fetchCorrectionSummary(target),
        ])
        this.items = list.items
        this.total = list.total
        this.page = list.page
        this.pages = list.pages
        this.summary = summary
      } catch (error) {
        this.error = (error as { message?: string }).message ?? '纠错台账加载失败'
      } finally {
        this.loading = false
      }
    },
  },
})
