<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  Columns2,
  Eye,
  FileText,
  Pencil,
  Plus,
  Search,
  Trash2,
} from 'lucide-vue-next'
import { computed, nextTick, onBeforeUnmount, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { http, type Note, type Tag } from '@/api/client'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import MarkdownEditor from '@/components/markdown/MarkdownEditor.vue'
import MarkdownPreview from '@/components/markdown/MarkdownPreview.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import TagEditor from '@/components/ui/TagEditor.vue'
import { formatDate } from '@/composables/useFormat'

interface Draft {
  id: number
  title: string
  content_md: string
  tag_ids: number[]
}

const router = useRouter()
const route = useRoute()
const queryClient = useQueryClient()

const keyword = ref('')
const appliedKeyword = ref('')
const tagFilter = ref<number | null>(null)
const selectedId = ref<number | null>(null)
const draft = ref<Draft | null>(null)
const mode = ref<'split' | 'edit' | 'preview'>('split')
const status = ref<'idle' | 'saving' | 'saved'>('idle')
const deleting = ref(false)
const deleteLoading = ref(false)

let searchTimer: ReturnType<typeof setTimeout> | null = null
watch(keyword, (value) => {
  if (searchTimer) clearTimeout(searchTimer)
  searchTimer = setTimeout(() => {
    appliedKeyword.value = value.trim()
  }, 260)
})

const notesQuery = useQuery({
  queryKey: computed(() => ['notes', appliedKeyword.value, tagFilter.value]),
  queryFn: async () => {
    const { data } = await http.get<{ items: Note[] }>('/notes', {
      params: {
        q: appliedKeyword.value || undefined,
        tag_id: tagFilter.value ?? undefined,
      },
    })
    return data.items
  },
})

const tagsQuery = useQuery({
  queryKey: ['tags', 'note'],
  queryFn: async () => {
    const { data } = await http.get<{ items: Tag[] }>('/tags', { params: { scope: 'note' } })
    return data.items
  },
})

const notes = computed(() => notesQuery.data.value ?? [])
const tags = computed(() => tagsQuery.data.value ?? [])

const detailQuery = useQuery({
  queryKey: computed(() => ['note', selectedId.value]),
  enabled: computed(() => selectedId.value !== null),
  queryFn: async () => {
    const { data } = await http.get<Note>(`/notes/${selectedId.value}`)
    return data
  },
})

/* ---------- 自动保存 ---------- */
let snapshot = ''
let saveTimer: ReturnType<typeof setTimeout> | null = null
let suppress = false

function snapshotOf(value: Draft): string {
  return JSON.stringify({ title: value.title, content_md: value.content_md, tag_ids: value.tag_ids })
}

watch(
  () => detailQuery.data.value,
  async (note) => {
    if (!note) return
    suppress = true
    draft.value = {
      id: note.id,
      title: note.title,
      content_md: note.content_md ?? '',
      tag_ids: note.tags.map((tag) => tag.id),
    }
    snapshot = snapshotOf(draft.value)
    status.value = 'idle'
    await nextTick()
    suppress = false
  },
)

watch(
  draft,
  () => {
    if (suppress || !draft.value) return
    if (snapshotOf(draft.value) === snapshot) return
    if (saveTimer) clearTimeout(saveTimer)
    saveTimer = setTimeout(() => void saveNow(), 900)
  },
  { deep: true },
)

async function saveNow(): Promise<void> {
  if (!draft.value) return
  if (snapshotOf(draft.value) === snapshot) return
  const payload = {
    title: draft.value.title || '无标题',
    content_md: draft.value.content_md,
    tag_ids: draft.value.tag_ids,
  }
  const current = snapshotOf(draft.value)
  status.value = 'saving'
  try {
    await http.patch(`/notes/${draft.value.id}`, payload)
    snapshot = current
    status.value = 'saved'
    await queryClient.invalidateQueries({ queryKey: ['notes'] })
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

async function selectNote(id: number): Promise<void> {
  if (selectedId.value === id) return
  await flush()
  selectedId.value = id
  void router.replace({ query: { id: String(id) } })
}

async function createNote(): Promise<void> {
  await flush()
  const { data } = await http.post<Note>('/notes', { title: '无标题', content_md: '' })
  await queryClient.invalidateQueries({ queryKey: ['notes'] })
  selectedId.value = data.id
  void router.replace({ query: { id: String(data.id) } })
}

async function confirmDelete(): Promise<void> {
  if (!draft.value) return
  deleteLoading.value = true
  try {
    await http.delete(`/notes/${draft.value.id}`)
    deleting.value = false
    draft.value = null
    selectedId.value = null
    snapshot = ''
    void router.replace({ query: {} })
    await queryClient.invalidateQueries()
  } finally {
    deleteLoading.value = false
  }
}

function setMode(value: string): void {
  mode.value = value as typeof mode.value
}

function onTagCreated(): void {
  void queryClient.invalidateQueries({ queryKey: ['tags', 'note'] })
}

const modeOptions = [
  { key: 'split', label: '分栏' },
  { key: 'edit', label: '编辑' },
  { key: 'preview', label: '预览' },
]

const saveLabel = computed(() => {
  if (status.value === 'saving') return '保存中…'
  if (status.value === 'saved') return '已自动保存'
  return '自动保存已开启'
})

onBeforeUnmount(() => {
  void flush()
})

const queryId = Number(route.query.id)
if (Number.isFinite(queryId) && queryId > 0) {
  selectedId.value = queryId
}

// 支持在同一页面内通过地址栏切换笔记（例如从首页预览跳转）
watch(
  () => route.query.id,
  (value) => {
    const id = Number(value)
    if (Number.isFinite(id) && id > 0 && id !== selectedId.value) {
      selectedId.value = id
    }
  },
)
</script>

<template>
  <AppShell>
    <PageHeader title="笔记" description="随手写下的东西，值得留在一个安静的地方。">
      <template #actions>
        <button type="button" class="btn-primary" @click="createNote">
          <Plus :size="15" :stroke-width="1.5" />
          新建笔记
        </button>
      </template>
    </PageHeader>

    <div class="grid gap-4 lg:grid-cols-[280px_minmax(0,1fr)]">
      <!-- 左栏 -->
      <aside class="surface flex max-h-[calc(100vh-190px)] flex-col overflow-hidden lg:sticky lg:top-6">
        <div class="border-b border-line p-3">
          <div class="relative">
            <Search
              :size="14"
              :stroke-width="1.5"
              class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
            />
            <input v-model="keyword" class="field !py-1.5 !pl-8" placeholder="搜索笔记" />
          </div>

          <div class="no-scrollbar mt-2 flex gap-1.5 overflow-x-auto pb-0.5">
            <button
              type="button"
              class="shrink-0 cursor-pointer rounded-full border px-2 py-0.5 text-[11px] transition"
              :class="
                tagFilter === null
                  ? 'border-clay-300 bg-clay-100 text-clay-700'
                  : 'border-line bg-paper-card text-ink-muted'
              "
              @click="tagFilter = null"
            >
              全部
            </button>
            <button
              v-for="tag in tags"
              :key="tag.id"
              type="button"
              class="shrink-0 cursor-pointer rounded-full border px-2 py-0.5 text-[11px] transition"
              :class="
                tagFilter === tag.id
                  ? 'border-clay-300 bg-clay-100 text-clay-700'
                  : 'border-line bg-paper-card text-ink-muted'
              "
              @click="tagFilter = tagFilter === tag.id ? null : tag.id"
            >
              {{ tag.name }}
            </button>
          </div>
        </div>

        <div class="min-h-0 flex-1 overflow-y-auto p-2">
          <div v-if="notesQuery.isPending.value" class="space-y-2 p-1">
            <div v-for="i in 4" :key="i" class="h-16 animate-pulse rounded-xl bg-paper-sunken" />
          </div>

          <template v-else>
            <button
              v-for="note in notes"
              :key="note.id"
              type="button"
              class="mb-1 w-full cursor-pointer rounded-xl border px-3 py-2.5 text-left transition"
              :class="
                selectedId === note.id
                  ? 'border-clay-200 bg-clay-50'
                  : 'border-transparent hover:border-line hover:bg-paper-sunken/60'
              "
              @click="selectNote(note.id)"
            >
              <p class="truncate text-[13px] font-medium text-ink">{{ note.title || '无标题' }}</p>
              <p class="mt-1 line-clamp-2 text-[11.5px] leading-relaxed text-ink-muted">
                {{ note.excerpt || '（空白笔记）' }}
              </p>
              <div class="mt-1.5 flex flex-wrap items-center gap-1.5">
                <span
                  v-for="tag in note.tags"
                  :key="tag.id"
                  class="rounded-full border border-line bg-paper-card px-1.5 py-0.5 text-[10px] text-ink-muted"
                >
                  {{ tag.name }}
                </span>
                <span class="num ml-auto text-[10px] text-ink-faint">
                  {{ formatDate(note.updated_at).replace('年', '/').replace('月', '/').replace('日', '') }}
                </span>
              </div>
            </button>
          </template>

          <EmptyState
            v-if="!notesQuery.isPending.value && notes.length === 0"
            title="还没有笔记"
            hint="点右上角新建，写下第一行字。"
            class="!border-0 !py-8"
            :icon="false"
          />
        </div>
      </aside>

      <!-- 主区 -->
      <section v-if="draft" class="surface flex min-h-[70vh] flex-col overflow-hidden">
        <div class="border-b border-line px-4 py-3">
          <div class="flex flex-wrap items-center gap-3">
            <input
              v-model="draft.title"
              class="min-w-0 flex-1 rounded-lg border-0 bg-transparent px-1 py-0.5 text-[17px] font-semibold text-ink placeholder:text-ink-faint focus:outline-none focus:ring-0 focus-visible:ring-0"
              placeholder="笔记标题"
            />

            <span class="text-[11.5px] text-ink-faint">{{ saveLabel }}</span>

            <div class="hidden sm:block">
              <SegmentedControl :model-value="mode" :options="modeOptions" @update:model-value="setMode" />
            </div>

            <button
              type="button"
              class="flex h-8 w-8 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-sunken hover:text-negative"
              aria-label="删除笔记"
              @click="deleting = true"
            >
              <Trash2 :size="15" :stroke-width="1.5" />
            </button>
          </div>

          <div class="mt-2">
            <TagEditor
              v-model="draft.tag_ids"
              :tags="tags"
              scope="note"
              @created="onTagCreated"
            />
          </div>
        </div>

        <!-- 移动端模式切换 -->
        <div class="flex items-center gap-2 border-b border-line px-4 py-2 sm:hidden">
          <button
            v-for="option in modeOptions.filter((item) => item.key !== 'split')"
            :key="option.key"
            type="button"
            class="flex cursor-pointer items-center gap-1.5 rounded-lg px-2.5 py-1 text-[12px] transition"
            :class="
              mode === option.key || (mode === 'split' && option.key === 'edit')
                ? 'bg-clay-100 text-clay-700'
                : 'text-ink-muted'
            "
            @click="setMode(option.key)"
          >
            <component
              :is="option.key === 'edit' ? Pencil : Eye"
              :size="13"
              :stroke-width="1.5"
            />
            {{ option.label }}
          </button>
        </div>

        <div
          class="grid min-h-0 flex-1 lg:divide-x lg:divide-line"
          :class="mode === 'split' ? 'lg:grid-cols-2' : 'grid-cols-1'"
        >
          <div
            class="min-h-[320px] overflow-hidden"
            :class="mode === 'preview' ? 'hidden' : 'block'"
          >
            <MarkdownEditor v-model="draft.content_md" placeholder="支持 Markdown，右侧实时预览" />
          </div>

          <div
            v-if="mode !== 'edit'"
            class="hidden min-h-[320px] overflow-y-auto px-4 py-3 lg:block"
          >
            <MarkdownPreview :content="draft.content_md" />
          </div>
        </div>

        <div class="hidden items-center gap-2 border-t border-line px-4 py-2 text-[11px] text-ink-faint lg:flex">
          <Columns2 :size="12" :stroke-width="1.5" />
          左侧编写，右侧实时预览；代码块自动高亮并显示行号。
        </div>

        <!-- 移动端预览 -->
        <div
          v-if="mode === 'preview'"
          class="min-h-[320px] flex-1 overflow-y-auto px-4 py-3 lg:hidden"
        >
          <MarkdownPreview :content="draft.content_md" />
        </div>
      </section>

      <section v-else class="surface flex min-h-[60vh] items-center justify-center">
        <EmptyState
          title="选择一篇笔记开始"
          hint="左侧列表点选笔记，或新建一篇。编辑内容会自动保存。"
          class="!border-0"
        >
          <button type="button" class="btn-ghost" @click="createNote">
            <FileText :size="14" :stroke-width="1.5" />
            新建笔记
          </button>
        </EmptyState>
      </section>
    </div>

    <ConfirmDialog
      :open="deleting"
      title="删除笔记"
      :message="`确认删除「${draft?.title || '无标题'}」吗？删除后不可恢复。`"
      :loading="deleteLoading"
      @cancel="deleting = false"
      @confirm="confirmDelete"
    />
  </AppShell>
</template>
