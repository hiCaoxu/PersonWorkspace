const WEEKDAYS = ['周日', '周一', '周二', '周三', '周四', '周五', '周六']

export function formatMoney(value: string | number | null | undefined, symbol = true): string {
  if (value === null || value === undefined || value === '') return symbol ? '¥0.00' : '0.00'
  const num = typeof value === 'number' ? value : Number(value)
  if (!Number.isFinite(num)) return symbol ? '¥0.00' : '0.00'
  const fixed = Math.abs(num).toFixed(2)
  const [intPart, decPart] = fixed.split('.')
  const withSeparator = intPart.replace(/\B(?=(\d{3})+(?!\d))/g, ',')
  const sign = num < 0 ? '-' : ''
  return `${sign}${symbol ? '¥' : ''}${withSeparator}.${decPart}`
}

export function formatCompact(value: string | number | null | undefined): string {
  const num = typeof value === 'number' ? value : Number(value ?? 0)
  if (!Number.isFinite(num)) return '0'
  if (Math.abs(num) >= 10000) return `${(num / 10000).toFixed(1)}万`
  return formatMoney(num, false)
}

export function formatDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [y, m, d] = iso.slice(0, 10).split('-')
  return `${y}年${Number(m)}月${Number(d)}日`
}

export function formatShortDate(iso: string | null | undefined): string {
  if (!iso) return '—'
  const [, m, d] = iso.slice(0, 10).split('-')
  return `${Number(m)}/${Number(d)}`
}

export function todayISO(): string {
  const now = new Date()
  const offset = now.getTimezoneOffset()
  return new Date(now.getTime() - offset * 60000).toISOString().slice(0, 10)
}

export function shiftDate(iso: string, days: number): string {
  const date = new Date(`${iso}T00:00:00`)
  date.setDate(date.getDate() + days)
  const offset = date.getTimezoneOffset()
  return new Date(date.getTime() - offset * 60000).toISOString().slice(0, 10)
}

export function weekdayOf(iso: string): string {
  const date = new Date(`${iso}T00:00:00`)
  return WEEKDAYS[date.getDay()]
}

export function monthStart(iso: string): string {
  return `${iso.slice(0, 7)}-01`
}

export function monthRange(iso: string): { start: string; end: string } {
  const [year, month] = iso.split('-').map(Number)
  const last = new Date(year, month, 0).getDate()
  return {
    start: `${iso.slice(0, 7)}-01`,
    end: `${iso.slice(0, 7)}-${String(last).padStart(2, '0')}`,
  }
}

/** ISO 周：周一为周首、周日为周末。 */
export function weekRange(iso: string): { start: string; end: string } {
  const date = new Date(`${iso}T00:00:00`)
  const offset = (date.getDay() + 6) % 7
  const start = shiftDate(iso, -offset)
  return { start, end: shiftDate(start, 6) }
}

export function addMonths(iso: string, delta: number): string {
  const [year, month] = iso.split('-').map(Number)
  const date = new Date(year, month - 1 + delta, 1)
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-01`
}

export function formatMinutes(minutes: number | string | null | undefined): string {
  const total = Number(minutes ?? 0)
  if (!Number.isFinite(total) || total <= 0) return '0 分钟'
  const hours = Math.floor(total / 60)
  const rest = Math.round(total % 60)
  if (!hours) return `${rest} 分钟`
  return rest ? `${hours} 小时 ${rest} 分` : `${hours} 小时`
}

export function formatKcal(value: string | number | null | undefined): string {
  const num = Number(value ?? 0)
  if (!Number.isFinite(num)) return '0 kcal'
  return `${Math.round(num * 10) / 10} kcal`
}

export function formatDateTime(iso: string | null | undefined): string {
  if (!iso) return '—'
  return iso.replace('T', ' ').slice(0, 16)
}

export function greeting(): string {
  const hour = new Date().getHours()
  if (hour < 6) return '夜深了'
  if (hour < 11) return '早上好'
  if (hour < 14) return '中午好'
  if (hour < 18) return '下午好'
  return '晚上好'
}

export function mealLabel(meal: string): string {
  return { breakfast: '早餐', lunch: '午餐', dinner: '晚餐', snack: '加餐' }[meal] ?? meal
}

export function entTypeLabel(type: string): string {
  return (
    { movie: '电影', tv: '电视剧', documentary: '纪录片', podcast: '播客', book: '书籍' }[type] ?? type
  )
}

export function statusLabel(status: string): string {
  return { want: '想看', doing: '在看', done: '看完' }[status] ?? status
}
