<script setup lang="ts">
import { useMutation, useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  ArrowDownLeft,
  ArrowLeftRight,
  ArrowUpRight,
  Banknote,
  ChevronLeft,
  ChevronRight,
  CreditCard,
  Landmark,
  PiggyBank,
  Plus,
  Smartphone,
  Trash2,
  Wallet,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'

import {
  http,
  type Account,
  type Category,
  type FinanceSummary,
  type Transaction,
} from '@/api/client'
import TrendChart from '@/components/charts/TrendChart.vue'
import AccountDialog from '@/components/finance/AccountDialog.vue'
import TransactionDialog from '@/components/finance/TransactionDialog.vue'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import SegmentedControl from '@/components/ui/SegmentedControl.vue'
import { formatMoney, monthRange, todayISO } from '@/composables/useFormat'

const queryClient = useQueryClient()

const [initialYear, initialMonth] = todayISO().split('-').map(Number)
const cursor = ref({ year: initialYear, month: initialMonth })

const accountFilter = ref<number | null>(null)
const categoryFilter = ref<number | null>(null)

const txDialogOpen = ref(false)
const accountDialogOpen = ref(false)
const editingAccount = ref<Account | null>(null)
const deleting = ref<Transaction | null>(null)
const deleteLoading = ref(false)

const currentMonthISO = computed(
  () => `${cursor.value.year}-${String(cursor.value.month).padStart(2, '0')}-01`,
)
const range = computed(() => monthRange(currentMonthISO.value))
const monthLabel = computed(() => `${cursor.value.year} 年 ${cursor.value.month} 月`)

const summaryQuery = useQuery({
  queryKey: computed(() => ['finance-summary', cursor.value.year, cursor.value.month]),
  queryFn: async () => {
    const { data } = await http.get<FinanceSummary>('/finance/summary', {
      params: { year: cursor.value.year, month: cursor.value.month },
    })
    return data
  },
})

const accountsQuery = useQuery({
  queryKey: ['accounts'],
  queryFn: async () => {
    const { data } = await http.get<{ items: Account[] }>('/finance/accounts')
    return data.items
  },
})

const categoriesQuery = useQuery({
  queryKey: ['categories'],
  queryFn: async () => {
    const { data } = await http.get<{ items: Category[] }>('/finance/categories')
    return data.items
  },
})

const transactionsQuery = useQuery({
  queryKey: computed(() => [
    'transactions',
    range.value.start,
    range.value.end,
    accountFilter.value,
    categoryFilter.value,
  ]),
  queryFn: async () => {
    const { data } = await http.get<{ items: Transaction[] }>('/finance/transactions', {
      params: {
        start: range.value.start,
        end: range.value.end,
        account_id: accountFilter.value ?? undefined,
        category_id: categoryFilter.value ?? undefined,
      },
    })
    return data.items
  },
})

const summary = computed(() => summaryQuery.data.value)
const accounts = computed(() => (accountsQuery.data.value ?? []).filter((item) => !item.is_archived))
const categories = computed(() => categoriesQuery.data.value ?? [])
const transactions = computed(() => transactionsQuery.data.value ?? [])

const categoryMap = computed(
  () => new Map(categories.value.map((item) => [item.id, item.name])),
)

const groups = computed(() => {
  const map = new Map<string, Transaction[]>()
  for (const tx of transactions.value) {
    const list = map.get(tx.occurred_on) ?? []
    list.push(tx)
    map.set(tx.occurred_on, list)
  }
  return [...map.entries()].map(([date, items]) => ({ date, items }))
})

const donutCategories = computed(() =>
  (summary.value?.expense_categories ?? []).map((row) => row.name),
)
const donutValues = computed(() =>
  (summary.value?.expense_categories ?? []).map((row) => Number(row.total)),
)
const trendCategories = computed(() =>
  (summary.value?.trend ?? []).map((row) => `${Number(row.month.slice(5, 7))}月`),
)
const trendMode = ref<'all' | 'income' | 'expense'>('all')
const trendOptions = [
  { key: 'all', label: '全部' },
  { key: 'income', label: '只看收入' },
  { key: 'expense', label: '只看支出' },
]

function setTrendMode(value: string): void {
  trendMode.value = value as typeof trendMode.value
}

const trendSeries = computed(() => {
  const rows = summary.value?.trend ?? []
  const series: {
    name: string
    values: number[]
    color: string
    kind: 'bar'
  }[] = []
  if (trendMode.value !== 'expense') {
    series.push({
      name: '收入',
      values: rows.map((row) => Number(row.income)),
      color: '#7A9E7E',
      kind: 'bar',
    })
  }
  if (trendMode.value !== 'income') {
    series.push({
      name: '支出',
      values: rows.map((row) => Number(row.expense)),
      color: '#C0714F',
      kind: 'bar',
    })
  }
  return series
})

const ICON_MAP: Record<string, typeof Wallet> = {
  wallet: Wallet,
  loan: Landmark,
  landmark: Landmark,
  smartphone: Smartphone,
  'credit-card': CreditCard,
  'piggy-bank': PiggyBank,
  banknote: Banknote,
}

function accountIcon(account: Account) {
  return ICON_MAP[account.icon ?? 'wallet'] ?? Wallet
}

function shiftMonth(delta: number): void {
  const date = new Date(cursor.value.year, cursor.value.month - 1 + delta, 1)
  cursor.value = { year: date.getFullYear(), month: date.getMonth() + 1 }
}

function clearFilters(): void {
  accountFilter.value = null
  categoryFilter.value = null
}

function openCreateAccount(): void {
  editingAccount.value = null
  accountDialogOpen.value = true
}

function openEditAccount(account: Account): void {
  editingAccount.value = account
  accountDialogOpen.value = true
}

const removeTransaction = useMutation({
  mutationFn: async (tx: Transaction) => {
    await http.delete(`/finance/transactions/${tx.id}`)
  },
  onSuccess: () => queryClient.invalidateQueries(),
})

async function confirmDelete(): Promise<void> {
  if (!deleting.value) return
  deleteLoading.value = true
  try {
    await removeTransaction.mutateAsync(deleting.value)
    deleting.value = null
  } finally {
    deleteLoading.value = false
  }
}

function txIcon(tx: Transaction) {
  if (tx.tx_type === 'income') return ArrowDownLeft
  if (tx.tx_type === 'expense') return ArrowUpRight
  return ArrowLeftRight
}

function txTitle(tx: Transaction): string {
  if (tx.tx_type === 'transfer') {
    return `${tx.account_name ?? '账户'} → ${tx.to_account_name ?? '账户'}`
  }
  return tx.category_id ? (categoryMap.value.get(tx.category_id) ?? '未分类') : '未分类'
}

function amountText(tx: Transaction): string {
  if (tx.tx_type === 'income') return `+${formatMoney(tx.amount)}`
  if (tx.tx_type === 'expense') return `-${formatMoney(tx.amount)}`
  return formatMoney(tx.amount)
}

function amountClass(tx: Transaction): string {
  if (tx.tx_type === 'income') return 'text-positive'
  if (tx.tx_type === 'expense') return 'text-negative'
  return 'text-ink-muted'
}
</script>

<template>
  <AppShell>
    <PageHeader title="记账" description="钱去了哪里，一眼看清。转账只在账户间移动。">
      <template #actions>
        <button type="button" class="btn-ghost" @click="openCreateAccount">
          <Plus :size="15" :stroke-width="1.5" />
          添加账户
        </button>
        <button type="button" class="btn-primary" @click="txDialogOpen = true">
          <Plus :size="15" :stroke-width="1.5" />
          记一笔
        </button>
      </template>
    </PageHeader>

    <div v-if="summaryQuery.isPending.value" class="space-y-4">
      <div class="h-28 animate-pulse rounded-2xl bg-paper-sunken" />
      <div class="grid gap-4 sm:grid-cols-3">
        <div v-for="i in 3" :key="i" class="h-24 animate-pulse rounded-2xl bg-paper-sunken" />
      </div>
    </div>

    <template v-else>
      <!-- 汇总 -->
      <section class="grid gap-4 lg:grid-cols-3">
        <article
          class="surface relative overflow-hidden p-5 lg:col-span-1"
          style="background-image: linear-gradient(135deg, #ffffff 0%, #fbf6f0 60%, #f3e9de 100%)"
        >
          <div class="flex items-center justify-between">
            <span class="text-[12.5px] text-ink-muted">总资产</span>
            <Wallet :size="15" :stroke-width="1.5" class="text-clay-500" />
          </div>
          <p class="num mt-3 text-[28px] font-semibold tracking-tight text-ink">
            {{ formatMoney(summary?.total_assets) }}
          </p>
          <p class="mt-2 text-[11.5px] text-ink-faint">
            {{ accounts.length }} 个在用账户 · 不含停用账户
          </p>
        </article>

        <div class="grid gap-4 sm:grid-cols-3 lg:col-span-2">
          <article class="surface p-4">
            <div class="flex items-center justify-between">
              <span class="text-[12px] text-ink-muted">本月收入</span>
              <ArrowDownLeft :size="14" :stroke-width="1.5" class="text-positive" />
            </div>
            <p class="num mt-2.5 text-[19px] font-semibold text-ink">
              {{ formatMoney(summary?.month_income) }}
            </p>
          </article>

          <article class="surface p-4">
            <div class="flex items-center justify-between">
              <span class="text-[12px] text-ink-muted">本月支出</span>
              <ArrowUpRight :size="14" :stroke-width="1.5" class="text-negative" />
            </div>
            <p class="num mt-2.5 text-[19px] font-semibold text-ink">
              {{ formatMoney(summary?.month_expense) }}
            </p>
          </article>

          <article class="surface p-4">
            <div class="flex items-center justify-between">
              <span class="text-[12px] text-ink-muted">本月结余</span>
              <ArrowLeftRight :size="14" :stroke-width="1.5" class="text-clay-500" />
            </div>
            <p
              class="num mt-2.5 text-[19px] font-semibold"
              :class="Number(summary?.month_net ?? 0) >= 0 ? 'text-ink' : 'text-negative'"
            >
              {{ formatMoney(summary?.month_net) }}
            </p>
          </article>
        </div>
      </section>

      <!-- 账户 -->
      <section class="mt-5">
        <div class="no-scrollbar flex gap-3 overflow-x-auto pb-1">
          <button
            v-for="account in accounts"
            :key="account.id"
            type="button"
            class="surface surface-hover min-w-[190px] shrink-0 cursor-pointer p-4 text-left"
            :class="accountFilter === account.id ? '!border-clay-300' : ''"
            @click="accountFilter = accountFilter === account.id ? null : account.id"
            @dblclick="openEditAccount(account)"
          >
            <div class="flex items-center gap-2.5">
              <span
                class="flex h-8 w-8 items-center justify-center rounded-xl"
                :style="{
                  backgroundColor: `${account.color ?? '#B08968'}1F`,
                  color: account.color ?? '#B08968',
                }"
              >
                <component :is="accountIcon(account)" :size="16" :stroke-width="1.5" />
              </span>
              <div class="min-w-0">
                <p class="truncate text-[12.5px] text-ink">{{ account.name }}</p>
                <p
                  class="num text-[11px]"
                  :class="account.account_type === 'loan' ? 'text-clay-600' : 'text-ink-faint'"
                >
                  {{ account.account_type === 'loan' ? '待还 ' : ''
                  }}{{ formatMoney(account.balance ?? account.initial_balance) }}
                </p>
              </div>
            </div>
            <p class="mt-2 text-[10.5px] text-ink-faint">双击编辑</p>
          </button>

          <button
            type="button"
            class="flex min-w-[130px] shrink-0 cursor-pointer flex-col items-center justify-center gap-1.5 rounded-2xl border border-dashed border-line bg-transparent px-4 py-4 text-[12px] text-ink-faint transition hover:border-clay-300 hover:text-clay-700"
            @click="openCreateAccount"
          >
            <Plus :size="16" :stroke-width="1.5" />
            添加账户
          </button>
        </div>
      </section>

      <!-- 图表 -->
      <section class="mt-5 grid gap-4 lg:grid-cols-2">
        <article class="surface p-4">
          <h2 class="mb-2 text-[13.5px] font-medium text-ink">支出分类</h2>
          <TrendChart
            v-if="donutValues.length"
            kind="donut"
            :categories="donutCategories"
            :series="[{ name: '支出', values: donutValues }]"
            unit=" 元"
            :height="230"
          />
          <EmptyState
            v-else
            title="本月还没有支出"
            hint="记下第一笔支出，这里就会出现分类占比。"
            class="!border-0 !py-6"
            :icon="false"
          />
        </article>

        <article class="surface p-4">
          <div class="mb-2 flex flex-wrap items-center justify-between gap-2">
            <h2 class="text-[13.5px] font-medium text-ink">近六月收支</h2>
            <SegmentedControl
              :model-value="trendMode"
              :options="trendOptions"
              @update:model-value="setTrendMode"
            />
          </div>
          <TrendChart
            v-if="trendCategories.length"
            kind="bar"
            :categories="trendCategories"
            :series="trendSeries"
            unit=" 元"
            :height="230"
          />
          <EmptyState
            v-else
            title="暂无趋势数据"
            hint="记账一段时间后，这里会显示收支走势。"
            class="!border-0 !py-6"
            :icon="false"
          />
        </article>
      </section>

      <!-- 流水 -->
      <section class="mt-5">
        <div class="mb-3 flex flex-wrap items-center gap-2">
          <div class="flex items-center gap-1">
            <button
              type="button"
              class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-muted hover:bg-paper-sunken"
              aria-label="上个月"
              @click="shiftMonth(-1)"
            >
              <ChevronLeft :size="15" :stroke-width="1.5" />
            </button>
            <span class="min-w-[92px] text-center text-[12.5px] text-ink">{{ monthLabel }}</span>
            <button
              type="button"
              class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-muted hover:bg-paper-sunken"
              aria-label="下个月"
              @click="shiftMonth(1)"
            >
              <ChevronRight :size="15" :stroke-width="1.5" />
            </button>
          </div>

          <select v-model.number="categoryFilter" class="field !w-auto !py-1.5 text-[12px]">
            <option :value="null">全部分类</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">{{ cat.name }}</option>
          </select>

          <button
            v-if="accountFilter !== null || categoryFilter !== null"
            type="button"
            class="btn-quiet !py-1 !text-[11.5px]"
            @click="clearFilters"
          >
            清除筛选
          </button>

          <span class="ml-auto text-[11.5px] text-ink-faint">{{ transactions.length }} 笔</span>
        </div>

        <div v-if="transactions.length" class="surface divide-y divide-line overflow-hidden">
          <div v-for="group in groups" :key="group.date">
            <div class="flex items-center justify-between bg-paper-sunken/50 px-4 py-1.5">
              <span class="num text-[11px] text-ink-muted">{{ group.date }}</span>
              <span class="text-[10.5px] text-ink-faint">{{ group.items.length }} 笔</span>
            </div>

            <div
              v-for="tx in group.items"
              :key="tx.id"
              class="group flex items-center gap-3 px-4 py-2.5 transition hover:bg-paper-sunken/40"
            >
              <span
                class="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl"
                :class="
                  tx.tx_type === 'income'
                    ? 'bg-[#7A9E7E]/10 text-positive'
                    : tx.tx_type === 'expense'
                      ? 'bg-[#C0714F]/10 text-negative'
                      : 'bg-clay-100 text-clay-700'
                "
              >
                <component :is="txIcon(tx)" :size="15" :stroke-width="1.5" />
              </span>

              <div class="min-w-0 flex-1">
                <p class="truncate text-[13px] text-ink">{{ txTitle(tx) }}</p>
                <p class="truncate text-[11px] text-ink-faint">
                  {{ tx.note || (tx.tx_type === 'transfer' ? '账户间转账' : tx.account_name || '—') }}
                </p>
              </div>

              <span class="num shrink-0 text-[13px] font-medium" :class="amountClass(tx)">
                {{ amountText(tx) }}
              </span>

              <button
                type="button"
                class="flex h-7 w-7 shrink-0 cursor-pointer items-center justify-center rounded-lg text-ink-faint opacity-0 transition hover:bg-paper-card hover:text-negative focus:opacity-100 group-hover:opacity-100"
                aria-label="删除流水"
                @click="deleting = tx"
              >
                <Trash2 :size="13" :stroke-width="1.5" />
              </button>
            </div>
          </div>
        </div>

        <EmptyState
          v-else
          title="这个月还没有流水"
          hint="点右上角「记一笔」，收入、支出、转账都能记。"
        >
          <button type="button" class="btn-ghost" @click="txDialogOpen = true">记一笔</button>
        </EmptyState>
      </section>
    </template>

    <TransactionDialog
      :open="txDialogOpen"
      :accounts="accounts"
      :categories="categories"
      @close="txDialogOpen = false"
      @saved="queryClient.invalidateQueries()"
    />

    <AccountDialog
      :open="accountDialogOpen"
      :account="editingAccount"
      @close="accountDialogOpen = false"
      @saved="queryClient.invalidateQueries()"
    />

    <ConfirmDialog
      :open="deleting !== null"
      title="删除流水"
      message="确认删除这笔流水吗？账户余额会随之回退。"
      :loading="deleteLoading"
      @cancel="deleting = null"
      @confirm="confirmDelete"
    />
  </AppShell>
</template>
