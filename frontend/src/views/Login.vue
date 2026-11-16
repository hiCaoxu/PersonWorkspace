<script setup lang="ts">
import { ArrowRight, Lock } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { useSessionStore } from '@/stores/session'

const passcode = ref('')
const error = ref('')
const loading = ref(false)

const session = useSessionStore()
const router = useRouter()
const route = useRoute()

async function submit(): Promise<void> {
  if (!passcode.value.trim()) {
    error.value = '请输入口令'
    return
  }
  loading.value = true
  error.value = ''
  try {
    await session.login(passcode.value)
    const redirect = typeof route.query.redirect === 'string' ? route.query.redirect : '/'
    router.replace(redirect)
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-paper px-5">
    <div class="w-full max-w-[380px] animate-fade-up">
      <div class="mb-8 text-center">
        <div
          class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl border border-line bg-paper-card text-clay-600 shadow-soft"
        >
          <Lock :size="20" :stroke-width="1.5" />
        </div>
        <h1 class="text-[20px] font-semibold tracking-tight text-ink">个人工作台</h1>
        <p class="mt-1.5 text-[12.5px] text-ink-muted">输入口令进入，数据只保存在你自己的服务器</p>
      </div>

      <form class="surface p-6" @submit.prevent="submit">
        <label class="label-text" for="passcode">访问口令</label>
        <input
          id="passcode"
          v-model="passcode"
          type="password"
          autocomplete="current-password"
          class="field"
          placeholder="请输入你的口令"
          :disabled="loading"
        />

        <p v-if="error" class="mt-2 text-[12px] text-negative">{{ error }}</p>

        <button type="submit" class="btn-primary mt-5 w-full" :disabled="loading">
          {{ loading ? '验证中…' : '进入工作台' }}
          <ArrowRight v-if="!loading" :size="15" :stroke-width="1.5" />
        </button>
      </form>

      <p class="mt-5 text-center text-[11.5px] leading-relaxed text-ink-faint">
        首次部署的口令来自服务器环境变量 ADMIN_PASSWORD，
        登录后可在档案页修改。
      </p>
    </div>
  </main>
</template>
