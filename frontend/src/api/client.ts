import axios from 'axios'

export const http = axios.create({
  baseURL: '/api/v1',
  withCredentials: true,
  timeout: 20000,
  headers: { 'X-Requested-With': 'XMLHttpRequest' },
})

http.interceptors.response.use(
  (response) => response,
  (error) => {
    const status = error?.response?.status
    const url = String(error?.config?.url ?? '')
    // 登录、改口令、身份证揭示等接口的 401 属于业务校验失败，不能整页跳转
    if (status === 401 && !url.startsWith('/auth/') && !window.location.pathname.startsWith('/login')) {
      window.location.href = '/login'
    }
    const message =
      error?.response?.data?.error?.message ?? error?.message ?? '网络异常，请稍后重试'
    return Promise.reject(new Error(message))
  },
)

export interface ApiError {
  error: { code: string; message: string }
}

export interface Tag {
  id: number
  name: string
  scope: 'todo' | 'note'
  color: string
}

export interface LunarInfo {
  date: string
  lunar: string
  lunar_full: string
  weekday: string
  iso_week: number
  title: string
  zodiac: string
}

export interface Todo {
  id: number
  title: string
  description: string | null
  due_date: string | null
  done: boolean
  completed_at: string | null
  system_key: 'finance' | 'exercise' | 'diet' | null
  frequency: 'none' | 'daily' | 'weekly' | 'monthly' | 'yearly'
  interval: number
  weekdays: number[]
  until: string | null
  parent_id: number | null
  sort_order: number
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface Note {
  id: number
  title: string
  content_md?: string
  excerpt?: string
  is_pinned: boolean
  tags: Tag[]
  created_at: string
  updated_at: string
}

export interface Food {
  id: number
  name: string
  alias: string | null
  pinyin_abbr: string | null
  category: string
  energy_kcal_per_100g: string
  protein_g: string | null
  fat_g: string | null
  carb_g: string | null
  default_serving_g: string | null
  default_serving_label: string | null
  is_system: boolean
}

export interface DietRecord {
  id: number
  record_date: string
  meal: 'breakfast' | 'lunch' | 'dinner' | 'snack'
  food_item_id: number | null
  food_name: string
  quantity_g: string
  calories_kcal: string
  calories_manual: boolean
  protein_g?: string | null
  fat_g?: string | null
  carb_g?: string | null
  note: string | null
}

export interface ExerciseRecord {
  id: number
  record_date: string
  exercise_type: string
  duration_min: number
  calories: string | null
  distance_km: string | null
  intensity: string | null
  note: string | null
}

export interface WeightRecord {
  id: number
  record_date: string
  weight_kg: string
  body_fat_pct: string | null
  note: string | null
}

export interface SleepRecord {
  id: number
  record_date: string
  sleep_at: string | null
  wake_at: string | null
  duration_min: number
  quality: number | null
  note: string | null
}

export interface Account {
  id: number
  name: string
  account_type: string
  initial_balance: string
  currency?: string
  balance?: string
  icon: string | null
  color: string | null
  is_archived: boolean
  sort_order: number
}

export interface Category {
  id: number
  name: string
  kind: 'income' | 'expense'
  icon: string | null
  sort_order: number
}

export interface Transaction {
  id: number
  tx_type: 'income' | 'expense' | 'transfer'
  amount: string
  account_id: number
  account_name: string | null
  to_account_id: number | null
  to_account_name: string | null
  category_id: number | null
  occurred_on: string
  note: string | null
}

export interface Entertainment {
  id: number
  ent_type: 'movie' | 'tv' | 'documentary' | 'podcast' | 'book'
  status: 'want' | 'doing' | 'done'
  title: string
  cover_url: string | null
  year: number | null
  rating: string | null
  progress: number
  review: string | null
  external_url: string | null
  is_pinned: boolean
}

export interface LifeEvent {
  id: number
  title: string
  event_date: string
  event_type: string
  location: string | null
  description: string | null
  image_url: string | null
  is_highlight: boolean
  lunar?: string
}

export interface Profile {
  name: string
  id_card_masked: string | null
  id_card_birthday: string | null
  lunar_birthday: string
  solar_birthday: string | null
  lunar_birthday_month: number
  lunar_birthday_day: number
  zodiac: string | null
  constellation: string | null
  next_birthday: string | null
  days_to_birthday: number | null
  age: number | null
  phone: string | null
  email: string | null
  wechat: string | null
  blood_type: string | null
  address: string | null
  avatar_url?: string | null
  height_cm: string | null
  bio: string | null
  today_lunar: string
}

export interface DashboardSummary {
  date: string
  lunar: string
  zodiac: string
  week_range: { start: string; end: string }
  month_income: string
  month_expense: string
  total_assets: string
  today_todos: Todo[]
  week_todos: Todo[]
  random_note: Note | null
}

export interface FinanceSummary {
  year: number
  month: number
  month_income: string
  month_expense: string
  month_net: string
  total_assets: string
  expense_categories: { name: string; total: string }[]
  trend: { month: string; income: string; expense: string }[]
}

export interface HealthSummary {
  range: { start: string; end: string }
  diet: { total_kcal: string; record_count: number; avg_kcal_per_day: string }
  diet_by_meal: Record<string, { kcal: string; count: number }>
  exercise: { total_minutes: number; record_count: number; total_kcal: string }
  sleep: { avg_minutes: number; total_minutes: number; record_count: number; avg_quality: string }
  weight: { date: string; weight_kg: string; body_fat_pct: string | null }[]
  today: Record<string, string | number | null>
}
