<template>
  <el-select v-model="selectedPlatform" placeholder="选择平台" @change="handleChange">
    <el-option
      v-for="platform in platforms"
      :key="platform.code"
      :label="platform.name"
      :value="platform.code"
    />
  </el-select>
</template>

<script setup>
import { ref, watch, onMounted } from 'vue'
import { usePlatformStore } from '../stores/platform'

const platformStore = usePlatformStore()
const platforms = ref([])
const selectedPlatform = ref('')

const emit = defineEmits(['change'])

onMounted(async () => {
  await platformStore.loadPlatforms()
  platforms.value = platformStore.platforms
  if (platforms.value.length > 0) {
    selectedPlatform.value = platforms.value[0].code
    handleChange(selectedPlatform.value)
  }
})

const handleChange = (value) => {
  emit('change', value)
}

watch(() => platformStore.platforms, (newVal) => {
  platforms.value = newVal
})
</script>

<style scoped>
/* 选择器暗色样式 */
:deep(.el-select .el-input__wrapper) {
  background: #1a1a2e !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}

:deep(.el-select-dropdown) {
  background: #16213e;
  border-color: #2d3748;
}

:deep(.el-select-dropdown__item) {
  color: #e0e0e0;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background: #0f3460;
}
</style>
