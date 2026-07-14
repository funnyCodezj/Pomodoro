<script setup>
import { ref, provide, onMounted } from 'vue'
import { api } from './utils/api.js'
import TimerSection from './components/TimerSection.vue'
import StatsSection from './components/StatsSection.vue'
import HistorySection from './components/HistorySection.vue'
import SettingsSheet from './components/SettingsSheet.vue'

const activeTab = ref('timer')
const showSettings = ref(false)
const settings = ref({
  work_duration: 25,
  short_break: 5,
  long_break: 15,
  cycles_before_long: 4,
})
const stats = ref({
  today_focus_seconds: 0,
  today_sessions: 0,
  week_data: [],
  total_focus_seconds: 0,
  total_sessions: 0,
  current_streak: 0,
})
const sessions = ref([])
const errorMessage = ref('')
let errorTimeoutId = null

provide('settings', settings)
provide('stats', stats)
provide('sessions', sessions)
provide('refreshStats', refreshStats)
provide('notifyError', notifyError)

function notifyError(message) {
  errorMessage.value = message || '操作失败，请稍后重试。'
  clearTimeout(errorTimeoutId)
  errorTimeoutId = setTimeout(() => {
    errorMessage.value = ''
  }, 5000)
}

async function refreshStats() {
  try {
    const [newStats, newSessions] = await Promise.all([
      api.getStats(),
      api.getSessions(50),
    ])
    stats.value = newStats
    sessions.value = newSessions
  } catch (e) {
    console.error('Failed to fetch stats:', e)
    notifyError('无法加载统计数据，请确认应用服务正在运行。')
  }
}

async function loadSettings() {
  try {
    settings.value = await api.getSettings()
  } catch (e) {
    console.error('Failed to load settings:', e)
    notifyError('无法加载设置，请确认应用服务正在运行。')
  }
}

onMounted(() => {
  loadSettings()
  refreshStats()
})
</script>

<template>
  <div class="app">
    <header class="top-bar">
      <div class="logo">🍅 番茄钟</div>
      <button class="gear-btn" @click="showSettings = true">⚙️</button>
    </header>

    <div v-if="errorMessage" class="error-toast" role="alert">
      {{ errorMessage }}
    </div>

    <main class="content">
      <TimerSection v-show="activeTab === 'timer'" />
      <StatsSection v-show="activeTab === 'stats'" />
      <HistorySection v-show="activeTab === 'history'" />
    </main>

    <nav class="tab-bar">
      <button
        :class="['tab-btn', { active: activeTab === 'timer' }]"
        @click="activeTab = 'timer'"
      >
        ⏱ 计时
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'stats' }]"
        @click="activeTab = 'stats'"
      >
        📊 统计
      </button>
      <button
        :class="['tab-btn', { active: activeTab === 'history' }]"
        @click="activeTab = 'history'"
      >
        📋 记录
      </button>
    </nav>

    <SettingsSheet
      v-if="showSettings"
      @close="showSettings = false"
    />
  </div>
</template>

<style scoped>
.app {
  width: 100vw;
  height: 100vh;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 16px 20px 8px;
  -webkit-app-region: drag;
}

.logo {
  font-size: 18px;
  font-weight: 600;
}

.gear-btn {
  width: 36px;
  height: 36px;
  border: none;
  border-radius: 50%;
  background: transparent;
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
  -webkit-app-region: no-drag;
}

.gear-btn:hover {
  background: rgba(255, 255, 255, 0.08);
}

.content {
  flex: 1;
  overflow-y: auto;
}

.error-toast {
  position: absolute;
  top: 58px;
  left: 20px;
  right: 20px;
  z-index: 200;
  padding: 10px 14px;
  border: 1px solid rgba(255, 107, 107, 0.45);
  border-radius: var(--radius-xs);
  background: rgba(101, 31, 40, 0.96);
  color: #ffe4e4;
  font-size: 13px;
  box-shadow: 0 8px 24px rgba(0, 0, 0, 0.24);
}

.tab-bar {
  display: flex;
  padding: 8px 12px;
  gap: 6px;
  background: rgba(255, 255, 255, 0.03);
  border-top: 1px solid var(--border);
  -webkit-app-region: no-drag;
}

.tab-btn {
  flex: 1;
  padding: 10px;
  border: none;
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 14px;
  font-weight: 500;
  transition: color 0.2s, background 0.2s;
}

.tab-btn.active {
  color: var(--text-primary);
  background: rgba(255, 255, 255, 0.06);
}

.tab-btn:hover:not(.active) {
  color: var(--text-secondary);
}
</style>
