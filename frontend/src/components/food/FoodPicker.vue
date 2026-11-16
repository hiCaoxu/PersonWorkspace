<script setup lang="ts">
import { Loader2, Plus, Search, X } from 'lucide-vue-next'
import { computed, onMounted, ref, watch } from 'vue'

import { http, type Food } from '@/api/client'

export interface DietDraft {
  food: Food | null
  foodName: string
  quantity: number
  manualCalories: number | null
}

const props = defineProps<{ draft: DietDraft }>()
const emit = defineEmits<{ 'update:draft': [DietDraft] }>()

const keyword = ref(props.draft.foodName || '')
const results = ref<Food[]>([])
const frequent = ref<Food[]>([])
const loading = ref(false)
const open = ref(false)
const creating = ref(false)
const newName = ref('')
const newKcal = ref('')

let timer: ReturnType<typeof setTimeout> | null = null

const selected = computed(() => props.draft.food)

const computedKcal = computed(() => {
  const food = selected.value
  if (!food) return null
  const per = Number(food.energy_kcal_per_100g)
  const quantity = Number(props.draft.quantity || 0)
  if (!Number.isFinite(per) || quantity <= 0) return null
  return Math.round((per * quantity) / 100 * 10) / 10
})

const displayKcal = computed(() =>
  props.draft.manualCalories !== null ? props.draft.manualCalories : computedKcal.value,
)

function patch(partial: Partial<DietDraft>): void {
  emit('update:draft', { ...props.draft, ...partial })
}

async function search(q: string): Promise<void> {
  loading.value = true
  try {
    const { data } = await http.get('/foods', { params: { q, limit: 20 } })
    results.value = data.items ?? []
  } catch (error) {
    console.error('搜索食物失败', error)
    results.value = []
  } finally {
    loading.value = false
  }
}

watch(keyword, (value) => {
  // 输入内容同时作为「未匹配到食物时」的自定义名称，保证手动录入也能保存
  if (props.draft.food?.name !== value) {
    patch({ food: null, foodName: value })
  }
  if (timer) clearTimeout(timer)
  timer = setTimeout(() => {
    open.value = true
    void search(value.trim())
  }, 220)
})

onMounted(async () => {
  try {
    const { data } = await http.get('/foods/frequent')
    frequent.value = data.items ?? []
  } catch (error) {
    console.error('加载常用食物失败', error)
  }
})

function pick(food: Food): void {
  const serving = food.default_serving_g ? Number(food.default_serving_g) : 100
  keyword.value = food.name
  open.value = false
  patch({
    food,
    foodName: food.name,
    quantity: serving,
    manualCalories: null,
  })
}

function clearFood(): void {
  keyword.value = ''
  results.value = []
  patch({ food: null, foodName: '', quantity: 100, manualCalories: null })
}

function applyServing(grams: number): void {
  patch({ quantity: grams })
}

function overrideManual(value: string): void {
  const num = Number(value)
  patch({ manualCalories: value === '' || !Number.isFinite(num) ? null : num })
}

async function createFood(): Promise<void> {
  if (!newName.value.trim() || !newKcal.value) return
  try {
    const { data } = await http.post('/foods', {
      name: newName.value.trim(),
      energy_kcal_per_100g: Number(newKcal.value),
      category: '菜肴',
    })
    creating.value = false
    newName.value = ''
    newKcal.value = ''
    pick(data as Food)
  } catch (error) {
    console.error('新建食物失败', error)
  }
}
</script>

<template>
  <div class="space-y-3">
    <div class="relative">
      <label class="label-text">食物</label>
      <div class="relative">
        <Search
          :size="15"
          :stroke-width="1.5"
          class="pointer-events-none absolute left-3 top-1/2 -translate-y-1/2 text-ink-faint"
        />
        <input
          v-model="keyword"
          class="field !pl-9"
          placeholder="输入食物名称，如「米饭」或拼音首字母 mf"
          @focus="open = true"
        />
        <Loader2
          v-if="loading"
          :size="14"
          class="absolute right-3 top-1/2 -translate-y-1/2 animate-spin text-ink-faint"
        />
        <button
          v-else-if="keyword"
          type="button"
          class="absolute right-2.5 top-1/2 -translate-y-1/2 cursor-pointer text-ink-faint hover:text-ink"
          @click="clearFood"
        >
          <X :size="14" />
        </button>
      </div>

      <div
        v-if="open"
        class="absolute z-20 mt-1 max-h-64 w-full overflow-y-auto rounded-xl border border-line bg-paper-card p-1 shadow-lift"
      >
        <p v-if="!keyword && frequent.length" class="px-2 py-1 text-[11px] text-ink-faint">常吃</p>
        <button
          v-for="food in keyword ? results : frequent"
          :key="food.id"
          type="button"
          class="flex w-full cursor-pointer items-center justify-between rounded-lg px-2.5 py-2 text-left text-[13px] text-ink hover:bg-paper-sunken"
          @click="pick(food)"
        >
          <span>{{ food.name }}</span>
          <span class="num text-[11.5px] text-ink-faint">
            {{ Number(food.energy_kcal_per_100g) }} kcal/100g
          </span>
        </button>

        <p
          v-if="(keyword ? results : frequent).length === 0"
          class="px-2.5 py-3 text-[12px] text-ink-faint"
        >
          没有找到匹配的食物，可在下方新建
        </p>

        <button
          type="button"
          class="mt-1 flex w-full cursor-pointer items-center gap-1.5 rounded-lg px-2.5 py-2 text-[12.5px] text-clay-700 hover:bg-clay-50"
          @click="creating = true"
        >
          <Plus :size="13" :stroke-width="1.5" />
          新建食物
        </button>
      </div>
    </div>

    <div v-if="creating" class="rounded-xl border border-line bg-paper p-3">
      <div class="flex gap-2">
        <input v-model="newName" class="field flex-1" placeholder="食物名称" />
        <input v-model="newKcal" class="field w-28" type="number" placeholder="kcal/100g" />
        <button type="button" class="btn-primary" @click="createFood">保存</button>
      </div>
      <p class="mt-2 text-[11px] text-ink-faint">保存后会自动选中该食物，下次可直接搜索。</p>
    </div>

    <div class="grid grid-cols-2 gap-3">
      <div>
        <label class="label-text">摄入克数</label>
        <input
          :value="draft.quantity"
          type="number"
          min="1"
          class="field num"
          @input="patch({ quantity: Number(($event.target as HTMLInputElement).value) })"
        />
      </div>
      <div>
        <label class="label-text">热量 (kcal)</label>
        <input
          :value="draft.manualCalories ?? ''"
          type="number"
          min="0"
          class="field num"
          :placeholder="computedKcal === null ? '手动填写' : String(computedKcal)"
          @input="overrideManual(($event.target as HTMLInputElement).value)"
        />
      </div>
    </div>

    <p class="text-[11px] leading-relaxed text-ink-faint">
      选中内置食物后按克数自动折算；也可以只写名称、手动填热量，或新建一条自定义食物。
    </p>

    <div class="flex flex-wrap items-center gap-2">
      <button
        v-if="selected?.default_serving_label"
        type="button"
        class="rounded-lg border border-line px-2.5 py-1 text-[11.5px] text-ink-muted hover:border-clay-300 hover:text-clay-700"
        @click="applyServing(Number(selected.default_serving_g ?? 100))"
      >
        {{ selected.default_serving_label }} ≈ {{ selected.default_serving_g }}g
      </button>
      <button
        type="button"
        class="rounded-lg border border-line px-2.5 py-1 text-[11.5px] text-ink-muted hover:border-clay-300 hover:text-clay-700"
        @click="applyServing(100)"
      >
        100g
      </button>
      <span v-if="draft.manualCalories !== null" class="text-[11px] text-ink-faint">已手动调整</span>
      <span v-else-if="displayKcal !== null" class="num text-[11.5px] text-clay-700">
        约 {{ displayKcal }} kcal
      </span>
    </div>
  </div>
</template>
