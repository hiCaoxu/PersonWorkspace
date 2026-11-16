<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import {
  http,
  type DietRecord,
  type ExerciseRecord,
  type SleepRecord,
  type WeightRecord,
} from '@/api/client'
import FoodPicker, { type DietDraft } from '@/components/food/FoodPicker.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import { todayISO } from '@/composables/useFormat'

export type HealthKind = 'exercise' | 'diet' | 'weight' | 'sleep'

type AnyRecord = ExerciseRecord | DietRecord | WeightRecord | SleepRecord

const props = defineProps<{
  open: boolean
  kind: HealthKind
  record: AnyRecord | null
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const TITLES: Record<HealthKind, string> = {
  exercise: '锻炼',
  diet: '饮食',
  weight: '体重',
  sleep: '睡眠',
}

const saving = ref(false)
const error = ref('')

const recordDate = ref(todayISO())
const note = ref('')

const exerciseType = ref('跑步')
const duration = ref('30')
const calories = ref('')
const distance = ref('')
const intensity = ref('')

const meal = ref<'breakfast' | 'lunch' | 'dinner' | 'snack'>('lunch')
const draft = ref<DietDraft>({ food: null, foodName: '', quantity: 100, manualCalories: null })

const weight = ref('')
const bodyFat = ref('')

const sleepAt = ref('')
const wakeAt = ref('')
const sleepMinutes = ref('480')
const quality = ref(3)

const title = computed(
  () => `${props.record ? '编辑' : '记录'}${TITLES[props.kind]}`,
)

function toLocalInput(value: string | null): string {
  return value ? value.slice(0, 16) : ''
}

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const record = props.record
    error.value = ''
    recordDate.value = record?.record_date ?? todayISO()
    note.value = record?.note ?? ''
    exerciseType.value = '跑步'
    duration.value = '30'
    calories.value = ''
    distance.value = ''
    intensity.value = ''
    meal.value = 'lunch'
    draft.value = { food: null, foodName: '', quantity: 100, manualCalories: null }
    weight.value = ''
    bodyFat.value = ''
    sleepAt.value = ''
    wakeAt.value = ''
    sleepMinutes.value = '480'
    quality.value = 3

    if (!record) return

    if (props.kind === 'exercise' && 'exercise_type' in record) {
      exerciseType.value = record.exercise_type
      duration.value = String(record.duration_min)
      calories.value = record.calories ?? ''
      distance.value = record.distance_km ?? ''
      intensity.value = record.intensity ?? ''
    } else if (props.kind === 'diet' && 'food_name' in record) {
      meal.value = record.meal
      draft.value = {
        food: null,
        foodName: record.food_name,
        quantity: Number(record.quantity_g),
        manualCalories: Number(record.calories_kcal),
      }
    } else if (props.kind === 'weight' && 'weight_kg' in record) {
      weight.value = record.weight_kg
      bodyFat.value = record.body_fat_pct ?? ''
    } else if (props.kind === 'sleep') {
      const sleep = record as SleepRecord
      sleepAt.value = toLocalInput(sleep.sleep_at)
      wakeAt.value = toLocalInput(sleep.wake_at)
      sleepMinutes.value = String(sleep.duration_min)
      quality.value = sleep.quality ?? 3
    }
  },
  { immediate: true },
)

watch([sleepAt, wakeAt], ([start, end]) => {
  if (!start || !end) return
  const diff = (new Date(end).getTime() - new Date(start).getTime()) / 60000
  if (Number.isFinite(diff) && diff > 0) sleepMinutes.value = String(Math.round(diff))
})

async function save(): Promise<void> {
  saving.value = true
  error.value = ''
  const id = props.record?.id

  try {
    if (props.kind === 'exercise') {
      const payload = {
        record_date: recordDate.value,
        exercise_type: exerciseType.value.trim() || '锻炼',
        duration_min: Number(duration.value || 0),
        calories: calories.value ? Number(calories.value) : null,
        distance_km: distance.value ? Number(distance.value) : null,
        intensity: intensity.value || null,
        note: note.value || null,
      }
      if (id) await http.patch(`/health/exercises/${id}`, payload)
      else await http.post('/health/exercises', payload)
    } else if (props.kind === 'diet') {
      const foodId = draft.value.food?.id ?? null
      const name = draft.value.foodName.trim()
      if (!foodId && !name) throw new Error('请选择食物或填写名称')
      const payload = {
        record_date: recordDate.value,
        meal: meal.value,
        food_item_id: foodId,
        food_name: foodId ? null : name,
        quantity_g: draft.value.quantity,
        calories_kcal: draft.value.manualCalories,
        note: note.value || null,
      }
      if (id) await http.patch(`/health/diets/${id}`, payload)
      else await http.post('/health/diets', payload)
    } else if (props.kind === 'weight') {
      if (!weight.value) throw new Error('请填写体重')
      const payload = {
        record_date: recordDate.value,
        weight_kg: Number(weight.value),
        body_fat_pct: bodyFat.value ? Number(bodyFat.value) : null,
        note: note.value || null,
      }
      if (id) await http.patch(`/health/weights/${id}`, payload)
      else await http.post('/health/weights', payload)
    } else {
      const payload = {
        record_date: recordDate.value,
        sleep_at: sleepAt.value || null,
        wake_at: wakeAt.value || null,
        duration_min: Number(sleepMinutes.value || 0),
        quality: quality.value || null,
        note: note.value || null,
      }
      if (id) await http.patch(`/health/sleeps/${id}`, payload)
      else await http.post('/health/sleeps', payload)
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
  <AppDialog :open="open" :title="title" @close="emit('close')">
    <div class="space-y-3">
      <div>
        <label class="label-text">日期</label>
        <input v-model="recordDate" type="date" class="field num" />
      </div>

      <!-- 锻炼 -->
      <template v-if="kind === 'exercise'">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">项目</label>
            <input v-model="exerciseType" class="field" placeholder="跑步 / 力量 / 游泳" />
          </div>
          <div>
            <label class="label-text">时长（分钟）</label>
            <input v-model="duration" type="number" min="0" class="field num" />
          </div>
          <div>
            <label class="label-text">消耗（kcal，选填）</label>
            <input v-model="calories" type="number" min="0" class="field num" placeholder="300" />
          </div>
          <div>
            <label class="label-text">距离（km，选填）</label>
            <input v-model="distance" type="number" step="0.1" min="0" class="field num" placeholder="5.0" />
          </div>
        </div>
        <div>
          <label class="label-text">强度（选填）</label>
          <div class="flex gap-1.5">
            <button
              v-for="item in ['轻松', '适中', '高强度']"
              :key="item"
              type="button"
              class="cursor-pointer rounded-lg border px-2.5 py-1 text-[11.5px] transition"
              :class="
                intensity === item
                  ? 'border-clay-300 bg-clay-100 text-clay-700'
                  : 'border-line text-ink-muted hover:border-line-strong'
              "
              @click="intensity = intensity === item ? '' : item"
            >
              {{ item }}
            </button>
          </div>
        </div>
      </template>

      <!-- 饮食 -->
      <template v-else-if="kind === 'diet'">
        <div>
          <label class="label-text">餐次</label>
          <div class="flex gap-1 rounded-xl bg-paper-sunken p-1">
            <button
              v-for="option in [
                { key: 'breakfast', label: '早餐' },
                { key: 'lunch', label: '午餐' },
                { key: 'dinner', label: '晚餐' },
                { key: 'snack', label: '加餐' },
              ]"
              :key="option.key"
              type="button"
              class="flex-1 cursor-pointer rounded-lg py-1.5 text-[12.5px] transition"
              :class="
                meal === option.key
                  ? 'bg-paper-card text-ink shadow-soft'
                  : 'text-ink-muted hover:text-ink'
              "
              @click="meal = option.key as typeof meal"
            >
              {{ option.label }}
            </button>
          </div>
        </div>
        <FoodPicker v-model:draft="draft" />
      </template>

      <!-- 体重 -->
      <template v-else-if="kind === 'weight'">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">体重（kg）</label>
            <input v-model="weight" type="number" step="0.1" class="field num" placeholder="70.0" />
          </div>
          <div>
            <label class="label-text">体脂率（%，选填）</label>
            <input v-model="bodyFat" type="number" step="0.1" class="field num" placeholder="18.5" />
          </div>
        </div>
      </template>

      <!-- 睡眠 -->
      <template v-else>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">入睡时间</label>
            <input v-model="sleepAt" type="datetime-local" class="field num" />
          </div>
          <div>
            <label class="label-text">起床时间</label>
            <input v-model="wakeAt" type="datetime-local" class="field num" />
          </div>
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">时长（分钟）</label>
            <input v-model="sleepMinutes" type="number" min="0" class="field num" />
          </div>
          <div>
            <label class="label-text">睡眠质量</label>
            <div class="flex gap-1">
              <button
                v-for="score in [1, 2, 3, 4, 5]"
                :key="score"
                type="button"
                class="h-8 flex-1 cursor-pointer rounded-lg border text-[12px] transition"
                :class="
                  quality === score
                    ? 'border-clay-300 bg-clay-100 text-clay-700'
                    : 'border-line text-ink-muted hover:border-line-strong'
                "
                @click="quality = score"
              >
                {{ score }}
              </button>
            </div>
          </div>
        </div>
        <p class="text-[11px] text-ink-faint">填写入睡与起床时间会自动算出时长；质量 1 最差、5 最好。</p>
      </template>

      <div>
        <label class="label-text">备注（选填）</label>
        <input v-model="note" class="field" placeholder="身体感受、配速、吃了什么" />
      </div>

      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost" @click="emit('close')">取消</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </div>
    </template>
  </AppDialog>
</template>
