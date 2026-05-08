<script setup>
import { ref, inject } from 'vue'
import { api } from '../utils/api.js'

const emit = defineEmits(['close'])
const settings = inject('settings')

const local = ref({ ...settings.value })
const saving = ref(false)

async function save() {
  saving.value = true
  try {
    const updated = await api.updateSettings(local.value)
    settings.value = updated
    emit('close')
  } catch (e) {
    console.error('Failed to save settings:', e)
  } finally {
    saving.value = false
  }
}

function cancel() {
  emit('close')
}
</script>

<template>
  <div class="overlay" @click.self="cancel">
    <div class="sheet">
      <div class="sheet-handle" />
      <h2 class="sheet-title">⚙️ 设置</h2>

      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">专注时长</div>
          <div class="setting-desc">分钟</div>
        </div>
        <div class="setting-control">
          <button class="adj-btn" @click="local.work_duration = Math.max(1, local.work_duration - 1)">−</button>
          <span class="setting-value">{{ local.work_duration }}</span>
          <button class="adj-btn" @click="local.work_duration = Math.min(120, local.work_duration + 1)">+</button>
        </div>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">短休息</div>
          <div class="setting-desc">分钟</div>
        </div>
        <div class="setting-control">
          <button class="adj-btn" @click="local.short_break = Math.max(1, local.short_break - 1)">−</button>
          <span class="setting-value">{{ local.short_break }}</span>
          <button class="adj-btn" @click="local.short_break = Math.min(30, local.short_break + 1)">+</button>
        </div>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">长休息</div>
          <div class="setting-desc">分钟</div>
        </div>
        <div class="setting-control">
          <button class="adj-btn" @click="local.long_break = Math.max(1, local.long_break - 1)">−</button>
          <span class="setting-value">{{ local.long_break }}</span>
          <button class="adj-btn" @click="local.long_break = Math.min(60, local.long_break + 1)">+</button>
        </div>
      </div>

      <div class="setting-row">
        <div class="setting-info">
          <div class="setting-name">长休息间隔</div>
          <div class="setting-desc">每 N 个番茄钟后</div>
        </div>
        <div class="setting-control">
          <button class="adj-btn" @click="local.cycles_before_long = Math.max(2, local.cycles_before_long - 1)">−</button>
          <span class="setting-value">{{ local.cycles_before_long }}</span>
          <button class="adj-btn" @click="local.cycles_before_long = Math.min(10, local.cycles_before_long + 1)">+</button>
        </div>
      </div>

      <div class="sheet-actions">
        <button class="btn-cancel" @click="cancel">取消</button>
        <button class="btn-save" :disabled="saving" @click="save">
          {{ saving ? '保存中...' : '保存' }}
        </button>
      </div>
    </div>
  </div>
</template>

<style scoped>
.overlay {
  position: fixed;
  inset: 0;
  background: rgba(0, 0, 0, 0.5);
  display: flex;
  align-items: flex-end;
  z-index: 100;
  animation: fadeIn 0.2s ease;
}

.sheet {
  width: 100%;
  background: var(--bg-secondary);
  border-radius: 20px 20px 0 0;
  padding: 12px 24px 32px;
  animation: slideUp 0.3s ease;
}

.sheet-handle {
  width: 36px;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  margin: 0 auto 16px;
}

.sheet-title {
  font-size: 20px;
  font-weight: 600;
  margin-bottom: 24px;
}

.setting-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  border-bottom: 1px solid var(--border);
}

.setting-name {
  font-size: 15px;
  font-weight: 500;
}

.setting-desc {
  font-size: 12px;
  color: var(--text-tertiary);
  margin-top: 2px;
}

.setting-control {
  display: flex;
  align-items: center;
  gap: 14px;
}

.setting-value {
  font-size: 20px;
  font-weight: 600;
  width: 40px;
  text-align: center;
}

.adj-btn {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  border: 1px solid var(--border);
  background: rgba(255, 255, 255, 0.04);
  color: var(--text-primary);
  font-size: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s;
}

.adj-btn:hover {
  background: var(--bg-card-hover);
}

.sheet-actions {
  display: flex;
  gap: 12px;
  margin-top: 24px;
}

.btn-cancel,
.btn-save {
  flex: 1;
  padding: 14px;
  border-radius: var(--radius-sm);
  font-size: 15px;
  font-weight: 600;
  border: none;
}

.btn-cancel {
  background: rgba(255, 255, 255, 0.06);
  color: var(--text-secondary);
}

.btn-save {
  background: var(--work);
  color: #fff;
}

.btn-save:disabled {
  opacity: 0.5;
}

@keyframes slideUp {
  from { transform: translateY(100%); }
  to { transform: translateY(0); }
}
</style>
