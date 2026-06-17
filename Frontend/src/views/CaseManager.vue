<template>
  <div class="page">
    <div class="page-header">
      <h2>用例管理</h2>
      <el-button type="primary" @click="openDialog()">
        <el-icon><Plus /></el-icon> 新增用例
      </el-button>
    </div>

    <!-- 搜索栏 -->
    <el-card class="search-card">
      <el-input
        v-model="keyword"
        placeholder="搜索用例名称..."
        clearable
        style="width: 300px"
        @input="filterCases"
      >
        <template #prefix><el-icon><Search /></el-icon></template>
      </el-input>
    </el-card>

    <!-- 用例表格 -->
    <el-card>
      <el-table :data="filteredCases" stripe v-loading="loading" style="width:100%">
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column prop="case_name" label="用例名称" min-width="160" />
        <el-table-column prop="browser" label="浏览器" width="90" />
        <el-table-column label="步骤预览" min-width="260">
          <template #default="{ row }">
            <el-text truncated class="steps-preview">{{ stepsPreview(row.steps) }}</el-text>
          </template>
        </el-table-column>
        <el-table-column prop="create_time" label="创建时间" width="160" />
        <el-table-column label="操作" width="150" fixed="right">
          <template #default="{ row }">
            <el-button text type="primary" @click="openDialog(row)">编辑</el-button>
            <el-button text type="danger" @click="deleteCase(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <!-- 新增/编辑弹窗 -->
    <el-dialog
      v-model="dialogVisible"
      :title="editId ? '编辑用例' : '新增用例'"
      width="640px"
      destroy-on-close
    >
      <el-form :model="form" :rules="rules" ref="formRef" label-width="90px">
        <el-form-item label="用例名称" prop="case_name">
          <el-input v-model="form.case_name" placeholder="例：登录验证" />
        </el-form-item>

        <el-form-item label="步骤 JSON" prop="steps">
          <el-input
            v-model="form.steps"
            type="textarea"
            :rows="10"
            placeholder='[
  {"action": "open_url", "url": "https://mes.nat.zhsvr.com"},
  {"action": "login", "role": "supply"}
]'
          />
        </el-form-item>

        <el-form-item label="浏览器">
          <el-select v-model="form.browser">
            <el-option label="Chrome" value="chrome" />
            <el-option label="Chrome（无头）" value="chrome-headless" />
          </el-select>
        </el-form-item>
      </el-form>

      <template #footer>
        <el-button @click="dialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="saveCase">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { caseApi } from '@/api/index.js'

const loading = ref(false)
const saving = ref(false)
const cases = ref([])
const keyword = ref('')
const dialogVisible = ref(false)
const editId = ref(null)
const formRef = ref()

const form = ref({
  case_name: '',
  steps: '',
  browser: 'chrome',
})

const rules = {
  case_name: [{ required: true, message: '请输入用例名称', trigger: 'blur' }],
  steps: [
    { required: true, message: '请输入步骤 JSON', trigger: 'blur' },
    {
      validator: (_, val, cb) => {
        try { JSON.parse(val); cb() }
        catch { cb(new Error('JSON 格式有误')) }
      },
      trigger: 'blur',
    },
  ],
}

const filteredCases = computed(() => {
  if (!keyword.value) return cases.value
  return cases.value.filter(c =>
    c.case_name.includes(keyword.value)
  )
})

function stepsPreview(steps) {
  try {
    const arr = typeof steps === 'string' ? JSON.parse(steps) : steps
    return arr.map(s => s.action).join(' → ')
  } catch { return steps }
}

async function fetchCases() {
  loading.value = true
  try {
    const res = await caseApi.list()
    cases.value = res.cases || []
  } finally {
    loading.value = false
  }
}

function openDialog(row = null) {
  editId.value = row?.id || null
  form.value = {
    case_name: row?.case_name || '',
    steps: row
      ? (typeof row.steps === 'string' ? JSON.stringify(JSON.parse(row.steps), null, 2) : JSON.stringify(row.steps, null, 2))
      : '',
    browser: row?.browser || 'chrome',
  }
  dialogVisible.value = true
}

async function saveCase() {
  await formRef.value.validate()
  saving.value = true
  try {
    if (editId.value) {
      await caseApi.update(editId.value, form.value)
      ElMessage.success('用例已更新')
    } else {
      await caseApi.create(form.value)
      ElMessage.success('用例已创建')
    }
    dialogVisible.value = false
    await fetchCases()
  } finally {
    saving.value = false
  }
}

async function deleteCase(id) {
  await ElMessageBox.confirm('确定删除这条用例？', '确认', { type: 'warning' })
  await caseApi.remove(id)
  ElMessage.success('已删除')
  await fetchCases()
}

onMounted(fetchCases)
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
.search-card { margin-bottom: 16px; }
.steps-preview { font-size: 12px; color: #909399; }
</style>
