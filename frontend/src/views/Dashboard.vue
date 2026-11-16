<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  ArrowDownLeft,
  ArrowUpRight,
  Check,
  Dumbbell,
  Moon,
  NotebookPen,
  Plus,
  RefreshCw,
  Scale,
  Utensils,
  Wallet,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { http, type DashboardSummary, type Todo } from '@/api/client'
import AppShell from '@/components/layout/AppShell.vue'
import NotePreviewDialog from '@/components/note/NotePreviewDialog.vue'
import QuickEntryDialog, { type QuickKind } from '@/components/quick/QuickEntryDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatMoney, formatShortDate, greeting } from '@/composables/useFormat'

const queryClient = useQueryClient()

const { data, isPending, isError, refetch } = useQuery({
  queryKey: ['dashboard'],
  queryFn: async () => {
    const { data } = await http.get<DashboardSummary>('/dashboard/summary')
    return data
  },
})

const quickKind = ref<QuickKind | null>(null)
const quickOpen = ref(false)
const previewOpen = ref(false)

const summary = computed(() => data.value)

const quickActions: { kind: QuickKind; label: string; icon: typeof Plus }[] = [
  { kind: 'todo', label: '新增待办', icon: Plus },
  { kind: 'note', label: '新增笔记', icon: NotebookPen },
  { kind: 'transaction', label: '新增收支', icon: Wallet },
  { kind: 'exercise', label: '记录锻炼', icon: Dumbbell },
  { kind: 'diet', label: '记录饮食', icon: Utensils },
  { kind: 'weight', label: '记录体重', icon: Scale },
  { kind: 'sleep', label: '记录睡眠', icon: Moon },
]

function openQuick(kind: QuickKind): void {
  quickKind.value = kind
  quickOpen.value = true
}

const toggle = useMutation({
  mutationFn: async (todo: Todo) => {
    await http.post(`/todos/${todo.id}/toggle`)
  },
  onSuccess: () => queryClient.invalidateQueries(),
})

function systemIcon(key: string | null) {
  if (key === 'finance') return Wallet
  if (key === 'exercise') return Dumbbell
  if (key === 'diet') return Utensils
  return null
}

async function refreshAll(): Promise<void> {
  await queryClient.invalidateQueries()
}
</script>

<template>
  <AppShell>
    <div v-if="isPending" class="space-y-4">
      <div class="h-24 animate-pulse rounded-2xl bg-paper-sunken" />
      <div class="grid gap-4 sm:grid-cols-3">
        <div v-for="i in 3" :key="i" class="h-28 animate-pulse rounded-2xl bg-paper-sunken" />
      </div>
    </div>

    <div v-else-if="summary" class="space-y-6">
      <!-- 顶部问候 -->
      <header class="flex flex-wrap items-end justify-between gap-3">
        <div>
          <p class="text-[12px] text-ink-faint">{{ summary.date }} · 农历{{ summary.lunar }}</p>
          <h1 class="mt-1 text-[26px] font-semibold tracking-tight text-ink">
            {{ greeting() }}，今天也从容一点
          </h1>
        </div>
        <button type="button" class="btn-quiet" @click="refreshAll">
          <RefreshCw :size="14" :stroke-width="1.5" />
          刷新
        </button>
      </header>

      <!-- 三张数字卡 -->
      <section class="grid gap-4 sm:grid-cols-3">
        <article class="surface surface-hover p-5">
          <div class="flex items-center justify-between">
            <span class="text-[12.5px] text-ink-muted">本月收入</span>
            <ArrowDownLeft :size="15" :stroke-width="1.5" class="text-positive" />
          </div>
          <p class="num mt-3 text-[24px] font-semibold tracking-tight text-ink">
            {{ formatMoney(summary.month_income) }}
          </p>
          <div class="mt-3 h-1 overflow-hidden rounded-full bg-paper-sunken">
            <div class="h-full w-2/3 rounded-full bg-positive/60" />
          </div>
        </article>

        <article class="surface surface-hover p-5">
          <div class="flex items-center justify-between">
            <span class="text-[12.5px] text-ink-muted">本月支出</span>
            <ArrowUpRight :size="15" :stroke-width="1.5" class="text-negative" />
          </div>
          <p class="num mt-3 text-[24px] font-semibold tracking-tight text-ink">
            {{ formatMoney(summary.month_expense) }}
          </p>
          <div class="mt-3 h-1 overflow-hidden rounded-full bg-paper-sunken">
            <div class="h-full w-1/3 rounded-full bg-negative/60" />
          </div>
        </article>

        <article class="surface surface-hover p-5">
          <div class="flex items-center justify-between">
            <span class="text-[12.5px] text-ink-muted">总资产</span>
            <Wallet :size="15" :stroke-width="1.5" class="text-clay-500" />
          </div>
          <p class="num mt-3 text-[24px] font-semibold tracking-tight text-ink">
            {{ formatMoney(summary.total_assets) }}
          </p>
          <RouterLink to="/finance" class="mt-3 inline-block text-[11.5px] text-clay-600 hover:underline">
            查看账户明细 →
          </RouterLink>
        </article>
      </section>

      <!-- 待办 -->
      <section class="grid gap-4 lg:grid-cols-2">
        <article class="surface p-5">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-[14px] font-medium text-ink">今日待办</h2>
            <span class="text-[11.5px] text-ink-faint">{{ summary.today_todos.length }} 项</span>
          </div>

          <ul v-if="summary.today_todos.length" class="space-y-1">
            <li v-for="todo in summary.today_todos" :key="todo.id">
              <button
                type="button"
                class="group flex w-full cursor-pointer items-start gap-2.5 rounded-xl px-2 py-2 text-left transition hover:bg-paper-sunken"
                @click="toggle.mutate(todo)"
              >
                <span
                  class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-[5px] border transition"
                  :class="
                    todo.done
                      ? 'border-clay-500 bg-clay-500 text-white'
                      : 'border-line-strong bg-paper-card text-transparent group-hover:border-clay-400'
                  "
                >
                  <Check :size="11" :stroke-width="2.5" />
                </span>
                <span class="min-w-0 flex-1">
                  <span
                    class="block truncate text-[13px] transition"
                    :class="todo.done ? 'text-ink-faint line-through' : 'text-ink'"
                  >
                    {{ todo.title }}
                  </span>
                  <span v-if="todo.system_key" class="mt-0.5 flex items-center gap-1 text-[11px] text-clay-600">
                    <component :is="systemIcon(todo.system_key)" :size="11" :stroke-width="1.5" />
                    每日固定
                  </span>
                </span>
              </button>
            </li>
          </ul>

          <EmptyState
            v-else
            title="今天还没有待办"
            hint="三条每日固定待办会自动生成，也可以在下方快捷入口手动添加。"
            class="!border-0 !py-8"
          />
        </article>

        <article class="surface p-5">
          <div class="mb-3 flex items-center justify-between">
            <h2 class="text-[14px] font-medium text-ink">本周待办</h2>
            <span class="text-[11.5px] text-ink-faint">
              {{ formatShortDate(summary.week_range.start) }} -
              {{ formatShortDate(summary.week_range.end) }}
            </span>
          </div>

          <ul v-if="summary.week_todos.length" class="max-h-[260px] space-y-0.5 overflow-y-auto">
            <li v-for="todo in summary.week_todos" :key="todo.id">
              <button
                type="button"
                class="group flex w-full cursor-pointer items-center gap-2.5 rounded-xl px-2 py-2 text-left transition hover:bg-paper-sunken"
                @click="toggle.mutate(todo)"
              >
                <span
                  class="mt-0.5 flex h-4 w-4 shrink-0 items-center justify-center rounded-[5px] border transition"
                  :class="
                    todo.done
                      ? 'border-clay-500 bg-clay-500 text-white'
                      : 'border-line-strong bg-paper-card text-transparent group-hover:border-clay-400'
                  "
                >
                  <Check :size="11" :stroke-width="2.5" />
                </span>
                <span
                  class="min-w-0 flex-1 truncate text-[13px]"
                  :class="todo.done ? 'text-ink-faint line-through' : 'text-ink'"
                >
                  {{ todo.title }}
                </span>
                <span class="num shrink-0 text-[11px] text-ink-faint">
                  {{ formatShortDate(todo.due_date) }}
                </span>
              </button>
            </li>
          </ul>

          <EmptyState
            v-else
            title="本周暂无安排"
            hint="把想做的事排进本周，节奏会清晰很多。"
            class="!border-0 !py-8"
          />
        </article>
      </section>

      <!-- 随机笔记 + 快捷记录 -->
      <section class="grid items-start gap-4 lg:grid-cols-2">
        <article class="surface p-5">
        <div class="mb-3 flex items-center justify-between">
          <h2 class="text-[14px] font-medium text-ink">随机笔记</h2>
          <button type="button" class="btn-quiet !py-1" @click="refreshAll">
            <RefreshCw :size="13" :stroke-width="1.5" />
            换一篇
          </button>
        </div>

        <button
          v-if="summary.random_note"
          type="button"
          class="w-full cursor-pointer rounded-xl border border-line bg-paper p-4 text-left transition hover:border-clay-300 hover:shadow-soft"
          @click="previewOpen = true"
        >
          <div class="flex flex-wrap items-center gap-2">
            <span
              v-for="tag in summary.random_note.tags"
              :key="tag.id"
              class="rounded-full border border-line bg-paper-card px-2 py-0.5 text-[11px] text-ink-muted"
            >
              {{ tag.name }}
            </span>
          </div>
          <h3 class="mt-2 text-[15px] font-medium text-ink">{{ summary.random_note.title }}</h3>
          <p class="mt-1 line-clamp-2 text-[12.5px] leading-relaxed text-ink-muted">
            {{ summary.random_note.excerpt || '（空白笔记）' }}
          </p>
          <span class="mt-2 inline-block text-[11.5px] text-clay-600">点击预览全文 →</span>
        </button>

        <EmptyState
          v-else
          title="还没有笔记"
          hint="随手记下一点想法，这里会随机抽一篇给你看。"
          class="!border-0 !py-8"
        >
          <button type="button" class="btn-ghost" @click="openQuick('note')">写第一篇</button>
        </EmptyState>
        </article>

        <article class="surface p-5">
        <h2 class="mb-4 text-[14px] font-medium text-ink">快捷记录</h2>
        <div class="grid grid-cols-3 gap-3 sm:grid-cols-4 lg:grid-cols-7">
          <button
            v-for="action in quickActions"
            :key="action.kind"
            type="button"
            class="group flex cursor-pointer flex-col items-center gap-2 rounded-2xl border border-line bg-paper py-4 transition-all duration-200 ease-calm hover:-translate-y-0.5 hover:border-clay-300 hover:shadow-soft"
            @click="openQuick(action.kind)"
          >
            <component
              :is="action.icon"
              :size="19"
              :stroke-width="1.5"
              class="text-clay-600 transition-colors group-hover:text-clay-700"
            />
            <span class="text-[11.5px] text-ink-muted">{{ action.label }}</span>
          </button>
        </div>
        </article>
      </section>
    </div>

    <EmptyState
      v-else
      title="首页数据没有加载出来"
      hint="可能是网络中断或服务暂时不可用，稍后重试一次。"
      icon
    >
      <button v-if="isError" type="button" class="btn-ghost" @click="refetch()">重新加载</button>
    </EmptyState>

    <QuickEntryDialog
      :kind="quickKind"
      :open="quickOpen"
      @close="quickOpen = false"
      @saved="refreshAll"
    />
    <NotePreviewDialog
      :open="previewOpen"
      :note-id="summary?.random_note?.id ?? null"
      @close="previewOpen = false"
    />
  </AppShell>
</template>
