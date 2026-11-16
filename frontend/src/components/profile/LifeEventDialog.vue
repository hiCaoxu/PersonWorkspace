<script setup lang="ts">
import { ImagePlus, Loader2, Trash2, X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { http, type LifeEvent } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'
import LunarHint from '@/components/ui/LunarHint.vue'
import { todayISO } from '@/composables/useFormat'
import { useUpload } from '@/composables/useUpload'

const props = defineProps<{ open: boolean; event: LifeEvent | null }>()
const emit = defineEmits<{ close: []; saved: []; remove: [] }>()

const uploader = useUpload()

const title = ref('')
const eventDate = ref(todayISO())
const eventType = ref('other')
const location = ref('')
const description = ref('')
const imageUrl = ref('')
const highlight = ref(false)
const saving = ref(false)
const error = ref('')
const dragging = ref(false)

const editing = computed(() => props.event !== null)

const TYPES = [
  { value: 'birth', label: '出生' },
  { value: 'study', label: '求学' },
  { value: 'work', label: '工作' },
  { value: 'travel', label: '旅行' },
  { value: 'family', label: '家庭' },
  { value: 'other', label: '其他' },
]

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const event = props.event
    title.value = event?.title ?? ''
    eventDate.value = event?.event_date ?? todayISO()
    eventType.value = event?.event_type ?? 'other'
    location.value = event?.location ?? ''
    description.value = event?.description ?? ''
    imageUrl.value = event?.image_url ?? ''
    highlight.value = event?.is_highlight ?? false
    error.value = ''
  },
  { immediate: true },
)

async function handleFile(file: File | undefined): Promise<void> {
  if (!file) return
  const result = await uploader.upload(file)
  if (result) imageUrl.value = result.url
  if (uploader.error.value) error.value = uploader.error.value
}

function onDrop(event: DragEvent): void {
  dragging.value = false
  void handleFile(event.dataTransfer?.files?.[0])
}

function onPick(event: Event): void {
  const input = event.target as HTMLInputElement
  void handleFile(input.files?.[0])
  input.value = ''
}

async function save(): Promise<void> {
  if (!title.value.trim()) {
    error.value = '请填写事件标题'
    return
  }

  saving.value = true
  error.value = ''
  const payload = {
    title: title.value.trim(),
    event_date: eventDate.value,
    event_type: eventType.value,
    location: location.value || null,
    description: description.value || null,
    image_url: imageUrl.value || null,
    is_highlight: highlight.value,
  }

  try {
    if (props.event) {
      await http.patch(`/life-events/${props.event.id}`, payload)
    } else {
      await http.post('/life-events', payload)
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
  <AppDialog :open="open" :title="editing ? '编辑人生大事' : '记录人生大事'" wide @close="emit('close')">
    <div class="space-y-3">
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label-text">标题</label>
          <input v-model="title" class="field" placeholder="如：毕业、第一份工作" />
        </div>
        <div>
          <label class="label-text">类型</label>
          <select v-model="eventType" class="field">
            <option v-for="option in TYPES" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
      </div>

      <div>
        <label class="label-text">日期</label>
        <input v-model="eventDate" type="date" class="field num" />
        <LunarHint :date="eventDate" />
      </div>

      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label-text">地点</label>
          <input v-model="location" class="field" placeholder="城市 / 学校 / 公司" />
        </div>
        <div class="flex items-end">
          <label class="flex cursor-pointer items-center gap-2 text-[12.5px] text-ink-muted">
            <input v-model="highlight" type="checkbox" class="h-4 w-4 accent-clay-500" />
            标记为重要节点
          </label>
        </div>
      </div>

      <div>
        <label class="label-text">描述</label>
        <textarea v-model="description" rows="3" class="field resize-y" placeholder="当时发生了什么" />
      </div>

      <div>
        <label class="label-text">配图</label>
        <div
          class="flex items-start gap-3"
          @dragover.prevent="dragging = true"
          @dragleave.prevent="dragging = false"
          @drop.prevent="onDrop"
        >
          <div
            v-if="imageUrl"
            class="relative h-24 w-32 overflow-hidden rounded-xl border border-line"
          >
            <img :src="imageUrl" alt="" class="h-full w-full object-cover" />
            <button
              type="button"
              class="absolute right-1 top-1 flex h-5 w-5 cursor-pointer items-center justify-center rounded-full bg-ink/60 text-white"
              aria-label="移除配图"
              @click="imageUrl = ''"
            >
              <X :size="11" :stroke-width="2" />
            </button>
          </div>

          <label
            class="flex h-24 w-32 cursor-pointer flex-col items-center justify-center gap-1 rounded-xl border border-dashed text-[11px] transition"
            :class="dragging ? 'border-clay-400 bg-clay-50 text-clay-700' : 'border-line text-ink-faint hover:border-clay-300'"
          >
            <Loader2 v-if="uploader.uploading.value" :size="16" class="animate-spin" />
            <ImagePlus v-else :size="17" :stroke-width="1.5" />
            选择图片
            <input type="file" accept="image/*" class="hidden" @change="onPick" />
          </label>
        </div>
      </div>

      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex items-center justify-between gap-2">
        <button v-if="editing" type="button" class="btn-quiet !text-negative" @click="emit('remove')">
          <Trash2 :size="14" :stroke-width="1.5" />
          删除
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
