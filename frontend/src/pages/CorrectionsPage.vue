<template>
  <div class="paper-page">
    <PageHeader
      eyebrow="correction ledger"
      title="纠错台账"
      subtitle="报送前的待修正清单：命中行按业务键归并，修正版整份重传后只结转清单——修好的关闭，没修好的继续，重复执行不新增。"
      :meta="meta"
    >
      <template #actions>
        <select v-model="datasetId" class="input !w-[220px]" @change="reload">
          <option v-for="dataset in datasetStore.items" :key="dataset.id" :value="dataset.id">{{ dataset.name }}</option>
        </select>
      </template>
    </PageHeader>

    <PermissionNotice v-if="!auth.canWrite" class="mb-3" />

    <div class="flex flex-wrap items-center gap-3 py-2 text-[11.5px]">
      <span class="eyebrow">业务键列</span>
      <select v-model="keyColumn" class="input !w-[200px]" :disabled="!auth.canWrite">
        <option :value="null">未设置（按行号锚定）</option>
        <option v-for="column in columns" :key="column" :value="column">{{ column }}</option>
      </select>
      <button class="btn !py-1" :disabled="!auth.canWrite || !keyDirty" @click="saveKey">保存键列</button>
      <span class="text-ink-soft">键列变更会清空台账，下一批次按新键重建</span>
      <span v-if="keyMessage" class="text-emerald-700">{{ keyMessage }}</span>
      <span v-if="keyError" class="text-red-600">{{ keyError }}</span>
    </div>

    <CorrectionSummaryCards :summary="correctionStore.summary" />

    <div class="flex items-center gap-2 py-2 text-[11.5px]">
      <span class="eyebrow">状态</span>
      <button
        v-for="option in statusOptions"
        :key="option.label"
        class="btn btn-quiet !px-2 !py-0.5"
        :class="{ 'font-semibold underline': filters.status === option.value }"
        @click="pickStatus(option.value)"
      >
        {{ option.label }}
      </button>
    </div>

    <ErrorNotice :error="correctionStore.error" />

    <CorrectionTable :items="correctionStore.items" />

    <EmptyState
      v-if="!correctionStore.items.length && !correctionStore.loading"
      class="mt-6"
      title="清单是空的"
      description="执行一次规则批次后，命中行会按业务键进入待修正清单；修正版重传后再执行，这里只结转不重复。"
    >
      <RouterLink to="/runs" class="btn">去看执行台账</RouterLink>
    </EmptyState>

    <div class="mt-8 border-t border-rule pt-3 flex items-center justify-between text-[10.5px] text-ink-soft">
      <span>共 {{ correctionStore.total }} 条清单记录 · 同一业务行在同一规则下只计一条</span>
      <span v-if="correctionStore.pages > 1" class="tabular-nums">
        <button class="link-button" :disabled="correctionStore.page <= 1" @click="turnPage(-1)">上一页</button>
        {{ correctionStore.page }} / {{ correctionStore.pages }}
        <button class="link-button" :disabled="correctionStore.page >= correctionStore.pages" @click="turnPage(1)">下一页</button>
      </span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute } from 'vue-router'
import PageHeader from '../components/common/PageHeader.vue'
import EmptyState from '../components/common/EmptyState.vue'
import ErrorNotice from '../components/common/ErrorNotice.vue'
import PermissionNotice from '../components/common/PermissionNotice.vue'
import CorrectionSummaryCards from '../components/correction/CorrectionSummaryCards.vue'
import CorrectionTable from '../components/correction/CorrectionTable.vue'
import { useCorrectionStore } from '../stores/correctionStore'
import { useDatasetStore } from '../stores/datasetStore'
import { useAuthStore } from '../stores/authStore'
import { useCorrectionFilter } from '../hooks/useCorrectionFilter'
import { fetchProfile } from '../api/profile'
import { updateBusinessKey } from '../api/correction'
import { CorrectionStatus, CORRECTION_STATUS_LABELS } from '../constants/correctionStatus'

const route = useRoute()
const correctionStore = useCorrectionStore()
const datasetStore = useDatasetStore()
const auth = useAuthStore()
const { filters, apply } = useCorrectionFilter()

const datasetId = ref<number | null>(null)
const columns = ref<string[]>([])
const keyColumn = ref<string | null>(null)
const keyMessage = ref('')
const keyError = ref('')

const statusOptions = [
  { label: '全部', value: null },
  { label: CORRECTION_STATUS_LABELS[CorrectionStatus.OPEN], value: CorrectionStatus.OPEN },
  { label: CORRECTION_STATUS_LABELS[CorrectionStatus.FIXED], value: CorrectionStatus.FIXED },
]

const keyDirty = computed(() => keyColumn.value !== (correctionStore.summary?.business_key_column ?? null))
const meta = computed(() => [
  { label: '待修正业务行', value: String(correctionStore.summary?.open_bad_rows ?? '-') },
  { label: '最终可用记录', value: String(correctionStore.summary?.usable_rows ?? '-') },
  { label: '已修好', value: String(correctionStore.summary?.fixed_entries ?? '-') },
])

onMounted(async () => {
  if (!datasetStore.items.length) await datasetStore.load()
  const fromQuery = Number(route.query.dataset ?? 0)
  datasetId.value = fromQuery || datasetStore.items[0]?.id || null
  await reload()
})

async function reload() {
  if (!datasetId.value) return
  keyMessage.value = ''
  keyError.value = ''
  await correctionStore.load(datasetId.value)
  keyColumn.value = correctionStore.summary?.business_key_column ?? null
  try {
    const profile = await fetchProfile(datasetId.value)
    columns.value = profile.columns.map((column) => column.column_name)
  } catch {
    columns.value = []
  }
  const current = correctionStore.summary?.business_key_column
  if (current && !columns.value.includes(current)) columns.value = [current, ...columns.value]
}

async function saveKey() {
  if (!datasetId.value) return
  keyMessage.value = ''
  keyError.value = ''
  try {
    await updateBusinessKey(datasetId.value, keyColumn.value)
    keyMessage.value = '已保存，台账将在下一批次按新键重建'
    await datasetStore.load()
    await correctionStore.load(datasetId.value)
  } catch (error) {
    keyError.value = (error as { message?: string }).message ?? '保存失败'
  }
}

async function pickStatus(value: string | null) {
  filters.status = value
  await apply()
}

async function turnPage(delta: number) {
  await correctionStore.load(null, correctionStore.page + delta)
}
</script>
