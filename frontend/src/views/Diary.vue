<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  ChevronLeft,
  ChevronRight,
  CloudSun,
  RotateCcw,
  Sparkles,
} from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'

import { http } from '@/api/client'
import AppShell from '@/components/layout/AppShell.vue'
import { shiftDate, todayISO } from '@/composables/useFormat'

interface DiaryEntry {
  id: number
  diary_date: string
  title: string
  content: string
  mood: string | null
  weather: string | null
  lunar: string
  updated_at: string
}

const queryClient = useQueryClient()

const today = todayISO()
const selectedDate = ref(today)
const [initialYear, initialMonth] = today.split('-').map(Number)
const cursor = ref({ year: initialYear, month: initialMonth })

const MOODS = ['平静', '愉悦', '充实', '疲惫', '低落']
const WEATHERS = ['晴', '多云', '阴', '雨', '雪']

const entryQuery = useQuery({
  queryKey: computed(() => ['diary', selectedDate.value]),
  queryFn: async () => {
    const { data } = await http.get<DiaryEntry>(`/diaries/by-date/${selectedDate.value}`)
    return data
  },
})

const monthQuery = useQuery({
  queryKey: computed(() => ['diary-month', cursor.value.year, cursor.value.month]),
  queryFn: async () => {
    const { data } = await http.get<{ items: { id: number; diary_date: string }[] }>('/diaries', {
      params: { year: cursor.value.year, month: cursor.value.month },
    })
    return data.items
  },
})

const markedDates = computed(
  () => new Set((monthQuery.data.value ?? []).map((item) => item.diary_date)),
)

/* ---------- 日历 ---------- */
const WEEK_LABELS = ['一', '二', '三', '四', '五', '六', '日']

const calendarCells = computed(() => {
  const { year, month } = cursor.value
  const first = new Date(year, month - 1, 1)
  const offset = (first.getDay() + 6) % 7
  const total = new Date(year, month, 0).getDate()
  const cells: { key: string; date: string | null; day: number }[] = []

  for (let i = 0; i < offset; i += 1) {
    cells.push({ key: `blank-${i}`, date: null, day: 0 })
  }
  for (let day = 1; day <= total; day += 1) {
    const iso = `${year}-${String(month).padStart(2, '0')}-${String(day).padStart(2, '0')}`
    cells.push({ key: iso, date: iso, day })
  }
  return cells
})

const monthLabel = computed(() => `${cursor.value.year} 年 ${cursor.value.month} 月`)

function shiftMonth(delta: number): void {
  const date = new Date(cursor.value.year, cursor.value.month - 1 + delta, 1)
  cursor.value = { year: date.getFullYear(), month: date.getMonth() + 1 }
}

function pickDate(iso: string): void {
  void openDate(iso)
  const [year, month] = iso.split('-').map(Number)
  cursor.value = { year, month }
}

/* ---------- 编辑与自动保存 ---------- */
const draft = ref({ content: '', mood: null as string | null, weather: null as string | null })
const status = ref<'idle' | 'saving' | 'saved'>('idle')
let snapshot = ''
let saveTimer: ReturnType<typeof setTimeout> | null = null
let suppress = false

watch(
  () => entryQuery.data.value,
  async (entry) => {
    if (!entry) return
    suppress = true
    draft.value = { content: entry.content, mood: entry.mood, weather: entry.weather }
    snapshot = JSON.stringify(draft.value)
    status.value = 'idle'
    await nextTick()
    suppress = false
  },
  { immediate: true },
)

watch(
  draft,
  () => {
    if (suppress) return
    if (JSON.stringify(draft.value) === snapshot) return
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => void saveNow(), 800)
  },
  { deep: true },
)

async function saveNow(): Promise<void> {
  const entry = entryQuery.data.value
  if (!entry) return
  if (JSON.stringify(draft.value) === snapshot) return
  const current = JSON.stringify(draft.value)
  status.value = 'saving'
  try {
    const { data: updated } = await http.patch<DiaryEntry>(`/diaries/${entry.id}`, {
      content: draft.value.content,
      mood: draft.value.mood,
      weather: draft.value.weather,
    })
    // 同步缓存，避免离开后再进入时先看到旧正文
    queryClient.setQueryData(['diary', selectedDate.value], updated)
    snapshot = current
    status.value = 'saved'
    void queryClient.invalidateQueries({ queryKey: ['diary-month'] })
  } catch {
    status.value = 'idle'
  }
}

async function flush(): Promise<void> {
  if (saveTimer) {
    clearTimeout(saveTimer)
    saveTimer = null
  }
  await saveNow()
}

async function openDate(iso: string): Promise<void> {
  if (iso === selectedDate.value) return
  await flush()
  selectedDate.value = iso
}

function step(delta: number): void {
  const next = shiftDate(selectedDate.value, delta)
  const [year, month] = next.split('-').map(Number)
  cursor.value = { year, month }
  void openDate(next)
}

function backToday(): void {
  cursor.value = { year: initialYear, month: initialMonth }
  void openDate(today)
}

function toggleMood(value: string): void {
  draft.value.mood = draft.value.mood === value ? null : value
}

function toggleWeather(value: string): void {
  draft.value.weather = draft.value.weather === value ? null : value
}

const statusLabel = computed(() => {
  if (status.value === 'saving') return '保存中…'
  if (status.value === 'saved') return '已保存'
  return '自动保存'
})

onBeforeUnmount(() => {
  void flush()
})
</script>

<template>
  <AppShell>
    <header class="mb-5">
      <h1 class="text-[22px] font-semibold tracking-tight text-ink">日记</h1>
      <p class="mt-1 text-[13px] text-ink-muted">
        每天自动一篇，标题按 ISO 周生成，写下就当留档。
      </p>
    </header>

    <div class="grid gap-4 lg:grid-cols-[300px_minmax(0,1fr)]">
      <!-- 月历 -->
      <aside class="surface h-fit p-4 lg:sticky lg:top-6">
        <div class="mb-3 flex items-center justify-between">
          <button
            type="button"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-muted hover:bg-paper-sunken"
            aria-label="上个月"
            @click="shiftMonth(-1)"
          >
            <ChevronLeft :size="15" :stroke-width="1.5" />
          </button>
          <span class="text-[13px] font-medium text-ink">{{ monthLabel }}</span>
          <button
            type="button"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-muted hover:bg-paper-sunken"
            aria-label="下个月"
            @click="shiftMonth(1)"
          >
            <ChevronRight :size="15" :stroke-width="1.5" />
          </button>
        </div>

        <div class="mb-1 grid grid-cols-7 gap-1">
          <span
            v-for="label in WEEK_LABELS"
            :key="label"
            class="flex h-6 items-center justify-center text-[11px] text-ink-faint"
          >
            {{ label }}
          </span>
        </div>

        <div class="grid grid-cols-7 gap-1">
          <template v-for="cell in calendarCells" :key="cell.key">
            <span v-if="!cell.date" class="h-9" />
            <button
              v-else
              type="button"
              class="relative flex h-9 cursor-pointer flex-col items-center justify-center rounded-lg text-[12.5px] transition"
              :class="
                cell.date === selectedDate
                  ? 'bg-clay-500 text-white'
                  : cell.date === today
                    ? 'border border-clay-300 text-clay-700 hover:bg-clay-50'
                    : 'text-ink hover:bg-paper-sunken'
              "
              @click="pickDate(cell.date)"
            >
              {{ cell.day }}
              <span
                v-if="markedDates.has(cell.date)"
                class="absolute bottom-1 h-1 w-1 rounded-full"
                :class="cell.date === selectedDate ? 'bg-white/80' : 'bg-clay-400'"
              />
            </button>
          </template>
        </div>

        <p class="mt-3 border-t border-line pt-3 text-[11px] text-ink-faint">
          暖褐小圆点表示当天已写下内容。
        </p>
      </aside>

      <!-- 正文 -->
      <section class="surface flex min-h-[70vh] flex-col p-5 sm:p-7">
        <div v-if="entryQuery.isPending.value" class="space-y-4">
          <div class="h-8 w-2/3 animate-pulse rounded bg-paper-sunken" />
          <div class="h-4 w-1/3 animate-pulse rounded bg-paper-sunken" />
          <div class="h-40 animate-pulse rounded-xl bg-paper-sunken" />
        </div>

        <template v-else-if="entryQuery.data.value">
          <header>
            <h2 class="text-[24px] font-semibold leading-snug tracking-tight text-ink sm:text-[28px]">
              {{ entryQuery.data.value.title }}
            </h2>
            <p class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-[12px] text-ink-faint">
              <span class="flex items-center gap-1">
                <CloudSun :size="12" :stroke-width="1.5" />
                农历{{ entryQuery.data.value.lunar }}
              </span>
              <span>·</span>
              <span>{{ statusLabel }}</span>
            </p>
          </header>

          <div class="mt-4 flex flex-wrap items-center gap-1.5">
            <span class="text-[11.5px] text-ink-faint">天气</span>
            <button
              v-for="item in WEATHERS"
              :key="item"
              type="button"
              class="cursor-pointer rounded-full border px-2.5 py-1 text-[11.5px] transition"
              :class="
                draft.weather === item
                  ? 'border-clay-300 bg-clay-100 text-clay-700'
                  : 'border-line bg-paper-card text-ink-muted hover:border-line-strong'
              "
              @click="toggleWeather(item)"
            >
              {{ item }}
            </button>
          </div>

          <div class="mt-2 flex flex-wrap items-center gap-1.5">
            <span class="text-[11.5px] text-ink-faint">心情</span>
            <button
              v-for="item in MOODS"
              :key="item"
              type="button"
              class="cursor-pointer rounded-full border px-2.5 py-1 text-[11.5px] transition"
              :class="
                draft.mood === item
                  ? 'border-clay-300 bg-clay-100 text-clay-700'
                  : 'border-line bg-paper-card text-ink-muted hover:border-line-strong'
              "
              @click="toggleMood(item)"
            >
              {{ item }}
            </button>
          </div>

          <textarea
            v-model="draft.content"
            rows="16"
            class="mt-4 min-h-[320px] flex-1 resize-none border-0 bg-transparent text-[14px] leading-[1.9] text-ink placeholder:text-ink-faint focus:outline-none"
            placeholder="今天发生了什么？想到什么就写什么。"
          />

          <footer class="mt-4 flex flex-wrap items-center justify-between gap-2 border-t border-line pt-3">
            <div class="flex items-center gap-1.5">
              <button type="button" class="btn-quiet !px-2 !py-1.5" @click="step(-1)">
                <ChevronLeft :size="15" :stroke-width="1.5" />
                前一天
              </button>
              <button type="button" class="btn-quiet !px-2 !py-1.5" @click="step(1)">
                后一天
                <ChevronRight :size="15" :stroke-width="1.5" />
              </button>
            </div>

            <button type="button" class="btn-ghost !py-1.5" @click="backToday">
              <RotateCcw :size="13" :stroke-width="1.5" />
              回到今天
            </button>
          </footer>
        </template>

        <div v-else class="flex flex-1 items-center justify-center">
          <p class="flex items-center gap-2 text-[13px] text-ink-faint">
            <Sparkles :size="15" :stroke-width="1.5" />
            这一天的日记没有加载出来，试着切换日期。
          </p>
        </div>
      </section>
    </div>
  </AppShell>
</template>
