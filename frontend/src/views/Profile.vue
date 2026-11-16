<script setup lang="ts">
import { useQuery, useQueryClient } from '@tanstack/vue-query'
import {
  Cake,
  Eye,
  KeyRound,
  MapPin,
  Pencil,
  Plus,
  Sparkles,
  Star,
  Trash2,
  UserRound,
} from 'lucide-vue-next'
import { computed, onBeforeUnmount, ref } from 'vue'

import { http, type LifeEvent, type Profile } from '@/api/client'
import AppShell from '@/components/layout/AppShell.vue'
import PageHeader from '@/components/layout/PageHeader.vue'
import LifeEventDialog from '@/components/profile/LifeEventDialog.vue'
import PasscodeDialog from '@/components/profile/PasscodeDialog.vue'
import ProfileEditDialog from '@/components/profile/ProfileEditDialog.vue'
import AppDialog from '@/components/ui/AppDialog.vue'
import ConfirmDialog from '@/components/ui/ConfirmDialog.vue'
import EmptyState from '@/components/ui/EmptyState.vue'
import { formatDate } from '@/composables/useFormat'

const queryClient = useQueryClient()

const profileQuery = useQuery({
  queryKey: ['profile'],
  queryFn: async () => {
    const { data } = await http.get<Profile>('/profile')
    return data
  },
})

const eventsQuery = useQuery({
  queryKey: ['life-events'],
  queryFn: async () => {
    const { data } = await http.get<{ items: LifeEvent[] }>('/life-events')
    return data.items
  },
})

const profile = computed(() => profileQuery.data.value)
const events = computed(() => eventsQuery.data.value ?? [])

const editOpen = ref(false)
const passcodeOpen = ref(false)
const eventDialogOpen = ref(false)
const editingEvent = ref<LifeEvent | null>(null)
const deletingEvent = ref<LifeEvent | null>(null)
const deleteLoading = ref(false)

/* ---------- 身份证揭示 ---------- */
const revealOpen = ref(false)
const passcode = ref('')
const revealing = ref(false)
const revealError = ref('')
const revealedId = ref('')
let hideTimer: ReturnType<typeof setTimeout> | null = null

async function reveal(): Promise<void> {
  if (!passcode.value) {
    revealError.value = '请输入登录口令'
    return
  }
  revealing.value = true
  revealError.value = ''
  try {
    const ticketRes = await http.post<{ ticket: string }>('/auth/reveal', {
      passcode: passcode.value,
    })
    const cardRes = await http.post<{ id_card: string }>('/profile/reveal', {
      ticket: ticketRes.data.ticket,
    })
    revealedId.value = cardRes.data.id_card
    revealOpen.value = false
    passcode.value = ''
    if (hideTimer) clearTimeout(hideTimer)
    hideTimer = setTimeout(() => {
      revealedId.value = ''
    }, 5 * 60 * 1000)
  } catch (err) {
    revealError.value = (err as Error).message
  } finally {
    revealing.value = false
  }
}

function closeReveal(): void {
  revealOpen.value = false
  passcode.value = ''
  revealError.value = ''
}

onBeforeUnmount(() => {
  if (hideTimer) clearTimeout(hideTimer)
})

/* ---------- 时间线 ---------- */
function openCreateEvent(): void {
  editingEvent.value = null
  eventDialogOpen.value = true
}

function openEditEvent(event: LifeEvent): void {
  editingEvent.value = event
  eventDialogOpen.value = true
}

function onRemoveEvent(): void {
  if (!editingEvent.value) return
  deletingEvent.value = editingEvent.value
  eventDialogOpen.value = false
}

async function confirmDeleteEvent(): Promise<void> {
  if (!deletingEvent.value) return
  deleteLoading.value = true
  try {
    await http.delete(`/life-events/${deletingEvent.value.id}`)
    deletingEvent.value = null
    await queryClient.invalidateQueries({ queryKey: ['life-events'] })
  } finally {
    deleteLoading.value = false
  }
}

const infoRows = computed(() => {
  const data = profile.value
  if (!data) return []
  return [
    { label: '姓名', value: data.name },
    { label: '手机', value: data.phone },
    { label: '邮箱', value: data.email },
    { label: '微信', value: data.wechat },
    { label: '血型', value: data.blood_type ? `${data.blood_type} 型` : null },
    { label: '身高', value: data.height_cm ? `${data.height_cm} cm` : null },
    { label: '住址', value: data.address },
  ]
})

const birthdayLine = computed(() => {
  const data = profile.value
  if (!data) return ''
  const parts = [
    data.solar_birthday ? `公历 ${formatDate(data.solar_birthday)}` : null,
    data.lunar_birthday,
  ].filter(Boolean)
  return parts.join(' · ')
})
</script>

<template>
  <AppShell>
    <PageHeader title="档案" description="只写给自己的资料与人生节点，证件号默认脱敏。">
      <template #actions>
        <button type="button" class="btn-ghost" @click="passcodeOpen = true">
          <KeyRound :size="15" :stroke-width="1.5" />
          修改口令
        </button>
        <button type="button" class="btn-primary" @click="editOpen = true">
          <Pencil :size="15" :stroke-width="1.5" />
          编辑资料
        </button>
      </template>
    </PageHeader>

    <div v-if="profileQuery.isPending.value" class="space-y-4">
      <div class="h-32 animate-pulse rounded-2xl bg-paper-sunken" />
      <div class="h-48 animate-pulse rounded-2xl bg-paper-sunken" />
    </div>

    <template v-else-if="profile">
      <section class="grid gap-4 lg:grid-cols-[minmax(0,1.15fr)_minmax(0,1fr)]">
        <!-- 个人信息 -->
        <article class="surface p-5">
          <header class="flex items-start gap-4 border-b border-line pb-4">
            <div
              class="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-line bg-clay-50 text-[20px] font-semibold text-clay-700"
            >
              {{ profile.name?.slice(0, 1) || '我' }}
            </div>
            <div class="min-w-0">
              <h2 class="text-[18px] font-semibold text-ink">{{ profile.name }}</h2>
              <p class="mt-1 text-[12px] text-ink-muted">
                {{ profile.bio || '还没有写自我介绍' }}
              </p>
              <p class="mt-1 flex items-center gap-1 text-[11px] text-ink-faint">
                <Sparkles :size="11" :stroke-width="1.5" />
                农历{{ profile.today_lunar }}
              </p>
            </div>
          </header>

          <dl class="mt-4 grid gap-x-6 gap-y-3 sm:grid-cols-2">
            <div v-for="row in infoRows" :key="row.label" class="min-w-0">
              <dt class="text-[11.5px] text-ink-faint">{{ row.label }}</dt>
              <dd class="mt-0.5 truncate text-[13px] text-ink">{{ row.value || '—' }}</dd>
            </div>

            <!-- 身份证 -->
            <div class="min-w-0 sm:col-span-2">
              <dt class="text-[11.5px] text-ink-faint">身份证</dt>
              <dd class="mt-0.5 flex items-center gap-2">
                <span class="num text-[13px] tracking-wide text-ink">
                  {{ revealedId || profile.id_card_masked || '未填写' }}
                </span>
                <button
                  v-if="!revealedId"
                  type="button"
                  class="flex cursor-pointer items-center gap-1 text-[11.5px] text-clay-600 hover:text-clay-700"
                  @click="revealOpen = true"
                >
                  <Eye :size="12" :stroke-width="1.5" />
                  查看
                </button>
                <span v-else class="flex items-center gap-1 text-[11px] text-ink-faint">
                  <Eye :size="12" :stroke-width="1.5" />
                  5 分钟后自动隐藏
                </span>
              </dd>
            </div>
          </dl>
        </article>

        <!-- 生日与生肖 -->
        <article class="surface p-5">
          <div class="flex items-center gap-2">
            <span class="flex h-8 w-8 items-center justify-center rounded-xl bg-clay-100 text-clay-700">
              <Cake :size="15" :stroke-width="1.5" />
            </span>
            <h2 class="text-[14px] font-medium text-ink">生日与生肖</h2>
          </div>

          <p class="mt-3 text-[13px] leading-relaxed text-ink">{{ birthdayLine }}</p>

          <div class="mt-3 grid grid-cols-3 gap-2">
            <div class="rounded-xl bg-paper p-3 text-center">
              <p class="text-[10.5px] text-ink-faint">生肖</p>
              <p class="mt-1 text-[14px] font-medium text-ink">{{ profile.zodiac || '—' }}</p>
            </div>
            <div class="rounded-xl bg-paper p-3 text-center">
              <p class="text-[10.5px] text-ink-faint">星座</p>
              <p class="mt-1 text-[14px] font-medium text-ink">{{ profile.constellation || '—' }}</p>
            </div>
            <div class="rounded-xl bg-paper p-3 text-center">
              <p class="text-[10.5px] text-ink-faint">年龄</p>
              <p class="num mt-1 text-[14px] font-medium text-ink">
                {{ profile.age !== null ? `${profile.age} 岁` : '—' }}
              </p>
            </div>
          </div>

          <div class="mt-3 rounded-xl border border-line bg-paper px-3 py-2.5">
            <p class="text-[12px] text-ink-muted">
              距下次农历生日还有
              <span class="num mx-1 text-[15px] font-semibold text-clay-700">
                {{ profile.days_to_birthday ?? '—' }}
              </span>
              天
            </p>
            <p v-if="profile.next_birthday" class="num mt-0.5 text-[11px] text-ink-faint">
              {{ formatDate(profile.next_birthday) }}
            </p>
          </div>

          <p class="mt-3 flex items-start gap-1.5 text-[11px] leading-relaxed text-ink-faint">
            <MapPin :size="12" :stroke-width="1.5" class="mt-0.5 shrink-0" />
            身份证号使用 AES-256-GCM 加密存储，列表只展示前 6 位与后 4 位。
          </p>
        </article>
      </section>

      <!-- 人生大事 -->
      <section class="mt-6">
        <div class="mb-4 flex items-center justify-between">
          <h2 class="text-[15px] font-medium text-ink">人生大事</h2>
          <button type="button" class="btn-ghost !py-1.5" @click="openCreateEvent">
            <Plus :size="14" :stroke-width="1.5" />
            记录一件
          </button>
        </div>

        <ol v-if="events.length" class="relative ml-2 border-l border-line pl-6">
          <li v-for="event in events" :key="event.id" class="relative pb-6 last:pb-0">
            <span
              class="absolute -left-[27px] top-1.5 h-2.5 w-2.5 rounded-full border-2 border-paper-card"
              :class="event.is_highlight ? 'bg-clay-500' : 'bg-clay-300'"
            />

            <div class="surface group p-4 transition hover:border-line-strong">
              <div class="flex flex-wrap items-start justify-between gap-2">
                <div class="min-w-0">
                  <div class="flex items-center gap-2">
                    <h3 class="text-[14px] font-medium text-ink">{{ event.title }}</h3>
                    <Star
                      v-if="event.is_highlight"
                      :size="12"
                      :stroke-width="1.5"
                      class="text-clay-500"
                    />
                  </div>
                  <p class="num mt-1 flex flex-wrap items-center gap-x-2 text-[11.5px] text-ink-faint">
                    <span>{{ formatDate(event.event_date) }}</span>
                    <span v-if="event.lunar">农历{{ event.lunar }}</span>
                    <span v-if="event.location" class="flex items-center gap-0.5">
                      <MapPin :size="10" :stroke-width="1.5" />
                      {{ event.location }}
                    </span>
                  </p>
                </div>

                <div class="flex items-center gap-0.5 opacity-0 transition group-hover:opacity-100 focus-within:opacity-100">
                  <button
                    type="button"
                    class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-sunken hover:text-ink"
                    aria-label="编辑"
                    @click="openEditEvent(event)"
                  >
                    <Pencil :size="13" :stroke-width="1.5" />
                  </button>
                  <button
                    type="button"
                    class="flex h-7 w-7 cursor-pointer items-center justify-center rounded-lg text-ink-faint hover:bg-paper-sunken hover:text-negative"
                    aria-label="删除"
                    @click="deletingEvent = event"
                  >
                    <Trash2 :size="13" :stroke-width="1.5" />
                  </button>
                </div>
              </div>

              <p v-if="event.description" class="mt-2 text-[12.5px] leading-relaxed text-ink-muted">
                {{ event.description }}
              </p>

              <img
                v-if="event.image_url"
                :src="event.image_url"
                alt=""
                class="mt-3 max-h-56 w-full rounded-xl border border-line object-cover"
                loading="lazy"
              />
            </div>
          </li>
        </ol>

        <EmptyState
          v-else
          title="还没有记录人生大事"
          hint="毕业、第一份工作、搬家、旅行，都值得记一笔。"
        >
          <button type="button" class="btn-ghost" @click="openCreateEvent">
            <Plus :size="14" :stroke-width="1.5" />
            记录一件
          </button>
        </EmptyState>
      </section>
    </template>

    <div v-else class="surface flex items-center justify-center py-16">
      <EmptyState title="档案尚未初始化" hint="检查后端种子数据是否执行成功。" :icon="false" />
    </div>

    <ProfileEditDialog
      :open="editOpen"
      :profile="profile ?? null"
      @close="editOpen = false"
      @saved="queryClient.invalidateQueries({ queryKey: ['profile'] })"
    />

    <PasscodeDialog :open="passcodeOpen" @close="passcodeOpen = false" @saved="passcodeOpen = false" />

    <AppDialog :open="revealOpen" title="查看完整身份证号" @close="closeReveal">
      <div class="space-y-3">
        <p class="flex items-center gap-1.5 text-[12.5px] text-ink-muted">
          <UserRound :size="14" :stroke-width="1.5" class="text-clay-600" />
          再次输入登录口令，验证通过后显示 5 分钟。
        </p>
        <input
          v-model="passcode"
          type="password"
          class="field"
          autocomplete="current-password"
          placeholder="登录口令"
          @keydown.enter="reveal"
        />
        <p v-if="revealError" class="text-[12px] text-negative">{{ revealError }}</p>
      </div>

      <template #footer>
        <div class="flex justify-end gap-2">
          <button type="button" class="btn-ghost" @click="closeReveal">取消</button>
          <button type="button" class="btn-primary" :disabled="revealing" @click="reveal">
            {{ revealing ? '验证中…' : '验证并查看' }}
          </button>
        </div>
      </template>
    </AppDialog>

    <LifeEventDialog
      v-if="eventDialogOpen"
      :open="eventDialogOpen"
      :event="editingEvent"
      @close="eventDialogOpen = false"
      @saved="queryClient.invalidateQueries()"
      @remove="onRemoveEvent"
    />

    <ConfirmDialog
      :open="deletingEvent !== null"
      title="删除人生大事"
      :message="`确认删除「${deletingEvent?.title ?? ''}」吗？删除后不可恢复。`"
      :loading="deleteLoading"
      @cancel="deletingEvent = null"
      @confirm="confirmDeleteEvent"
    />
  </AppShell>
</template>
