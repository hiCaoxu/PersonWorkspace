<script setup lang="ts">
import { Plus } from 'lucide-vue-next'
import { ref } from 'vue'

import { http, type Tag } from '@/api/client'

const props = defineProps<{
  modelValue: number[]
  tags: Tag[]
  scope: 'todo' | 'note'
}>()

const emit = defineEmits<{
  'update:modelValue': [number[]]
  created: [Tag]
}>()

const draft = ref('')
const creating = ref(false)
const error = ref('')

function toggle(id: number): void {
  const next = props.modelValue.includes(id)
    ? props.modelValue.filter((item) => item !== id)
    : [...props.modelValue, id]
  emit('update:modelValue', next)
}

async function create(): Promise<void> {
  const name = draft.value.trim()
  if (!name) return
  const exists = props.tags.find((tag) => tag.name === name)
  if (exists) {
    if (!props.modelValue.includes(exists.id)) toggle(exists.id)
    draft.value = ''
    return
  }

  creating.value = true
  error.value = ''
  try {
    const { data } = await http.post<Tag>('/tags', { name, scope: props.scope })
    emit('created', data)
    emit('update:modelValue', [...props.modelValue, data.id])
    draft.value = ''
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    creating.value = false
  }
}
</script>

<template>
  <div>
    <div class="flex flex-wrap items-center gap-1.5">
      <button
        v-for="tag in tags"
        :key="tag.id"
        type="button"
        class="cursor-pointer rounded-full border px-2.5 py-1 text-[11.5px] transition"
        :class="
          modelValue.includes(tag.id)
            ? 'border-clay-300 bg-clay-100 text-clay-700'
            : 'border-line bg-paper-card text-ink-muted hover:border-line-strong hover:text-ink'
        "
        @click="toggle(tag.id)"
      >
        {{ tag.name }}
      </button>

      <div class="flex items-center gap-1">
        <input
          v-model="draft"
          class="w-24 rounded-full border border-dashed border-line bg-transparent px-2.5 py-1 text-[11.5px] text-ink placeholder:text-ink-faint focus:border-clay-300 focus:outline-none"
          placeholder="新标签"
          @keydown.enter.prevent="create"
        />
        <button
          type="button"
          class="flex h-6 w-6 cursor-pointer items-center justify-center rounded-full text-ink-faint hover:bg-paper-sunken hover:text-clay-700"
          :disabled="creating"
          aria-label="添加标签"
          @click="create"
        >
          <Plus :size="13" :stroke-width="1.5" />
        </button>
      </div>
    </div>
    <p v-if="error" class="mt-1 text-[11.5px] text-negative">{{ error }}</p>
  </div>
</template>
