<script setup lang="ts">
import { useQuery } from '@tanstack/vue-query'
import { CalendarDays } from 'lucide-vue-next'
import { computed } from 'vue'

import { http, type LunarInfo } from '@/api/client'

const props = defineProps<{ date: string | null | undefined }>()

const { data } = useQuery({
  queryKey: computed(() => ['lunar', props.date ?? '']),
  enabled: computed(() => Boolean(props.date)),
  staleTime: 1000 * 60 * 60 * 24,
  queryFn: async () => {
    const { data } = await http.get<LunarInfo>('/meta/lunar', { params: { day: props.date } })
    return data
  },
})

const text = computed(() => (data.value ? `农历${data.value.lunar} · ${data.value.weekday}` : ''))
</script>

<template>
  <p v-if="text" class="mt-1.5 flex items-center gap-1.5 text-[11.5px] text-ink-faint">
    <CalendarDays :size="12" :stroke-width="1.5" />
    {{ text }}
  </p>
</template>
