<template>
  <table v-if="items.length" class="table-base mt-1">
    <thead>
      <tr>
        <th class="w-[170px]">业务键</th>
        <th class="w-[64px] text-right">原行</th>
        <th class="w-[64px] text-right">当前行</th>
        <th>规则 / 列</th>
        <th class="w-[240px]">命中原因</th>
        <th class="w-[80px]">状态</th>
        <th class="w-[130px]">批次</th>
      </tr>
    </thead>
    <tbody>
      <tr v-for="item in items" :key="item.id">
        <td class="tabular-nums text-[11.5px] break-all">
          {{ item.business_key
          }}<span v-if="item.key_occurrence > 1" class="text-ink-soft">#{{ item.key_occurrence }}</span>
        </td>
        <td class="num">{{ item.first_row_index }}</td>
        <td class="num">{{ item.row_index }}</td>
        <td>
          <div class="text-[12px]">{{ item.rule_name }}</div>
          <div class="text-[10.5px] text-ink-soft">{{ item.column_name }} · {{ item.severity_label }}</div>
        </td>
        <td class="text-[11.5px] break-all">
          <span v-if="item.observed_value === ''" class="text-ink-soft">（空）</span>
          <span v-else>{{ item.observed_value }}</span>
          <span class="text-ink-soft"> → {{ item.expected_expr }}</span>
        </td>
        <td class="text-[11.5px]">
          <span :class="item.status === 'open' ? 'text-amber-700' : 'text-emerald-700'">{{ item.status_label }}</span>
        </td>
        <td class="text-[10.5px] text-ink-soft tabular-nums">
          <div>首中 #{{ item.first_seen_run_id ?? '-' }}</div>
          <div v-if="item.status === 'open'">最近 #{{ item.last_seen_run_id ?? '-' }}</div>
          <div v-else>关闭 #{{ item.fixed_run_id ?? '-' }}</div>
        </td>
      </tr>
    </tbody>
  </table>
</template>

<script setup lang="ts">
import type { CorrectionItem } from '../../types/correction'

defineProps<{ items: CorrectionItem[] }>()
</script>
