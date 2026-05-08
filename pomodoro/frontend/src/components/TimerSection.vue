<script setup>
import { ref, computed, watch, onUnmounted, inject } from 'vue'
import { api } from '../utils/api.js'

const settings = inject('settings')
const refreshStats = inject('refreshStats')

const phase = ref('work') // work | short_break | long_break
const status = ref('idle') // idle | running | paused
const timeLeft = ref(0)
const currentCycle = ref(0) // completed work cycles before long break
const totalTime = ref(0)

let timeoutId = null

const durationMap = computed(() => ({
  work: settings.value.work_duration * 60,
  short_break: settings.value.short_break * 60,
  long_break: settings.value.long_break * 60,
}))

function resetTimer() {
  stopTimer()
  status.value = 'idle'
  totalTime.value = durationMap.value[phase.value]
  timeLeft.value = totalTime.value
}

function start() {
  if (timeLeft.value <= 0) return
  status.value = 'running'
  startTimer()
}

function pause() {
  status.value = 'paused'
  stopTimer()
}

function toggle() {
  if (status.value === 'running') pause()
  else start()
}

function skip() {
  stopTimer()
  completeSession(true)
}

function startTimer() {
  stopTimer()
  const tick = () => {
    timeLeft.value--
    if (timeLeft.value <= 0) {
      timeLeft.value = 0
      completeSession(false)
    } else {
      timeoutId = setTimeout(tick, 1000)
    }
  }
  timeoutId = setTimeout(tick, 1000)
}

function stopTimer() {
  if (timeoutId !== null) {
    clearTimeout(timeoutId)
    timeoutId = null
  }
}

async function completeSession(skipped) {
  stopTimer()
  status.value = 'idle'
  const wasWork = phase.value === 'work'

  if (wasWork && !skipped) {
    currentCycle.value++
    try {
      await api.createSession('work', totalTime.value)
      refreshStats()
    } catch (e) {
      console.error('Failed to save session:', e)
    }
    playNotification()
  }

  if (wasWork) {
    const cyclesBeforeLong = settings.value.cycles_before_long
    phase.value =
      currentCycle.value % cyclesBeforeLong === 0 ? 'long_break' : 'short_break'
  } else {
    phase.value = 'work'
  }

  totalTime.value = durationMap.value[phase.value]
  timeLeft.value = totalTime.value
  start()
}

function playNotification() {
  try {
    const ctx = new (window.AudioContext || window.webkitAudioContext)()
    const play = (freq, start, dur) => {
      const osc = ctx.createOscillator()
      const gain = ctx.createGain()
      osc.connect(gain)
      gain.connect(ctx.destination)
      osc.frequency.value = freq
      osc.type = 'sine'
      gain.gain.setValueAtTime(0.3, start)
      gain.gain.exponentialRampToValueAtTime(0.01, start + dur)
      osc.start(start)
      osc.stop(start + dur)
    }
    play(880, ctx.currentTime, 0.15)
    play(1100, ctx.currentTime + 0.2, 0.15)
    play(1320, ctx.currentTime + 0.4, 0.3)
    setTimeout(() => ctx.close(), 1000)
  } catch (e) {
    // Audio not available
  }
}

function formatTime(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`
}

const progress = computed(() => {
  if (totalTime.value <= 0) return 1
  return 1 - timeLeft.value / totalTime.value
})

const circumference = 2 * Math.PI * 130
const dashOffset = computed(() => circumference * (1 - progress.value))

const accentColor = computed(() => {
  if (phase.value === 'work') return 'var(--work)'
  if (phase.value === 'long_break') return 'var(--focus)'
  return 'var(--break)'
})
const glowColor = computed(() =>
  phase.value === 'work' ? 'var(--work-glow)' : 'var(--break-glow)'
)

const phaseLabel = computed(() => {
  if (phase.value === 'work') return '专注时间'
  if (phase.value === 'short_break') return '短休息'
  return '长休息'
})

const isPomo = computed(() => phase.value === 'work')

watch(
  () => settings.value,
  () => {
    if (status.value === 'idle') {
      totalTime.value = durationMap.value[phase.value]
      timeLeft.value = totalTime.value
    }
  },
  { deep: true }
)

// Initialize
resetTimer()

onUnmounted(() => stopTimer())
</script>

<template>
  <div class="timer-section">
    <div class="timer-card">
      <div class="timer-ring-wrap">
        <svg width="300" height="300" viewBox="0 0 300 300">
          <circle
            cx="150" cy="150" r="130"
            fill="none" stroke="rgba(255,255,255,0.05)"
            stroke-width="6"
          />
          <circle
            cx="150" cy="150" r="130"
            fill="none" :stroke="accentColor"
            stroke-width="6"
            stroke-linecap="round"
            :stroke-dasharray="circumference"
            :stroke-dashoffset="dashOffset"
            transform="rotate(-90, 150, 150)"
            class="progress-ring"
            :style="{ filter: `drop-shadow(0 0 10px ${glowColor})` }"
          />
        </svg>
        <div class="timer-center">
          <div class="timer-display" :class="{ pulse: status === 'running' && timeLeft <= 60 }">
            {{ formatTime(timeLeft) }}
          </div>
          <div class="phase-label" :style="{ color: accentColor }">
            {{ phaseLabel }}
          </div>
          <div v-if="isPomo && currentCycle > 0" class="cycle-info">
            第 {{ currentCycle % settings.cycles_before_long || settings.cycles_before_long }} / {{ settings.cycles_before_long }} 轮
          </div>
        </div>
      </div>

      <div class="controls">
        <button
          class="btn-primary"
          :style="{ background: accentColor }"
          @click="toggle"
        >
          <span v-if="status === 'running'">⏸ 暂停</span>
          <span v-else-if="status === 'paused'">▶ 继续</span>
          <span v-else>▶ 开始</span>
        </button>
        <button class="btn-secondary" @click="resetTimer">
          ↺ 重置
        </button>
        <button class="btn-secondary" @click="skip">
          ⏭ 跳过
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.timer-section {
  padding: 24px 20px 0;
  animation: fadeIn 0.4s ease;
}

.timer-card {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  padding: 32px 20px 24px;
  display: flex;
  flex-direction: column;
  align-items: center;
  backdrop-filter: blur(12px);
}

.timer-ring-wrap {
  position: relative;
  width: 300px;
  height: 300px;
}

.timer-center {
  position: absolute;
  top: 0; left: 0; right: 0; bottom: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
}

.timer-display {
  font-size: 64px;
  font-weight: 700;
  letter-spacing: 4px;
  font-variant-numeric: tabular-nums;
  transition: color 0.3s;
}

.timer-display.pulse {
  animation: pulse 1s infinite;
}

.progress-ring {
  transition: stroke-dashoffset 0.5s ease, stroke 0.5s ease, filter 0.3s ease;
}

.phase-label {
  font-size: 16px;
  font-weight: 500;
  margin-top: 4px;
  transition: color 0.3s;
}

.cycle-info {
  font-size: 13px;
  color: var(--text-secondary);
  margin-top: 4px;
}

.controls {
  display: flex;
  gap: 10px;
  margin-top: 24px;
}

.btn-primary {
  padding: 12px 32px;
  border: none;
  border-radius: 50px;
  color: #fff;
  font-size: 15px;
  font-weight: 600;
  transition: box-shadow 0.2s, transform 0.1s;
}

.btn-primary:hover {
  box-shadow: 0 0 20px var(--work-glow);
}

.btn-secondary {
  padding: 12px 20px;
  border: 1px solid var(--border);
  border-radius: 50px;
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-secondary);
  font-size: 14px;
  font-weight: 500;
  transition: background 0.2s, color 0.2s;
}

.btn-secondary:hover {
  background: var(--bg-card-hover);
  color: var(--text-primary);
}
</style>
