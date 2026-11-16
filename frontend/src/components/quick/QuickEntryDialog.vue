<script setup lang="ts">
import { useQueryClient } from '@tanstack/vue-query'
import { onMounted, ref, watch } from 'vue'

import { http, type Account, type Category } from '@/api/client'
import FoodPicker, { type DietDraft } from '@/components/food/FoodPicker.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import { todayISO } from '@/composables/useFormat'

export type QuickKind = 'todo' | 'note' | 'transaction' | 'exercise' | 'diet' | 'weight' | 'sleep'

const props = defineProps<{ kind: QuickKind | null; open: boolean }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const TITLES: Record<QuickKind, string> = {
  todo: '新增待办',
  note: '新增笔记',
  transaction: '记录收支',
  exercise: '记录锻炼',
  diet: '记录饮食',
  weight: '记录体重',
  sleep: '记录睡眠',
}

const queryClient = useQueryClient()
const saving = ref(false)
const error = ref('')

const title = ref('')
const content = ref('')
const amount = ref('')
const txType = ref<'income' | 'expense' | 'transfer'>('expense')
const accountId = ref<number | null>(null)
const toAccountId = ref<number | null>(null)
const categoryId = ref<number | null>(null)
const exerciseType = ref('跑步')
const duration = ref('30')
const weight = ref('')
const bodyFat = ref('')
const meal = ref<'breakfast' | 'lunch' | 'dinner' | 'snack'>('lunch')
const sleepAt = ref('')
const wakeAt = ref('')
const sleepMinutes = ref('480')
const sleepQuality = ref(3)
const note = ref('')

const draft = ref<DietDraft>({ food: null, foodName: '', quantity: 100, manualCalories: null })

const accounts = ref<Account[]>([])
const categories = ref<Category[]>([])

function reset(): void {
  title.value = ''
  content.value = ''
  amount.value = ''
  txType.value = 'expense'
  accountId.value = null
  toAccountId.value = null
  categoryId.value = null
  exerciseType.value = '跑步'
  duration.value = '30'
  weight.value = ''
  bodyFat.value = ''
  meal.value = 'lunch'
  sleepAt.value = ''
  wakeAt.value = ''
  sleepMinutes.value = '480'
  sleepQuality.value = 3
  note.value = ''
  draft.value = { food: null, foodName: '', quantity: 100, manualCalories: null }
  error.value = ''
}

async function loadFinanceOptions(): Promise<void> {
  if (accounts.value.length) return
  try {
    const [acc, cat] = await Promise.all([
      http.get('/finance/accounts'),
      http.get('/finance/categories'),
    ])
    accounts.value = (acc.data.items ?? []).filter((a: Account) => !a.is_archived)
    categories.value = cat.data.items ?? []
    if (accounts.value.length) accountId.value = accounts.value[0].id
  } catch (err) {
    console.error('加载记账选项失败', err)
  }
}

watch(
  () => props.open,
  (open) => {
    if (open) {
      reset()
      if (props.kind === 'transaction') void loadFinanceOptions()
    }
  },
)

watch([sleepAt, wakeAt], ([start, end]) => {
  if (!start || !end) return
  const minutes = (new Date(end).getTime() - new Date(start).getTime()) / 60000
  if (Number.isFinite(minutes) && minutes > 0) sleepMinutes.value = String(Math.round(minutes))
})

onMounted(() => {
  if (props.open && props.kind === 'transaction') void loadFinanceOptions()
})

async function save(): Promise<void> {
  error.value = ''
  saving.value = true
  const day = todayISO()

  try {
    if (props.kind === 'todo') {
      if (!title.value.trim()) throw new Error('请填写待办标题')
      await http.post('/todos', { title: title.value.trim(), due_date: day })
    } else if (props.kind === 'note') {
      await http.post('/notes', {
        title: title.value.trim() || '无标题',
        content_md: content.value,
      })
    } else if (props.kind === 'transaction') {
      if (!amount.value || !accountId.value) throw new Error('请填写金额并选择账户')
      await http.post('/finance/transactions', {
        tx_type: txType.value,
        amount: Number(amount.value),
        account_id: accountId.value,
        to_account_id: txType.value === 'transfer' ? toAccountId.value : null,
        category_id: categoryId.value,
        occurred_on: day,
        note: note.value || null,
      })
    } else if (props.kind === 'exercise') {
      await http.post('/health/exercises', {
        record_date: day,
        exercise_type: exerciseType.value,
        duration_min: Number(duration.value || 0),
        note: note.value || null,
      })
    } else if (props.kind === 'diet') {
      const foodId = draft.value.food?.id ?? null
      const name = draft.value.foodName || draft.value.food?.name || ''
      if (!foodId && !name) throw new Error('请选择食物或填写名称')
      await http.post('/health/diets', {
        record_date: day,
        meal: meal.value,
        food_item_id: foodId,
        food_name: foodId ? null : name,
        quantity_g: draft.value.quantity,
        calories_kcal: draft.value.manualCalories,
        note: note.value || null,
      })
    } else if (props.kind === 'weight') {
      if (!weight.value) throw new Error('请填写体重')
      await http.post('/health/weights', {
        record_date: day,
        weight_kg: Number(weight.value),
        body_fat_pct: bodyFat.value ? Number(bodyFat.value) : null,
      })
    } else if (props.kind === 'sleep') {
      await http.post('/health/sleeps', {
        record_date: day,
        sleep_at: sleepAt.value || null,
        wake_at: wakeAt.value || null,
        duration_min: Number(sleepMinutes.value || 0),
        quality: sleepQuality.value,
      })
    }

    await queryClient.invalidateQueries()
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
  <AppDialog
    :open="open"
    :title="kind ? TITLES[kind] : ''"
    @close="emit('close')"
  >
    <div class="space-y-3">
      <template v-if="kind === 'todo'">
        <div>
          <label class="label-text">标题</label>
          <input v-model="title" class="field" placeholder="今天要完成什么" />
        </div>
        <p class="text-[11.5px] text-ink-faint">到期日默认为今天，可稍后在待办页修改。</p>
      </template>

      <template v-else-if="kind === 'note'">
        <div>
          <label class="label-text">标题</label>
          <input v-model="title" class="field" placeholder="给这条笔记起个名字" />
        </div>
        <div>
          <label class="label-text">正文（Markdown）</label>
          <textarea
            v-model="content"
            rows="6"
            class="field resize-y font-mono text-[12.5px]"
            placeholder="支持 Markdown，保存后可在笔记页分栏编辑"
          />
        </div>
      </template>

      <template v-else-if="kind === 'transaction'">
        <div class="flex gap-1 rounded-xl bg-paper-sunken p-1">
          <button
            v-for="option in [
              { key: 'expense', label: '支出' },
              { key: 'income', label: '收入' },
              { key: 'transfer', label: '转账' },
            ]"
            :key="option.key"
            type="button"
            class="flex-1 cursor-pointer rounded-lg py-1.5 text-[12.5px] transition"
            :class="
              txType === option.key
                ? 'bg-paper-card text-ink shadow-soft'
                : 'text-ink-muted hover:text-ink'
            "
            @click="txType = option.key as 'income' | 'expense' | 'transfer'"
          >
            {{ option.label }}
          </button>
        </div>
        <div>
          <label class="label-text">金额</label>
          <input v-model="amount" type="number" step="0.01" class="field num" placeholder="0.00" />
        </div>
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">{{ txType === 'transfer' ? '转出账户' : '账户' }}</label>
            <select v-model.number="accountId" class="field">
              <option v-for="acc in accounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
          </div>
          <div v-if="txType === 'transfer'">
            <label class="label-text">转入账户</label>
            <select v-model.number="toAccountId" class="field">
              <option v-for="acc in accounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
            </select>
          </div>
          <div v-else>
            <label class="label-text">分类</label>
            <select v-model.number="categoryId" class="field">
              <option :value="null">未分类</option>
              <option
                v-for="cat in categories.filter((c) => c.kind === (txType === 'income' ? 'income' : 'expense'))"
                :key="cat.id"
                :value="cat.id"
              >
                {{ cat.name }}
              </option>
            </select>
          </div>
        </div>
        <div>
          <label class="label-text">备注</label>
          <input v-model="note" class="field" placeholder="买了什么" />
        </div>
      </template>

      <template v-else-if="kind === 'exercise'">
        <div class="grid grid-cols-2 gap-3">
          <div>
            <label class="label-text">项目</label>
            <input v-model="exerciseType" class="field" placeholder="跑步 / 力量 / 游泳" />
          </div>
          <div>
            <label class="label-text">时长（分钟）</label>
            <input v-model="duration" type="number" class="field num" />
          </div>
        </div>
        <div>
          <label class="label-text">备注</label>
          <input v-model="note" class="field" placeholder="配速、感受等" />
        </div>
      </template>

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

      <template v-else-if="kind === 'sleep'">
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
            <label class="label-text">质量（1-5）</label>
            <input v-model.number="sleepQuality" type="number" min="1" max="5" class="field num" />
          </div>
        </div>
        <p class="text-[11px] text-ink-faint">填写入睡与起床时间会自动计算时长。</p>
      </template>

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
