<script setup lang="ts">
import { Compass } from 'lucide-vue-next'
import { useRouter } from 'vue-router'

const router = useRouter()
</script>

<template>
  <main class="flex min-h-screen items-center justify-center bg-paper px-6">
    <div class="surface w-full max-w-md p-8 text-center animate-scale-in">
      <div class="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-paper-sunken text-ink-muted">
        <Compass :size="22" :stroke-width="1.5" />
      </div>
      <h1 class="text-[18px] font-semibold text-ink">这里没有内容</h1>
      <p class="mt-2 text-[13px] leading-relaxed text-ink-muted">
        路径可能已经变化，或者这条记录被删除了。
      </p>
      <button class="btn-ghost mt-6" type="button" @click="router.push('/')">回到首页</button>
    </div>
  </main>
</template>
