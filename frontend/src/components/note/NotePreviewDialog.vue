<script setup lang="ts">
import { Pencil } from 'lucide-vue-next'
import { useQuery } from '@tanstack/vue-query'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import { http, type Note } from '@/api/client'
import MarkdownPreview from '@/components/markdown/MarkdownPreview.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import { formatDate } from '@/composables/useFormat'

const props = defineProps<{ open: boolean; noteId: number | null }>()
const emit = defineEmits<{ close: [] }>()

const router = useRouter()

const query = useQuery({
  queryKey: computed(() => ['note-preview', props.noteId]),
  enabled: computed(() => props.open && props.noteId !== null),
  queryFn: async () => {
    const { data } = await http.get<Note>(`/notes/${props.noteId}`)
    return data
  },
})

function goEdit(): void {
  const id = props.noteId
  emit('close')
  router.push({ path: '/notes', query: { id: String(id) } })
}
</script>

<template>
  <AppDialog :open="open" title="笔记预览" wide @close="emit('close')">
    <div v-if="query.isPending.value" class="py-10 text-center text-[13px] text-ink-faint">
      正在加载…
    </div>

    <article v-else-if="query.data.value" class="animate-fade-up">
      <header class="mb-4 border-b border-line pb-3">
        <div class="flex items-start justify-between gap-3">
          <h1 class="text-[22px] font-semibold leading-snug text-ink">
            {{ query.data.value.title }}
          </h1>
          <button type="button" class="btn-ghost shrink-0 !py-1.5" @click="goEdit">
            <Pencil :size="14" :stroke-width="1.5" />
            编辑
          </button>
        </div>
        <div class="mt-2 flex flex-wrap items-center gap-2">
          <span
            v-for="tag in query.data.value.tags"
            :key="tag.id"
            class="rounded-full border border-line bg-paper px-2 py-0.5 text-[11px] text-ink-muted"
          >
            {{ tag.name }}
          </span>
          <span class="text-[11.5px] text-ink-faint">
            更新于 {{ formatDate(query.data.value.updated_at) }}
          </span>
        </div>
      </header>

      <MarkdownPreview :content="query.data.value.content_md ?? ''" />
    </article>

    <div v-else class="py-10 text-center text-[13px] text-ink-faint">笔记不存在或已被删除</div>
  </AppDialog>
</template>
