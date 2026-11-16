<script setup lang="ts">
import { Feather } from 'lucide-vue-next'

withDefaults(defineProps<{ title: string; hint?: string; icon?: boolean }>(), {
  hint: '',
  icon: true,
})
</script>

<template>
  <div class="flex flex-col items-center justify-center rounded-2xl border border-dashed border-line px-6 py-12 text-center">
    <div
      v-if="icon"
      class="mb-3 flex h-11 w-11 items-center justify-center rounded-2xl bg-paper-sunken text-clay-400"
    >
      <Feather :size="19" :stroke-width="1.5" />
    </div>
    <p class="text-[14px] font-medium text-ink">{{ title }}</p>
    <p v-if="hint" class="mt-1.5 max-w-sm text-[12.5px] leading-relaxed text-ink-muted">{{ hint }}</p>
    <div v-if="$slots.default" class="mt-4"><slot /></div>
  </div>
</template>
