<template>
  <div class="user-management">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')">返回首页</el-button>
        <span class="title">账户管理</span>
      </el-header>

      <el-main>
        <el-card>
          <template #header>
            <div class="card-header">
              <span>用户列表</span>
              <el-button type="primary" @click="loadUsers" :loading="loading">刷新</el-button>
            </div>
          </template>

          <el-table :data="users" style="width: 100%" v-loading="loading">
            <el-table-column prop="id" label="ID" width="60" />
            <el-table-column prop="username" label="用户名" width="150" />
            <el-table-column label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_admin === 1 ? 'danger' : 'info'">
                  {{ row.is_admin === 1 ? '管理员' : '普通用户' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="row.is_disabled === 1 ? 'danger' : 'success'">
                  {{ row.is_disabled === 1 ? '已禁用' : '正常' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="created_at" label="创建时间" width="180" />
            <el-table-column prop="updated_at" label="更新时间" width="180" />
            <el-table-column label="操作" fixed="right" width="250">
              <template #default="{ row }">
                <el-button 
                  v-if="row.username !== 'admin'"
                  size="small" 
                  @click="openEditDialog(row)"
                >
                  编辑
                </el-button>
                <el-button 
                  v-if="row.username !== 'admin'"
                  size="small" 
                  :type="row.is_disabled === 1 ? 'success' : 'warning'"
                  @click="toggleDisable(row)"
                >
                  {{ row.is_disabled === 1 ? '启用' : '禁用' }}
                </el-button>
                <el-button 
                  v-if="row.username !== 'admin'"
                  size="small" 
                  type="danger" 
                  @click="deleteUser(row)"
                >
                  删除
                </el-button>
                <el-tag v-if="row.username === 'admin'" size="small" type="info">
                  不可操作
                </el-tag>
              </template>
            </el-table-column>
          </el-table>
        </el-card>

        <!-- 编辑对话框 -->
        <el-dialog v-model="editDialogVisible" title="编辑用户" width="500px">
          <el-form :model="editForm" label-width="100px">
            <el-form-item label="用户名">
              <el-input v-model="editForm.username" placeholder="留空则不修改" />
            </el-form-item>
            <el-form-item label="新密码">
              <el-input 
                v-model="editForm.password" 
                type="password" 
                placeholder="留空则不修改"
                show-password
              />
            </el-form-item>
            <el-form-item label="角色">
              <el-select v-model="editForm.is_admin" placeholder="选择角色">
                <el-option label="普通用户" :value="0" />
                <el-option label="管理员" :value="1" />
              </el-select>
            </el-form-item>
            <el-form-item label="状态">
              <el-select v-model="editForm.is_disabled" placeholder="选择状态">
                <el-option label="正常" :value="0" />
                <el-option label="禁用" :value="1" />
              </el-select>
            </el-form-item>
          </el-form>
          <template #footer>
            <el-button @click="editDialogVisible = false">取消</el-button>
            <el-button type="primary" @click="saveEdit" :loading="saving">保存</el-button>
          </template>
        </el-dialog>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import axios from 'axios'
import { useAuthStore } from '../stores/auth'

const authStore = useAuthStore()
const users = ref([])
const loading = ref(false)
const saving = ref(false)
const editDialogVisible = ref(false)
const editForm = ref({
  id: null,
  username: '',
  password: '',
  is_admin: 0,
  is_disabled: 0
})

onMounted(() => {
  // 检查是否为admin用户
  if (authStore.username !== 'admin') {
    ElMessage.error('无权访问')
    window.location.href = '/'
    return
  }
  loadUsers()
})

const loadUsers = async () => {
  loading.value = true
  try {
    const response = await axios.get('/api/admin/users', {
      headers: { Authorization: `Bearer ${authStore.token}` }
    })
    if (response.data.success) {
      users.value = response.data.users
    }
  } catch (error) {
    ElMessage.error('加载用户列表失败')
  } finally {
    loading.value = false
  }
}

const openEditDialog = (user) => {
  editForm.value = {
    id: user.id,
    username: '',
    password: '',
    is_admin: user.is_admin,
    is_disabled: user.is_disabled
  }
  editDialogVisible.value = true
}

const saveEdit = async () => {
  saving.value = true
  try {
    const updateData = {
      is_admin: editForm.value.is_admin,
      is_disabled: editForm.value.is_disabled
    }
    
    if (editForm.value.username) {
      updateData.username = editForm.value.username
    }
    if (editForm.value.password) {
      if (editForm.value.password.length < 6) {
        ElMessage.warning('密码长度不能少于6位')
        return
      }
      updateData.password = editForm.value.password
    }

    const response = await axios.put(
      `/api/admin/users/${editForm.value.id}`,
      updateData,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    
    if (response.data.success) {
      ElMessage.success('更新成功')
      editDialogVisible.value = false
      loadUsers()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '更新失败')
  } finally {
    saving.value = false
  }
}

const toggleDisable = async (user) => {
  try {
    const response = await axios.post(
      `/api/admin/users/${user.id}/toggle-disable`,
      {},
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    
    if (response.data.success) {
      ElMessage.success(response.data.message)
      loadUsers()
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '操作失败')
  }
}

const deleteUser = async (user) => {
  try {
    await ElMessageBox.confirm(
      `确定要删除用户 "${user.username}" 吗？此操作不可恢复，将同时删除该用户的所有平台配置和订单记录。`,
      '确认删除',
      {
        confirmButtonText: '确定删除',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )

    const response = await axios.delete(
      `/api/admin/users/${user.id}`,
      { headers: { Authorization: `Bearer ${authStore.token}` } }
    )
    
    if (response.data.success) {
      ElMessage.success('删除成功')
      loadUsers()
    }
  } catch (error) {
    if (error !== 'cancel') {
      ElMessage.error(error.response?.data?.detail || '删除失败')
    }
  }
}
</script>

<style scoped>
.user-management {
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

/* 表格暗色样式 */
:deep(.el-table) {
  background: #16213e;
  color: #e0e0e0;
}

:deep(.el-table th) {
  background: #0f3460;
  color: #e0e0e0;
}

:deep(.el-table td) {
  background: #16213e;
  color: #e0e0e0;
  border-color: #2d3748;
}

:deep(.el-table--border::after),
:deep(.el-table--group::after) {
  background-color: #2d3748;
}

/* 对话框暗色样式 */
:deep(.el-dialog) {
  background: #16213e;
}

:deep(.el-dialog__title) {
  color: #e0e0e0;
}

:deep(.el-dialog__body) {
  color: #e0e0e0;
}

:deep(.el-form-item__label) {
  color: #e0e0e0;
}

/* 按钮样式 */
:deep(.el-button) {
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

:deep(.el-select-dropdown__item:hover) {
  background: #0f3460 !important;
}

/* 输入框暗色样式 */
:deep(.el-input__wrapper) {
  background: #1a1a2e !important;
  box-shadow: none !important;
}

:deep(.el-input__inner) {
  background: #1a1a2e !important;
  color: #e0e0e0 !important;
}
</style>
