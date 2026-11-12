import { reactive } from 'vue'
import { useCorrectionStore } from '../stores/correctionStore'
import type { CorrectionFilterState } from '../stores/correctionStore'

export function useCorrectionFilter(initial: Partial<CorrectionFilterState> = {}) {
  const store = useCorrectionStore()
  const filters = reactive<CorrectionFilterState>({
    status: initial.status ?? null,
  })

  async function apply() {
    store.filters = { ...filters }
    await store.load()
  }

  function reset() {
    filters.status = null
    apply()
  }

  return { filters, apply, reset }
}
