<template>
  <div class="page">
    <div class="page-header">
      <h2>执行历史</h2>
      <div class="header-actions">
        <el-button @click="fetchTasks" :loading="loading">
          <el-icon><Refresh /></el-icon> 刷新
        </el-button>
        <el-popconfirm
          title="确定要清空所有执行记录和截图吗？此操作不可恢复"
          confirm-button-text="确认清空"
          cancel-button-text="取消"
          @confirm="clearAll"
        >
          <template #reference>
            <el-button type="danger" :loading="clearing" plain>
              <el-icon><Delete /></el-icon> 一键清空
            </el-button>
          </template>
        </el-popconfirm>
      </div>
    </div>

    <!-- 按用例分组折叠 -->
    <el-collapse v-model="activeGroups" v-loading="loading">
      <el-collapse-item
        v-for="group in groupedTasks"
        :key="group.case_id"
        :name="group.case_id"
      >
        <template #title>
          <div class="group-title">
            <span class="case-name">{{ group.case_name }}</span>
            <el-tag size="small" type="info" effect="plain" style="margin-left:12px">
              {{ group.tasks.length }} 次执行
            </el-tag>
            <span class="case-meta">用例ID: {{ group.case_id }}</span>
            <span class="case-meta">最近执行: {{ group.tasks[0]?.start_time || '-' }}</span>
          </div>
        </template>

        <el-table :data="group.tasks" stripe size="small" style="width:100%">
          <el-table-column prop="id" label="任务ID" width="70" />
          <el-table-column label="状态" min-width="90">
            <template #default="{ row }">
              <el-tag :type="statusTagType(row.status)" size="small">
                {{ statusLabel(row.status) }}
              </el-tag>
            </template>
          </el-table-column>
          <el-table-column prop="start_time" label="开始时间" min-width="150" />
          <el-table-column prop="end_time" label="结束时间" min-width="150" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button text type="primary" size="small" @click="showDetail(row)">详情</el-button>
            </template>
          </el-table-column>
        </el-table>
      </el-collapse-item>
    </el-collapse>

    <!-- 无数据 -->
    <el-empty v-if="!loading && groupedTasks.length === 0" description="暂无执行记录" />

    <!-- 详情抽屉 -->
    <el-drawer
      v-model="drawerVisible"
      title="任务详情"
      size="50%"
      destroy-on-close
    >
      <div v-if="detail" class="detail">
        <el-descriptions :column="2" border size="small" style="margin-bottom:16px">
          <el-descriptions-item label="任务 ID">{{ detail.id }}</el-descriptions-item>
          <el-descriptions-item label="用例 ID">{{ detail.case_id }}</el-descriptions-item>
          <el-descriptions-item label="状态">
            <el-tag :type="statusTagType(detail.status)" size="small">
              {{ statusLabel(detail.status) }}
            </el-tag>
          </el-descriptions-item>
          <el-descriptions-item label="开始时间">{{ detail.start_time }}</el-descriptions-item>
          <el-descriptions-item label="结束时间">{{ detail.end_time }}</el-descriptions-item>
        </el-descriptions>

        <!-- 执行日志 -->
        <div v-if="parsedLog.length" style="margin-bottom:16px">
          <div class="section-title">执行步骤日志</div>
          <div class="log-box">
            <div
              v-for="(step, i) in parsedLog"
              :key="i"
              :class="['log-row', step.status === 'error' ? 'log-error' : '']"
            >
              <span class="log-index">{{ i + 1 }}</span>
              <span class="log-action">{{ step.action }}</span>
              <span class="log-desc">{{ step.desc || step.url || step.value || '' }}</span>
              <el-tag
                size="small"
                :type="step.status === 'ok' ? 'success' : 'danger'"
                style="margin-left:auto; flex-shrink:0"
              >
                {{ step.status }}
              </el-tag>
            </div>
          </div>
        </div>

        <!-- 截图 -->
        <div v-if="detail.screenshots?.length">
          <div class="section-title">截图（{{ detail.screenshots.length }} 张）</div>
          <div class="screenshot-grid">
            <el-image
              v-for="(s, i) in detail.screenshots"
              :key="i"
              :src="`http://127.0.0.1:8000${s.screenshot_path}`"
              :preview-src-list="detail.screenshots.map(x => `http://127.0.0.1:8000${x.screenshot_path}`)"
              :initial-index="i"
              fit="cover"
              class="screenshot-thumb"
            />
          </div>
        </div>
      </div>
    </el-drawer>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { taskApi } from '@/api/index.js'

const loading = ref(false)
const clearing = ref(false)
const tasks = ref([])
const activeGroups = ref([])
const drawerVisible = ref(false)
const detail = ref(null)

const statusLabel = (s) => ({ 0: '待执行', 1: '执行中', 2: '成功', 3: '步骤失败', 4: '异常崩溃' }[s] || '未知')
const statusTagType = (s) => ({ 2: 'success', 3: 'danger', 4: 'danger', 1: 'warning' }[s] || 'info')

// 按 case_id 分组
const groupedTasks = computed(() => {
  const map = {}
  for (const t of tasks.value) {
    const cid = t.case_id
    if (!map[cid]) {
      map[cid] = {
        case_id: cid,
        case_name: t.case_name || `用例#${cid}`,
        tasks: [],
      }
    }
    map[cid].tasks.push(t)
  }
  return Object.values(map)
})

const parsedLog = computed(() => {
  if (!detail.value?.result_log) return []
  try { return JSON.parse(detail.value.result_log) }
  catch { return [] }
})

async function fetchTasks() {
  loading.value = true
  try {
    const res = await taskApi.list()
    tasks.value = (res.tasks || []).reverse()
    activeGroups.value = [...new Set(tasks.value.map(t => t.case_id))]
  } finally {
    loading.value = false
  }
}

async function clearAll() {
  clearing.value = true
  try {
    await taskApi.clear()
    tasks.value = []
    ElMessage.success('已清空所有执行记录')
  } finally {
    clearing.value = false
  }
}

async function showDetail(row) {
  const res = await taskApi.get(row.id)
  detail.value = res
  drawerVisible.value = true
}

onMounted(fetchTasks)
</script>

<style scoped>
.page { padding: 24px; }
.page-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 16px;
}
.page-header h2 { font-size: 20px; color: #303133; }
.header-actions { display: flex; gap: 10px; }

/* 分组标题 */
.group-title {
  display: flex;
  align-items: center;
  width: 100%;
}
.case-name {
  font-size: 15px;
  font-weight: 600;
  color: #303133;
}
.case-meta {
  font-size: 12px;
  color: #909399;
  margin-left: 20px;
}

/* 详情 */
.detail { padding: 8px; }

.section-title {
  font-size: 13px;
  font-weight: 600;
  color: #606266;
  margin-bottom: 8px;
}

.log-box {
  background: #f8f9fb;
  border: 1px solid #e4e7ed;
  border-radius: 6px;
  overflow: hidden;
}
.log-row {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 7px 12px;
  font-size: 13px;
  border-bottom: 1px solid #ebeef5;
}
.log-row:last-child { border-bottom: none; }
.log-error { background: #fff5f5; }
.log-index { width: 20px; text-align: center; font-size: 11px; color: #c0c4cc; flex-shrink: 0; }
.log-action { width: 90px; font-family: monospace; color: #409eff; flex-shrink: 0; }
.log-desc { flex: 1; color: #606266; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }

.screenshot-grid { display: flex; flex-wrap: wrap; gap: 8px; }
.screenshot-thumb {
  width: 140px;
  height: 90px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
}
</style>
