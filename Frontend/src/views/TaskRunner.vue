<template>
  <div class="page">
    <div class="page-header">
      <h2>任务执行</h2>
      <p class="sub">选择用例 → 编辑步骤 → 点击执行</p>
    </div>

    <el-row :gutter="16">
      <!-- 左侧：配置区 -->
      <el-col :span="10">
        <el-card class="card">
          <template #header>
            <span>执行配置</span>
          </template>

          <!-- 选择已有用例 -->
          <el-form label-width="80px" size="default">
            <el-form-item label="选择用例">
              <el-select
                v-model="selectedCaseId"
                placeholder="可选：从已有用例加载步骤"
                clearable
                style="width: 100%"
                @change="loadCase"
              >
                <el-option
                  v-for="c in cases"
                  :key="c.id"
                  :label="c.case_name"
                  :value="c.id"
                />
              </el-select>
            </el-form-item>

            <el-form-item label="步骤 JSON">
              <el-input
                v-model="stepsJson"
                type="textarea"
                :rows="12"
                placeholder='示例：
[
  {"action": "open_url", "url": "https://mes.nat.zhsvr.com"},
  {"action": "login", "role": "dist"},
  {"action": "import_order", "file_path": "订单Excel路径"},
  {"action": "import_waybill", "file_path": "面单PDF路径"}
]'
                font-family="monospace"
              />
            </el-form-item>

            <el-form-item label="浏览器模式">
              <el-radio-group v-model="headless">
                <el-radio :value="false">有界面</el-radio>
                <el-radio :value="true">无头（后台）</el-radio>
              </el-radio-group>
            </el-form-item>

            <el-form-item>
              <el-button
                type="primary"
                :loading="running"
                @click="runTask"
                style="width: 100%"
              >
                {{ running ? '执行中...' : '▶ 开始执行' }}
              </el-button>
            </el-form-item>
          </el-form>
        </el-card>
      </el-col>

      <!-- 右侧：结果区 -->
      <el-col :span="14">
        <el-card class="card" v-if="result">
          <template #header>
            <div style="display:flex; align-items:center; gap:8px">
              <span>执行结果</span>
              <el-tag :type="statusTagType" size="small">{{ statusLabel }}</el-tag>
              <span style="margin-left:auto; color:#999; font-size:12px">
                任务 #{{ result.id }}
              </span>
            </div>
          </template>

          <!-- 执行日志 -->
          <div v-if="result.result_log" style="margin-bottom:16px">
            <div class="section-title">执行日志</div>
            <div class="log-box">
              <div
                v-for="(step, i) in parsedLog"
                :key="i"
                :class="['log-row', step.status === 'fail' ? 'log-error' : 'log-ok']"
              >
                <span class="log-index">{{ i + 1 }}</span>
                <span class="log-action">{{ step.action }}</span>
                <span class="log-desc">{{ step.desc || step.url || step.value || '' }}</span>
                <el-tag
                  size="small"
                  :type="step.status === 'success' ? 'success' : step.status === 'fail' ? 'danger' : 'info'"
                  style="margin-left:auto; flex-shrink:0"
                >
                  {{ step.status }}
                </el-tag>
              </div>
            </div>
          </div>

          <!-- 截图 -->
          <div v-if="result.screenshots && result.screenshots.length">
            <div class="section-title">截图（{{ result.screenshots.length }} 张）</div>
            <el-scrollbar height="280px">
              <div class="screenshot-grid">
                <el-image
                  v-for="(s, i) in result.screenshots"
                  :key="i"
                  :src="`http://127.0.0.1:8000${s.screenshot_path}`"
                  :preview-src-list="result.screenshots.map(x => `http://127.0.0.1:8000${x.screenshot_path}`)"
                  :initial-index="i"
                  fit="cover"
                  class="screenshot-thumb"
                />
              </div>
            </el-scrollbar>
          </div>

          <el-empty v-if="!result.result_log && !result.screenshots?.length" description="暂无详细数据" />
        </el-card>

        <el-card class="card empty-card" v-else>
          <el-empty description="执行后结果将在这里显示" />
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { caseApi, taskApi } from '@/api/index.js'

const cases = ref([])
const selectedCaseId = ref(null)
const stepsJson = ref('')
const headless = ref(false)
const running = ref(false)
const result = ref(null)
let pollingTimer = null

// 加载用例列表
onMounted(async () => {
  try {
    const res = await caseApi.list()
    cases.value = res.cases || []
  } catch {}
})

// 选择用例后加载步骤
async function loadCase(id) {
  if (!id) { stepsJson.value = ''; return }
  try {
    const res = await caseApi.get(id)
    stepsJson.value = typeof res.steps === 'string'
      ? JSON.stringify(JSON.parse(res.steps), null, 2)
      : JSON.stringify(res.steps, null, 2)
  } catch {
    ElMessage.error('加载用例失败')
  }
}

// 执行任务
async function runTask() {
  let steps
  try {
    steps = JSON.parse(stepsJson.value)
  } catch {
    ElMessage.error('步骤 JSON 格式有误，请检查')
    return
  }

  running.value = true
  result.value = null

  try {
    const res = await taskApi.run({
      case_id: selectedCaseId.value || 0,
      steps,
      headless: headless.value,
    })
    ElMessage.success(`任务已提交，ID: ${res.task_id}`)
    // 开始轮询结果
    pollResult(res.task_id)
  } catch {
    running.value = false
  }
}

// 轮询任务状态
function pollResult(taskId) {
  pollingTimer = setInterval(async () => {
    try {
      const res = await taskApi.get(taskId)
      // status: 0=待执行 1=执行中 2=成功 3=步骤失败 4=异常崩溃
      if (res.status >= 2) {
        clearInterval(pollingTimer)
        running.value = false
        result.value = res
      }
    } catch {
      clearInterval(pollingTimer)
      running.value = false
    }
  }, 2000)
}

// 状态标签
const statusTagType = computed(() => {
  if (!result.value) return 'info'
  const map = { 2: 'success', 3: 'danger', 4: 'danger' }
  return map[result.value.status] || 'warning'
})

const statusLabel = computed(() => {
  if (!result.value) return ''
  const map = { 0: '待执行', 1: '执行中', 2: '成功', 3: '步骤失败', 4: '异常崩溃' }
  return map[result.value.status] || '未知'
})

// 解析日志 JSON
const parsedLog = computed(() => {
  if (!result.value?.result_log) return []
  try {
    const data = JSON.parse(result.value.result_log)
    return data.steps || []
  } catch {
    return []
  }
})
</script>

<style scoped>
.page { padding: 24px; }
.page-header { margin-bottom: 20px; }
.page-header h2 { font-size: 20px; color: #303133; }
.sub { font-size: 13px; color: #909399; margin-top: 4px; }

.card { height: calc(100vh - 140px); overflow-y: auto; }
.empty-card { display: flex; align-items: center; justify-content: center; }

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

.log-index {
  width: 20px;
  text-align: center;
  font-size: 11px;
  color: #c0c4cc;
  flex-shrink: 0;
}
.log-action {
  width: 90px;
  font-family: monospace;
  color: #409eff;
  flex-shrink: 0;
}
.log-desc {
  flex: 1;
  color: #606266;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.screenshot-grid {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  padding: 4px;
}
.screenshot-thumb {
  width: 120px;
  height: 80px;
  border-radius: 4px;
  border: 1px solid #e4e7ed;
  cursor: pointer;
}
</style>
