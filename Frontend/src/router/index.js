import { createRouter, createWebHistory } from 'vue-router'

const routes = [
  {
    path: '/',
    name: 'TaskRunner',
    component: () => import('../views/TaskRunner.vue'),
    meta: { title: '任务执行', icon: 'VideoPlay' },
  },
  {
    path: '/cases',
    name: 'CaseManager',
    component: () => import('../views/CaseManager.vue'),
    meta: { title: '用例管理', icon: 'Document' },
  },
  {
    path: '/tasks',
    name: 'TaskHistory',
    component: () => import('../views/TaskHistory.vue'),
    meta: { title: '执行历史', icon: 'List' },
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
