<template>
  <div class="register-container">
    <el-card class="register-card">
      <h2 class="register-title">注册账号</h2>
      <el-form :model="form" @submit.prevent="handleRegister">
        <el-form-item>
          <el-input
            v-model="form.username"
            placeholder="用户名（3-50字符）"
            prefix-icon="User"
            size="large"
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.password"
            type="password"
            placeholder="密码（6-100字符）"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-input
            v-model="form.confirmPassword"
            type="password"
            placeholder="确认密码"
            prefix-icon="Lock"
            size="large"
            show-password
          />
        </el-form-item>
        <el-form-item>
          <el-button
            type="primary"
            size="large"
            @click="handleRegister"
            :loading="loading"
            style="width: 100%"
          >
            注册
          </el-button>
        </el-form-item>
        <div class="login-link">
          已有账号？
          <router-link to="/login">立即登录</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { register } from '../api/auth'

const router = useRouter()
const loading = ref(false)
const form = ref({
  username: '',
  password: '',
  confirmPassword: ''
})

const handleRegister = async () => {
  if (!form.value.username || !form.value.password) {
    ElMessage.warning('请填写完整信息')
    return
  }

  if (form.value.password !== form.value.confirmPassword) {
    ElMessage.warning('两次密码不一致')
    return
  }

  loading.value = true
  try {
    await register(form.value.username, form.value.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.register-container {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 100vh;
  background: #1a1a2e;
}

.register-card {
  width: 400px;
  background: #16213e;
  border-color: #2d3748;
}

.register-title {
  text-align: center;
  margin-bottom: 30px;
  color: #e0e0e0;
}

.login-link {
  text-align: center;
  color: #a0a0a0;
}

.login-link a {
  color: #409eff;
  text-decoration: none;
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
