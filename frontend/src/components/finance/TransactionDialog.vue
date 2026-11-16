<script setup lang="ts">
import { computed, ref, watch } from 'vue'

import { http, type Account, type Category } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'
import { todayISO } from '@/composables/useFormat'

const props = defineProps<{
  open: boolean
  accounts: Account[]
  categories: Category[]
}>()

const emit = defineEmits<{ close: []; saved: [] }>()

const txType = ref<'expense' | 'income' | 'transfer'>('expense')
const amount = ref('')
const accountId = ref<number | null>(null)
const toAccountId = ref<number | null>(null)
const categoryId = ref<number | null>(null)
const occurredOn = ref(todayISO())
const note = ref('')
const saving = ref(false)
const error = ref('')

const activeAccounts = computed(() => props.accounts.filter((item) => !item.is_archived))

const filteredCategories = computed(() =>
  props.categories.filter((item) => item.kind === (txType.value === 'income' ? 'income' : 'expense')),
)

watch(
  () => props.open,
  (open) => {
    if (!open) return
    txType.value = 'expense'
    amount.value = ''
    categoryId.value = null
    occurredOn.value = todayISO()
    note.value = ''
    error.value = ''
    accountId.value = activeAccounts.value[0]?.id ?? null
    toAccountId.value = activeAccounts.value[1]?.id ?? activeAccounts.value[0]?.id ?? null
  },
)

watch(txType, () => {
  categoryId.value = null
})

async function save(): Promise<void> {
  error.value = ''
  if (!amount.value || Number(amount.value) <= 0) {
    error.value = '请填写大于 0 的金额'
    return
  }
  if (!accountId.value) {
    error.value = '请选择账户'
    return
  }
  if (txType.value === 'transfer') {
    if (!toAccountId.value) {
      error.value = '请选择转入账户'
      return
    }
    if (toAccountId.value === accountId.value) {
      error.value = '转出与转入账户不能相同'
      return
    }
  }

  saving.value = true
  try {
    await http.post('/finance/transactions', {
      tx_type: txType.value,
      amount: Number(amount.value),
      account_id: accountId.value,
      to_account_id: txType.value === 'transfer' ? toAccountId.value : null,
      category_id: txType.value === 'transfer' ? null : categoryId.value,
      occurred_on: occurredOn.value,
      note: note.value || null,
    })
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
  <AppDialog :open="open" title="记一笔" @close="emit('close')">
    <div class="space-y-3">
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
        <input v-model="amount" type="number" step="0.01" min="0" class="field num" placeholder="0.00" />
        <p class="mt-1 text-[11px] text-ink-faint">转账不计入收入与支出统计，只在账户间移动。</p>
      </div>

      <div class="grid grid-cols-2 gap-3">
        <div>
          <label class="label-text">{{ txType === 'transfer' ? '转出账户' : '账户' }}</label>
          <select v-model.number="accountId" class="field">
            <option v-for="acc in activeAccounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
          </select>
        </div>

        <div v-if="txType === 'transfer'">
          <label class="label-text">转入账户</label>
          <select v-model.number="toAccountId" class="field">
            <option v-for="acc in activeAccounts" :key="acc.id" :value="acc.id">{{ acc.name }}</option>
          </select>
        </div>

        <div v-else>
          <label class="label-text">分类</label>
          <select v-model.number="categoryId" class="field">
            <option :value="null">未分类</option>
            <option v-for="cat in filteredCategories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>
      </div>

      <div>
        <label class="label-text">日期</label>
        <input v-model="occurredOn" type="date" class="field num" />
      </div>

      <div>
        <label class="label-text">备注</label>
        <input v-model="note" class="field" placeholder="买了什么，或者为什么记这笔" />
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
