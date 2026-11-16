<script setup lang="ts">
import { ImagePlus, Loader2, Trash2, X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { http, type Entertainment } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'
import { useUpload } from '@/composables/useUpload'

const props = defineProps<{
  open: boolean
  item: Entertainment | null
  defaultType: Entertainment['ent_type']
  defaultStatus: Entertainment['status']
}>()

const emit = defineEmits<{ close: []; saved: []; remove: [] }>()

const uploader = useUpload()

const title = ref('')
const entType = ref<Entertainment['ent_type']>('movie')
const status = ref<Entertainment['status']>('want')
const year = ref('')
const rating = ref('')
const progress = ref(0)
const review = ref('')
const coverUrl = ref('')
const externalUrl = ref('')
const saving = ref(false)
const error = ref('')
const dragging = ref(false)

const editing = computed(() => props.item !== null)

const TYPES: { value: Entertainment['ent_type']; label: string }[] = [
  { value: 'movie', label: '电影' },
  { value: 'tv', label: '电视剧' },
  { value: 'documentary', label: '纪录片' },
  { value: 'podcast', label: '播客' },
  { value: 'book', label: '书籍' },
]

const STATUSES: { value: Entertainment['status']; label: string }[] = [
  { value: 'want', label: '想看' },
  { value: 'doing', label: '在看' },
  { value: 'done', label: '看完' },
]

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const item = props.item
    title.value = item?.title ?? ''
    entType.value = item?.ent_type ?? props.defaultType
    status.value = item?.status ?? props.defaultStatus
    year.value = item?.year ? String(item.year) : ''
    rating.value = item?.rating ?? ''
    progress.value = item?.progress ?? 0
    review.value = item?.review ?? ''
    coverUrl.value = item?.cover_url ?? ''
    externalUrl.value = item?.external_url ?? ''
    error.value = ''
  },
  { immediate: true },
)

async function handleFile(file: File | undefined): Promise<void> {
  if (!file) return
  const result = await uploader.upload(file)
  if (result) coverUrl.value = result.url
  if (uploader.error.value) error.value = uploader.error.value
}

function onDrop(event: DragEvent): void {
  dragging.value = false
  const file = event.dataTransfer?.files?.[0]
  void handleFile(file)
}

function onPick(event: Event): void {
  const input = event.target as HTMLInputElement
  void handleFile(input.files?.[0])
  input.value = ''
}

async function save(): Promise<void> {
  if (!title.value.trim()) {
    error.value = '请填写标题'
    return
  }

  saving.value = true
  error.value = ''
  const payload = {
    title: title.value.trim(),
    ent_type: entType.value,
    status: status.value,
    year: year.value ? Number(year.value) : null,
    rating: rating.value ? Number(rating.value) : null,
    progress: Math.max(0, Math.min(100, Number(progress.value) || 0)),
    review: review.value || null,
    cover_url: coverUrl.value || null,
    external_url: externalUrl.value || null,
  }

  try {
    if (props.item) {
      await http.patch(`/entertainment/${props.item.id}`, payload)
    } else {
      await http.post('/entertainment', payload)
    }
    emit('saved')
    emit('close')
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppDialog :open="open" :title="editing ? '编辑条目' : '新增条目'" @close="emit('close')">
    <div class="space-y-3">
      <div class="flex gap-4">
        <div
          class="relative flex w-24 shrink-0 flex-col items-center justify-center overflow-hidden rounded-xl border border-dashed text-center transition"
          :class="dragging ? 'border-clay-400 bg-clay-50' : 'border-line bg-paper'"
          style="aspect-ratio: 2 / 3"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <img v-if="coverUrl" :src="coverUrl" alt="" class="h-full w-full object-cover" />
          <div v-else class="flex flex-col items-center gap-1 px-2 text-ink-faint">
            <ImagePlus :size="18" :stroke-width="1.5" />
            <span class="text-[10.5px] leading-tight">拖入图片<br />或点击上传</span>
          </div>

          <label class="absolute inset-0 cursor-pointer">
            <input type="file" accept="image/*" class="hidden" @change="onPick" />
          </label>

          <Loader2
            v-if="uploader.uploading.value"
            :size="16"
            class="absolute animate-spin text-clay-600"
          />
          <button
            v-if="coverUrl"
            type="button"
            class="absolute right-1 top-1 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full bg-ink/60 text-white"
            aria-label="移除封面"
            @click.stop.prevent="coverUrl = ''"
          >
            <X :size="11" :stroke-width="2" />
          </button>
        </div>

        <div class="min-w-0 flex-1 space-y-2.5">
          <div>
            <label class="label-text">标题</label>
            <input v-model="title" class="field" placeholder="片名 / 书名 / 播客名" />
          </div>
          <div>
            <label class="label-text">类型</label>
            <select v-model="entType" class="field">
              <option v-for="option in TYPES" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
      </div>

      <div>
        <label class="label-text">状态</label>
        <div class="flex gap-1 rounded-xl bg-paper-sunken p-1">
          <button
            v-for="option in STATUSES"
            :key="option.value"
            type="button"
            class="flex-1 cursor-pointer rounded-lg py-1.5 text-[12.5px] transition"
            :class="
              status === option.value
                ? 'bg-paper-card text-ink shadow-soft'
                : 'text-ink-muted hover:text-ink'
            "
            @click="status = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div class="grid grid-cols-3 gap-3">
        <div>
          <label class="label-text">年份</label>
          <input v-model="year" type="number" min="1900" max="2100" class="field num" placeholder="2024" />
        </div>
        <div>
          <label class="label-text">评分</label>
          <input v-model="rating" type="number" min="0" max="10" step="0.1" class="field num" placeholder="8.5" />
        </div>
        <div>
          <label class="label-text">进度 %</label>
          <input v-model.number="progress" type="number" min="0" max="100" class="field num" />
        </div>
      </div>

      <div>
        <label class="label-text">备注</label>
        <textarea v-model="review" rows="3" class="field resize-y" placeholder="一句话短评，或者看到哪了" />
      </div>

      <div>
        <label class="label-text">外部链接（选填）</label>
        <input v-model="externalUrl" class="field" placeholder="https://" />
      </div>

      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-2">
        <button
          v-if="editing"
          type="button"
          class="btn-quiet !text-negative"
          @click="emit('remove')"
        >
          <Trash2 :size="14" :stroke-width="1.5" />
        </button>
        <span v-else />

        <div class="flex gap-2">
          <button type="button" class="btn-ghost" @click="emit('close')">取消</button>
          <button type="button" class="btn-primary" :disabled="saving" @click="save">
            {{ saving ? '保存中…' : '保存' }}
          </button>
        </div>
      </div>
    </template>
  </AppDialog>
</template>
