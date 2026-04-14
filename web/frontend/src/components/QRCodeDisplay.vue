<template>
  <div class="qr-display">
    <el-card v-if="qrCode">
      <template #header>
        <div class="card-header">
          <span>支付二维码</span>
          <el-button size="small" @click="copyImage">复制图片</el-button>
        </div>
      </template>
      <div class="qr-content">
        <img ref="qrImageRef" :src="qrCode" alt="支付二维码" class="qr-image" />
        <p class="qr-tip">请使用支付宝扫码支付</p>
      </div>
    </el-card>
    <el-empty v-else description="暂无二维码" />
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { ElMessage } from 'element-plus'

const props = defineProps({
  qrCode: {
    type: String,
    default: ''
  },
  paymentUrl: {
    type: String,
    default: ''
  }
})

const qrImageRef = ref(null)

const copyImage = async () => {
  try {
    if (!qrImageRef.value) {
      ElMessage.warning('暂无二维码可复制')
      return
    }

    // 创建canvas并绘制二维码图片
    const canvas = document.createElement('canvas')
    const img = qrImageRef.value
    canvas.width = img.naturalWidth
    canvas.height = img.naturalHeight
    
    const ctx = canvas.getContext('2d')
    ctx.drawImage(img, 0, 0)
    
    // 将canvas转换为Blob
    const blob = await new Promise((resolve) => {
      canvas.toBlob(resolve, 'image/png')
    })
    
    // 复制到剪贴板
    await navigator.clipboard.write([
      new ClipboardItem({ 'image/png': blob })
    ])
    
    ElMessage.success('二维码图片已复制到剪贴板')
  } catch (error) {
    console.error('复制失败:', error)
    ElMessage.error('复制失败，请确保浏览器支持Clipboard API')
  }
}
</script>

<style scoped>
.qr-display {
  text-align: center;
}

.qr-content {
  padding: 20px;
  background: #16213e;
}

.qr-image {
  max-width: 250px;
  border: 2px solid #2d3748;
  border-radius: 8px;
  background: #fff; /* 二维码背景保持白色以确保可扫描 */
  padding: 10px;
}

.qr-tip {
  margin-top: 15px;
  color: #a0a0a0;
}

/* 卡片暗色样式 */
:deep(.el-card) {
  background: #16213e;
  border-color: #2d3748;
}

:deep(.el-card__header) {
  background: #0f3460;
  border-bottom-color: #2d3748;
  color: #e0e0e0;
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #e0e0e0;
}

/* 空状态暗色样式 */
:deep(.el-empty) {
  background: #16213e;
  color: #e0e0e0;
}
</style>
