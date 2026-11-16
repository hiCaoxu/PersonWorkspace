<script setup lang="ts">
interface Option {
  key: string
  label: string
  count?: number
}

defineProps<{ modelValue: string; options: Option[] }>()
const emit = defineEmits<{ 'update:modelValue': [string] }>()
</script>

<template>
  <div class="no-scrollbar inline-flex max-w-full gap-1 overflow-x-auto rounded-xl bg-paper-sunken p-1">
    <button
      v-for="option in options"
      :key="option.key"
      type="button"
      class="shrink-0 cursor-pointer rounded-lg px-3 py-1.5 text-[12.5px] transition-all duration-200 ease-calm"
      :class="
        modelValue === option.key
          ? 'bg-paper-card text-ink shadow-soft'
          : 'text-ink-muted hover:text-ink'
      "
      @click="emit('update:modelValue', option.key)"
    >
      {{ option.label }}
      <span v-if="option.count !== undefined" class="num ml-1 text-[11px] text-ink-faint">
        {{ option.count }}
      </span>
    </button>
  </div>
</template>
