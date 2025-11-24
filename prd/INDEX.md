# Fiido 智能客服系统 - PRD 文档索引

> 版本: v2.3.3 | 更新时间: 2025-11-24

## 文档导航

本目录包含 Fiido 智能客服系统的完整产品需求文档，按照以下结构组织：

---

## 一、全局指导文档 (`01_全局指导/`)

最高规格的开发指导内容，定义系统的整体架构、功能范围和核心目标。

| 文档 | 说明 | 优先级 |
|------|------|--------|
| [prd.md](./01_全局指导/prd.md) | 主PRD文档 - 系统总体需求定义 | ⭐⭐⭐ |
| [PRD_COMPLETE_v3.0.md](./01_全局指导/PRD_COMPLETE_v3.0.md) | 完整版PRD - 详细功能说明 | ⭐⭐⭐ |
| [README.md](./01_全局指导/README.md) | 项目概述和快速入门 | ⭐⭐ |

---

## 二、约束与原则 (`02_约束与原则/`)

开发过程中必须遵守的技术限制、约束条件和设计原则。

| 文档 | 说明 | 重要性 |
|------|------|--------|
| [CONSTRAINTS_AND_PRINCIPLES.md](./02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md) | 核心约束与开发原则 | 🔴 必读 |
| [TECHNICAL_CONSTRAINTS.md](./02_约束与原则/TECHNICAL_CONSTRAINTS.md) | 技术约束详细说明 | 🔴 必读 |
| [coze.md](./02_约束与原则/coze.md) | Coze API 使用约束和规范 | 🟠 重要 |

---

## 三、技术方案 (`03_技术方案/`)

系统的技术架构设计、API 接口定义等技术实现方案。

| 文档 | 说明 | 用途 |
|------|------|------|
| [TECHNICAL_SOLUTION_v1.0.md](./03_技术方案/TECHNICAL_SOLUTION_v1.0.md) | 技术架构方案 | 架构参考 |
| [api_contract.md](./03_技术方案/api_contract.md) | API 接口契约文档 | 接口开发 |

---

## 四、任务拆解 (`04_任务拆解/`)

开发任务的详细拆解，按模块划分的具体实现任务。

| 文档 | 说明 | 模块 |
|------|------|------|
| [IMPLEMENTATION_TASKS_v1.0.md](./04_任务拆解/IMPLEMENTATION_TASKS_v1.0.md) | 总体任务拆解 | 全局 |
| [backend_tasks.md](./04_任务拆解/backend_tasks.md) | 后端开发任务 | Backend |
| [frontend_client_tasks.md](./04_任务拆解/frontend_client_tasks.md) | 用户端前端任务 | Frontend |
| [agent_workbench_tasks.md](./04_任务拆解/agent_workbench_tasks.md) | 坐席工作台任务 | Agent |
| [email_and_monitoring_tasks.md](./04_任务拆解/email_and_monitoring_tasks.md) | 邮件和监控任务 | P1 |

---

## 五、验收与记录 (`05_验收与记录/`)

验收标准、实施记录和文档总结。

| 文档 | 说明 | 用途 |
|------|------|------|
| [ACCEPTANCE_CRITERIA_v1.0.md](./05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md) | 详细验收标准 | 测试验收 |
| [implementation_notes.md](./05_验收与记录/implementation_notes.md) | 实施过程笔记 | 开发参考 |
| [PRD_REVIEW.md](./05_验收与记录/PRD_REVIEW.md) | PRD 评审记录 | 历史记录 |
| [DOCUMENTATION_SUMMARY.md](./05_验收与记录/DOCUMENTATION_SUMMARY.md) | 文档总结 | 索引参考 |
| [TESTING_GUIDE.md](./05_验收与记录/TESTING_GUIDE.md) | 测试流程规范 | 测试参考 |

---

## 六、企业部署 (`06_企业部署/`)

独立站部署和生产环境配置。

| 文档 | 说明 | 用途 |
|------|------|------|
| [ENTERPRISE_DEPLOYMENT_PRD.md](./06_企业部署/ENTERPRISE_DEPLOYMENT_PRD.md) | 企业级部署需求 | 生产部署 |
| [DEPLOYMENT_TASKS.md](./06_企业部署/DEPLOYMENT_TASKS.md) | 部署开发任务拆解 | 任务执行 |

---

## 快速参考

### 新开发者入门顺序

1. **了解项目** → `01_全局指导/README.md`
2. **理解需求** → `01_全局指导/PRD_COMPLETE_v3.0.md`
3. **学习约束** → `02_约束与原则/CONSTRAINTS_AND_PRINCIPLES.md`
4. **查看任务** → `04_任务拆解/IMPLEMENTATION_TASKS_v1.0.md`
5. **接口开发** → `03_技术方案/api_contract.md`

### 按角色查阅

- **后端开发**: `04_任务拆解/backend_tasks.md` + `03_技术方案/api_contract.md`
- **前端开发**: `04_任务拆解/frontend_client_tasks.md` + `04_任务拆解/agent_workbench_tasks.md`
- **测试人员**: `05_验收与记录/ACCEPTANCE_CRITERIA_v1.0.md`
- **产品经理**: `01_全局指导/PRD_COMPLETE_v3.0.md`

### 关键约束速查

| 约束类型 | 核心要点 |
|----------|----------|
| Coze API | conversation_id 由 Coze 自动生成，不可手动创建 |
| 会话隔离 | 必须使用 session_name 实现 JWT 级别隔离 |
| 状态机 | bot_active → pending_manual → manual_live → bot_active |
| 人工接管 | 人工接管期间必须阻止 AI 对话 |

---

## 版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| v2.3.4 | 2025-11-24 | 文档整理：新增文档导航和 GitHub 提交规范 |
| v2.3.3 | 2025-11-24 | 文档整理：移动过程文档和归档旧版本 |
| v2.4.0 | 2025-11-23 | 文档重新组织，添加索引导航 |
| v2.3.0 | 2025-11-22 | P3 增强功能实现 |
| v2.2.0 | 2025-11-21 | P1 邮件服务实现 |
| v2.1.0 | 2025-11-20 | P0 核心功能完成 |

---

## 文档维护说明

1. **原则**: 所有原始文档内容保持不变，仅做组织结构调整
2. **更新**: 新功能开发时，在对应分类目录下添加或更新文档
3. **索引**: 每次添加新文档后，更新本索引文件

---

## 归档文档

以下文档已移至 `../docs/` 目录归档：

- **过程性文档** (`docs/process/`) - 15 个文件
  - P0 开发过程报告和审查报告
  - 会话隔离实现历程和技术总结
  - 模块审查报告和测试指南

- **旧版本文档** (`docs/archive/prd_root_old/`) - 17 个文件
  - prd/ 根目录的旧版本文档（已在子目录中有更新版本）
  - 归档时间: 2025-11-24

