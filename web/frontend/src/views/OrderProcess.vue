<template>
  <div class="order-process">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')">返回首页</el-button>
        <span class="title">订单处理</span>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
            <el-card>
              <template #header>订单配置</template>

              <el-form :model="form" label-width="100px">
                <el-form-item label="选择平台">
                  <PlatformSelector @change="handlePlatformChange" />
                </el-form-item>

                <el-form-item label="商品链接">
                  <el-select
                    v-model="form.product_url"
                    placeholder="选择或输入商品链接"
                    filterable
                    allow-create
                  >
                    <el-option
                      v-for="url in productUrls"
                      :key="url"
                      :label="url"
                      :value="url"
                    />
                  </el-select>
                </el-form-item>

                <el-form-item label="新价格">
                  <el-input-number
                    v-model="form.new_price"
                    :min="0.01"
                    :precision="2"
                    :step="0.01"
                  />
                </el-form-item>

                <el-form-item>
                  <el-row :gutter="10">
                    <el-col :span="8">
                      <el-button
                        type="primary"
                        @click="handleGetPrice"
                        :loading="priceLoading"
                      >
                        获取价格
                      </el-button>
                    </el-col>
                    <el-col :span="8">
                      <el-button
                        type="warning"
                        @click="handleModifyPrice"
                        :loading="modifyPriceLoading"
                        :disabled="!priceInfo.product_id"
                      >
                        修改价格
                      </el-button>
                    </el-col>
                    <el-col :span="8">
                      <el-button
                        type="success"
                        @click="handleProcessOrder"
                        :loading="orderStore.processing"
                      >
                        生成二维码
                      </el-button>
                    </el-col>
                  </el-row>
                </el-form-item>
              </el-form>

              <el-card v-if="orderStore.priceInfo" style="margin-top: 20px">
                <template #header>商品信息</template>
                <el-descriptions :column="1" border>
                  <el-descriptions-item label="商品ID">
                    {{ orderStore.priceInfo.product_id || '未知' }}
                  </el-descriptions-item>
                  <el-descriptions-item label="商品名称">
                    {{ orderStore.priceInfo.product_name }}
                  </el-descriptions-item>
                  <el-descriptions-item label="原始价格">
                    ¥{{ orderStore.priceInfo.original_price }}
                  </el-descriptions-item>
                  <el-descriptions-item label="当前价格" v-if="currentPrice">
                    <span style="color: #67C23A; font-weight: bold">¥{{ currentPrice }}</span>
                  </el-descriptions-item>
                  <el-descriptions-item label="库存">
                    {{ orderStore.priceInfo.stock }}
                  </el-descriptions-item>
                </el-descriptions>
              </el-card>
            </el-card>
          </el-col>

          <el-col :xs="24" :sm="24" :md="12" :lg="12" :xl="12">
            <QRCodeDisplay
              :qr-code="orderStore.qrCode"
              :payment-url="orderStore.paymentUrl"
            />
            <LogViewer :logs="orderStore.logs" style="margin-top: 20px" />
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { useOrderStore } from '../stores/order'
import { usePlatformStore } from '../stores/platform'
import PlatformSelector from '../components/PlatformSelector.vue'
import QRCodeDisplay from '../components/QRCodeDisplay.vue'
import LogViewer from '../components/LogViewer.vue'

const orderStore = useOrderStore()
const platformStore = usePlatformStore()
const currentPlatform = ref('')
const priceLoading = ref(false)
const modifyPriceLoading = ref(false)
const currentPrice = ref('')

const form = ref({
  product_url: '',
  new_price: 0.01
})

const priceInfo = computed(() => {
  return orderStore.priceInfo || {}
})

const productUrls = computed(() => {
  return platformStore.config.product_urls || []
})

onMounted(async () => {
  await platformStore.loadPlatforms()
})

const handlePlatformChange = async (platformCode) => {
  currentPlatform.value = platformCode
  await platformStore.loadConfig(platformCode)
}

const handleGetPrice = async () => {
  if (!form.value.product_url) {
    ElMessage.warning('请输入商品链接')
    return
  }

  priceLoading.value = true
  try {
    const result = await orderStore.getPrice(currentPlatform.value, form.value.product_url)
    if (result.success) {
      ElMessage.success('价格获取成功')
      // 保存当前价格
      currentPrice.value = orderStore.priceInfo?.original_price || ''
    } else {
      ElMessage.error(result.message || '价格获取失败')
    }
  } catch (error) {
    ElMessage.error('价格获取失败')
  } finally {
    priceLoading.value = false
  }
}

const handleModifyPrice = async () => {
  if (!priceInfo.value.product_id) {
    ElMessage.warning('请先获取商品信息')
    return
  }

  if (!form.value.new_price || form.value.new_price <= 0) {
    ElMessage.warning('请输入有效的价格')
    return
  }

  modifyPriceLoading.value = true
  try {
    const result = await orderStore.modifyPrice(
      currentPlatform.value,
      priceInfo.value.product_id,
      form.value.new_price.toString()
    )

    if (result.success) {
      ElMessage.success(result.message || '价格修改成功')
      // 更新当前价格显示
      currentPrice.value = form.value.new_price.toString()
    } else {
      ElMessage.error(result.message || '价格修改失败')
    }
  } catch (error) {
    ElMessage.error('价格修改失败')
  } finally {
    modifyPriceLoading.value = false
  }
}

const handleProcessOrder = async () => {
  if (!form.value.product_url) {
    ElMessage.warning('请输入商品链接')
    return
  }

  try {
    const result = await orderStore.processOrder(
      currentPlatform.value,
      form.value.product_url,
      form.value.new_price
    )

    if (result.success) {
      ElMessage.success('订单处理成功')
    } else {
      ElMessage.error(result.error_message || '订单处理失败')
    }
  } catch (error) {
    ElMessage.error('订单处理失败')
  }
}
</script>

<style scoped>
.order-process {
  min-height: 100vh;
  background: #1a1a2e;
  color: #e0e0e0;
}

.el-header {
  background: #0f3460;
  display: flex;
  align-items: center;
  gap: 20px;
  color: #e0e0e0;
}

.el-header .el-button {
  background: #2d3748 !important;
  border-color: #2d3748 !important;
  color: #ffffff !important;
}

.el-header .el-button:hover {
  background: #3d4d68 !important;
  border-color: #3d4d68 !important;
}

.el-header .el-button span {
  color: #ffffff !important;
}

.title {
  font-size: 20px;
  font-weight: bold;
  color: #e0e0e0;
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

/* 表单元素暗色样式 */
:deep(.el-form-item__label) {
  color: #e0e0e0 !important;
}

:deep(.el-input__inner) {
  background: #1a1a2e !important;
  border-color: #2d3748 !important;
  color: #e0e0e0 !important;
}

:deep(.el-input__wrapper) {
  background: #1a1a2e !important;
  box-shadow: none !important;
}

:deep(.el-input .el-input__wrapper) {
  background: #1a1a2e !important;
}

:deep(.el-input-number) {
  --el-fill-color-blank: #1a1a2e !important;
  --el-input-bg-color: #1a1a2e !important;
  --el-input-text-color: #e0e0e0 !important;
  background: #1a1a2e !important;
}

:deep(.el-input-number .el-input__inner) {
  background: #1a1a2e !important;
  border-color: #2d3748 !important;
  color: #e0e0e0 !important;
}

:deep(.el-input-number__decrease),
:deep(.el-input-number__increase) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
  border-color: #2d3748 !important;
}

/* 选择器暗色样式 */
:deep(.el-select .el-input__wrapper) {
  background: #1a1a2e !important;
  box-shadow: none !important;
}

:deep(.el-select .el-input__inner) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}

:deep(.el-select-dropdown) {
  background: #16213e !important;
  border-color: #2d3748 !important;
}

:deep(.el-select-dropdown__item) {
  color: #e0e0e0 !important;
}

:deep(.el-select-dropdown__item.hover),
:deep(.el-select-dropdown__item:hover) {
  background: #0f3460 !important;
}

/* 描述列表暗色样式 */
:deep(.el-descriptions) {
  color: #e0e0e0;
}

:deep(.el-descriptions__label) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}

:deep(.el-descriptions__content) {
  background: #16213e !important;
  color: #e0e0e0 !important;
}

:deep(.el-descriptions__cell) {
  border-color: #2d3748 !important;
}

/* 按钮样式调整 */
:deep(.el-button) {
  color: #ffffff !important;
}

:deep(.el-button--default) {
  background: #2d3748 !important;
  border-color: #2d3748 !important;
  color: #ffffff !important;
}

:deep(.el-button--default:hover) {
  background: #3d4d68 !important;
  border-color: #3d4d68 !important;
}

:deep(.el-button--default) {
  background: #2d3748;
  border-color: #2d3748;
  color: #ffffff;
}

:deep(.el-button--default:hover) {
  background: #3d4d68;
  border-color: #3d4d68;
}

/* 选择器暗色样式 */
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

/* 空状态暗色样式 */
:deep(.el-empty) {
  background: #16213e;
  border-color: #2d3748;
  color: #e0e0e0;
}

/* 移动端响应式优化 */
@media screen and (max-width: 768px) {
  .el-header {
    padding: 0 10px !important;
    flex-wrap: nowrap !important;
  }

  .el-header .el-button {
    padding: 6px 10px !important;
    font-size: 12px !important;
    min-width: auto !important;
    width: auto !important;
    flex-shrink: 0 !important;
  }

  .title {
    font-size: 16px !important;
    white-space: nowrap !important;
    flex-shrink: 1 !important;
  }

  .el-main {
    padding: 10px !important;
  }

  :deep(.el-card__header) {
    padding: 10px 15px !important;
    font-size: 14px !important;
  }

  :deep(.el-form-item__label) {
    font-size: 13px !important;
  }

  :deep(.el-form) {
    padding: 0 5px !important;
  }

  /* 按钮在小屏幕上全宽显示 */
  :deep(.el-row .el-col) {
    margin-bottom: 10px;
  }

  :deep(.el-button) {
    width: 100% !important;
    margin-bottom: 5px !important;
  }

  /* 二维码图片缩小 */
  .qr-image {
    max-width: 200px !important;
  }
}
</style>
