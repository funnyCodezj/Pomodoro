<script setup>
import { ref, computed, onMounted, inject, watch } from 'vue'
import { api } from '../utils/api.js'

const stats = inject('stats')
const refreshStats = inject('refreshStats')

const maxBarSeconds = ref(1)
const yearlyData = ref(null)
const selectedYear = ref(new Date().getFullYear())

const chartLayout = { left: 36, right: 324, top: 20, bottom: 132 }
const chartW = chartLayout.right - chartLayout.left
const chartH = chartLayout.bottom - chartLayout.top
const dx = chartW / 11

const availableYears = computed(() => {
  const y = new Date().getFullYear()
  const years = []
  for (let i = 2025; i <= y; i++) years.push(i)
  return years
})

const maxMonthSeconds = computed(() => {
  const data = yearlyData.value?.monthly_data || []
  return Math.max(...data.map(d => d.seconds), 1)
})

const gridLines = computed(() =>
  [0, 1, 2, 3, 4].map(i => chartLayout.top + (chartH / 4) * i)
)

const points = computed(() => {
  const max = maxMonthSeconds.value
  const data = yearlyData.value?.monthly_data || []
  return data.map((d, i) => ({
    x: chartLayout.left + i * dx,
    y: chartLayout.bottom - (d.seconds / max) * chartH,
    seconds: d.seconds,
  }))
})

const linePath = computed(() => {
  if (points.value.length === 0) return ''
  return points.value.map((p, i) => `${i === 0 ? 'M' : 'L'}${p.x},${p.y}`).join(' ')
})

onMounted(async () => {
  await refreshStats()
  updateMaxBar()
  loadYearlyStats()
})

watch(stats, () => {
  updateMaxBar()
  loadYearlyStats()
})

function updateMaxBar() {
  if (stats.value.week_data) {
    maxBarSeconds.value = Math.max(
      ...stats.value.week_data.map((d) => d.seconds),
      1
    )
  }
}

function formatDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h} 小时 ${m} 分钟`
  return `${m} 分钟`
}

function shortDuration(seconds) {
  const h = Math.floor(seconds / 3600)
  const m = Math.floor((seconds % 3600) / 60)
  if (h > 0) return `${h}h ${m}m`
  return `${m}m`
}

async function loadYearlyStats() {
  try {
    yearlyData.value = await api.getYearlyStats(selectedYear.value)
  } catch (e) {
    console.error(e)
  }
}
</script>

<template>
  <div class="stats-section">
    <h2 class="section-title">📊 统计</h2>

    <div class="summary-grid">
      <div class="summary-card">
        <div class="summary-value">{{ formatDuration(stats.today_focus_seconds) }}</div>
        <div class="summary-label">今日专注</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ stats.today_sessions }}</div>
        <div class="summary-label">今日番茄</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">🔥 {{ stats.current_streak }}</div>
        <div class="summary-label">连续天数</div>
      </div>
      <div class="summary-card">
        <div class="summary-value">{{ stats.total_sessions }}</div>
        <div class="summary-label">总计番茄</div>
      </div>
    </div>

    <div class="chart-card">
      <h3 class="chart-title">本周专注时间</h3>
      <div class="bar-chart">
        <div
          v-for="day in stats.week_data"
          :key="day.date"
          class="bar-item"
        >
          <div class="bar-value">{{ shortDuration(day.seconds) }}</div>
          <div class="bar-track">
            <div
              class="bar-fill"
              :style="{
                height: (day.seconds / maxBarSeconds) * 100 + '%',
              }"
            />
          </div>
          <div class="bar-label">{{ day.weekday }}</div>
        </div>
      </div>
    </div>

    <div class="chart-card">
      <div class="yearly-header">
        <h3 class="chart-title">年度专注统计</h3>
        <select v-model="selectedYear" class="year-select" @change="loadYearlyStats">
          <option v-for="y in availableYears" :key="y" :value="y">{{ y }}年</option>
        </select>
      </div>
      <svg :viewBox="`0 0 340 165`" class="line-chart">
        <!-- Grid lines -->
        <line v-for="(y, i) in gridLines" :key="'g'+i"
          x1="36" :x2="324" :y1="y" :y2="y" stroke="rgba(255,255,255,0.06)" stroke-width="1"/>
        <text v-for="(y, i) in gridLines" :key="'yl'+i"
          x="33" :y="y+3" text-anchor="end" class="chart-label">{{ shortDuration(Math.round(maxMonthSeconds * (4 - i) / 4)) }}</text>
        <!-- Line -->
        <path :d="linePath" fill="none" stroke="var(--work)" stroke-width="2" stroke-linejoin="round" stroke-linecap="round"/>
        <!-- Dots -->
        <circle v-for="(p, i) in points" :key="'d'+i"
          :cx="p.x" :cy="p.y" r="3" class="chart-dot"/>
        <!-- Data values -->
        <text v-for="(p, i) in points" :key="'v'+i"
          :x="p.x" :y="p.y - 8" text-anchor="middle" class="chart-value">{{ shortDuration(p.seconds) }}</text>
        <!-- Month labels -->
        <text v-for="m in 12" :key="'m'+m"
          :x="chartLayout.left + (m - 1) * dx" y="147" text-anchor="middle" class="chart-label">{{ m }}月</text>
      </svg>
    </div>

    <div class="totals-row">
      <span>累计专注：{{ formatDuration(stats.total_focus_seconds) }}</span>
    </div>
  </div>
</template>

<style scoped>
.stats-section {
  padding: 24px 20px 0;
  animation: fadeIn 0.4s ease;
  overflow-y: auto;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 16px;
}

.summary-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 10px;
  margin-bottom: 16px;
}

.summary-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 16px;
  text-align: center;
}

.summary-value {
  font-size: 22px;
  font-weight: 700;
  margin-bottom: 4px;
}

.summary-label {
  font-size: 13px;
  color: var(--text-secondary);
}

.chart-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius-sm);
  padding: 20px;
  margin-bottom: 12px;
}

.chart-title {
  font-size: 15px;
  font-weight: 500;
  margin-bottom: 20px;
  color: var(--text-secondary);
}

.bar-chart {
  display: flex;
  justify-content: space-between;
  align-items: flex-end;
  height: 160px;
}

.bar-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  flex: 1;
  gap: 6px;
}

.bar-value {
  font-size: 11px;
  color: var(--text-tertiary);
  white-space: nowrap;
}

.bar-track {
  width: 28px;
  height: 100px;
  background: rgba(255, 255, 255, 0.04);
  border-radius: 14px;
  position: relative;
  overflow: hidden;
}

.bar-fill {
  position: absolute;
  bottom: 0;
  width: 100%;
  background: linear-gradient(to top, var(--work), #ff8e8e);
  border-radius: 14px;
  transition: height 0.6s ease;
  min-height: 4px;
}

.bar-label {
  font-size: 12px;
  color: var(--text-secondary);
}

.totals-row {
  font-size: 13px;
  color: var(--text-secondary);
  text-align: center;
  padding: 8px 0 16px;
}

.yearly-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}

.year-select {
  background: var(--bg-card-hover);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  color: var(--text-primary);
  font-size: 13px;
  padding: 4px 8px;
  font-family: inherit;
  cursor: pointer;
  outline: none;
}

.year-select:focus {
  border-color: var(--work);
}

.line-chart {
  width: 100%;
  display: block;
}

.line-chart .chart-label {
  fill: var(--text-tertiary);
  font-size: 10px;
  font-family: inherit;
}

.line-chart .chart-value {
  fill: var(--text-secondary);
  font-size: 10px;
  font-family: inherit;
}

.line-chart .chart-dot {
  fill: var(--work);
  stroke: var(--bg-secondary);
  stroke-width: 1.5;
}
</style>
