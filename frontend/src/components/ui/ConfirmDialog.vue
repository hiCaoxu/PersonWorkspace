<script setup lang="ts">
import AppDialog from '@/components/ui/AppDialog.vue'

withDefaults(
  defineProps<{
    open: boolean
    title: string
    message: string
    confirmText?: string
    danger?: boolean
    loading?: boolean
  }>(),
  { confirmText: '确认删除', danger: true, loading: false },
)

const emit = defineEmits<{ confirm: []; cancel: [] }>()
</script>

<template>
  <AppDialog :open="open" :title="title" @close="emit('cancel')">
    <p class="text-[13.5px] leading-relaxed text-ink-muted">{{ message }}</p>
    <template #footer>
      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost" @click="emit('cancel')">取消</button>
        <button
          type="button"
          :class="danger ? 'btn-primary !bg-negative hover:!bg-[#a85f40]' : 'btn-primary'"
          :disabled="loading"
          @click="emit('confirm')"
        >
          {{ loading ? '处理中…' : confirmText }}
        </button>
      </div>
    </template>
  </AppDialog>
</template>
