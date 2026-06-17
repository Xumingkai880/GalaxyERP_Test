<template>
  <el-container class="layout">
    <!-- 侧边栏 -->
    <el-aside width="200px" class="sidebar">
      <div class="logo">
        <el-icon size="22"><Monitor /></el-icon>
        <span>GalaxyERP 测试平台</span>
      </div>
      <el-menu
        :default-active="$route.path"
        router
        background-color="#1e2330"
        text-color="#c0c4cc"
        active-text-color="#409eff"
      >
        <el-menu-item
          v-for="item in menuItems"
          :key="item.path"
          :index="item.path"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.title }}</span>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <!-- 主内容区 -->
    <el-main class="main">
      <router-view />
    </el-main>
  </el-container>
</template>

<script setup>
const menuItems = [
  { path: '/',       title: '任务执行', icon: 'VideoPlay' },
  { path: '/cases',  title: '用例管理', icon: 'Document'  },
  { path: '/tasks',  title: '执行历史', icon: 'List'      },
]
</script>

<style>
* { box-sizing: border-box; margin: 0; padding: 0; }
html, body, #app { height: 100%; }
</style>

<style scoped>
.layout { height: 100vh; }

.sidebar {
  background: #1e2330;
  display: flex;
  flex-direction: column;
}

.logo {
  height: 56px;
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 0 20px;
  color: #fff;
  font-size: 14px;
  font-weight: 600;
  border-bottom: 1px solid #2d3347;
  flex-shrink: 0;
}

.el-menu { border-right: none; flex: 1; }

.main {
  background: #f5f7fa;
  overflow-y: auto;
}
</style>
