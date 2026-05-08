<script setup>
import { inject, ref, reactive, onMounted, onUnmounted } from 'vue'
import { api } from '../utils/api.js'

const sessions = inject('sessions')
const refreshStats = inject('refreshStats')

const showConfirm = ref(false)
const confirmText = ref('')
const swipeOffsets = reactive({})
const activeSwipeId = ref(null)

function formatDate(dateStr) {
  const d = new Date(dateStr)
  const month = String(d.getMonth() + 1).padStart(2, '0')
  const day = String(d.getDate()).padStart(2, '0')
  const hours = String(d.getHours()).padStart(2, '0')
  const mins = String(d.getMinutes()).padStart(2, '0')
  return `${month}-${day} ${hours}:${mins}`
}

function formatDuration(seconds) {
  const m = Math.floor(seconds / 60)
  const s = seconds % 60
  if (m > 0) return `${m}分${s}秒`
  return `${s}秒`
}

function typeLabel(type) {
  if (type === 'work') return '🍅 专注'
  if (type === 'short_break') return '☕ 短休'
  return '🌿 长休'
}

function typeClass(type) {
  if (type === 'work') return 'tag-work'
  if (type === 'short_break') return 'tag-break'
  return 'tag-break'
}

function confirmClear() {
  confirmText.value = ''
  showConfirm.value = true
}

async function doClear() {
  if (confirmText.value !== '删除数据') return
  showConfirm.value = false
  confirmText.value = ''
  closeAllSwipes()
  try {
    await api.clearSessions()
    await refreshStats()
  } catch (e) {
    console.error(e)
  }
}

function cancelClear() {
  showConfirm.value = false
  confirmText.value = ''
}

// --- Swipe to delete ---
let swipeStartX = 0
let swipeBaseOffset = 0
let suppressClick = false

function startSwipe(e, id) {
  closeAllSwipes()
  const clientX = e.type.startsWith('touch') ? e.touches[0].clientX : e.clientX
  swipeStartX = clientX
  swipeBaseOffset = swipeOffsets[id] || 0
  activeSwipeId.value = id

  document.addEventListener('mousemove', onSwipeMove)
  document.addEventListener('mouseup', onSwipeEnd)
  document.addEventListener('touchmove', onSwipeMove, { passive: false })
  document.addEventListener('touchend', onSwipeEnd)
}

function onSwipeMove(e) {
  if (!activeSwipeId.value) return
  e.preventDefault()
  const clientX = e.type.startsWith('touch') ? e.touches[0].clientX : e.clientX
  const delta = swipeStartX - clientX
  swipeOffsets[activeSwipeId.value] = Math.max(0, Math.min(70, swipeBaseOffset + delta))
}

function onSwipeEnd() {
  if (!activeSwipeId.value) return
  const id = activeSwipeId.value
  const offset = swipeOffsets[id] || 0
  swipeOffsets[id] = offset > 35 ? 70 : 0
  if (swipeOffsets[id] === 70) {
    suppressClick = true
    setTimeout(() => { suppressClick = false }, 300)
  }
  activeSwipeId.value = null

  document.removeEventListener('mousemove', onSwipeMove)
  document.removeEventListener('mouseup', onSwipeEnd)
  document.removeEventListener('touchmove', onSwipeMove)
  document.removeEventListener('touchend', onSwipeEnd)
}

function closeAllSwipes() {
  for (const key in swipeOffsets) {
    swipeOffsets[key] = 0
  }
}

function onDocClick() {
  if (suppressClick) return
  closeAllSwipes()
}

async function deleteSession(id) {
  try {
    await api.deleteSession(id)
    swipeOffsets[id] = 0
    await refreshStats()
  } catch (e) {
    console.error(e)
  }
}

onMounted(() => {
  document.addEventListener('click', onDocClick)
})

onUnmounted(() => {
  document.removeEventListener('click', onDocClick)
  document.removeEventListener('mousemove', onSwipeMove)
  document.removeEventListener('mouseup', onSwipeEnd)
  document.removeEventListener('touchmove', onSwipeMove)
  document.removeEventListener('touchend', onSwipeEnd)
})
</script>

<template>
  <div class="history-section">
    <div class="history-header">
      <h2 class="section-title">📋 记录</h2>
      <button v-if="sessions.length > 0" class="clear-btn" @click="confirmClear">
        清除
      </button>
    </div>

    <!-- Confirm modal -->
    <div v-if="showConfirm" class="modal-overlay" @click.self="cancelClear">
      <div class="modal-box">
        <p class="modal-text">该操作将删除所有统计数据，请在下方输入框输入"删除数据"以继续操作</p>
        <input
          v-model="confirmText"
          class="confirm-input"
          placeholder="请输入'删除数据'"
          @keyup.enter="doClear"
        />
        <div class="modal-actions">
          <button class="modal-btn modal-cancel" @click="cancelClear">取消</button>
          <button
            class="modal-btn modal-confirm"
            :disabled="confirmText !== '删除数据'"
            @click="doClear"
          >确定</button>
        </div>
      </div>
    </div>

    <div v-if="sessions.length === 0" class="empty">
      还没有完成记录，开始第一个番茄钟吧！
    </div>

    <div v-else class="session-list">
      <div
        v-for="s in sessions"
        :key="s.id"
        class="swipe-wrap"
      >
        <div
          class="swipe-inner"
          :class="{ dragging: activeSwipeId === s.id }"
          :style="{ transform: `translateX(${-(swipeOffsets[s.id] || 0)}px)` }"
        >
          <div
            class="session-item"
            @mousedown.prevent="startSwipe($event, s.id)"
            @touchstart.prevent="startSwipe($event, s.id)"
          >
            <div class="session-left">
              <span class="session-tag" :class="typeClass(s.type)">
                {{ typeLabel(s.type) }}
              </span>
              <span class="session-time">{{ formatDate(s.completed_at) }}</span>
            </div>
            <div class="session-duration">{{ formatDuration(s.duration) }}</div>
          </div>
          <button class="swipe-delete" @click.stop="deleteSession(s.id)">删除</button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.history-section {
  padding: 24px 20px 0;
  animation: fadeIn 0.4s ease;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.section-title {
  font-size: 20px;
  font-weight: 600;
}

.clear-btn {
  padding: 6px 14px;
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  background: transparent;
  color: var(--text-tertiary);
  font-size: 12px;
  transition: color 0.2s, border-color 0.2s;
}

.clear-btn:hover {
  color: var(--work);
  border-color: var(--work);
}

.empty {
  text-align: center;
  padding: 60px 20px;
  color: var(--text-secondary);
  font-size: 14px;
}

.session-list {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.swipe-wrap {
  overflow: hidden;
  border-radius: var(--radius-sm);
  position: relative;
}

.swipe-inner {
  display: flex;
  width: calc(100% + 70px);
  transition: transform 0.2s ease;
  user-select: none;
}

.swipe-inner.dragging {
  transition: none;
}

.swipe-delete {
  width: 70px;
  flex-shrink: 0;
  background: #e74c3c;
  color: #fff;
  border: none;
  font-size: 13px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}

.session-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 12px 16px;
  width: calc(100% - 70px);
  flex-shrink: 0;
  background: var(--bg-card);
  border: 1px solid var(--border);
  cursor: grab;
  transition: background 0.2s;
}

.session-item:hover {
  background: var(--bg-card-hover);
}

.session-item:active {
  cursor: grabbing;
}

.session-left {
  display: flex;
  align-items: center;
  gap: 10px;
}

.session-tag {
  font-size: 13px;
  font-weight: 500;
  padding: 2px 10px;
  border-radius: 20px;
}

.tag-work {
  background: var(--work-glow);
  color: var(--work);
}

.tag-break {
  background: var(--break-glow);
  color: var(--break);
}

.session-time {
  font-size: 13px;
  color: var(--text-secondary);
}

.session-duration {
  font-size: 14px;
  font-weight: 500;
  color: var(--text-primary);
}

.modal-overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 100;
  padding: 24px;
}

.modal-box {
  background: var(--bg-card);
  border: 1px solid var(--border);
  border-radius: 12px;
  padding: 28px 24px 20px;
  width: 100%;
  max-width: 320px;
  text-align: center;
  animation: fadeIn 0.2s ease;
}

.modal-text {
  font-size: 15px;
  color: var(--text-primary);
  margin-bottom: 24px;
  line-height: 1.5;
}

.modal-actions {
  display: flex;
  gap: 12px;
  justify-content: center;
}

.modal-btn {
  flex: 1;
  max-width: 120px;
  padding: 8px 0;
  border-radius: var(--radius-xs);
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: opacity 0.2s;
  border: none;
}

.modal-btn:active {
  transform: scale(0.96);
}

.modal-cancel {
  background: var(--bg-card-hover);
  color: var(--text-secondary);
  border: 1px solid var(--border);
}

.modal-confirm {
  background: var(--work);
  color: #fff;
}

.modal-confirm:disabled {
  opacity: 0.4;
  cursor: not-allowed;
}

.confirm-input {
  width: 100%;
  padding: 10px 12px;
  margin-bottom: 20px;
  background: var(--bg-primary);
  border: 1px solid var(--border);
  border-radius: var(--radius-xs);
  color: var(--text-primary);
  font-size: 14px;
  font-family: inherit;
  outline: none;
  transition: border-color 0.2s;
}

.confirm-input:focus {
  border-color: var(--work);
}

.confirm-input::placeholder {
  color: var(--text-tertiary);
}
</style>
