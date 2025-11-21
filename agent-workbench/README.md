# Fiido 坐席工作台

基于 Vue 3 + TypeScript + Vite 的智能客服坐席工作台。

## ✨ 特性

- ✅ **现代化技术栈** - Vue 3 + TypeScript + Pinia + Vue Router
- ✅ **独立运行** - 独立于用户前端，运行在端口 5174
- ✅ **API 代理** - 自动代理 `/api` 请求到后端 8000 端口
- ✅ **类型安全** - 完整的 TypeScript 类型定义

## 🚀 快速开始

### 安装依赖

```bash
npm install
```

### 启动开发服务器

```bash
npm run dev
```

访问 `http://localhost:5174/`

### 构建生产版本

```bash
npm run build
```

## 📁 项目结构

```
agent-workbench/
├── src/
│   ├── views/          # 页面组件
│   ├── components/     # 通用组件
│   ├── stores/         # Pinia 状态管理
│   ├── api/            # API 接口
│   ├── types/          # TypeScript 类型定义
│   ├── assets/         # 静态资源
│   ├── App.vue         # 根组件
│   └── main.ts         # 应用入口
├── public/             # 公共资源
├── vite.config.ts      # Vite 配置
├── tsconfig.json       # TypeScript 配置
└── package.json        # 依赖配置
```

## 🔧 配置说明

### Vite 配置 (vite.config.ts)

- **端口**: 5174（独立于用户前端的 5173）
- **API 代理**: `/api` 请求自动转发到 `http://localhost:8000`
- **路径别名**: `@` 指向 `src` 目录

## 🛠️ 技术栈

- **Vue 3** - 渐进式 JavaScript 框架
- **TypeScript** - 类型安全的 JavaScript
- **Vite** - 下一代前端构建工具
- **Pinia** - Vue 官方状态管理库
- **Vue Router** - Vue 官方路由管理器
- **Axios** - HTTP 客户端
- **Marked** - Markdown 解析器

## 📝 开发计划

- [x] P0-10: 创建工作台项目 ✅
- [x] P0-11: 实现登录认证 ✅
- [ ] P0-12: 实现会话列表
- [ ] P0-13: 实现接入操作
- [ ] P0-14: 实现坐席聊天
- [ ] P0-15: 实现释放操作

## 🎯 已完成功能

### P0-11: 登录认证 (2025-11-21)

**功能列表**:
- ✅ 登录页面（`/login`）- 坐席ID + 姓名登录
- ✅ 工作台首页（`/dashboard`）- 显示坐席信息
- ✅ 路由守卫 - 未登录自动跳转登录页
- ✅ 会话持久化 - 刷新页面保持登录状态
- ✅ 退出登录 - 清除会话并跳转

**技术实现**:
- 使用 Pinia Store 管理坐席状态
- localStorage 持久化登录信息
- Vue Router 导航守卫保护路由
- TypeScript 类型安全

## 📄 许可证

MIT License

---

**创建日期**: 2025-11-21
**当前版本**: v0.1.0
**维护者**: Claude Code
