<template>
  <div v-if="summary" class="border-y border-rule py-3">
    <div class="flex flex-wrap items-baseline gap-x-8 gap-y-2">
      <div>
        <div class="label">原文件行数</div>
        <div class="text-[15px] tabular-nums">{{ summary.total_rows.toLocaleString() }}</div>
      </div>
      <div class="text-ink-soft text-[13px]">=</div>
      <div>
        <div class="label">最终可用记录</div>
        <div class="text-[15px] tabular-nums">{{ summary.usable_rows.toLocaleString() }}</div>
      </div>
      <div class="text-ink-soft text-[13px]">+</div>
      <div>
        <div class="label">待修正业务行（去重）</div>
        <div class="text-[15px] tabular-nums">{{ summary.open_bad_rows.toLocaleString() }}</div>
      </div>
      <span
        class="text-[10.5px] px-1.5 py-0.5 border"
        :class="summary.balanced ? 'border-emerald-300 text-emerald-700' : 'border-red-300 text-red-600'"
      >
        {{ summary.balanced ? '对账平衡' : '对账不平' }}
      </span>
    </div>
    <div class="mt-2 flex flex-wrap gap-x-6 gap-y-1 text-[10.5px] text-ink-soft tabular-nums">
      <span>清单条目（按规则计） {{ summary.open_entries }}</span>
      <span>已修好关闭 {{ summary.fixed_entries }}</span>
      <span>业务键列 {{ summary.business_key_column ?? '未设置（按行号锚定）' }}</span>
      <span v-if="summary.as_of_run_id">截至批次 #{{ summary.as_of_run_id }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import type { CorrectionSummary } from '../../types/correction'

defineProps<{ summary: CorrectionSummary | null }>()
</script>
