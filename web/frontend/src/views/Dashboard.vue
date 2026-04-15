<template>
  <div class="dashboard">
    <el-container>
      <el-header>
        <div class="header-content">
          <h1>GetPayurl Web</h1>
          <div class="header-right">
            <span>欢迎，{{ authStore.username }}</span>
            <el-button type="danger" size="small" @click="handleLogout">
              退出登录
            </el-button>
          </div>
        </div>
      </el-header>
      
      <el-main>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="8">
            <el-card @click="$router.push('/platform')" class="action-card">
              <el-icon :size="50" color="#409eff"><Setting /></el-icon>
              <h3>平台管理</h3>
              <p>配置店铺账号和商品链接</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="24" :md="8">
            <el-card @click="$router.push('/order')" class="action-card">
              <el-icon :size="50" color="#67c23a"><Money /></el-icon>
              <h3>订单处理</h3>
              <p>生成支付二维码</p>
            </el-card>
          </el-col>
          <el-col :xs="24" :sm="24" :md="8">
            <el-card @click="$router.push('/order-query')" class="action-card">
              <el-icon :size="50" color="#e6a23c"><Document /></el-icon>
              <h3>订单查询</h3>
              <p>查看已付款订单列表</p>
            </el-card>
          </el-col>
        </el-row>
        
        <el-card style="margin-top: 20px">
          <template #header>
            <div class="card-header">
              <span>最近订单</span>
            </div>
          </template>
          <el-empty description="暂无订单记录" />
        </el-card>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import { Setting, Money, Document } from '@element-plus/icons-vue'

const router = useRouter()
const authStore = useAuthStore()

const handleLogout = () => {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.dashboard {
  min-height: 100vh;
  background: #1a1a2e;
  color: #e0e0e0;
}

.el-header {
  background: #0f3460;
  box-shadow: 0 2px 8px rgba(0,0,0,0.3);
  color: #e0e0e0;
}

.header-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  height: 100%;
}

.header-content h1 {
  margin: 0;
  color: #e0e0e0;
  font-size: 20px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 15px;
  color: #e0e0e0;
}

.action-card {
  cursor: pointer;
  text-align: center;
  transition: all 0.3s;
  background: #16213e;
  border-color: #2d3748;
  height: 100%;
  display: flex;
  flex-direction: column;
  justify-content: center;
  min-height: 180px;
}

.action-card:hover {
  transform: translateY(-5px);
  box-shadow: 0 4px 12px rgba(0,0,0,0.4);
}

.action-card h3 {
  margin: 15px 0 10px;
  color: #e0e0e0;
  font-size: 18px;
}

.action-card p {
  margin: 0;
  color: #a0a0a0;
  font-size: 14px;
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
  color: #e0e0e0;
}

/* 空状态暗色样式 */
:deep(.el-empty) {
  background: #16213e;
  color: #e0e0e0;
}

/* 移动端响应式优化 */
@media screen and (max-width: 768px) {
  .header-content h1 {
    font-size: 16px !important;
  }

  .header-right span {
    font-size: 12px !important;
  }

  .el-header {
    padding: 0 10px !important;
  }

  .el-main {
    padding: 10px !important;
  }

  .action-card {
    min-height: 140px !important;
  }

  .action-card h3 {
    font-size: 16px !important;
  }

  .action-card p {
    font-size: 12px !important;
  }

  :deep(.el-card__header) {
    padding: 10px 15px !important;
    font-size: 14px !important;
  }
}
</style>
