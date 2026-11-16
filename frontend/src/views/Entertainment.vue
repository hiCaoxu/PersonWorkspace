<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  BookOpen,
  Clapperboard,
  Film,
  GripVertical,
  Mic,
  Plus,
  Search,
  Tv,
} from 'lucide-vue-next'
import { computed, reactive, ref, watch } from 'vue'
import { VueDraggable } from 'vue-draggable-plus'

import { http, type Entertainment } from '@/api/client'
import EntertainmentDialog from '@/components/entertainment/EntertainmentDialog.vue'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'

type EntType = Entertainment['ent_type']
type EntStatus = Entertainment['status']

const queryClient = useQueryClient()

const entType = ref<EntType>('movie')
const keyword = ref('')
const appliedKeyword = ref('')
const dialogOpen = ref(false)
const editing = ref<Entertainment | null>(null)
const defaultStatus = ref<EntStatus>('want')
const deleting = ref<Entertainment | null>(null)
const deleteLoading = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(keyword, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    appliedKeyword.value = value.trim()
  }, 260)
})

const TYPES: { value: EntType; label: string; icon: typeof Film }[] = [
  { value: 'movie', label: '电影', icon: Film },
  { value: 'tv', label: '电视剧', icon: Tv },
  { value: 'documentary', label: '纪录片', icon: Clapperboard },
  { value: 'podcast', label: '播客', icon: Mic },
  { value: 'book', label: '书籍', icon: BookOpen },
]

const COLUMNS: { value: EntStatus; label: string }[] = [
  { value: 'want', label: '想看' },
  { value: 'doing', label: '在看' },
  { value: 'done', label: '看完' },
]

const typeLabel = computed(() => TYPES.find((item) => item.value === entType.value)?.label ?? '')
const typeOptions = TYPES.map((item) => ({ key: item.value, label: item.label }))

const itemsQuery = useQuery({
  queryKey: computed(() => ['entertainment', entType.value, appliedKeyword.value]),
  queryFn: async () => {
    const { data } = await http.get<{ items: Entertainment[] }>('/entertainment', {
      params: {
        ent_type: entType.value,
        q: appliedKeyword.value || undefined,
      },
    })
    return data.items
  },
})

const columns = reactive<Record<EntStatus, Entertainment[]>>({ want: [], doing: [], done: [] })
const draggingBoard = ref(false)

watch(
  () => itemsQuery.data.value,
  (list) => {
    const source = list ?? []
    columns.want = source.filter((item) => item.status === 'want')
    columns.doing = source.filter((item) => item.status === 'doing')
    columns.done = source.filter((item) => item.status === 'done')
  },
  { immediate: true },
)

const counts = computed(() => ({
  want: columns.want.length,
  doing: columns.doing.length,
  done: columns.done.length,
}))

async function syncStatuses(): Promise<void> {
  const changes: Entertainment[] = []
  for (const column of COLUMNS) {
    for (const item of columns[column.value]) {
      if (item.status !== column.value) changes.push(item)
    }
  }
  if (!changes.length) return

  await Promise.all(
    changes.map(async (item) => {
      const target = COLUMNS.find((column) => columns[column.value].includes(item))?.value
      if (!target || target === item.status) return
      const previous = item.status
      item.status = target
      if (target === 'done') item.progress = 100
      try {
        await http.patch(`/entertainment/${item.id}/status`, null, { params: { status: target } })
      } catch {
        item.status = previous
      }
    }),
  )
  await queryClient.invalidateQueries({ queryKey: ['entertainment'] })
}

function openCreate(status: EntStatus): void {
  editing.value = null
  defaultStatus.value = status
  dialogOpen.value = true
}

function openEdit(item: Entertainment): void {
  // 拖拽结束会紧接着触发一次 click，避免误打开编辑弹窗
  if (draggingBoard.value) return
  editing.value = item
  dialogOpen.value = true
}

function onDragStart(): void {
  draggingBoard.value = true
}

async function onDragEnd(): Promise<void> {
  await syncStatuses()
  setTimeout(() => {
    draggingBoard.value = false
  }, 120)
}

function typeIcon(type: EntType) {
  return TYPES.find((item) => item.value === type)?.icon ?? Film
}

function setType(value: string): void {
  entType.value = value as EntType
}

function onRemove(): void {
  if (!editing.value) return
  deleting.value = editing.value
  dialogOpen.value = false
}

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await http.delete(`/entertainment/${deleting.value.id}`)
    deleting.value = null
    await queryClient.invalidateQueries({ queryKey: ['entertainment'] })
  } finally {
    deleteLoading.value = false
  }
}
</script>

<template>
  <AppShell>
    <PageHeader title="娱乐" description="电影、剧、纪录片、播客与书，想看就在看，看完再评价。">
      <template #actions>
        <button type="button" class="btn-primary" @click="openCreate('want')">
          <Plus :size="15" :stroke-width="1.5" />
          新增{{ typeLabel }}
        </button>
      </template>
    </PageHeader>

    <div class="mb-4 flex flex-wrap items-center gap-3">
      <SegmentedControl :model-value="entType" :options="typeOptions" @update:model-value="setType" />

      <div class="relative ml-auto w-full sm:w-56">
        <Search
          :size="14"
          :stroke-width="1.5"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
        />
        <input v-model="keyword" class="field !py-1.5 !pl-8" placeholder="搜索标题或备注" />
      </div>
    </div>

    <div :key="entType" class="grid gap-4 animate-fade-up md:grid-cols-3">
      <section v-for="column in COLUMNS" :key="column.value" class="flex flex-col">
        <div class="mb-2 flex items-center justify-between px-1">
          <h2 class="flex items-center gap-1.5 text-[13px] font-medium text-ink">
            {{ column.label }}
            <span class="num text-[11px] text-ink-faint">{{ counts[column.value] }}</span>
          </h2>
        </div>

        <VueDraggable
          v-model="columns[column.value]"
          :group="{ name: 'entertainment' }"
          item-key="id"
          :animation="160"
          ghost-class="drag-ghost"
          drag-class="drag-active"
          class="min-h-[120px] flex-1 space-y-2 rounded-2xl bg-paper-sunken/40 p-2"
          @start="onDragStart"
          @end="onDragEnd"
        >
          <article
            v-for="item in columns[column.value]"
            :key="item.id"
            class="group cursor-pointer rounded-xl border border-line bg-paper-card p-2.5 shadow-soft transition-all duration-200 ease-calm hover:-translate-y-0.5 hover:border-line-strong hover:shadow-lift"
            @click="openEdit(item)"
          >
            <div class="flex gap-2.5">
              <div
                class="w-14 shrink-0 overflow-hidden rounded-lg bg-paper-sunken"
                style="aspect-ratio: 2 / 3"
              >
                <img
                  v-if="item.cover_url"
                  :src="item.cover_url"
                  alt=""
                  class="h-full w-full object-cover"
                  loading="lazy"
                />
                <div v-else class="flex h-full w-full items-center justify-center text-clay-400">
                  <component :is="typeIcon(item.ent_type)" :size="18" :stroke-width="1.5" />
                </div>
              </div>

              <div class="min-w-0 flex-1">
                <div class="flex items-start gap-1">
                  <p class="line-clamp-2 flex-1 text-[12.5px] font-medium leading-snug text-ink">
                    {{ item.title }}
                  </p>
                  <GripVertical
                    :size="13"
                    :stroke-width="1.5"
                    class="mt-0.5 shrink-0 cursor-grab text-ink-faint opacity-0 transition group-hover:opacity-100"
                  />
                </div>

                <p class="num mt-1 text-[10.5px] text-ink-faint">
                  <span v-if="item.year">{{ item.year }}</span>
                  <span v-if="item.rating"> · {{ item.rating }} 分</span>
                  <span v-if="!item.year && !item.rating">未标注</span>
                </p>

                <div v-if="item.progress > 0 && item.status !== 'done'" class="mt-1.5">
                  <div class="h-1 overflow-hidden rounded-full bg-paper-sunken">
                    <div class="h-full rounded-full bg-clay-400" :style="{ width: `${item.progress}%` }" />
                  </div>
                  <p class="num mt-0.5 text-[10px] text-ink-faint">{{ item.progress }}%</p>
                </div>

                <p
                  v-if="item.review"
                  class="mt-1 line-clamp-2 text-[10.5px] leading-relaxed text-ink-muted"
                >
                  {{ item.review }}
                </p>
              </div>
            </div>
          </article>

          <button
            type="button"
            class="flex w-full cursor-pointer items-center justify-center gap-1.5 rounded-xl border border-dashed border-line py-2.5 text-[11.5px] text-ink-faint transition hover:border-clay-300 hover:bg-paper-card hover:text-clay-700"
            @click="openCreate(column.value)"
          >
            <Plus :size="13" :stroke-width="1.5" />
            添加到{{ column.label }}
          </button>
        </VueDraggable>
      </section>
    </div>

    <EntertainmentDialog
      v-if="dialogOpen"
      :open="dialogOpen"
      :item="editing"
      :default-type="entType"
      :default-status="defaultStatus"
      @close="dialogOpen = false"
      @saved="queryClient.invalidateQueries({ queryKey: ['entertainment'] })"
      @remove="onRemove"
    />

    <ConfirmDialog
      :open="deleting !== null"
      title="删除条目"
      :message="`确认删除「${deleting?.title ?? ''}」吗？删除后不可恢复。`"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
  </AppShell>
</template>
