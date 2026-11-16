<script setup lang="ts">
defineProps<{
  title: string
  description?: string
}>()
</script>

<template>
  <header class="mb-6 flex flex-wrap items-end justify-between gap-3">
    <div>
      <h1 class="text-[22px] font-semibold tracking-tight text-ink">{{ title }}</h1>
      <p v-if="description" class="mt-1 text-[13px] text-ink-muted">{{ description }}</p>
    </div>
    <div v-if="$slots.actions" class="flex items-center gap-2"><slot name="actions" /></div>
  </header>
</template>
