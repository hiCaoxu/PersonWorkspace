<script setup lang="ts">
import {
  BookOpen,
  Clapperboard,
  HeartPulse,
  Home,
  ListTodo,
  LogOut,
  MoreHorizontal,
  NotebookPen,
  UserRound,
  Wallet,
  X,
} from 'lucide-vue-next'
import { ref } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/stores/session'

const nav = [
  { to: '/', label: '首页', icon: Home },
  { to: '/todos', label: '待办', icon: ListTodo },
  { to: '/diary', label: '日记', icon: BookOpen },
  { to: '/notes', label: '笔记', icon: NotebookPen },
  { to: '/health', label: '健康', icon: HeartPulse },
  { to: '/entertainment', label: '娱乐', icon: Clapperboard },
  { to: '/finance', label: '记账', icon: Wallet },
  { to: '/profile', label: '档案', icon: UserRound },
]

const primaryMobile = nav.slice(0, 4)
const moreMobile = nav.slice(4)

const route = useRoute()
const router = useRouter()
const session = useSessionStore()
const moreOpen = ref(false)

function isActive(path: string): boolean {
  return path === '/' ? route.path === '/' : route.path.startsWith(path)
}

async function handleLogout(): Promise<void> {
  await session.logout()
  router.push('/login')
}
</script>

<template>
  <div class="min-h-screen bg-paper">
    <!-- 桌面侧栏 -->
    <aside
      class="fixed left-0 top-0 z-30 hidden h-screen w-[76px] flex-col items-center gap-1 border-r border-line bg-paper-card/80 py-5 backdrop-blur lg:flex"
    >
      <div
        class="mb-4 flex h-10 w-10 items-center justify-center rounded-xl border border-line bg-paper text-[15px] font-semibold text-clay-700"
      >
        工
      </div>

      <RouterLink
        v-for="item in nav"
        :key="item.to"
        :to="item.to"
        class="group relative flex h-11 w-11 items-center justify-center rounded-xl transition-all duration-200 ease-calm"
        :class="
          isActive(item.to)
            ? 'bg-clay-100 text-clay-700'
            : 'text-ink-faint hover:bg-paper-sunken hover:text-ink-muted'
        "
      >
        <component :is="item.icon" :size="19" :stroke-width="1.5" />
        <span
          class="pointer-events-none absolute left-[52px] whitespace-nowrap rounded-lg border border-line bg-paper-card px-2 py-1 text-[12px] text-ink opacity-0 shadow-soft transition-opacity duration-150 group-hover:opacity-100"
        >
          {{ item.label }}
        </span>
      </RouterLink>

      <div class="mt-auto flex flex-col items-center gap-2">
        <button
          type="button"
          class="flex h-11 w-11 cursor-pointer items-center justify-center rounded-xl text-ink-faint transition hover:bg-paper-sunken hover:text-negative"
          title="退出登录"
          @click="handleLogout"
        >
          <LogOut :size="18" :stroke-width="1.5" />
        </button>
      </div>
    </aside>

    <!-- 内容区 -->
    <main class="mx-auto w-full max-w-[1200px] px-4 pb-24 pt-6 sm:px-6 lg:pb-12 lg:pl-[calc(76px+24px)]">
      <slot />
    </main>

    <!-- 移动底栏 -->
    <nav
      class="fixed bottom-0 left-0 right-0 z-30 flex items-center justify-around border-t border-line bg-paper-card/95 px-2 pb-[env(safe-area-inset-bottom)] backdrop-blur lg:hidden"
    >
      <RouterLink
        v-for="item in primaryMobile"
        :key="item.to"
        :to="item.to"
        class="flex min-h-[56px] flex-1 flex-col items-center justify-center gap-1 text-[11px] transition"
        :class="isActive(item.to) ? 'text-clay-700' : 'text-ink-faint'"
      >
        <component :is="item.icon" :size="19" :stroke-width="1.5" />
        {{ item.label }}
      </RouterLink>

      <button
        type="button"
        class="flex min-h-[56px] flex-1 cursor-pointer flex-col items-center justify-center gap-1 text-[11px] text-ink-faint"
        @click="moreOpen = true"
      >
        <MoreHorizontal :size="19" :stroke-width="1.5" />
        更多
      </button>
    </nav>

    <!-- 移动端更多抽屉 -->
    <Teleport to="body">
      <div v-if="moreOpen" class="fixed inset-0 z-40 flex items-end lg:hidden">
        <div class="absolute inset-0 bg-ink/25" @click="moreOpen = false" />
        <div class="relative w-full rounded-t-3xl border-t border-line bg-paper-card p-5 pb-8 animate-fade-up">
          <div class="mb-4 flex items-center justify-between">
            <span class="text-[14px] font-medium text-ink">全部模块</span>
            <button type="button" class="btn-quiet !px-2 !py-1" @click="moreOpen = false">
              <X :size="16" :stroke-width="1.5" />
            </button>
          </div>
          <div class="grid grid-cols-4 gap-3">
            <RouterLink
              v-for="item in moreMobile"
              :key="item.to"
              :to="item.to"
              class="flex flex-col items-center gap-2 rounded-2xl border border-line bg-paper py-4 text-[12px] text-ink"
              @click="moreOpen = false"
            >
              <component :is="item.icon" :size="19" :stroke-width="1.5" class="text-clay-600" />
              {{ item.label }}
            </RouterLink>
            <button
              type="button"
              class="flex flex-col items-center gap-2 rounded-2xl border border-line bg-paper py-4 text-[12px] text-ink"
              @click="handleLogout"
            >
              <LogOut :size="19" :stroke-width="1.5" class="text-negative" />
              退出
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>
