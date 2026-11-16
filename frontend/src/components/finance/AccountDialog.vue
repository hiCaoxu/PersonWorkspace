<script setup lang="ts">
import { Archive } from 'lucide-vue-next'
import { computed, ref, watch } from 'vue'

import { http, type Account } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'

const props = defineProps<{ open: boolean; account: Account | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const ACCOUNT_TYPES = [
  { value: 'bank', label: '银行卡' },
  { value: 'alipay', label: '支付宝' },
  { value: 'wechat', label: '微信' },
  { value: 'cash', label: '现金' },
  { value: 'credit', label: '信用卡' },
  { value: 'loan', label: '借贷（负债）' },
  { value: 'other', label: '其他' },
]

const ICONS = [
  { value: 'wallet', label: '钱包' },
  { value: 'landmark', label: '银行' },
  { value: 'smartphone', label: '移动支付' },
  { value: 'credit-card', label: '卡' },
  { value: 'piggy-bank', label: '储蓄' },
  { value: 'banknote', label: '现金' },
]

const COLORS = ['#B08968', '#7A9E7E', '#C0714F', '#8A7F70', '#9A7355', '#A8BFA1']

const name = ref('')
const accountType = ref('bank')
const initialBalance = ref('0')
const icon = ref('wallet')
const color = ref(COLORS[0])
const saving = ref(false)
const error = ref('')

const editing = computed(() => props.account !== null)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const account = props.account
    name.value = account?.name ?? ''
    accountType.value = account?.account_type ?? 'bank'
    initialBalance.value = account?.initial_balance ?? '0'
    icon.value = account?.icon ?? 'wallet'
    color.value = account?.color ?? COLORS[0]
    error.value = ''
  },
)

async function save(): Promise<void> {
  if (!name.value.trim()) {
    error.value = '请填写账户名称'
    return
  }
  saving.value = true
  error.value = ''
  const payload = {
    name: name.value.trim(),
    account_type: accountType.value,
    initial_balance: Number(initialBalance.value || 0),
    icon: icon.value,
    color: color.value,
  }

  try {
    if (props.account) {
      await http.patch(`/finance/accounts/${props.account.id}`, payload)
    } else {
      await http.post('/finance/accounts', payload)
    }
    emit('saved')
    emit('close')
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    saving.value = false
  }
}

async function archive(): Promise<void> {
  if (!props.account) return
  saving.value = true
  try {
    await http.patch(`/finance/accounts/${props.account.id}`, { is_archived: true })
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
  <AppDialog :open="open" :title="editing ? '编辑账户' : '添加账户'" @close="emit('close')">
    <div class="space-y-3">
      <div>
        <label class="label-text">账户名称</label>
        <input v-model="name" class="field" placeholder="如：招商银行储蓄卡" />
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label-text">类型</label>
          <select v-model="accountType" class="field">
            <option v-for="option in ACCOUNT_TYPES" :key="option.value" :value="option.value">
              {{ option.label }}
            </option>
          </select>
        </div>
        <div>
          <label class="label-text">初始余额</label>
          <input v-model="initialBalance" type="number" step="0.01" class="field num" />
        </div>
      </div>

      <div>
        <label class="label-text">图标</label>
        <div class="flex flex-wrap gap-1.5">
          <button
            v-for="option in ICONS"
            :key="option.value"
            type="button"
            class="cursor-pointer rounded-lg border px-2.5 py-1 text-[11.5px] transition"
            :class="
              icon === option.value
                ? 'border-clay-300 bg-clay-100 text-clay-700'
                : 'border-line text-ink-muted hover:border-line-strong'
            "
            @click="icon = option.value"
          >
            {{ option.label }}
          </button>
        </div>
      </div>

      <div>
        <label class="label-text">颜色</label>
        <div class="flex gap-2">
          <button
            v-for="item in COLORS"
            :key="item"
            type="button"
            class="h-6 w-6 cursor-pointer rounded-full border-2 transition"
            :class="color === item ? 'border-ink/40' : 'border-transparent'"
            :style="{ backgroundColor: item }"
            :aria-label="`颜色 ${item}`"
            @click="color = item"
          />
        </div>
      </div>

      <p v-if="accountType === 'loan'" class="text-[11px] text-clay-600">
        借贷账户用于记录负债，余额会显示但不会计入首页与记账的总资产。
      </p>
      <p v-if="editing" class="text-[11px] text-ink-faint">
        账户已有流水时不会删除，只会停用并从新增流水中隐藏。
      </p>

      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex w-full items-center justify-between gap-2">
        <button
          v-if="editing"
          type="button"
          class="btn-quiet !text-negative"
          :disabled="saving"
          @click="archive"
        >
          <Archive :size="14" :stroke-width="1.5" />
          停用账户
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
