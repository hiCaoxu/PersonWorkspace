/**
 * 本地 UI 走查用的假接口（无数据库依赖）。
 * 用法：
 *   node tests/e2e/mock-api.mjs            # 监听 127.0.0.1:8010
 *   VITE_API_TARGET=http://127.0.0.1:8010 npm run dev
 *
 * 只实现前端会请求的接口与少量内存态变更，用于检查布局、交互与控制台报错，
 * 不作为业务逻辑的正确性依据。
 */
import http from 'node:http'

const PORT = Number(process.env.MOCK_PORT || 8010)
const TODAY = '2026-11-15'
const WEEK_START = '2026-11-09'

let idSeq = 1000
const nextId = () => (idSeq += 1)

const tags = [
  { id: 1, name: '工作', scope: 'todo', color: '#B08968' },
  { id: 2, name: '生活', scope: 'todo', color: '#7A9E7E' },
  { id: 3, name: '学习', scope: 'todo', color: '#C0714F' },
  { id: 4, name: '灵感', scope: 'note', color: '#B08968' },
  { id: 5, name: '读书', scope: 'note', color: '#8A7F70' },
]

const todos = [
  {
    id: 1,
    title: '记一笔今天的账',
    description: null,
    due_date: TODAY,
    done: false,
    completed_at: null,
    system_key: 'finance',
    frequency: 'none',
    interval: 1,
    weekdays: [],
    until: null,
    parent_id: null,
    sort_order: 0,
    tags: [],
    created_at: `${TODAY}T00:05:00+08:00`,
    updated_at: `${TODAY}T00:05:00+08:00`,
  },
  {
    id: 2,
    title: '记录锻炼',
    description: null,
    due_date: TODAY,
    done: false,
    completed_at: null,
    system_key: 'exercise',
    frequency: 'none',
    interval: 1,
    weekdays: [],
    until: null,
    parent_id: null,
    sort_order: 0,
    tags: [],
    created_at: `${TODAY}T00:05:00+08:00`,
    updated_at: `${TODAY}T00:05:00+08:00`,
  },
  {
    id: 3,
    title: '记录饮食',
    description: null,
    due_date: TODAY,
    done: false,
    completed_at: null,
    system_key: 'diet',
    frequency: 'none',
    interval: 1,
    weekdays: [],
    until: null,
    parent_id: null,
    sort_order: 0,
    tags: [],
    created_at: `${TODAY}T00:05:00+08:00`,
    updated_at: `${TODAY}T00:05:00+08:00`,
  },
  {
    id: 4,
    title: '写周报',
    description: '整理本周进展与下周计划',
    due_date: TODAY,
    done: false,
    completed_at: null,
    system_key: null,
    frequency: 'weekly',
    interval: 1,
    weekdays: [6],
    until: null,
    parent_id: null,
    sort_order: 1,
    tags: [tags[0]],
    created_at: `${TODAY}T09:00:00+08:00`,
    updated_at: `${TODAY}T09:00:00+08:00`,
  },
  {
    id: 5,
    title: '读完《人类简史》第三章',
    description: null,
    due_date: '2026-11-17',
    done: false,
    completed_at: null,
    system_key: null,
    frequency: 'none',
    interval: 1,
    weekdays: [],
    until: null,
    parent_id: null,
    sort_order: 2,
    tags: [tags[2]],
    created_at: `${TODAY}T09:00:00+08:00`,
    updated_at: `${TODAY}T09:00:00+08:00`,
  },
  {
    id: 6,
    title: '给绿植浇水',
    description: null,
    due_date: '2026-11-14',
    done: true,
    completed_at: '2026-11-14T20:00:00+08:00',
    system_key: null,
    frequency: 'none',
    interval: 1,
    weekdays: [],
    until: null,
    parent_id: null,
    sort_order: 3,
    tags: [tags[1]],
    created_at: '2026-11-14T09:00:00+08:00',
    updated_at: '2026-11-14T20:00:00+08:00',
  },
]

const notes = [
  {
    id: 11,
    title: '十一月的节奏',
    content_md:
      '# 十一月的节奏\n\n这个月只做三件事：**早睡**、每天走八千步、把读书笔记写完。\n\n- 早上不碰手机\n- 午饭后散步十分钟\n- 晚上十一点前关灯\n\n```python\ndef daily_check(day):\n    return {\n        "sleep": day.sleep_hours >= 7,\n        "walk": day.steps >= 8000,\n    }\n```\n\n> 慢一点，但不要停。',
    tags: [tags[3]],
    is_pinned: false,
    created_at: '2026-11-02T10:00:00+08:00',
    updated_at: '2026-11-14T22:00:00+08:00',
  },
  {
    id: 12,
    title: '读书摘记：把时间当朋友',
    content_md:
      '## 摘记\n\n心智的成熟，是从接受「不完美」开始的。\n\n- 时间不可管理，能管理的只有自己\n- 所有学习都是重复\n\n`积累` 比 `灵感` 更可靠。',
    tags: [tags[4], tags[3]],
    is_pinned: true,
    created_at: '2026-11-05T21:00:00+08:00',
    updated_at: '2026-11-12T21:30:00+08:00',
  },
]

const diaries = {
  [TODAY]: {
    id: 21,
    diary_date: TODAY,
    title: '2026年11月15日 46周星期日',
    content:
      '今天降温了，窗外的风有点硬。\n\n上午把待办清空，下午读了三十页书。晚上煮了一锅汤，味道比想象中好。',
    mood: '平静',
    weather: '多云',
  },
  '2026-11-14': {
    id: 22,
    diary_date: '2026-11-14',
    title: '2026年11月14日 46周星期六',
    content: '去了一趟菜市场，买到了很新鲜的青菜。',
    mood: '愉悦',
    weather: '晴',
  },
  '2026-11-02': {
    id: 23,
    diary_date: '2026-11-02',
    title: '2026年11月2日 45周星期一',
    content: '新的一个月，列了三件想坚持的小事。',
    mood: null,
    weather: null,
  },
}

const accounts = [
  {
    id: 31,
    name: '招商银行储蓄卡',
    account_type: 'bank',
    initial_balance: '12000.00',
    balance: '15860.50',
    icon: 'landmark',
    color: '#B08968',
    is_archived: false,
    sort_order: 0,
  },
  {
    id: 32,
    name: '支付宝',
    account_type: 'alipay',
    initial_balance: '500.00',
    balance: '1320.00',
    icon: 'smartphone',
    color: '#7A9E7E',
    is_archived: false,
    sort_order: 1,
  },
  {
    id: 33,
    name: '现金',
    account_type: 'cash',
    initial_balance: '200.00',
    balance: '80.00',
    icon: 'banknote',
    color: '#C0714F',
    is_archived: false,
    sort_order: 2,
  },
]

const categories = [
  { id: 41, name: '餐饮', kind: 'expense', icon: 'utensils', sort_order: 0 },
  { id: 42, name: '交通', kind: 'expense', icon: 'bus', sort_order: 1 },
  { id: 43, name: '日用', kind: 'expense', icon: 'shopping-basket', sort_order: 2 },
  { id: 44, name: '居住', kind: 'expense', icon: 'home', sort_order: 3 },
  { id: 45, name: '工资', kind: 'income', icon: 'wallet', sort_order: 0 },
  { id: 46, name: '副业', kind: 'income', icon: 'sparkles', sort_order: 1 },
]

const transactions = [
  {
    id: 51,
    tx_type: 'expense',
    amount: '38.50',
    account_id: 32,
    account_name: '支付宝',
    to_account_id: null,
    to_account_name: null,
    category_id: 41,
    occurred_on: '2026-11-15',
    note: '午饭 牛肉面',
  },
  {
    id: 52,
    tx_type: 'income',
    amount: '12000.00',
    account_id: 31,
    account_name: '招商银行储蓄卡',
    to_account_id: null,
    to_account_name: null,
    category_id: 45,
    occurred_on: '2026-11-10',
    note: '十一月工资',
  },
  {
    id: 53,
    tx_type: 'expense',
    amount: '2400.00',
    account_id: 31,
    account_name: '招商银行储蓄卡',
    to_account_id: null,
    to_account_name: null,
    category_id: 44,
    occurred_on: '2026-11-03',
    note: '房租',
  },
  {
    id: 54,
    tx_type: 'transfer',
    amount: '1000.00',
    account_id: 31,
    account_name: '招商银行储蓄卡',
    to_account_id: 32,
    to_account_name: '支付宝',
    category_id: null,
    occurred_on: '2026-11-08',
    note: '转到支付宝日常开销',
  },
  {
    id: 55,
    tx_type: 'expense',
    amount: '126.00',
    account_id: 33,
    account_name: '现金',
    to_account_id: null,
    to_account_name: null,
    category_id: 43,
    occurred_on: '2026-11-06',
    note: '洗衣液与纸巾',
  },
]

const exercises = [
  {
    id: 61,
    record_date: TODAY,
    exercise_type: '慢跑',
    duration_min: 42,
    calories: '320.0',
    distance_km: '6.20',
    intensity: '适中',
    note: '江边，配速 6 分 40',
  },
  {
    id: 62,
    record_date: '2026-11-13',
    exercise_type: '力量训练',
    duration_min: 35,
    calories: '210.0',
    distance_km: null,
    intensity: '高强度',
    note: '深蹲与硬拉',
  },
  {
    id: 63,
    record_date: '2026-11-11',
    exercise_type: '游泳',
    duration_min: 50,
    calories: '430.0',
    distance_km: '1.20',
    intensity: '轻松',
    note: null,
  },
]

const diets = [
  {
    id: 71,
    record_date: TODAY,
    meal: 'breakfast',
    food_item_id: 1,
    food_name: '米饭',
    quantity_g: '150.0',
    calories_kcal: '174.0',
    calories_manual: false,
    note: null,
  },
  {
    id: 72,
    record_date: TODAY,
    meal: 'lunch',
    food_item_id: 2,
    food_name: '鸡胸肉',
    quantity_g: '120.0',
    calories_kcal: '159.6',
    calories_manual: false,
    note: '水煮',
  },
  {
    id: 73,
    record_date: '2026-11-14',
    meal: 'dinner',
    food_item_id: 3,
    food_name: '西红柿炒蛋',
    quantity_g: '220.0',
    calories_kcal: '240.0',
    calories_manual: true,
    note: '自己做的，少放油',
  },
  {
    id: 74,
    record_date: '2026-11-13',
    meal: 'snack',
    food_item_id: 4,
    food_name: '苹果',
    quantity_g: '200.0',
    calories_kcal: '106.0',
    calories_manual: false,
    note: null,
  },
]

const weights = [
  { id: 81, record_date: '2026-11-02', weight_kg: '71.20', body_fat_pct: '19.4', note: null },
  { id: 82, record_date: '2026-11-09', weight_kg: '70.60', body_fat_pct: '19.0', note: null },
  { id: 83, record_date: TODAY, weight_kg: '70.10', body_fat_pct: '18.6', note: '早起空腹' },
]

const sleeps = [
  {
    id: 91,
    record_date: TODAY,
    sleep_at: '2026-11-14T23:20:00',
    wake_at: '2026-11-15T07:05:00',
    duration_min: 465,
    quality: 4,
    note: null,
  },
  {
    id: 92,
    record_date: '2026-11-14',
    sleep_at: '2026-11-13T00:10:00',
    wake_at: '2026-11-14T07:00:00',
    duration_min: 410,
    quality: 3,
    note: '睡得有点晚',
  },
]

const foods = [
  {
    id: 1,
    name: '米饭',
    alias: '白米饭,大米饭',
    pinyin_abbr: 'mf',
    category: '谷薯类',
    energy_kcal_per_100g: '116.00',
    protein_g: '2.60',
    fat_g: '0.30',
    carb_g: '25.90',
    default_serving_g: '150.0',
    default_serving_label: '1碗',
    is_system: true,
  },
  {
    id: 2,
    name: '鸡胸肉',
    alias: '鸡脯肉',
    pinyin_abbr: 'jxr',
    category: '肉禽蛋',
    energy_kcal_per_100g: '133.00',
    protein_g: '19.40',
    fat_g: '5.00',
    carb_g: '2.50',
    default_serving_g: '120.0',
    default_serving_label: '1块',
    is_system: true,
  },
  {
    id: 3,
    name: '西红柿炒蛋',
    alias: '番茄炒蛋',
    pinyin_abbr: 'xhscy',
    category: '菜肴',
    energy_kcal_per_100g: '109.00',
    protein_g: '5.40',
    fat_g: '7.20',
    carb_g: '5.40',
    default_serving_g: '220.0',
    default_serving_label: '1盘',
    is_system: true,
  },
  {
    id: 4,
    name: '苹果',
    alias: '红富士',
    pinyin_abbr: 'pg',
    category: '蔬果',
    energy_kcal_per_100g: '53.00',
    protein_g: '0.30',
    fat_g: '0.20',
    carb_g: '13.70',
    default_serving_g: '200.0',
    default_serving_label: '1个',
    is_system: true,
  },
  {
    id: 5,
    name: '全脂牛奶',
    alias: '牛奶',
    pinyin_abbr: 'qznn',
    category: '奶豆',
    energy_kcal_per_100g: '65.00',
    protein_g: '3.30',
    fat_g: '3.60',
    carb_g: '4.90',
    default_serving_g: '250.0',
    default_serving_label: '1杯',
    is_system: true,
  },
]

const entertainments = [
  {
    id: 101,
    ent_type: 'movie',
    status: 'want',
    title: '海边的曼彻斯特',
    cover_url: null,
    year: 2016,
    rating: '8.6',
    progress: 0,
    review: '朋友推荐，留着周末看',
    external_url: null,
    is_pinned: false,
  },
  {
    id: 102,
    ent_type: 'movie',
    status: 'doing',
    title: '奥本海默',
    cover_url: null,
    year: 2023,
    rating: '8.8',
    progress: 45,
    review: '看到中间，节奏很稳',
    external_url: null,
    is_pinned: false,
  },
  {
    id: 103,
    ent_type: 'movie',
    status: 'done',
    title: '宇宙探索编辑部',
    cover_url: null,
    year: 2023,
    rating: '8.3',
    progress: 100,
    review: '荒诞又温柔，很喜欢结尾',
    external_url: null,
    is_pinned: true,
  },
  {
    id: 104,
    ent_type: 'tv',
    status: 'doing',
    title: '漫长的季节',
    cover_url: null,
    year: 2023,
    rating: '9.4',
    progress: 60,
    review: '东北的秋天拍得真好看',
    external_url: null,
    is_pinned: false,
  },
  {
    id: 105,
    ent_type: 'book',
    status: 'doing',
    title: '人类简史',
    cover_url: null,
    year: 2014,
    rating: '9.1',
    progress: 30,
    review: '每天读二十页',
    external_url: null,
    is_pinned: false,
  },
  {
    id: 106,
    ent_type: 'podcast',
    status: 'want',
    title: '忽左忽右',
    cover_url: null,
    year: 2024,
    rating: '8.9',
    progress: 0,
    review: '通勤时听',
    external_url: null,
    is_pinned: false,
  },
]

const profile = {
  name: '林川',
  id_card_masked: '340322********7851',
  id_card_birthday: '1992-03-18',
  lunar_birthday: '农历1992年2月15日',
  solar_birthday: '1992-03-18',
  lunar_birthday_month: 2,
  lunar_birthday_day: 15,
  zodiac: '猴',
  constellation: '双鱼座',
  next_birthday: '2027-03-22',
  days_to_birthday: 127,
  age: 34,
  phone: '138 0000 0000',
  email: 'lin@example.com',
  wechat: 'linchuan',
  blood_type: 'O',
  address: '杭州市西湖区',
  height_cm: '175.0',
  bio: '写代码，也写字。',
  today_lunar: '十月初六',
}

const lifeEvents = [
  {
    id: 111,
    title: '第一份工作',
    event_date: '2015-07-01',
    event_type: 'work',
    location: '杭州',
    description: '入职一家做企业服务的公司，第一次独立负责一个模块。',
    image_url: null,
    is_highlight: true,
    lunar: '五月十六',
  },
  {
    id: 112,
    title: '搬进现在的家',
    event_date: '2020-10-24',
    event_type: 'family',
    location: '杭州 · 西湖区',
    description: '有了一个可以放下书桌的阳台。',
    image_url: null,
    is_highlight: false,
    lunar: '九月初八',
  },
  {
    id: 113,
    title: '第一次一个人旅行',
    event_date: '2018-05-02',
    event_type: 'travel',
    location: '京都',
    description: '在鸭川边坐了一个下午，什么都没做。',
    image_url: null,
    is_highlight: true,
    lunar: '三月十七',
  },
]

const weekRange = { start: WEEK_START, end: TODAY }

const excerptOf = (text, length = 120) =>
  String(text || '')
    .replace(/```[\s\S]*?```/g, ' ')
    .replace(/`[^`]*`/g, ' ')
    .replace(/[#>*_`~|]/g, ' ')
    .replace(/\s+/g, ' ')
    .trim()
    .slice(0, length)

function todoView(view) {
  const pending = todos.filter((item) => !item.done)
  if (view === 'pending') return pending
  if (view === 'done') return todos.filter((item) => item.done)
  if (view === 'today') return todos.filter((item) => item.due_date === TODAY)
  if (view === 'week') {
    return todos.filter(
      (item) => item.due_date && item.due_date >= WEEK_START && item.due_date <= TODAY,
    )
  }
  return todos
}

function financeSummary() {
  const income = transactions
    .filter((tx) => tx.tx_type === 'income')
    .reduce((sum, tx) => sum + Number(tx.amount), 0)
  const expense = transactions
    .filter((tx) => tx.tx_type === 'expense')
    .reduce((sum, tx) => sum + Number(tx.amount), 0)
  const byCategory = new Map()
  for (const tx of transactions) {
    if (tx.tx_type !== 'expense') continue
    const name = categories.find((cat) => cat.id === tx.category_id)?.name ?? '未分类'
    byCategory.set(name, (byCategory.get(name) ?? 0) + Number(tx.amount))
  }
  return {
    year: 2026,
    month: 11,
    month_income: income.toFixed(2),
    month_expense: expense.toFixed(2),
    month_net: (income - expense).toFixed(2),
    total_assets: accounts.reduce((sum, item) => sum + Number(item.balance), 0).toFixed(2),
    expense_categories: [...byCategory.entries()].map(([name, total]) => ({
      name,
      total: total.toFixed(2),
    })),
    trend: [
      { month: '2026-06', income: '11000.00', expense: '7200.00' },
      { month: '2026-07', income: '11500.00', expense: '8100.00' },
      { month: '2026-08', income: '10800.00', expense: '6900.00' },
      { month: '2026-09', income: '12300.00', expense: '9300.00' },
      { month: '2026-10', income: '12000.00', expense: '8600.00' },
      { month: '2026-11', income: income.toFixed(2), expense: expense.toFixed(2) },
    ],
  }
}

function healthSummary(start, end) {
  const within = (row) => row.record_date >= start && row.record_date <= end
  const dietRows = diets.filter(within)
  const exerciseRows = exercises.filter(within)
  const sleepRows = sleeps.filter(within)
  const weightRows = weights.filter(within)
  const kcal = dietRows.reduce((sum, row) => sum + Number(row.calories_kcal), 0)
  const days = Math.max(1, Math.round((new Date(end) - new Date(start)) / 86400000) + 1)
  return {
    range: { start, end },
    diet: {
      total_kcal: kcal.toFixed(1),
      record_count: dietRows.length,
      avg_kcal_per_day: (kcal / days).toFixed(1),
    },
    diet_by_meal: {},
    exercise: {
      total_minutes: exerciseRows.reduce((sum, row) => sum + row.duration_min, 0),
      record_count: exerciseRows.length,
      total_kcal: exerciseRows.reduce((sum, row) => sum + Number(row.calories ?? 0), 0).toFixed(1),
    },
    sleep: {
      avg_minutes: sleepRows.length
        ? Math.round(sleepRows.reduce((sum, row) => sum + row.duration_min, 0) / sleepRows.length)
        : 0,
      total_minutes: sleepRows.reduce((sum, row) => sum + row.duration_min, 0),
      record_count: sleepRows.length,
      avg_quality: '3.5',
    },
    weight: weightRows.map((row) => ({
      date: row.record_date,
      weight_kg: row.weight_kg,
      body_fat_pct: row.body_fat_pct,
    })),
    today: {
      date: TODAY,
      kcal_today: diets
        .filter((row) => row.record_date === TODAY)
        .reduce((sum, row) => sum + Number(row.calories_kcal), 0)
        .toFixed(1),
      exercise_minutes: exercises
        .filter((row) => row.record_date === TODAY)
        .reduce((sum, row) => sum + row.duration_min, 0),
      sleep_minutes: sleeps.find((row) => row.record_date === TODAY)?.duration_min ?? 0,
      weight_kg: weights.find((row) => row.record_date === TODAY)?.weight_kg ?? null,
    },
  }
}

const LUNAR_MAP = {
  '2026-11-02': '九月十三',
  '2026-11-09': '九月二十',
  '2026-11-13': '九月廿四',
  '2026-11-14': '九月廿五',
  '2026-11-15': '十月初六',
  '2026-11-16': '十月初七',
  '2026-11-17': '十月初八',
}

function json(res, body, status = 200) {
  const payload = JSON.stringify(body)
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Content-Length': Buffer.byteLength(payload),
  })
  res.end(payload)
}

async function readBody(req) {
  const chunks = []
  for await (const chunk of req) chunks.push(chunk)
  if (!chunks.length) return {}
  try {
    return JSON.parse(Buffer.concat(chunks).toString('utf8'))
  } catch {
    return {}
  }
}

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host}`)
  const path = url.pathname.replace(/^\/api\/v1/, '')
  const method = req.method || 'GET'
  const cookie = req.headers.cookie || ''
  const authed = cookie.includes('pwb_session=')

  if (path === '/auth/login' && method === 'POST') {
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Set-Cookie': 'pwb_session=mock; Path=/; HttpOnly; SameSite=Lax',
    })
    res.end(JSON.stringify({ ok: true }))
    return
  }
  if (path === '/auth/logout') {
    res.writeHead(200, {
      'Content-Type': 'application/json',
      'Set-Cookie': 'pwb_session=; Path=/; Max-Age=0',
    })
    res.end(JSON.stringify({ ok: true }))
    return
  }
  if (path === '/auth/me') {
    if (!authed) return json(res, { error: { code: 'unauthorized', message: '未登录' } }, 401)
    return json(res, { owner: 'owner', app_name: '个人工作台' })
  }
  if (!authed) {
    return json(res, { error: { code: 'unauthorized', message: '未登录' } }, 401)
  }
  if (path === '/auth/reveal' && method === 'POST') {
    return json(res, { ticket: 'mock-ticket', expires_in: 300 })
  }
  if (path === '/profile/reveal' && method === 'POST') {
    return json(res, { id_card: '340322199203187851' })
  }
  if (path === '/auth/change-passcode') {
    return json(res, { ok: true })
  }

  if (path === '/meta/lunar') {
    const day = url.searchParams.get('day') || TODAY
    return json(res, {
      date: day,
      lunar: LUNAR_MAP[day] ?? '十月初六',
      lunar_full: `农历${LUNAR_MAP[day] ?? '十月初六'}`,
      weekday: '星期日',
      iso_week: 46,
      title: '2026年11月15日 46周星期日',
      zodiac: '马',
    })
  }
  if (path === '/meta/lunar/batch') {
    const days = (url.searchParams.get('days') || '').split(',').filter(Boolean)
    return json(res, {
      items: Object.fromEntries(days.map((day) => [day, LUNAR_MAP[day] ?? '十月初六'])),
    })
  }

  if (path === '/dashboard/summary') {
    return json(res, {
      date: TODAY,
      lunar: '十月初六',
      zodiac: '马',
      week_range: weekRange,
      month_income: financeSummary().month_income,
      month_expense: financeSummary().month_expense,
      total_assets: financeSummary().total_assets,
      today_todos: todos.filter((item) => item.due_date === TODAY),
      week_todos: todos.filter(
        (item) => item.due_date && item.due_date >= WEEK_START && item.due_date <= TODAY,
      ),
      random_note: { ...notes[0], excerpt: excerptOf(notes[0].content_md) },
    })
  }

  if (path === '/todos' && method === 'GET') {
    const view = url.searchParams.get('view') || 'all'
    const q = (url.searchParams.get('q') || '').trim()
    const tagId = Number(url.searchParams.get('tag_id') || 0)
    let items = todoView(view)
    if (q) items = items.filter((item) => item.title.includes(q))
    if (tagId) items = items.filter((item) => item.tags.some((tag) => tag.id === tagId))
    return json(res, { items, count: items.length })
  }
  if (path === '/todos' && method === 'POST') {
    const body = await readBody(req)
    const todo = {
      id: nextId(),
      title: body.title,
      description: body.description ?? null,
      due_date: body.due_date ?? TODAY,
      done: false,
      completed_at: null,
      system_key: null,
      frequency: body.frequency ?? 'none',
      interval: body.interval ?? 1,
      weekdays: body.weekdays ?? [],
      until: body.until ?? null,
      parent_id: null,
      sort_order: 9,
      tags: tags.filter((tag) => (body.tag_ids ?? []).includes(tag.id)),
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    todos.push(todo)
    return json(res, todo, 201)
  }
  const toggleMatch = path.match(/^\/todos\/(\d+)\/toggle$/)
  if (toggleMatch && method === 'POST') {
    const todo = todos.find((item) => item.id === Number(toggleMatch[1]))
    if (todo) {
      todo.done = !todo.done
      todo.completed_at = todo.done ? new Date().toISOString() : null
    }
    return json(res, { todo, next: null })
  }
  const todoMatch = path.match(/^\/todos\/(\d+)$/)
  if (todoMatch && method === 'PATCH') {
    const todo = todos.find((item) => item.id === Number(todoMatch[1]))
    const body = await readBody(req)
    if (todo) Object.assign(todo, body, { tags: tags.filter((tag) => (body.tag_ids ?? []).includes(tag.id)) })
    return json(res, todo)
  }
  if (todoMatch && method === 'DELETE') {
    const index = todos.findIndex((item) => item.id === Number(todoMatch[1]))
    if (index >= 0) todos.splice(index, 1)
    return json(res, { ok: true })
  }

  if (path === '/tags' && method === 'GET') {
    const scope = url.searchParams.get('scope')
    return json(res, { items: scope ? tags.filter((tag) => tag.scope === scope) : tags })
  }
  if (path === '/tags' && method === 'POST') {
    const body = await readBody(req)
    const tag = { id: nextId(), name: body.name, scope: body.scope ?? 'todo', color: '#B08968' }
    tags.push(tag)
    return json(res, tag, 201)
  }

  if (path === '/notes' && method === 'GET') {
    const q = (url.searchParams.get('q') || '').trim()
    let items = notes
    if (q) items = items.filter((note) => note.title.includes(q) || note.content_md.includes(q))
    return json(res, {
      items: items.map((note) => ({
        id: note.id,
        title: note.title,
        excerpt: excerptOf(note.content_md, 100),
        is_pinned: note.is_pinned,
        tags: note.tags,
        created_at: note.created_at,
        updated_at: note.updated_at,
      })),
      count: items.length,
    })
  }
  if (path === '/notes' && method === 'POST') {
    const body = await readBody(req)
    const note = {
      id: nextId(),
      title: body.title ?? '无标题',
      content_md: body.content_md ?? '',
      is_pinned: false,
      tags: [],
      created_at: new Date().toISOString(),
      updated_at: new Date().toISOString(),
    }
    notes.unshift(note)
    return json(res, note, 201)
  }
  const noteMatch = path.match(/^\/notes\/(\d+)$/)
  if (noteMatch && method === 'GET') {
    const note = notes.find((item) => item.id === Number(noteMatch[1]))
    return note ? json(res, note) : json(res, { error: { message: '笔记不存在' } }, 404)
  }
  if (noteMatch && (method === 'PATCH' || method === 'DELETE')) {
    const note = notes.find((item) => item.id === Number(noteMatch[1]))
    if (method === 'DELETE') {
      const index = notes.findIndex((item) => item.id === Number(noteMatch[1]))
      if (index >= 0) notes.splice(index, 1)
      return json(res, { ok: true })
    }
    const body = await readBody(req)
    if (note) {
      Object.assign(note, body, {
        tags: tags.filter((tag) => (body.tag_ids ?? note.tags.map((item) => item.id)).includes(tag.id)),
        updated_at: new Date().toISOString(),
      })
    }
    return json(res, note)
  }

  if (path === '/diaries' && method === 'GET') {
    const year = Number(url.searchParams.get('year'))
    const month = Number(url.searchParams.get('month'))
    const prefix = `${year}-${String(month).padStart(2, '0')}`
    return json(res, {
      items: Object.values(diaries)
        .filter((entry) => entry.diary_date.startsWith(prefix))
        .map((entry) => ({ id: entry.id, diary_date: entry.diary_date })),
      year,
      month,
    })
  }
  const diaryDateMatch = path.match(/^\/diaries\/by-date\/(\d{4}-\d{2}-\d{2})$/)
  if (diaryDateMatch) {
    const day = diaryDateMatch[1]
    if (!diaries[day]) {
      diaries[day] = {
        id: nextId(),
        diary_date: day,
        title: `${day.slice(0, 4)}年${Number(day.slice(5, 7))}月${Number(day.slice(8, 10))}日 46周星期日`,
        content: '',
        mood: null,
        weather: null,
      }
    }
    return json(res, {
      ...diaries[day],
      lunar: LUNAR_MAP[day] ?? '十月初六',
      updated_at: new Date().toISOString(),
    })
  }
  const diaryMatch = path.match(/^\/diaries\/(\d+)$/)
  if (diaryMatch && method === 'PATCH') {
    const body = await readBody(req)
    const entry = Object.values(diaries).find((item) => item.id === Number(diaryMatch[1]))
    if (entry) Object.assign(entry, body)
    return json(res, { ...entry, lunar: '十月初六', updated_at: new Date().toISOString() })
  }

  if (path === '/foods' && method === 'GET') {
    const q = (url.searchParams.get('q') || '').trim()
    const items = q
      ? foods.filter(
          (food) =>
            food.name.includes(q) ||
            (food.alias ?? '').includes(q) ||
            (food.pinyin_abbr ?? '').startsWith(q),
        )
      : foods
    return json(res, { items })
  }
  if (path === '/foods/frequent') {
    return json(res, { items: foods.slice(0, 3) })
  }
  if (path === '/foods' && method === 'POST') {
    const body = await readBody(req)
    const food = {
      id: nextId(),
      name: body.name,
      alias: null,
      pinyin_abbr: null,
      category: body.category ?? '菜肴',
      energy_kcal_per_100g: Number(body.energy_kcal_per_100g).toFixed(2),
      protein_g: null,
      fat_g: null,
      carb_g: null,
      default_serving_g: null,
      default_serving_label: null,
      is_system: false,
    }
    foods.unshift(food)
    return json(res, food, 201)
  }

  if (path === '/health/summary') {
    const start = url.searchParams.get('start') || TODAY
    const end = url.searchParams.get('end') || TODAY
    return json(res, healthSummary(start, end))
  }
  const healthMatch = path.match(/^\/health\/(exercises|diets|weights|sleeps)(?:\/(\d+))?$/)
  if (healthMatch) {
    const [, kind, rawId] = healthMatch
    const table =
      kind === 'exercises' ? exercises : kind === 'diets' ? diets : kind === 'weights' ? weights : sleeps
    if (method === 'GET') {
      const start = url.searchParams.get('start') || '2026-01-01'
      const end = url.searchParams.get('end') || '2026-12-31'
      return json(res, {
        items: table.filter((row) => row.record_date >= start && row.record_date <= end),
      })
    }
    if (method === 'POST') {
      const body = await readBody(req)
      const record = { id: nextId(), ...body }
      table.unshift(record)
      return json(res, record, 201)
    }
    if (method === 'PATCH' && rawId) {
      const body = await readBody(req)
      const record = table.find((row) => row.id === Number(rawId))
      if (record) Object.assign(record, body)
      return json(res, record)
    }
    if (method === 'DELETE' && rawId) {
      const index = table.findIndex((row) => row.id === Number(rawId))
      if (index >= 0) table.splice(index, 1)
      return json(res, { ok: true })
    }
  }

  if (path === '/finance/summary') return json(res, financeSummary())
  if (path === '/finance/accounts' && method === 'GET') return json(res, { items: accounts })
  if (path === '/finance/accounts' && method === 'POST') {
    const body = await readBody(req)
    const account = {
      id: nextId(),
      name: body.name,
      account_type: body.account_type ?? 'bank',
      initial_balance: Number(body.initial_balance ?? 0).toFixed(2),
      balance: Number(body.initial_balance ?? 0).toFixed(2),
      icon: body.icon ?? 'wallet',
      color: body.color ?? '#B08968',
      is_archived: false,
      sort_order: accounts.length,
    }
    accounts.push(account)
    return json(res, account, 201)
  }
  const accountMatch = path.match(/^\/finance\/accounts\/(\d+)$/)
  if (accountMatch && method === 'PATCH') {
    const body = await readBody(req)
    const account = accounts.find((item) => item.id === Number(accountMatch[1]))
    if (account) Object.assign(account, body)
    return json(res, account)
  }
  if (path === '/finance/categories') return json(res, { items: categories })
  if (path === '/finance/transactions' && method === 'GET') {
    const start = url.searchParams.get('start')
    const end = url.searchParams.get('end')
    const accountId = Number(url.searchParams.get('account_id') || 0)
    const categoryId = Number(url.searchParams.get('category_id') || 0)
    let items = transactions
    if (start) items = items.filter((tx) => tx.occurred_on >= start)
    if (end) items = items.filter((tx) => tx.occurred_on <= end)
    if (accountId) items = items.filter((tx) => tx.account_id === accountId)
    if (categoryId) items = items.filter((tx) => tx.category_id === categoryId)
    return json(res, { items, count: items.length })
  }
  if (path === '/finance/transactions' && method === 'POST') {
    const body = await readBody(req)
    const account = accounts.find((item) => item.id === body.account_id)
    const target = accounts.find((item) => item.id === body.to_account_id)
    const tx = {
      id: nextId(),
      tx_type: body.tx_type,
      amount: Number(body.amount).toFixed(2),
      account_id: body.account_id,
      account_name: account?.name ?? null,
      to_account_id: body.to_account_id ?? null,
      to_account_name: target?.name ?? null,
      category_id: body.category_id ?? null,
      occurred_on: body.occurred_on ?? TODAY,
      note: body.note ?? null,
    }
    transactions.unshift(tx)
    return json(res, tx, 201)
  }
  const txMatch = path.match(/^\/finance\/transactions\/(\d+)$/)
  if (txMatch && method === 'DELETE') {
    const index = transactions.findIndex((item) => item.id === Number(txMatch[1]))
    if (index >= 0) transactions.splice(index, 1)
    return json(res, { ok: true })
  }

  if (path === '/entertainment' && method === 'GET') {
    const type = url.searchParams.get('ent_type')
    const q = (url.searchParams.get('q') || '').trim()
    let items = entertainments
    if (type) items = items.filter((item) => item.ent_type === type)
    if (q) items = items.filter((item) => item.title.includes(q))
    return json(res, { items, count: items.length })
  }
  if (path === '/entertainment' && method === 'POST') {
    const body = await readBody(req)
    const item = {
      id: nextId(),
      ...body,
      cover_url: body.cover_url ?? null,
      is_pinned: false,
    }
    entertainments.push(item)
    return json(res, item, 201)
  }
  const statusMatch = path.match(/^\/entertainment\/(\d+)\/status$/)
  if (statusMatch && method === 'PATCH') {
    const status = url.searchParams.get('status')
    const item = entertainments.find((entry) => entry.id === Number(statusMatch[1]))
    if (item && status) {
      item.status = status
      if (status === 'done') item.progress = 100
    }
    return json(res, item)
  }
  const entMatch = path.match(/^\/entertainment\/(\d+)$/)
  if (entMatch && method === 'PATCH') {
    const body = await readBody(req)
    const item = entertainments.find((entry) => entry.id === Number(entMatch[1]))
    if (item) Object.assign(item, body)
    return json(res, item)
  }
  if (entMatch && method === 'DELETE') {
    const index = entertainments.findIndex((entry) => entry.id === Number(entMatch[1]))
    if (index >= 0) entertainments.splice(index, 1)
    return json(res, { ok: true })
  }

  if (path === '/profile' && method === 'GET') return json(res, profile)
  if (path === '/profile' && method === 'PATCH') {
    const body = await readBody(req)
    Object.assign(profile, body)
    return json(res, profile)
  }

  if (path === '/life-events' && method === 'GET') return json(res, { items: lifeEvents })
  if (path === '/life-events' && method === 'POST') {
    const body = await readBody(req)
    const event = { id: nextId(), ...body, lunar: '十月初六' }
    lifeEvents.unshift(event)
    return json(res, event, 201)
  }
  const eventMatch = path.match(/^\/life-events\/(\d+)$/)
  if (eventMatch && method === 'PATCH') {
    const body = await readBody(req)
    const event = lifeEvents.find((item) => item.id === Number(eventMatch[1]))
    if (event) Object.assign(event, body)
    return json(res, { ...event, lunar: '十月初六' })
  }
  if (eventMatch && method === 'DELETE') {
    const index = lifeEvents.findIndex((item) => item.id === Number(eventMatch[1]))
    if (index >= 0) lifeEvents.splice(index, 1)
    return json(res, { ok: true })
  }

  if (path === '/upload' && method === 'POST') {
    return json(res, { url: '/icons/icon.svg', thumb_url: '/icons/icon.svg' }, 201)
  }

  if (path === '/sync/changes') {
    return json(res, { server_time: new Date().toISOString(), changes: {} })
  }

  return json(res, { error: { code: 'not_found', message: `未实现: ${method} ${path}` } }, 404)
})

server.listen(PORT, '127.0.0.1', () => {
  console.log(`[mock-api] http://127.0.0.1:${PORT}`)
})
