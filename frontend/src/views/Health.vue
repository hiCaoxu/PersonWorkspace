<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  Activity,
  Dumbbell,
  Flame,
  Moon,
  Pencil,
  Plus,
  Scale,
  Trash2,
  Utensils,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'

import {
  http,
  type DietRecord,
  type ExerciseRecord,
  type HealthSummary,
  type SleepRecord,
  type WeightRecord,
} from '@/api/client'
import TrendChart from '@/components/charts/TrendChart.vue'
import HealthRecordDialog, {
  type HealthKind,
} from '@/components/health/HealthRecordDialog.vue'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import {
  formatKcal,
  formatMinutes,
  formatShortDate,
  mealLabel,
  monthRange,
  todayISO,
  weekRange,
} from '@/composables/useFormat'

type AnyRecord = ExerciseRecord | DietRecord | WeightRecord | SleepRecord

const queryClient = useQueryClient()

const rangeKey = ref<'today' | 'week' | 'month'>('week')
const tab = ref<HealthKind>('exercise')
const dialogOpen = ref(false)
const editing = ref<AnyRecord | null>(null)
const deleting = ref<{ kind: HealthKind; record: AnyRecord } | null>(null)
const deleteLoading = ref(false)

const today = todayISO()
const range = computed(() => {
  if (rangeKey.value === 'today') return { start: today, end: today }
  if (rangeKey.value === 'week') return weekRange(today)
  return monthRange(today)
})

const rangeOptions = [
  { key: 'today', label: '今日' },
  { key: 'week', label: '本周' },
  { key: 'month', label: '本月' },
]

function setRange(value: string): void {
  rangeKey.value = value as typeof rangeKey.value
}

const summaryQuery = useQuery({
  queryKey: computed(() => ['health-summary', range.value.start, range.value.end]),
  queryFn: async () => {
    const { data } = await http.get<HealthSummary>('/health/summary', {
      params: range.value,
    })
    return data
  },
})

function listQuery<T>(path: string, key: string) {
  return useQuery({
    queryKey: computed(() => [key, range.value.start, range.value.end]),
    queryFn: async () => {
      const { data } = await http.get<{ items: T[] }>(path, { params: range.value })
      return data.items
    },
  })
}

const exercisesQuery = listQuery<ExerciseRecord>('/health/exercises', 'health-exercises')
const dietsQuery = listQuery<DietRecord>('/health/diets', 'health-diets')
const weightsQuery = listQuery<WeightRecord>('/health/weights', 'health-weights')
const sleepsQuery = listQuery<SleepRecord>('/health/sleeps', 'health-sleeps')

const summary = computed(() => summaryQuery.data.value)
const exercises = computed(() => exercisesQuery.data.value ?? [])
const diets = computed(() => dietsQuery.data.value ?? [])
const weights = computed(() => weightsQuery.data.value ?? [])
const sleeps = computed(() => sleepsQuery.data.value ?? [])

const overview = computed(() => {
  const todayData = summary.value?.today ?? {}
  return [
    {
      key: 'exercise',
      label: '今日锻炼',
      value: formatMinutes(todayData.exercise_minutes as number | null),
      icon: Dumbbell,
    },
    {
      key: 'diet',
      label: '今日摄入',
      value: formatKcal(todayData.kcal_today as string | null),
      icon: Flame,
    },
    {
      key: 'weight',
      label: '最新体重',
      value: todayData.weight_kg ? `${todayData.weight_kg} kg` : '—',
      icon: Scale,
    },
    {
      key: 'sleep',
      label: '今日睡眠',
      value: formatMinutes(todayData.sleep_minutes as number | null),
      icon: Moon,
    },
  ]
})

const tabOptions = computed(() => [
  { key: 'exercise', label: '锻炼', count: exercises.value.length },
  { key: 'diet', label: '饮食', count: diets.value.length },
  { key: 'weight', label: '体重', count: weights.value.length },
  { key: 'sleep', label: '睡眠', count: sleeps.value.length },
])

const currentRecords = computed<AnyRecord[]>(() => {
  if (tab.value === 'exercise') return exercises.value
  if (tab.value === 'diet') return diets.value
  if (tab.value === 'weight') return weights.value
  return sleeps.value
})

function setTab(value: string): void {
  tab.value = value as HealthKind
}

/* ---------- 图表数据 ---------- */
function dailyTotals<T extends { record_date: string }>(
  records: T[],
  value: (record: T) => number,
): { date: string; value: number }[] {
  const map = new Map<string, number>()
  for (const record of records) {
    map.set(record.record_date, (map.get(record.record_date) ?? 0) + value(record))
  }
  return [...map.entries()]
    .map(([date, total]) => ({ date, value: Math.round(total * 10) / 10 }))
    .sort((a, b) => a.date.localeCompare(b.date))
}

const exerciseSeries = computed(() => dailyTotals(exercises.value, (item) => item.duration_min))
const dietSeries = computed(() => dailyTotals(diets.value, (item) => Number(item.calories_kcal)))
const sleepSeries = computed(() =>
  dailyTotals(sleeps.value, (item) => Math.round((item.duration_min / 60) * 10) / 10),
)
const weightPoints = computed(() =>
  [...weights.value].sort((a, b) => a.record_date.localeCompare(b.record_date)),
)

function shortLabels(points: { date: string }[]): string[] {
  return points.map((item) => formatShortDate(item.date))
}

const weightLabels = computed(() => weightPoints.value.map((item) => formatShortDate(item.record_date)))

/* ---------- 行为 ---------- */
function openCreate(): void {
  editing.value = null
  dialogOpen.value = true
}

function openEdit(record: AnyRecord): void {
  editing.value = record
  dialogOpen.value = true
}

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  const { kind, record } = deleting.value
  try {
    await http.delete(`/health/${kind}s/${record.id}`)
    deleting.value = null
    await queryClient.invalidateQueries()
  } finally {
    deleteLoading.value = false
  }
}

function recordTitle(record: AnyRecord): string {
  if (tab.value === 'exercise') return (record as ExerciseRecord).exercise_type
  if (tab.value === 'diet') return (record as DietRecord).food_name
  if (tab.value === 'weight') return `${(record as WeightRecord).weight_kg} kg`
  return formatMinutes((record as SleepRecord).duration_min)
}

function recordMeta(record: AnyRecord): string {
  if (tab.value === 'exercise') {
    const item = record as ExerciseRecord
    const parts = [`${item.duration_min} 分钟`]
    if (item.calories) parts.push(`${item.calories} kcal`)
    if (item.distance_km) parts.push(`${item.distance_km} km`)
    if (item.intensity) parts.push(item.intensity)
    return parts.join(' · ')
  }
  if (tab.value === 'diet') {
    const item = record as DietRecord
    return `${mealLabel(item.meal)} · ${item.quantity_g}g · ${formatKcal(item.calories_kcal)}`
  }
  if (tab.value === 'weight') {
    const item = record as WeightRecord
    return item.body_fat_pct ? `体脂 ${item.body_fat_pct}%` : '仅记录体重'
  }
  const item = record as SleepRecord
  return item.quality ? `质量 ${item.quality}/5` : '未评分'
}

const tabTitle = computed(
  () => ({ exercise: '锻炼记录', diet: '饮食记录', weight: '体重记录', sleep: '睡眠记录' })[tab.value],
)
</script>

<template>
  <AppShell>
    <PageHeader title="健康" description="吃、动、睡与体重，四个维度一起看才有意义。">
      <template #actions>
        <SegmentedControl :model-value="rangeKey" :options="rangeOptions" @update:model-value="setRange" />
        <button type="button" class="btn-primary" @click="openCreate">
          <Plus :size="15" :stroke-width="1.5" />
          新增记录
        </button>
      </template>
    </PageHeader>

    <!-- 今日概览 -->
    <section class="grid grid-cols-2 gap-3 sm:grid-cols-4">
      <article v-for="card in overview" :key="card.key" class="surface p-4">
        <div class="flex items-center justify-between">
          <span class="text-[11.5px] text-ink-muted">{{ card.label }}</span>
          <component :is="card.icon" :size="14" :stroke-width="1.5" class="text-clay-500" />
        </div>
        <p class="num mt-2 text-[17px] font-semibold text-ink">{{ card.value }}</p>
      </article>
    </section>

    <!-- 图表 -->
    <section class="mt-4 grid gap-4 lg:grid-cols-2">
      <article class="surface p-4">
        <h2 class="mb-2 text-[13.5px] font-medium text-ink">体重与体脂</h2>
        <TrendChart
          v-if="weightPoints.length"
          kind="line"
          :categories="weightLabels"
          :series="[
            { name: '体重 (kg)', values: weightPoints.map((item) => Number(item.weight_kg)), color: '#B08968' },
            {
              name: '体脂 (%)',
              values: weightPoints.map((item) => Number(item.body_fat_pct ?? 0)),
              color: '#7A9E7E',
              axis: 1,
            },
          ]"
          :height="220"
        />
        <EmptyState
          v-else
          title="还没有体重记录"
          hint="记录体重后，这里会显示趋势。"
          class="!border-0 !py-8"
          :icon="false"
        />
      </article>

      <article class="surface p-4">
        <h2 class="mb-2 text-[13.5px] font-medium text-ink">锻炼时长（分钟 / 天）</h2>
        <TrendChart
          v-if="exerciseSeries.length"
          kind="bar"
          :categories="shortLabels(exerciseSeries)"
          :series="[{ name: '分钟', values: exerciseSeries.map((item) => item.value), color: '#B08968' }]"
          :height="220"
        />
        <EmptyState
          v-else
          title="这个区间还没有锻炼"
          hint="动一动，记录一条。"
          class="!border-0 !py-8"
          :icon="false"
        />
      </article>

      <article class="surface p-4">
        <h2 class="mb-2 text-[13.5px] font-medium text-ink">热量摄入（kcal / 天）</h2>
        <TrendChart
          v-if="dietSeries.length"
          kind="line"
          :categories="shortLabels(dietSeries)"
          :series="[{ name: 'kcal', values: dietSeries.map((item) => item.value), color: '#C0714F' }]"
          :height="220"
        />
        <EmptyState
          v-else
          title="还没有饮食记录"
          hint="用食物选择器录入，热量自动折算。"
          class="!border-0 !py-8"
          :icon="false"
        />
      </article>

      <article class="surface p-4">
        <h2 class="mb-2 text-[13.5px] font-medium text-ink">睡眠时长（小时 / 天）</h2>
        <TrendChart
          v-if="sleepSeries.length"
          kind="bar"
          :categories="shortLabels(sleepSeries)"
          :series="[{ name: '小时', values: sleepSeries.map((item) => item.value), color: '#8A7F70' }]"
          :height="220"
        />
        <EmptyState
          v-else
          title="还没有睡眠记录"
          hint="睡得好不好，也值得被记住。"
          class="!border-0 !py-8"
          :icon="false"
        />
      </article>
    </section>

    <!-- 记录列表 -->
    <section class="mt-5">
      <div class="mb-3">
        <SegmentedControl :model-value="tab" :options="tabOptions" @update:model-value="setTab" />
      </div>

      <div v-if="summaryQuery.isPending.value" class="surface divide-y divide-line">
        <div v-for="i in 4" :key="i" class="flex items-center gap-3 px-4 py-3.5">
          <div class="h-8 w-8 animate-pulse rounded-xl bg-paper-sunken" />
          <div class="h-3.5 flex-1 animate-pulse rounded bg-paper-sunken" />
        </div>
      </div>

      <div v-else-if="currentRecords.length" class="surface divide-y divide-line overflow-hidden">
        <div
          v-for="record in currentRecords"
          :key="`${tab}-${record.id}`"
          class="group flex items-center gap-3 px-4 py-3 transition hover:bg-paper-sunken/50"
        >
          <span class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-clay-100 text-clay-700">
            <component
              :is="tab === 'exercise' ? Activity : tab === 'diet' ? Utensils : tab === 'weight' ? Scale : Moon"
              :size="15"
              :stroke-width="1.5"
            />
          </span>

          <div class="min-w-0 flex-1">
            <div class="flex items-baseline gap-2">
              <p class="truncate text-[13px] font-medium text-ink">{{ recordTitle(record) }}</p>
              <span class="num shrink-0 text-[11px] text-ink-faint">
                {{ formatShortDate(record.record_date) }}
              </span>
            </div>
            <p class="truncate text-[11.5px] text-ink-muted">{{ recordMeta(record) }}</p>
            <p v-if="record.note" class="mt-0.5 truncate text-[11px] text-ink-faint">{{ record.note }}</p>
          </div>

          <div class="flex shrink-0 items-center gap-0.5 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
            <button
              type="button"
              class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-card hover:text-ink"
              aria-label="编辑"
              @click="openEdit(record)"
            >
              <Pencil :size="14" :stroke-width="1.5" />
            </button>
            <button
              type="button"
              class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-card hover:text-negative"
              aria-label="删除"
              @click="deleting = { kind: tab, record }"
            >
              <Trash2 :size="14" :stroke-width="1.5" />
            </button>
          </div>
        </div>
      </div>

      <EmptyState
        v-else
        :title="`这个区间还没有${tabTitle}`"
        hint="点右上角「新增记录」，或者在首页快捷入口记一条。"
      />
    </section>

    <HealthRecordDialog
      v-if="dialogOpen"
      :open="dialogOpen"
      :kind="tab"
      :record="editing"
      @close="dialogOpen = false"
      @saved="queryClient.invalidateQueries()"
    />

    <ConfirmDialog
      :open="deleting !== null"
      title="删除记录"
      message="确认删除这条健康记录吗？删除后不可恢复。"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
  </AppShell>
</template>
