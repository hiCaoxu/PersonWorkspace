<script setup lang="ts">
import { X } from 'lucide-vue-next'

defineProps<{
  open: boolean
  title: string
  wide?: boolean
}>()

const emit = defineEmits<{ close: [] }>()
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-center justify-center p-4"
      role="dialog"
      aria-modal="true"
    >
      <div class="absolute inset-0 bg-ink/25 backdrop-blur-[2px]" @click="emit('close')" />
      <div
        class="relative flex max-h-[88vh] w-full flex-col overflow-hidden rounded-2xl border border-line bg-paper-card shadow-pop animate-scale-in"
        :class="wide ? 'max-w-3xl' : 'max-w-lg'"
      >
        <header class="flex shrink-0 items-center justify-between border-b border-line px-5 py-3.5">
          <h2 class="text-[15px] font-medium text-ink">{{ title }}</h2>
          <button
            type="button"
            class="btn-quiet cursor-pointer !px-2 !py-1"
            aria-label="关闭"
            @click="emit('close')"
          >
            <X :size="16" :stroke-width="1.5" />
          </button>
        </header>
        <div class="min-h-0 flex-1 overflow-y-auto px-5 py-4">
          <slot />
        </div>
        <footer v-if="$slots.footer" class="shrink-0 border-t border-line px-5 py-3">
          <slot name="footer" />
        </footer>
      </div>
    </div>
  </Teleport>
</template>
