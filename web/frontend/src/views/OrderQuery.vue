<template>
  <div class="order-query">
    <el-container>
      <el-header>
        <el-button @click="$router.push('/')" class="back-btn">
          <el-icon><ArrowLeft /></el-icon>
          返回首页
        </el-button>
        <span class="title">订单查询</span>
      </el-header>

      <el-main>
        <el-row :gutter="20">
          <el-col :xs="24" :sm="24" :md="24" :lg="24" :xl="24">
            <!-- 查询条件区域 -->
            <el-card class="query-card">
              <el-form :model="queryForm" label-width="100px">
                <el-row :gutter="20">
                  <el-col :xs="24" :sm="12" :md="8" :lg="6">
                    <el-form-item label="选择平台">
                      <el-select v-model="queryForm.platform" placeholder="请选择平台" style="width: 100%">
                        <el-option
                          v-for="platform in platforms"
                          :key="platform.code"
                          :label="platform.name"
                          :value="platform.code"
                        />
                      </el-select>
                    </el-form-item>
                  </el-col>

                  <el-col :xs="24" :sm="12" :md="12" :lg="12">
                    <el-form-item label="日期范围">
                      <el-date-picker
                        v-model="queryForm.dateRange"
                        type="daterange"
                        range-separator="至"
                        start-placeholder="开始日期"
                        end-placeholder="结束日期"
                        format="MM/DD/YYYY"
                        value-format="MM/DD/YYYY"
                        style="width: 100%"
                      />
                    </el-form-item>
                  </el-col>

                  <el-col :xs="24" :sm="24" :md="4" :lg="6">
                    <el-form-item>
                      <el-button
                        type="primary"
                        @click="handleQuery"
                        :loading="orderStore.orderQueryLoading"
                        style="width: 100%"
                      >
                        <el-icon><Search /></el-icon>
                        查询
                      </el-button>
                    </el-form-item>
                  </el-col>
                </el-row>
              </el-form>
            </el-card>

            <!-- 订单列表 -->
            <el-card class="table-card" style="margin-top: 20px">
              <el-table
                :data="paginatedOrders"
                v-loading="orderStore.orderQueryLoading"
                stripe
                border
                style="width: 100%"
                :empty-text="orderStore.orderQueryLoading ? '查询中...' : '暂无订单数据'"
              >
                <el-table-column prop="order_no" label="订单号" width="180" fixed />
                <el-table-column prop="order_type" label="订单类型" width="100" />
                <el-table-column prop="product_name" label="商品名称" min-width="200" show-overflow-tooltip />
                <el-table-column prop="payment_method" label="支付方式" width="100" />
                <el-table-column prop="total_price" label="总价" width="80" />
                <el-table-column prop="actual_price" label="实付款" width="80" />
                <el-table-column prop="buyer_info" label="购买者信息" width="140" show-overflow-tooltip />
                <el-table-column prop="status" label="状态" width="80">
                  <template #default="{ row }">
                    <el-tag :type="row.status === '已支付' ? 'success' : 'info'" size="small">
                      {{ row.status }}
                    </el-tag>
                  </template>
                </el-table-column>
                <el-table-column prop="card_status" label="取卡状态" width="90" />
                <el-table-column prop="trade_time" label="交易时间" width="160" />
              </el-table>

              <!-- 分页 -->
              <div class="pagination-wrapper">
                <el-pagination
                  v-model:current-page="currentPage"
                  v-model:page-size="pageSize"
                  :page-sizes="[10, 20, 50, 100]"
                  :total="orderStore.orderList.length"
                  layout="total, sizes, prev, pager, next, jumper"
                  @size-change="handleSizeChange"
                  @current-change="handlePageChange"
                />
              </div>
            </el-card>
          </el-col>
        </el-row>
      </el-main>
    </el-container>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { ArrowLeft, Search } from '@element-plus/icons-vue'
import { useOrderStore } from '../stores/order'
import { usePlatformStore } from '../stores/platform'

const router = useRouter()
const orderStore = useOrderStore()
const platformStore = usePlatformStore()

// 查询表单
const queryForm = ref({
  platform: 'houfaka',
  dateRange: []
})

// 分页
const currentPage = ref(1)
const pageSize = ref(20)

// 平台列表
const platforms = computed(() => platformStore.platforms)

// 分页后的订单数据
const paginatedOrders = computed(() => {
  const start = (currentPage.value - 1) * pageSize.value
  const end = start + pageSize.value
  return orderStore.orderList.slice(start, end)
})

// 初始化
onMounted(async () => {
  await platformStore.loadPlatforms()
  // 设置默认日期为今天
  const today = new Date()
  const formattedDate = formatDate(today)
  queryForm.value.dateRange = [formattedDate, formattedDate]
})

// 查询订单
const handleQuery = async () => {
  if (!queryForm.value.platform) {
    ElMessage.warning('请选择平台')
    return
  }

  if (!queryForm.value.dateRange || queryForm.value.dateRange.length !== 2) {
    ElMessage.warning('请选择日期范围')
    return
  }

  currentPage.value = 1

  try {
    const result = await orderStore.fetchOrders(queryForm.value.platform, {
      status: 1,
      start_date: queryForm.value.dateRange[0],
      end_date: queryForm.value.dateRange[1]
    })

    if (result.success) {
      ElMessage.success(`查询成功，共找到 ${result.total} 个订单`)
    } else {
      ElMessage.error(result.message || '查询失败')
    }
  } catch (error) {
    ElMessage.error(error.response?.data?.detail || '查询失败')
  }
}

// 分页变化
const handlePageChange = (page) => {
  currentPage.value = page
}

const handleSizeChange = (size) => {
  pageSize.value = size
  currentPage.value = 1
}

// 日期格式化
function formatDate(date) {
  const month = String(date.getMonth() + 1).padStart(2, '0')
  const day = String(date.getDate()).padStart(2, '0')
  const year = date.getFullYear()
  return `${month}/${day}/${year}`
}
</script>

<style scoped>
.order-query {
  min-height: 100vh;
  background: #1a1a2e;
  color: #e0e0e0;
}

.el-header {
  background: #0f3460;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 0 20px;
}

.back-btn {
  background: transparent;
  border: none;
  color: #e0e0e0;
}

.back-btn:hover {
  background: rgba(255, 255, 255, 0.1);
}

.title {
  font-size: 20px;
  font-weight: bold;
  color: #e0e0e0;
}

.query-card {
  background: #16213e;
  border-color: #2d3748;
}

.table-card {
  background: #16213e;
  border-color: #2d3748;
}

.pagination-wrapper {
  margin-top: 20px;
  display: flex;
  justify-content: center;
}

/* 暗色主题样式 */
:deep(.el-card) {
  background: #16213e;
  border-color: #2d3748;
}

:deep(.el-form-item__label) {
  color: #e0e0e0 !important;
}

:deep(.el-table) {
  background: #16213e;
  color: #e0e0e0;
}

:deep(.el-table th) {
  background: #0f3460;
  color: #e0e0e0;
}

:deep(.el-table tr) {
  background: #16213e;
}

:deep(.el-table td) {
  border-color: #2d3748;
  color: #e0e0e0;
}

:deep(.el-table--striped .el-table__body tr.el-table__row--striped td) {
  background: #1a1a2e;
}

:deep(.el-table--border) {
  border-color: #2d3748;
}

:deep(.el-table--border::after),
:deep(.el-table--border::before),
:deep(.el-table__inner-wrapper::before) {
  background-color: #2d3748;
}

/* 移动端响应式 */
@media screen and (max-width: 768px) {
  .el-header {
    padding: 0 10px !important;
  }

  .title {
    font-size: 16px;
  }

  :deep(.el-form-item__label) {
    width: 80px !important;
  }
}
</style>
