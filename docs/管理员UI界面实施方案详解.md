# 管理员UI界面实施方案详解

> **文档版本**: v1.0
> **创建时间**: 2025-11-25
> **功能模块**: 管理员坐席管理UI界面（P1任务）
> **依赖**: 管理员后端API v3.1.3（已完成）

---

## 📋 目录

1. [为什么需要这个功能？](#1-为什么需要这个功能)
2. [技术原理是什么？](#2-技术原理是什么)
3. [需要什么工具和配置？](#3-需要什么工具和配置)
4. [如何实现？](#4-如何实现)
5. [最终效果是什么？](#5-最终效果是什么)
6. [实施时间估算](#6-实施时间估算)
7. [常见问题FAQ](#7-常见问题faq)

---

## 1. 为什么需要这个功能？

### 1.1 当前问题分析

**问题现状**：
- ✅ 后端管理员API已完成（7个接口，测试通过）
- ❌ 前端UI界面完全缺失
- ❌ 管理员无法通过界面管理坐席
- ❌ 只能通过API或数据库直接操作

**实际场景演示**：

```
场景1：管理员想创建新坐席
现状：❌ 必须用curl命令或Postman调用API
期望：✅ 在UI界面点击"创建坐席"按钮，填写表单

场景2：管理员想查看所有坐席列表
现状：❌ 必须调用GET /api/agents接口查看JSON
期望：✅ 在UI界面看到格式化的表格，支持搜索筛选

场景3：坐席想修改自己的密码
现状：❌ 必须请求管理员或直接调用API
期望：✅ 在个人中心点击"修改密码"，输入旧密码和新密码
```

### 1.2 业务价值

| 价值点 | 当前状态 | 改进后 |
|--------|---------|--------|
| **管理效率** | 使用API工具，每次操作需5-10分钟 | UI操作，每次操作30秒 |
| **易用性** | 需要技术背景，普通管理员无法操作 | 任何管理员都能使用 |
| **安全性** | 直接暴露API细节，容易出错 | UI层验证，降低操作风险 |
| **审计** | 无UI操作记录 | 可追踪UI操作日志 |

### 1.3 用户群体

- **主要用户**：系统管理员（admin角色）
- **次要用户**：所有坐席（修改自己的密码和资料）
- **预期规模**：1-3个管理员，10-50个坐席

---

## 2. 技术原理是什么？

### 2.1 核心概念

**管理员UI = Vue 3 前端 + 后端API + JWT权限控制**

```
┌─────────────────────────────────────────────────┐
│             管理员UI界面                          │
│  ┌─────────────────────────────────────────┐   │
│  │   AdminManagement.vue (管理员主页面)     │   │
│  │   ├── AgentTable (坐席列表表格)         │   │
│  │   ├── CreateAgentDialog (创建对话框)    │   │
│  │   ├── EditAgentDialog (编辑对话框)      │   │
│  │   └── ResetPasswordDialog (重置密码)    │   │
│  └─────────────────────────────────────────┘   │
│                      ↓ HTTP请求                  │
│  ┌─────────────────────────────────────────┐   │
│  │   后端API (backend.py)                   │   │
│  │   ├── GET /api/agents (坐席列表)        │   │
│  │   ├── POST /api/agents (创建坐席)       │   │
│  │   ├── PUT /api/agents/{id} (修改)       │   │
│  │   ├── DELETE /api/agents/{id} (删除)    │   │
│  │   └── POST /api/agents/{id}/reset (重置)│   │
│  └─────────────────────────────────────────┘   │
│                      ↓                           │
│  ┌─────────────────────────────────────────┐   │
│  │   JWT权限验证                             │   │
│  │   ├── require_admin() - 管理员专用      │   │
│  │   └── require_agent() - 任何登录用户    │   │
│  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────┘
```

### 2.2 工作流程

#### 流程1：管理员查看坐席列表

```
1. 用户访问 /admin/agents 页面
   ↓
2. 路由守卫检查：isLoggedIn && role=admin
   ├─ 是 → 进入页面
   └─ 否 → 跳转到 /dashboard 或 /login
   ↓
3. 页面加载时调用 fetchAgents()
   ↓
4. 发送请求：GET /api/agents + Authorization: Bearer <token>
   ↓
5. 后端验证：require_admin()
   ├─ Token有效 && role=admin → 返回坐席列表
   └─ 验证失败 → 返回 401/403
   ↓
6. 前端渲染表格，显示坐席信息
```

#### 流程2：管理员创建坐席

```
1. 点击"创建坐席"按钮
   ↓
2. 弹出 CreateAgentDialog 对话框
   ↓
3. 填写表单：用户名、密码、姓名、角色等
   ↓
4. 前端验证：
   - 用户名：3-20字符，字母数字下划线
   - 密码：至少8字符，含字母和数字
   - 姓名：1-50字符
   ↓
5. 点击"确定"，发送请求：
   POST /api/agents + 表单数据 + Authorization: Bearer <token>
   ↓
6. 后端验证 + 创建坐席
   ├─ 成功 → 返回 200
   └─ 失败 → 返回 400/409（用户名已存在）
   ↓
7. 前端处理响应：
   ├─ 成功 → 关闭对话框，刷新列表，显示成功提示
   └─ 失败 → 显示错误信息
```

### 2.3 权限控制机制

**三层权限控制**：

```typescript
// 第一层：路由守卫（router/index.ts）
router.beforeEach((to, from, next) => {
  if (to.meta.requiresAdmin && agent.role !== 'admin') {
    next('/dashboard')  // 非管理员无法访问
  }
})

// 第二层：Pinia Store（stores/adminStore.ts）
async function deleteAgent(username: string) {
  const token = localStorage.getItem('access_token')
  // 每次请求都带上Token
  await axios.delete(`/api/agents/${username}`, {
    headers: { Authorization: `Bearer ${token}` }
  })
}

// 第三层：后端API（backend.py）
@app.delete("/api/agents/{username}")
async def delete_agent(
    username: str,
    admin: Dict = Depends(require_admin)  # ← 强制验证管理员
):
    # 只有通过验证的管理员才能执行
```

**权限矩阵**：

| 功能 | 管理员(admin) | 普通坐席(agent) | 未登录 |
|------|--------------|----------------|--------|
| 查看坐席列表 | ✅ | ❌ | ❌ |
| 创建坐席 | ✅ | ❌ | ❌ |
| 修改任意坐席 | ✅ | ❌ | ❌ |
| 删除坐席 | ✅ | ❌ | ❌ |
| 重置坐席密码 | ✅ | ❌ | ❌ |
| 修改自己密码 | ✅ | ✅ | ❌ |
| 修改自己资料 | ✅ | ✅ | ❌ |

---

## 3. 需要什么工具和配置？

### 3.1 开发环境

**已有环境**（无需新安装）：
- ✅ Node.js 16+
- ✅ Vue 3.5
- ✅ TypeScript 5.7
- ✅ Element Plus（UI组件库）
- ✅ Pinia（状态管理）
- ✅ Vue Router（路由）
- ✅ Axios（HTTP客户端）

### 3.2 项目结构

```
agent-workbench/
├── src/
│   ├── views/
│   │   ├── Login.vue                    ✅ 已有
│   │   ├── Dashboard.vue                ✅ 已有
│   │   └── AdminManagement.vue          ❌ 需新建（约300行）
│   ├── components/
│   │   ├── SessionList.vue              ✅ 已有
│   │   ├── QuickReplies.vue             ✅ 已有
│   │   ├── admin/
│   │   │   ├── AgentTable.vue           ❌ 需新建（约200行）
│   │   │   ├── CreateAgentDialog.vue    ❌ 需新建（约150行）
│   │   │   ├── EditAgentDialog.vue      ❌ 需新建（约150行）
│   │   │   ├── ResetPasswordDialog.vue  ❌ 需新建（约100行）
│   │   │   ├── ChangePasswordDialog.vue ❌ 需新建（约120行）
│   │   │   └── ProfileDialog.vue        ❌ 需新建（约100行）
│   ├── stores/
│   │   ├── agentStore.ts                ✅ 已有
│   │   ├── sessionStore.ts              ✅ 已有
│   │   └── adminStore.ts                ❌ 需新建（约200行）
│   ├── router/
│   │   └── index.ts                     🔄 需修改（添加路由守卫）
│   └── types/
│       └── index.ts                     🔄 需修改（添加类型定义）
```

**总计新增文件**: 7个Vue组件 + 1个Store文件
**总计代码量**: 约1,200行

### 3.3 依赖包

**无需新安装**，所有依赖已存在：
```json
{
  "vue": "^3.5.13",
  "vue-router": "^4.5.0",
  "pinia": "^2.3.0",
  "element-plus": "^2.9.1",
  "axios": "^1.7.9",
  "typescript": "^5.7.2"
}
```

---

## 4. 如何实现？

### 4.1 实施步骤

#### **第1步：创建类型定义** (15分钟)

```typescript
// src/types/index.ts (新增)

/** 坐席角色 */
export type AgentRole = 'admin' | 'agent'

/** 坐席状态 */
export type AgentStatus = 'online' | 'offline' | 'busy'

/** 坐席信息 */
export interface Agent {
  id: string
  username: string
  name: string
  role: AgentRole
  status: AgentStatus
  max_sessions: number
  created_at: number
  last_login: number
  avatar_url?: string
}

/** 创建坐席请求 */
export interface CreateAgentRequest {
  username: string
  password: string
  name: string
  role: AgentRole
  max_sessions?: number
  avatar_url?: string
}

/** 修改坐席请求 */
export interface UpdateAgentRequest {
  name?: string
  role?: AgentRole
  status?: AgentStatus
  max_sessions?: number
  avatar_url?: string
}

/** 修改密码请求 */
export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

/** 修改资料请求 */
export interface UpdateProfileRequest {
  name?: string
  avatar_url?: string
}
```

#### **第2步：创建管理员Store** (30分钟)

```typescript
// src/stores/adminStore.ts (新建)

import { defineStore } from 'pinia'
import { ref } from 'vue'
import axios from 'axios'
import type { Agent, CreateAgentRequest, UpdateAgentRequest } from '@/types'

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000'

export const useAdminStore = defineStore('admin', () => {
  const agents = ref<Agent[]>([])
  const loading = ref(false)
  const error = ref<string | null>(null)

  // 获取Authorization Header
  function getAuthHeader() {
    const token = localStorage.getItem('access_token')
    return { Authorization: `Bearer ${token}` }
  }

  // 获取坐席列表
  async function fetchAgents(params?: { role?: string; status?: string }) {
    loading.value = true
    error.value = null
    try {
      const response = await axios.get(`${API_BASE}/api/agents`, {
        headers: getAuthHeader(),
        params
      })
      agents.value = response.data.data.items
    } catch (e: any) {
      error.value = e.response?.data?.detail || '获取坐席列表失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 创建坐席
  async function createAgent(data: CreateAgentRequest) {
    loading.value = true
    error.value = null
    try {
      await axios.post(`${API_BASE}/api/agents`, data, {
        headers: getAuthHeader()
      })
      await fetchAgents()
    } catch (e: any) {
      error.value = e.response?.data?.detail || '创建坐席失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 修改坐席
  async function updateAgent(username: string, data: UpdateAgentRequest) {
    loading.value = true
    error.value = null
    try {
      await axios.put(`${API_BASE}/api/agents/${username}`, data, {
        headers: getAuthHeader()
      })
      await fetchAgents()
    } catch (e: any) {
      error.value = e.response?.data?.detail || '修改坐席失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 删除坐席
  async function deleteAgent(username: string) {
    loading.value = true
    error.value = null
    try {
      await axios.delete(`${API_BASE}/api/agents/${username}`, {
        headers: getAuthHeader()
      })
      await fetchAgents()
    } catch (e: any) {
      error.value = e.response?.data?.detail || '删除坐席失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  // 重置密码
  async function resetPassword(username: string, newPassword: string) {
    loading.value = true
    error.value = null
    try {
      await axios.post(
        `${API_BASE}/api/agents/${username}/reset-password`,
        { new_password: newPassword },
        { headers: getAuthHeader() }
      )
    } catch (e: any) {
      error.value = e.response?.data?.detail || '重置密码失败'
      throw e
    } finally {
      loading.value = false
    }
  }

  return {
    agents,
    loading,
    error,
    fetchAgents,
    createAgent,
    updateAgent,
    deleteAgent,
    resetPassword
  }
})
```

#### **第3步：更新路由配置** (15分钟)

```typescript
// src/router/index.ts (修改)

import { createRouter, createWebHistory } from 'vue-router'
import { useAgentStore } from '@/stores/agentStore'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/Login.vue'),
      meta: { requiresAuth: false }
    },
    {
      path: '/dashboard',
      name: 'Dashboard',
      component: () => import('@/views/Dashboard.vue'),
      meta: { requiresAuth: true }
    },
    // ← 新增：管理员页面路由
    {
      path: '/admin/agents',
      name: 'AdminManagement',
      component: () => import('@/views/AdminManagement.vue'),
      meta: { requiresAuth: true, requiresAdmin: true }
    },
    {
      path: '/',
      redirect: '/dashboard'
    }
  ]
})

// Navigation guard (扩展)
router.beforeEach((to, _from, next) => {
  const agentStore = useAgentStore()

  // 检查是否需要管理员权限
  if (to.meta.requiresAdmin) {
    if (!agentStore.isLoggedIn) {
      next('/login')
      return
    }
    if (agentStore.agent?.role !== 'admin') {
      // 非管理员无法访问管理页面
      ElMessage.warning('需要管理员权限')
      next('/dashboard')
      return
    }
  }

  // 检查是否需要认证
  if (to.meta.requiresAuth && !agentStore.isLoggedIn) {
    next('/login')
    return
  }

  // 已登录访问登录页，跳转到工作台
  if (to.path === '/login' && agentStore.isLoggedIn) {
    next('/dashboard')
    return
  }

  next()
})

export default router
```

#### **第4步：创建管理员主页面** (1小时)

创建 `src/views/AdminManagement.vue`（约300行代码），包含：
- 顶部工具栏（创建按钮、搜索框、筛选器）
- 坐席列表表格
- 分页组件
- 对话框容器

详细代码见实施时提供。

#### **第5步：创建UI组件** (2小时)

按顺序创建6个对话框组件：
1. `CreateAgentDialog.vue` - 创建坐席对话框
2. `EditAgentDialog.vue` - 编辑坐席对话框
3. `ResetPasswordDialog.vue` - 重置密码对话框
4. `ChangePasswordDialog.vue` - 修改密码对话框
5. `ProfileDialog.vue` - 修改资料对话框
6. `AgentTable.vue` - 坐席列表表格（可选，集成到主页面）

每个组件约100-150行。

#### **第6步：集成到Dashboard导航** (30分钟)

在 `Dashboard.vue` 顶部添加管理员菜单：

```vue
<!-- Dashboard.vue 顶部菜单 -->
<template>
  <div class="dashboard-header">
    <div class="left">
      <span class="title">Fiido 坐席工作台</span>
    </div>
    <div class="right">
      <!-- ← 新增：管理员菜单 -->
      <el-dropdown v-if="agentStore.agent?.role === 'admin'" style="margin-right: 20px">
        <el-button type="primary">
          <el-icon><Setting /></el-icon> 管理
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="router.push('/admin/agents')">
              <el-icon><User /></el-icon> 坐席管理
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>

      <!-- 原有的个人菜单 -->
      <el-dropdown>
        <el-button>
          <el-icon><Avatar /></el-icon> {{ agentStore.agent?.name }}
        </el-button>
        <template #dropdown>
          <el-dropdown-menu>
            <el-dropdown-item @click="showChangePasswordDialog = true">
              <el-icon><Lock /></el-icon> 修改密码
            </el-dropdown-item>
            <el-dropdown-item @click="showProfileDialog = true">
              <el-icon><Edit /></el-icon> 个人资料
            </el-dropdown-item>
            <el-dropdown-item divided @click="handleLogout">
              <el-icon><SwitchButton /></el-icon> 退出登录
            </el-dropdown-item>
          </el-dropdown-menu>
        </template>
      </el-dropdown>
    </div>
  </div>
</template>
```

#### **第7步：测试验证** (1小时)

创建测试脚本验证所有功能：
```bash
# tests/test_admin_ui.sh
# 1. 管理员登录
# 2. 访问 /admin/agents
# 3. 测试创建坐席
# 4. 测试修改坐席
# 5. 测试删除坐席
# 6. 测试重置密码
# 7. 普通坐席登录
# 8. 尝试访问 /admin/agents（应被拒绝）
# 9. 测试修改自己密码
# 10. 测试修改自己资料
```

---

## 5. 最终效果是什么？

### 5.1 Before/After 对比

#### Before（当前状态）

```
管理员想创建新坐席：
1. 打开Postman
2. 设置URL: POST http://localhost:8000/api/agents
3. 设置Header: Authorization: Bearer <token>
4. 编写JSON:
   {
     "username": "agent005",
     "password": "password123",
     "name": "客服小赵",
     "role": "agent",
     "max_sessions": 5
   }
5. 发送请求
6. 检查响应状态

耗时：3-5分钟
技能要求：熟悉API工具
错误风险：高（JSON格式、字段验证）
```

#### After（实施后）

```
管理员想创建新坐席：
1. 点击"创建坐席"按钮
2. 在对话框中填写表单：
   - 用户名：agent005
   - 密码：password123
   - 姓名：客服小赵
   - 角色：坐席
   - 最大会话数：5
3. 点击"确定"
4. 看到成功提示

耗时：30秒
技能要求：无
错误风险：低（前端自动验证）
```

### 5.2 UI界面预览

#### 管理员主页面

```
┌──────────────────────────────────────────────────────┐
│  Fiido 坐席工作台        [管理▼]  [头像] 管理员      │
├──────────────────────────────────────────────────────┤
│                                                       │
│  [+ 创建坐席]  [搜索框: 用户名/姓名]  [角色▼] [状态▼]│
│                                                       │
│  ┌────────────────────────────────────────────────┐ │
│  │ 用户名    │ 姓名    │ 角色  │ 状态   │ 操作    │ │
│  ├────────────────────────────────────────────────┤ │
│  │ admin     │ 管理员  │ admin │ online │ [编辑]  │ │
│  │ agent001  │ 客服A   │ agent │ online │ [编辑]  │ │
│  │ agent002  │ 客服B   │ agent │ busy   │ [编辑]  │ │
│  │           │         │       │        │ [重置]  │ │
│  │           │         │       │        │ [删除]  │ │
│  └────────────────────────────────────────────────┘ │
│                                                       │
│  [← 上一页]  第1/3页  [下一页 →]                     │
└──────────────────────────────────────────────────────┘
```

#### 创建坐席对话框

```
┌──────────────────────────────────┐
│   创建坐席                    [×] │
├──────────────────────────────────┤
│                                   │
│  用户名 *   [agent005________]    │
│            (3-20字符,字母数字_)   │
│                                   │
│  密码 *     [**************]      │
│            (至少8字符,含字母数字) │
│                                   │
│  姓名 *     [客服小赵________]    │
│            (1-50字符)             │
│                                   │
│  角色 *     [坐席 ▼]              │
│            (admin/agent)          │
│                                   │
│  最大会话数 [5___]                │
│            (1-100)                │
│                                   │
│  头像URL    [/avatars/zhao.png]   │
│            (可选)                 │
│                                   │
│       [取消]      [确定]          │
└──────────────────────────────────┘
```

### 5.3 验证标准

**功能验收**：

| 功能 | 验收标准 |
|------|---------|
| ✅ 管理员访问 | admin角色可以访问 /admin/agents |
| ✅ 权限拦截 | agent角色访问时跳转回Dashboard并提示 |
| ✅ 坐席列表 | 显示所有坐席，包含完整字段 |
| ✅ 搜索功能 | 按用户名/姓名实时搜索 |
| ✅ 筛选功能 | 按角色、状态筛选 |
| ✅ 创建坐席 | 表单验证通过后成功创建 |
| ✅ 编辑坐席 | 可修改姓名、角色等字段 |
| ✅ 删除坐席 | 二次确认后成功删除 |
| ✅ 重置密码 | 输入新密码后重置成功 |
| ✅ 修改密码 | 验证旧密码后修改成功 |
| ✅ 修改资料 | 修改姓名/头像成功 |
| ✅ 错误处理 | 所有失败情况显示友好提示 |

**性能验收**：

- 页面加载时间 < 1秒
- 列表渲染100条数据无卡顿
- 对话框打开/关闭动画流畅
- API响应超时3秒后提示

**兼容性验收**：

- Chrome 100+
- Firefox 100+
- Edge 100+
- 分辨率支持：1280px+

---

## 6. 实施时间估算

### 6.1 开发阶段

| 阶段 | 任务 | 预估工时 | 累计工时 |
|------|------|---------|---------|
| **准备** | 阅读约束文档、API文档 | 0.5h | 0.5h |
| **第1步** | 创建类型定义 | 0.25h | 0.75h |
| **第2步** | 创建adminStore | 0.5h | 1.25h |
| **第3步** | 更新路由配置 | 0.25h | 1.5h |
| **第4步** | 创建AdminManagement主页面 | 1h | 2.5h |
| **第5步** | 创建6个UI组件 | 2h | 4.5h |
| **第6步** | 集成Dashboard导航 | 0.5h | 5h |
| **第7步** | 测试验证 | 1h | 6h |
| **文档** | 更新PRD和API文档 | 0.5h | 6.5h |

**总计**: 约 6.5 小时（1个工作日）

### 6.2 里程碑

| 里程碑 | 完成标志 | 预计时间 |
|--------|---------|---------|
| M1 | Store和路由配置完成 | +1.5h |
| M2 | 主页面和表格完成 | +2.5h |
| M3 | 所有对话框组件完成 | +4.5h |
| M4 | 集成和测试完成 | +6h |
| M5 | 文档更新完成 | +6.5h |

---

## 7. 常见问题FAQ

### Q1: 为什么不直接在Dashboard中添加管理功能？

**A**: 分离关注点，便于维护：
- Dashboard专注于会话管理（坐席日常工作）
- AdminManagement专注于坐席管理（管理员工作）
- 代码更清晰，职责单一
- 权限控制更明确

### Q2: 普通坐席能看到管理菜单吗？

**A**: 不能。通过3层控制确保：
1. UI层：`v-if="agent.role === 'admin'"` 隐藏菜单
2. 路由层：`requiresAdmin` 守卫拦截
3. API层：`require_admin()` 拒绝请求

### Q3: 如果管理员删除自己会怎样？

**A**: 后端API有业务约束（约束6.2）：
- 不能删除最后一个管理员
- 不能删除自己
- 不能删除有活跃会话的坐席
- 前端应在删除前调用检查接口

### Q4: 坐席列表会自动刷新吗？

**A**: 不会自动刷新（避免干扰操作）：
- 创建/编辑/删除后手动刷新
- 可以点击"刷新"按钮
- 未来可添加定时刷新（可选）

### Q5: 如何处理并发操作冲突？

**A**: 乐观锁机制：
- 编辑时显示最新数据
- 保存时后端检查版本号
- 冲突时提示用户刷新重试

### Q6: 密码强度验证规则是什么？

**A**: 前后端双重验证：
- 前端：实时提示（至少8字符，含字母和数字）
- 后端：`validate_password()` 强制验证
- 一致性：前后端规则完全相同

### Q7: 头像URL如何处理？

**A**: 当前阶段简单处理：
- 输入相对路径（如 `/avatars/user.png`）
- 前端拼接完整URL显示
- 未来可升级为文件上传

### Q8: 如何测试权限控制？

**A**: 测试步骤：
```bash
# 1. 管理员登录
curl -X POST /api/agent/login -d '{"username":"admin","password":"admin123"}'

# 2. 访问管理页面（应成功）
访问 http://localhost:5174/admin/agents

# 3. 普通坐席登录
curl -X POST /api/agent/login -d '{"username":"agent001","password":"agent123"}'

# 4. 访问管理页面（应跳转到Dashboard）
访问 http://localhost:5174/admin/agents

# 5. 直接调用API（应返回403）
curl -X GET /api/agents -H "Authorization: Bearer <agent001_token>"
```

### Q9: 如何回滚？

**A**: Git版本控制：
```bash
# 查看提交历史
git log --oneline

# 回滚到上一版本
git reset --hard HEAD~1

# 或回滚到特定commit
git reset --hard <commit_hash>

# 重新启动前端
cd agent-workbench && npm run dev
```

### Q10: 如何扩展到更多管理功能？

**A**: 扩展路径：
1. 在 `AdminManagement.vue` 中添加Tabs
2. 创建新组件（如 `AuditLog.vue`）
3. 添加对应的Store方法
4. 添加API路由（如需要）

---

## 📚 参考文档

- **PRD文档**: `prd/04_任务拆解/admin_management_tasks.md`
- **API文档**: `prd/03_技术方案/api_contract.md`
- **约束文档**: `prd/02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
- **业务需求**: `codex.md`
- **开发规范**: `CLAUDE.md`

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-25
**文档版本**: v1.0
