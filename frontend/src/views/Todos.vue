<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  Check,
  Dumbbell,
  Pencil,
  Plus,
  Repeat,
  Search,
  Trash2,
  Utensils,
  Wallet,
} from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { http, type LunarInfo, type Tag, type Todo } from '@/api/client'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import QuickEntryDialog, { type QuickKind } from '@/components/quick/QuickEntryDialog.vue'
import TodoDrawer from '@/components/todo/TodoDrawer.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import { formatShortDate, todayISO } from '@/composables/useFormat'

const queryClient = useQueryClient()

const view = ref<'all' | 'today' | 'week' | 'done'>('all')
const tagId = ref<number | null>(null)
const keyword = ref('')
const appliedKeyword = ref('')

const drawerOpen = ref(false)
const editing = ref<Todo | null>(null)
const deleting = ref<Todo | null>(null)
const deleteLoading = ref(false)

const quickKind = ref<QuickKind | null>(null)
const quickOpen = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(keyword, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    appliedKeyword.value = value.trim()
  }, 260)
})

const todosQuery = useQuery({
  queryKey: computed(() => ['todos', view.value, tagId.value, appliedKeyword.value]),
  queryFn: async () => {
    const { data } = await http.get<{ items: Todo[] }>('/todos', {
      params: {
        view: view.value,
        tag_id: tagId.value ?? undefined,
        q: appliedKeyword.value || undefined,
      },
    })
    return data.items
  },
})

const tagsQuery = useQuery({
  queryKey: ['tags', 'todo'],
  queryFn: async () => {
    const { data } = await http.get<{ items: Tag[] }>('/tags', { params: { scope: 'todo' } })
    return data.items
  },
})

const items = computed(() => todosQuery.data.value ?? [])
const tags = computed(() => tagsQuery.data.value ?? [])
const remaining = computed(() => items.value.filter((todo) => !todo.done).length)

function setView(value: string): void {
  view.value = value as typeof view.value
}

const viewOptions = computed(() => [
  { key: 'all', label: '全部', count: items.value.length },
  { key: 'today', label: '今日' },
  { key: 'week', label: '本周' },
  { key: 'done', label: '已完成' },
])

const dueDates = computed(() =>
  [...new Set(items.value.map((todo) => todo.due_date).filter((value): value is string => Boolean(value)))].sort(),
)

const lunarQuery = useQuery({
  queryKey: computed(() => ['lunar-batch', dueDates.value.join(',')]),
  enabled: computed(() => dueDates.value.length > 0),
  staleTime: 1000 * 60 * 60 * 24,
  queryFn: async () => {
    const { data } = await http.get<{ items: Record<string, string> }>('/meta/lunar/batch', {
      params: { days: dueDates.value.join(',') },
    })
    return data.items
  },
})

const lunarMap = computed(() => lunarQuery.data.value ?? {})

const toggle = useMutation({
  mutationFn: async (todo: Todo) => {
    await http.post(`/todos/${todo.id}/toggle`)
  },
  onSuccess: () => queryClient.invalidateQueries(),
})

function openCreate(): void {
  editing.value = null
  drawerOpen.value = true
}

function openEdit(todo: Todo): void {
  editing.value = todo
  drawerOpen.value = true
}

const SYSTEM_KIND: Record<string, QuickKind> = {
  finance: 'transaction',
  exercise: 'exercise',
  diet: 'diet',
}

function systemIcon(key: string | null) {
  if (key === 'finance') return Wallet
  if (key === 'exercise') return Dumbbell
  if (key === 'diet') return Utensils
  return null
}

function openSystem(todo: Todo): void {
  const kind = todo.system_key ? SYSTEM_KIND[todo.system_key] : null
  if (!kind) return
  quickKind.value = kind
  quickOpen.value = true
}

function onTagCreated(): void {
  void queryClient.invalidateQueries({ queryKey: ['tags', 'todo'] })
}

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await http.delete(`/todos/${deleting.value.id}`)
    deleting.value = null
    await queryClient.invalidateQueries()
  } finally {
    deleteLoading.value = false
  }
}

function isOverdue(todo: Todo): boolean {
  return Boolean(todo.due_date && !todo.done && todo.due_date < todayISO())
}
</script>

<template>
  <AppShell>
    <PageHeader title="待办" description="把要做的事排好队，完成一件就少一件。">
      <template #actions>
        <button type="button" class="btn-primary" @click="openCreate">
          <Plus :size="15" :stroke-width="1.5" />
          新增待办
        </button>
      </template>
    </PageHeader>

    <!-- 筛选条 -->
    <div class="mb-4 flex flex-wrap items-center gap-3">
      <SegmentedControl :model-value="view" :options="viewOptions" @update:model-value="setView" />

      <div class="relative ml-auto w-full sm:w-56">
        <Search
          :size="14"
          :stroke-width="1.5"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
        />
        <input v-model="keyword" class="field !py-1.5 !pl-8" placeholder="搜索标题或描述" />
      </div>
    </div>

    <div class="no-scrollbar mb-4 flex items-center gap-1.5 overflow-x-auto pb-1">
      <button
        type="button"
        class="shrink-0 cursor-pointer rounded-full border px-2.5 py-1 text-[11.5px] transition"
        :class="
          tagId === null
            ? 'border-clay-300 bg-clay-100 text-clay-700'
            : 'border-line bg-paper-card text-ink-muted hover:border-line-strong'
        "
        @click="tagId = null"
      >
        全部标签
      </button>
      <button
        v-for="tag in tags"
        :key="tag.id"
        type="button"
        class="shrink-0 cursor-pointer rounded-full border px-2.5 py-1 text-[11.5px] transition"
        :class="
          tagId === tag.id
            ? 'border-clay-300 bg-clay-100 text-clay-700'
            : 'border-line bg-paper-card text-ink-muted hover:border-line-strong'
        "
        @click="tagId = tagId === tag.id ? null : tag.id"
      >
        {{ tag.name }}
      </button>
    </div>

    <!-- 列表 -->
    <div v-if="todosQuery.isPending.value" class="surface divide-y divide-line">
      <div v-for="i in 5" :key="i" class="flex items-center gap-3 px-4 py-4">
        <div class="h-4 w-4 animate-pulse rounded bg-paper-sunken" />
        <div class="h-3.5 flex-1 animate-pulse rounded bg-paper-sunken" />
      </div>
    </div>

    <div v-else-if="items.length" class="surface divide-y divide-line overflow-hidden">
      <div
        v-for="todo in items"
        :key="todo.id"
        class="group flex items-start gap-3 px-4 py-3 transition-colors"
        :class="todo.system_key ? 'bg-clay-50/50' : 'hover:bg-paper-sunken/60'"
      >
        <button
          type="button"
          class="mt-0.5 flex h-[18px] w-[18px] shrink-0 cursor-pointer items-center justify-center rounded-[6px] border transition"
          :class="
            todo.done
              ? 'border-clay-500 bg-clay-500 text-white'
              : 'border-line-strong bg-paper-card text-transparent hover:border-clay-400'
          "
          :aria-label="todo.done ? '标记为未完成' : '标记为已完成'"
          @click="toggle.mutate(todo)"
        >
          <Check :size="12" :stroke-width="2.5" />
        </button>

        <div class="min-w-0 flex-1">
          <div class="flex flex-wrap items-center gap-x-2 gap-y-1">
            <button
              v-if="todo.system_key"
              type="button"
              class="flex cursor-pointer items-center gap-1.5 text-left"
              @click="openSystem(todo)"
            >
              <component
                :is="systemIcon(todo.system_key)"
                :size="13"
                :stroke-width="1.5"
                class="text-clay-600"
              />
              <span
                class="text-[13.5px]"
                :class="todo.done ? 'text-ink-faint line-through' : 'text-ink'"
              >
                {{ todo.title }}
              </span>
              <span class="text-[10.5px] text-clay-600/80">每日固定</span>
            </button>

            <span
              v-else
              class="text-[13.5px]"
              :class="todo.done ? 'text-ink-faint line-through' : 'text-ink'"
            >
              {{ todo.title }}
            </span>

            <Repeat
              v-if="todo.frequency !== 'none'"
              :size="12"
              :stroke-width="1.5"
              class="text-ink-faint"
            />
          </div>

          <p
            v-if="todo.description"
            class="mt-0.5 line-clamp-1 text-[12px] text-ink-muted"
          >
            {{ todo.description }}
          </p>

          <div class="mt-1.5 flex flex-wrap items-center gap-x-3 gap-y-1">
            <span
              v-for="tag in todo.tags"
              :key="tag.id"
              class="rounded-full border border-line bg-paper-card px-2 py-0.5 text-[10.5px] text-ink-muted"
            >
              {{ tag.name }}
            </span>

            <span v-if="todo.due_date" class="num text-[11px]" :class="isOverdue(todo) ? 'text-negative' : 'text-ink-faint'">
              {{ formatShortDate(todo.due_date) }}
              <span v-if="lunarMap[todo.due_date]" class="ml-1">农历{{ lunarMap[todo.due_date] }}</span>
            </span>

            <span v-if="todo.until" class="text-[11px] text-ink-faint">
              至 {{ formatShortDate(todo.until) }}
            </span>
          </div>
        </div>

        <!-- 非系统待办的编辑与删除 -->
        <div
          v-if="!todo.system_key"
          class="flex shrink-0 items-center gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100"
        >
          <button
            type="button"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-card hover:text-ink"
            aria-label="编辑"
            @click="openEdit(todo)"
          >
            <Pencil :size="14" :stroke-width="1.5" />
          </button>
          <button
            type="button"
            class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-card hover:text-negative"
            aria-label="删除"
            @click="deleting = todo"
          >
            <Trash2 :size="14" :stroke-width="1.5" />
          </button>
        </div>
      </div>
    </div>

    <EmptyState
      v-else
      :title="view === 'done' ? '还没有完成的待办' : '这里空空如也'"
      :hint="
        view === 'done'
          ? '完成一件小事，这里就会留下痕迹。'
          : '新增一条待办，或者切换筛选看看其他清单。'
      "
    >
      <button type="button" class="btn-ghost" @click="openCreate">新增待办</button>
    </EmptyState>

    <p class="mt-3 text-right text-[11.5px] text-ink-faint">
      共 {{ items.length }} 条，未完成 {{ remaining }} 条
    </p>

    <TodoDrawer
      :open="drawerOpen"
      :todo="editing"
      :tags="tags"
      @close="drawerOpen = false"
      @saved="queryClient.invalidateQueries()"
      @refresh-tags="onTagCreated"
    />

    <ConfirmDialog
      :open="deleting !== null"
      title="删除待办"
      :message="`确认删除「${deleting?.title ?? ''}」吗？删除后不可恢复。`"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />

    <QuickEntryDialog
      :kind="quickKind"
      :open="quickOpen"
      @close="quickOpen = false"
      @saved="queryClient.invalidateQueries()"
    />
  </AppShell>
</template>
