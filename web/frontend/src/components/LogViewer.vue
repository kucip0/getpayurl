<template>
  <div class="log-viewer">
    <div class="log-header">处理日志</div>
    <div class="log-content" ref="logContainer">
      <div
        v-for="(log, index) in logs"
        :key="index"
        class="log-item"
        :class="{ 'log-error': log.includes('失败'), 'log-success': log.includes('成功') }"
      >
        {{ log }}
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, watch, nextTick } from 'vue'

const props = defineProps({
  logs: {
    type: Array,
    default: () => []
  }
})

const logContainer = ref(null)

watch(() => props.logs, async () => {
  await nextTick()
  if (logContainer.value) {
    logContainer.value.scrollTop = logContainer.value.scrollHeight
  }
}, { deep: true })
</script>

<style scoped>
.log-viewer {
  border: 1px solid #2d3748;
  border-radius: 4px;
  background: #16213e;
}

.log-header {
  padding: 10px 15px;
  background: #0f3460;
  border-bottom: 1px solid #2d3748;
  font-weight: bold;
  color: #e0e0e0;
}

.log-content {
  height: 300px;
  overflow-y: auto;
  padding: 10px;
  font-family: monospace;
  font-size: 12px;
  background: #1a1a2e;
}

.log-item {
  padding: 5px 0;
  color: #a0a0a0;
}

.log-success {
  color: #67c23a;
  font-weight: bold;
}

.log-error {
  color: #f56c6c;
  font-weight: bold;
}

/* 滚动条暗色样式 */
.log-content::-webkit-scrollbar {
  width: 8px;
}

.log-content::-webkit-scrollbar-track {
  background: #16213e;
}

.log-content::-webkit-scrollbar-thumb {
  background: #2d3748;
  border-radius: 4px;
}

.log-content::-webkit-scrollbar-thumb:hover {
  background: #0f3460;
}
</style>
