<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2 class="login-title">GetPayurl Web</h2>
      <el-form :model="form" @submit.prevent="handleLogin">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleLogin"
            :loading="loading"
            style="width: 100%"
          >
            登录
          </el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAuthStore } from '../stores/auth'

const router = useRouter()
const authStore = useAuthStore()
const loading = ref(false)
const form = ref({
  username: '',
  password: ''
})

const handleLogin = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请输入用户名和密码')
    return
  }

  loading.value = true
  try {
    await authStore.login(form.value.username, form.value.password)
    ElMessage.success('登录成功')
    router.push('/')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '登录失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1a2e;
}

.login-card {
  width: 400px;
  background: #16213e;
  border-color: #2d3748;
}

.login-title {
  text-align: center;
  margin-bottom: 30px;
  color: #e0e0e0;
}

/* 卡片暗色样式 */
:deep(.el-card) {
  background: #16213e;
  border-color: #2d3748;
}

/* 表单元素暗色样式 */
:deep(.el-input__inner) {
  background: #1a1a2e;
  border-color: #2d3748;
  color: #e0e0e0;
}

:deep(.el-input__wrapper) {
  background: #1a1a2e;
  box-shadow: none;
}
</style>
