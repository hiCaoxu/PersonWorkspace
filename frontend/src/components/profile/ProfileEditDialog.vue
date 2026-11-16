<script setup lang="ts">
import { ref, watch } from 'vue'

import { http, type Profile } from '@/api/client'
import AppDialog from '@/components/ui/AppDialog.vue'

const props = defineProps<{ open: boolean; profile: Profile | null }>()
const emit = defineEmits<{ close: []; saved: [] }>()

const name = ref('')
const phone = ref('')
const email = ref('')
const wechat = ref('')
const bloodType = ref('')
const address = ref('')
const height = ref('')
const bio = ref('')
const lunarMonth = ref('')
const lunarDay = ref('')
const saving = ref(false)
const error = ref('')

watch(
  () => props.open,
  (open) => {
    if (!open) return
    const profile = props.profile
    name.value = profile?.name ?? ''
    phone.value = profile?.phone ?? ''
    email.value = profile?.email ?? ''
    wechat.value = profile?.wechat ?? ''
    bloodType.value = profile?.blood_type ?? ''
    address.value = profile?.address ?? ''
    height.value = profile?.height_cm ?? ''
    bio.value = profile?.bio ?? ''
    lunarMonth.value = String(profile?.lunar_birthday_month ?? '')
    lunarDay.value = String(profile?.lunar_birthday_day ?? '')
    error.value = ''
  },
)

async function save(): Promise<void> {
  if (!name.value.trim()) {
    error.value = '请填写姓名'
    return
  }
  saving.value = true
  error.value = ''
  try {
    await http.patch('/profile', {
      name: name.value.trim(),
      phone: phone.value || null,
      email: email.value || null,
      wechat: wechat.value || null,
      blood_type: bloodType.value || null,
      address: address.value || null,
      height_cm: height.value ? Number(height.value) : null,
      bio: bio.value || null,
      lunar_birthday_month: lunarMonth.value ? Number(lunarMonth.value) : null,
      lunar_birthday_day: lunarDay.value ? Number(lunarDay.value) : null,
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
  <AppDialog :open="open" title="编辑个人信息" wide @close="emit('close')">
    <div class="space-y-3">
      <div class="grid gap-3 sm:grid-cols-2">
        <div>
          <label class="label-text">姓名</label>
          <input v-model="name" class="field" placeholder="你的名字" />
        </div>
        <div>
          <label class="label-text">手机</label>
          <input v-model="phone" class="field" placeholder="13800000000" />
        </div>
        <div>
          <label class="label-text">邮箱</label>
          <input v-model="email" type="email" class="field" placeholder="you@example.com" />
        </div>
        <div>
          <label class="label-text">微信</label>
          <input v-model="wechat" class="field" placeholder="微信号" />
        </div>
        <div>
          <label class="label-text">血型</label>
          <select v-model="bloodType" class="field">
            <option value="">未填写</option>
            <option v-for="item in ['A', 'B', 'AB', 'O']" :key="item" :value="item">{{ item }} 型</option>
          </select>
        </div>
        <div>
          <label class="label-text">身高（cm）</label>
          <input v-model="height" type="number" step="0.1" class="field num" placeholder="175" />
        </div>
      </div>

      <div>
        <label class="label-text">住址</label>
        <input v-model="address" class="field" placeholder="常住城市 / 详细地址" />
      </div>

      <div>
        <label class="label-text">农历生日</label>
        <div class="flex items-center gap-2">
          <input v-model="lunarMonth" type="number" min="1" max="12" class="field num" placeholder="月" />
          <span class="text-[12px] text-ink-faint">月</span>
          <input v-model="lunarDay" type="number" min="1" max="30" class="field num" placeholder="日" />
          <span class="text-[12px] text-ink-faint">日</span>
        </div>
        <p class="mt-1 text-[11px] text-ink-faint">修改农历生日后，公历生日与生肖星座会按农历重新换算。</p>
      </div>

      <div>
        <label class="label-text">自我介绍</label>
        <textarea v-model="bio" rows="2" class="field resize-y" placeholder="一句话介绍自己" />
      </div>

      <p v-if="error" class="text-[12px] text-negative">{{ error }}</p>
    </div>

    <template #footer>
      <div class="flex justify-end gap-2">
        <button type="button" class="btn-ghost" @click="emit('close')">取消</button>
        <button type="button" class="btn-primary" :disabled="saving" @click="save">
          {{ saving ? '保存中…' : '保存' }}
        </button>
      </div>
    </template>
  </AppDialog>
</template>
