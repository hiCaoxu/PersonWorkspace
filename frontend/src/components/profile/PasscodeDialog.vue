<script setup lang="ts">
import { ref, watch } from 'vue'

import { http } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'

const props = defineProps<{ open: boolean }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const oldPasscode = ref('')
const newPasscode = ref('')
const confirmPasscode = ref('')
const saving = ref(false)
const error = ref('')

watch(
  () => props.open,
  (open) => {
    if (!open) return
    oldPasscode.value = ''
    newPasscode.value = ''
    confirmPasscode.value = ''
    error.value = ''
  },
)

async function save(): Promise<void> {
  error.value = ''
  if (!oldPasscode.value || !newPasscode.value) {
    error.value = '请填写原口令与新口令'
    return
  }
  if (newPasscode.value.length < 6) {
    error.value = '新口令至少 6 位'
    return
  }
  if (newPasscode.value !== confirmPasscode.value) {
    error.value = '两次输入的新口令不一致'
    return
  }

  saving.value = true
  try {
    await http.post('/auth/change-passcode', {
      old_passcode: oldPasscode.value,
      new_passcode: newPasscode.value,
    })
    emit('saved')
    emit('close')
  } catch (err) {
    error.value = (err as Error).message
  } finally {
    saving.value = false
  }
}
</script>

<template>
  <AppDialog :open="open" title="修改访问口令" @close="emit('close')">
    <div class="space-y-3">
      <div>
        <label class="label-text">原口令</label>
        <input v-model="oldPasscode" type="password" autocomplete="current-password" class="field" />
      </div>
      <div>
        <label class="label-text">新口令</label>
        <input v-model="newPasscode" type="password" autocomplete="new-password" class="field" />
      </div>
      <div>
        <label class="label-text">确认新口令</label>
        <input v-model="confirmPasscode" type="password" autocomplete="new-password" class="field" />
      </div>
      <p class="text-[11px] leading-relaxed text-ink-faint">
        口令使用 argon2 哈希存储，修改后其他设备需要重新登录。
      </p>
      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost" @click="emit('close')">取消</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '确认修改' }}
        </button>
      </div>
    </template>
  </AppDialog>
</template>
