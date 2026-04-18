<template>
  <div class="platform-manage">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')">返回首页</el-button>
        <span class="title">平台管理</span>
      </el-header>

      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>选择平台</span>
              <PlatformSelector @change="handlePlatformChange" />
            </div>
          </template>

          <el-form :model="form" label-width="100px">
            <!-- 登录状态提示 -->
            <el-alert
              v-if="platformStore.config.has_login"
              title="店铺已配置账号密码"
              type="success"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            >
              <template #default>
                <div>
                  <p style="margin: 0 0 5px 0">
                    <strong>账号：</strong>{{ platformStore.config.shop_username }}
                  </p>
                  <p style="margin: 0; font-size: 12px; color: #909399">
                    ℹ️ 提示：生成二维码功能无需登录店铺，仅在需要修改商品价格时才需要重新登录
                  </p>
                </div>
              </template>
            </el-alert>

            <el-alert
              v-else
              title="店铺未配置账号密码"
              type="warning"
              :closable="false"
              show-icon
              style="margin-bottom: 20px"
            >
              <template #default>
                <p style="margin: 0; font-size: 12px">
                  ⚠️ 提示：生成二维码功能无需登录店铺。仅在需要修改商品价格时才需要填写账号密码并登录
                </p>
              </template>
            </el-alert>

            <el-form-item label="店铺账号">
              <el-input v-model="form.shop_username" placeholder="请输入店铺账号" />
            </el-form-item>

            <el-form-item label="店铺密码">
              <el-input
                v-model="form.shop_password"
                type="password"
                placeholder="请输入店铺密码（仅用于修改商品价格）"
                show-password
              />
            </el-form-item>

            <!-- 验证码（仅新发卡平台需要） -->
            <el-form-item v-if="currentPlatform === 'xinfaka'" label="验证码">
              <div style="display: flex; gap: 10px; align-items: center">
                <el-input 
                  v-model="form.verify_code" 
                  placeholder="请输入验证码" 
                  style="flex: 1"
                  maxlength="4"
                />
                <el-button 
                  @click="handleGetCaptcha" 
                  :loading="captchaLoading"
                  style="flex-shrink: 0"
                >
                  获取验证码
                </el-button>
                <img 
                  v-if="captchaImage" 
                  :src="captchaImage" 
                  alt="验证码"
                  style="height: 40px; cursor: pointer; border-radius: 4px"
                  @click="handleGetCaptcha"
                  title="点击刷新验证码"
                />
              </div>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                @click="handleShopLogin"
                :loading="loginLoading"
              >
                登录店铺
              </el-button>
              <el-tag
                v-if="platformStore.loginStatus.loggedIn"
                type="success"
                style="margin-left: 10px"
              >
                ✓ 已登录: {{ platformStore.loginStatus.shopName }}
              </el-tag>
              <el-tag
                v-else-if="platformStore.config.has_login"
                type="info"
                style="margin-left: 10px"
              >
                ℹ 已配置账号（无需登录即可生成二维码）
              </el-tag>
            </el-form-item>

            <!-- 余额显示区域 -->
            <el-form-item v-if="platformStore.loginStatus.loggedIn || platformStore.config.has_login" label="账户余额">
              <div style="display: flex; gap: 20px; align-items: center; flex-wrap: wrap">
                <el-button
                  type="success"
                  @click="handleGetBalance"
                  :loading="balanceLoading"
                >
                  查询余额
                </el-button>
                <div v-if="balance.withdrawable !== null" style="display: flex; gap: 15px; flex-wrap: wrap">
                  <div style="display: flex; align-items: center; gap: 8px; background: #1a3a2a; padding: 10px 20px; border-radius: 8px">
                    <el-tag type="success" effect="dark">可提现</el-tag>
                    <span style="color: #67c23a; font-size: 20px; font-weight: bold">{{ balance.withdrawable }} 元</span>
                  </div>
                  <div style="display: flex; align-items: center; gap: 8px; background: #3a2a1a; padding: 10px 20px; border-radius: 8px">
                    <el-tag type="warning" effect="dark">不可提现</el-tag>
                    <span style="color: #e6a23c; font-size: 20px; font-weight: bold">{{ balance.non_withdrawable }} 元</span>
                  </div>
                </div>
              </div>
            </el-form-item>

            <el-divider>商品链接</el-divider>

            <el-form-item label="商品链接">
              <div v-for="(url, index) in form.product_urls" :key="index" class="url-item">
                <el-input v-model="form.product_urls[index]" placeholder="输入商品链接" />
                <el-button
                  type="danger"
                  :icon="Delete"
                  @click="removeUrl(index)"
                  style="margin-left: 10px"
                />
              </div>
              <el-button type="primary" @click="addUrl" style="margin-top: 10px">
                添加链接
              </el-button>
            </el-form-item>

            <el-form-item>
              <el-button type="success" @click="saveConfig" :loading="saveLoading">
                保存配置
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { Delete } from '@element-plus/icons-vue'
import { usePlatformStore } from '../stores/platform'
import { getBalance, getCaptcha } from '../api/platforms'
import PlatformSelector from '../components/PlatformSelector.vue'

const platformStore = usePlatformStore()
const currentPlatform = ref('')
const loginLoading = ref(false)
const saveLoading = ref(false)
const balanceLoading = ref(false)
const captchaLoading = ref(false)
const captchaImage = ref('')

const form = ref({
  shop_username: '',
  shop_password: '',
  verify_code: '',
  product_urls: []
})

const balance = ref({
  withdrawable: null,
  non_withdrawable: null
})

onMounted(async () => {
  await platformStore.loadPlatforms()
})

const handlePlatformChange = async (platformCode) => {
  currentPlatform.value = platformCode
  await platformStore.loadConfig(platformCode)

  form.value.shop_username = platformStore.config.shop_username || ''
  form.value.shop_password = ''
  form.value.verify_code = ''
  form.value.product_urls = [...platformStore.config.product_urls]
  
  // 清空验证码
  captchaImage.value = ''
  
  // 根据配置更新登录状态显示
  if (platformStore.config.has_login) {
    platformStore.loginStatus = {
      loggedIn: true,
      shopName: platformStore.config.shop_username
    }
  } else {
    platformStore.loginStatus = {
      loggedIn: false,
      shopName: ''
    }
  }
}

const handleShopLogin = async () => {
  if (!form.value.shop_username || !form.value.shop_password) {
    ElMessage.warning('请输入账号密码')
    return
  }

  // 新发卡平台需要验证码
  if (currentPlatform.value === 'xinfaka' && !form.value.verify_code) {
    ElMessage.warning('请输入验证码')
    return
  }

  loginLoading.value = true
  try {
    const result = await platformStore.shopLogin(
      currentPlatform.value,
      form.value.shop_username,
      form.value.shop_password,
      form.value.verify_code
    )

    if (result.success) {
      ElMessage.success(result.message)
      // 清空验证码
      form.value.verify_code = ''
      captchaImage.value = ''
    } else {
      ElMessage.error(result.message)
    }
  } catch (error) {
    ElMessage.error('登录失败')
  } finally {
    loginLoading.value = false
  }
}

const handleGetCaptcha = async () => {
  if (!currentPlatform.value) {
    ElMessage.warning('请先选择平台')
    return
  }

  if (currentPlatform.value !== 'xinfaka') {
    ElMessage.warning('仅新发卡平台需要验证码')
    return
  }

  captchaLoading.value = true
  try {
    const response = await getCaptcha(currentPlatform.value)
    
    if (response.data.success) {
      // 将 hex 转换为 base64 图片
      const hex = response.data.captcha_base64
      const bytes = new Uint8Array(hex.length / 2)
      for (let i = 0; i < hex.length; i += 2) {
        bytes[i / 2] = parseInt(hex.substr(i, 2), 16)
      }
      const blob = new Blob([bytes], { type: 'image/png' })
      captchaImage.value = URL.createObjectURL(blob)
      
      // 清空验证码输入
      form.value.verify_code = ''
      
      ElMessage.success('验证码获取成功')
    } else {
      ElMessage.error('获取验证码失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '获取验证码失败')
  } finally {
    captchaLoading.value = false
  }
}

const addUrl = () => {
  form.value.product_urls.push('')
}

const removeUrl = (index) => {
  form.value.product_urls.splice(index, 1)
}

const saveConfig = async () => {
  saveLoading.value = true
  try {
    await platformStore.updateConfig(currentPlatform.value, {
      shop_username: form.value.shop_username,
      product_urls: form.value.product_urls.filter(url => url.trim())
    })
    ElMessage.success('配置保存成功')
  } catch (error) {
    ElMessage.error('配置保存失败')
  } finally {
    saveLoading.value = false
  }
}

const handleGetBalance = async () => {
  if (!currentPlatform.value) {
    ElMessage.warning('请先选择平台')
    return
  }

  balanceLoading.value = true
  try {
    const response = await getBalance(currentPlatform.value)
    
    if (response.data.success) {
      balance.value.withdrawable = response.data.withdrawable
      balance.value.non_withdrawable = response.data.non_withdrawable
      ElMessage.success('余额查询成功')
    } else {
      ElMessage.error(response.data.message || '余额查询失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '余额查询失败')
  } finally {
    balanceLoading.value = false
  }
}
</script>

<style scoped>
.platform-manage {
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

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  color: #e0e0e0;
}

.url-item {
  display: flex;
  align-items: center;
  margin-bottom: 10px;
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

/* 分割线暗色样式 */
:deep(.el-divider__text) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}

:deep(.el-divider) {
  border-color: #2d3748 !important;
}

/* 按钮样式调整 */
:deep(.el-button) {
  color: #ffffff !important;
}

:deep(.el-button--default),
.el-button:not([class*="el-button--"]) {
  background: #2d3748 !important;
  border-color: #2d3748 !important;
  color: #ffffff !important;
}

:deep(.el-button--default:hover),
.el-button:not([class*="el-button--"]):hover {
  background: #3d4d68 !important;
  border-color: #3d4d68 !important;
  color: #ffffff !important;
}

:deep(.el-button--danger) {
  color: #ffffff !important;
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

/* 标签暗色样式 */
:deep(.el-tag) {
  background: #2d3748 !important;
  border-color: #2d3748 !important;
  color: #e0e0e0 !important;
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
  :deep(.el-button) {
    width: 100% !important;
    margin-bottom: 5px !important;
  }

  .card-header {
    flex-direction: column;
    gap: 10px;
  }

  .url-item {
    flex-direction: column;
    gap: 5px;
  }

  .url-item .el-button {
    margin-left: 0 !important;
  }
}
</style>
