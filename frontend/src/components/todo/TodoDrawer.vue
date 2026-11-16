<script setup lang="ts">
import { X } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { http, type Tag, type Todo } from '@/api/client'
import TagEditor from '@/components/ui/TagEditor.vue'
import LunarHint from '@/components/ui/LunarHint.vue'
import { todayISO } from '@/composables/useFormat'

const props = defineProps<{
  open: boolean
  todo: Todo | null
  tags: Tag[]
}>()

const emit = defineEmits<{
  close: []
  saved: []
  'refresh-tags': [Tag]
}>()

const WEEKDAY_OPTIONS = [
  { value: 0, label: '一' },
  { value: 1, label: '二' },
  { value: 2, label: '三' },
  { value: 3, label: '四' },
  { value: 4, label: '五' },
  { value: 5, label: '六' },
  { value: 6, label: '日' },
]

type FrequencyChoice = Todo['frequency'] | 'custom'

const FREQUENCY_OPTIONS: { value: FrequencyChoice; label: string }[] = [
  { value: 'none', label: '不循环' },
  { value: 'daily', label: '每天' },
  { value: 'weekly', label: '每周' },
  { value: 'monthly', label: '每月' },
  { value: 'yearly', label: '每年' },
  { value: 'custom', label: '自定义…' },
]

const UNIT_OPTIONS: { value: Exclude<Todo['frequency'], 'none'>; label: string }[] = [
  { value: 'daily', label: '天' },
  { value: 'weekly', label: '周' },
  { value: 'monthly', label: '月' },
  { value: 'yearly', label: '年' },
]

const title = ref('')
const description = ref('')
const dueDate = ref(todayISO())
const frequency = ref<FrequencyChoice>('none')
const customUnit = ref<Exclude<Todo['frequency'], 'none'>>('daily')
const interval = ref(1)
const weekdays = ref<number[]>([])
const until = ref('')
const tagIds = ref<number[]>([])
const saving = ref(false)
const error = ref('')

const editing = computed(() => props.todo !== null)
const effectiveFrequency = computed(() =>
  frequency.value === 'custom' ? customUnit.value : frequency.value,
)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    error.value = ''
    const todo = props.todo
    title.value = todo?.title ?? ''
    description.value = todo?.description ?? ''
    dueDate.value = todo?.due_date ?? todayISO()
    frequency.value = todo?.frequency ?? 'none'
    if (todo?.frequency && todo.frequency !== 'none') customUnit.value = todo.frequency
    interval.value = todo?.interval ?? 1
    weekdays.value = todo?.weekdays ?? []
    until.value = todo?.until ?? ''
    tagIds.value = todo ? todo.tags.map((tag) => tag.id) : []
  },
  { immediate: true },
)

function toggleWeekday(value: number): void {
  weekdays.value = weekdays.value.includes(value)
    ? weekdays.value.filter((item) => item !== value)
    : [...weekdays.value, value].sort()
}

function onTagCreated(tag: Tag): void {
  emit('refresh-tags', tag)
}

async function save(): Promise<void> {
  if (!title.value.trim()) {
    error.value = '请填写待办标题'
    return
  }

  saving.value = true
  error.value = ''
  const payload = {
    title: title.value.trim(),
    description: description.value.trim() || null,
    due_date: dueDate.value || null,
    frequency: effectiveFrequency.value,
    interval: Math.max(1, Number(interval.value) || 1),
    weekdays: effectiveFrequency.value === 'weekly' ? weekdays.value : [],
    until: until.value || null,
    tag_ids: tagIds.value,
  }

  try {
    if (props.todo) {
      await http.patch(`/todos/${props.todo.id}`, payload)
    } else {
      await http.post('/todos', payload)
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
  <Teleport to="body">
    <div v-if="open" class="fixed inset-0 z-40">
      <div class="absolute inset-0 bg-ink/20 backdrop-blur-[1px]" @click="emit('close')" />
      <aside
        class="absolute right-0 top-0 flex h-full w-full max-w-[420px] flex-col border-l border-line bg-paper-card shadow-pop animate-slide-in-right"
      >
        <header class="flex shrink-0 items-center justify-between border-b border-line px-5 py-4">
          <h2 class="text-[15px] font-medium text-ink">{{ editing ? '编辑待办' : '新增待办' }}</h2>
          <button
            type="button"
            class="btn-quiet !px-2 !py-1"
            aria-label="关闭"
            @click="emit('close')"
          >
            <X :size="16" :stroke-width="1.5" />
          </button>
        </header>

        <div class="min-h-0 flex-1 space-y-4 overflow-y-auto px-5 py-4">
          <div>
            <label class="label-text">标题</label>
            <input v-model="title" class="field" placeholder="今天要完成什么" />
          </div>

          <div>
            <label class="label-text">描述（选填）</label>
            <textarea
              v-model="description"
              rows="3"
              class="field resize-y"
              placeholder="补充一点细节"
            />
          </div>

          <div>
            <label class="label-text">到期日</label>
            <input v-model="dueDate" type="date" class="field num" />
            <LunarHint :date="dueDate" />
          </div>

          <div class="grid grid-cols-2 gap-3">
            <div>
              <label class="label-text">循环</label>
              <select v-model="frequency" class="field">
                <option v-for="option in FREQUENCY_OPTIONS" :key="option.value" :value="option.value">
                  {{ option.label }}
                </option>
              </select>
            </div>
            <div v-if="frequency !== 'none'">
              <label class="label-text">间隔</label>
              <div class="flex items-center gap-2">
                <input v-model.number="interval" type="number" min="1" max="365" class="field num" />
                <span class="shrink-0 text-[12px] text-ink-faint">
                  {{ UNIT_OPTIONS.find((item) => item.value === effectiveFrequency)?.label }}
                </span>
              </div>
            </div>
          </div>

          <div v-if="frequency === 'custom'">
            <label class="label-text">自定义单位</label>
            <select v-model="customUnit" class="field">
              <option v-for="option in UNIT_OPTIONS" :key="option.value" :value="option.value">
                每 {{ option.label }}
              </option>
            </select>
          </div>

          <div v-if="effectiveFrequency === 'weekly'">
            <label class="label-text">星期几（可多选）</label>
            <div class="flex gap-1.5">
              <button
                v-for="option in WEEKDAY_OPTIONS"
                :key="option.value"
                type="button"
                class="h-8 w-8 cursor-pointer rounded-lg border text-[12px] transition"
                :class="
                  weekdays.includes(option.value)
                    ? 'border-clay-300 bg-clay-100 text-clay-700'
                    : 'border-line bg-paper-card text-ink-muted hover:border-line-strong'
                "
                @click="toggleWeekday(option.value)"
              >
                {{ option.label }}
              </button>
            </div>
          </div>

          <div v-if="frequency !== 'none'">
            <label class="label-text">结束于（选填）</label>
            <input v-model="until" type="date" class="field num" />
          </div>

          <div>
            <label class="label-text">标签</label>
            <TagEditor
              v-model="tagIds"
              :tags="tags"
              scope="todo"
              @created="onTagCreated"
            />
          </div>

          <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
        </div>

        <footer class="shrink-0 border-t border-line px-5 py-3">
          <div class="flex justify-end gap-2">
            <button type="button" class="btn-ghost" @click="emit('close')">取消</button>
            <button type="button" class="btn-primary" :disabled="saving" @click="save">
              {{ saving ? '保存中…' : '保存' }}
            </button>
          </div>
        </footer>
      </aside>
    </div>
  </Teleport>
</template>
