import { defineStore } from 'pinia'

import { http } from '@/api/client'

export const useSessionStore = defineStore('session', {
  state: () => ({
    checked: false,
    authed: false,
    owner: '',
    appName: '个人工作台',
  }),
  actions: {
    async fetchMe(): Promise<boolean> {
      try {
        const { data } = await http.get('/auth/me')
        this.authed = true
        this.owner = data.owner ?? 'owner'
        this.appName = data.app_name ?? '个人工作台'
      } catch {
        this.authed = false
      } finally {
        this.checked = true
      }
      return this.authed
    },
    async login(passcode: string): Promise<void> {
      await http.post('/auth/login', { passcode })
      await this.fetchMe()
    },
    async logout(): Promise<void> {
      try {
        await http.post('/auth/logout')
      } finally {
        this.authed = false
        this.checked = true
      }
    },
  },
})
