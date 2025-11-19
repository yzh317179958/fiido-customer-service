# 项目结构说明

最终整理后的专业项目结构

---

## 目录树

```
fiido-customer-service/
├── README.md                   # 项目主文档
├── requirements.txt            # Python 依赖
├── .env                        # 环境变量配置
├── private_key.pem             # OAuth 私钥
│
├── backend.py                  # FastAPI 后端主程序
├── index2.html                 # 前端页面
├── fiido2.png                  # 客服头像
│
├── src/                        # 源代码模块
│   ├── __init__.py
│   ├── jwt_signer.py           # JWT 签名工具
│   └── oauth_token_manager.py  # OAuth Token 管理器
│
├── tests/                      # 测试脚本
│   ├── test_simple.py          # 简单会话隔离测试 (推荐)
│   ├── test_session_name.py    # 完整会话隔离测试
│   └── test_session_isolation.py # 旧版测试 (已废弃)
│
├── docs/                       # 文档
│   ├── 配置指南.md              # 环境配置说明
│   ├── 会话隔离实现历程.md      # 实现过程记录
│   └── SDK使用示例.md           # Coze SDK 使用指南
│
└── archive/                    # 归档文件
    ├── backend_backup_*.py     # 代码备份
    ├── *.log                   # 日志文件
    └── *.html                  # 测试页面
```

---

## 核心文件说明

### 后端代码

| 文件 | 说明 | 关键功能 |
|------|------|---------|
| `backend.py` | FastAPI 主程序 | 聊天接口、会话隔离 |
| `src/jwt_signer.py` | JWT 签名工具 | 生成带 session_name 的 JWT |
| `src/oauth_token_manager.py` | Token 管理器 | 按 session 缓存 Token |

### 前端文件

| 文件 | 说明 |
|------|------|
| `index2.html` | 前端聊天界面 |
| `fiido2.png` | 客服头像图片 |

### 测试文件

| 文件 | 用途 | 推荐度 |
|------|------|-------|
| `tests/test_simple.py` | 快速测试会话隔离 | ⭐⭐⭐ 推荐 |
| `tests/test_session_name.py` | 完整功能测试 | ⭐⭐ 可选 |
| `tests/test_session_isolation.py` | 旧版测试 | ❌ 已废弃 |

### 文档

| 文件 | 内容 |
|------|------|
| `README.md` | 项目说明、快速开始 |
| `docs/配置指南.md` | 环境变量、Coze 配置 |
| `docs/会话隔离实现历程.md` | 问题发现→解决过程 |
| `docs/SDK使用示例.md` | Coze SDK 官方用法 |

---

## 快速导航

### 新手入门
1. 阅读 `README.md`
2. 参考 `docs/配置指南.md` 配置环境
3. 运行 `python3 tests/test_simple.py` 测试

### 了解实现
1. 查看 `docs/会话隔离实现历程.md` 了解实现过程
2. 阅读 `src/jwt_signer.py` 理解 JWT 签署
3. 阅读 `backend.py` 理解 API 调用

### 使用 SDK
1. 参考 `docs/SDK使用示例.md`
2. 对比官方 SDK 与本项目实现
3. 选择适合的方式集成

---

## 文件清理说明

### 已删除的冗余文档

以下文档已整理或删除:
- ❌ `测试报告.md` → 整合到 `会话隔离实现历程.md`
- ❌ `当前状态与配置指南.md` → 整理为 `配置指南.md`
- ❌ `会话隔离测试报告.md` → 整合到实现历程
- ❌ `会话隔离实现说明.md` → 已过时
- ❌ `会话隔离实现验证报告-最终版.md` → 整合到实现历程
- ❌ `快速参考.md` → 整合到 README
- ❌ `配置检查清单.md` → 整理为配置指南
- ❌ `问题诊断-大模型节点配置.md` → 已过时
- ❌ `修复说明.md` → 整合到实现历程
- ❌ `修复总结.md` → 整合到实现历程
- ❌ `修正配置指南-应用会话流.md` → 整理为配置指南
- ❌ `优化建议.md` → 已实现,不再需要
- ❌ `最终解决方案.md` → 整合到实现历程
- ❌ `Coze工作流配置*.md` (多个) → 整理为配置指南
- ❌ `SESSION_ISOLATION_*.md` → 整合到实现历程

### 归档文件

以下文件已移动到 `archive/`:
- 代码备份: `backend_backup_*.py`
- 日志文件: `*.log`
- 测试页面: `session_name.html`, `a.html`

---

## 版本记录

### v2.1.0 (2025-11-19) - 文档整理版
- ✅ 重新组织项目结构
- ✅ 整理和精简文档
- ✅ 创建专业的 README
- ✅ 记录完整实现历程
- ✅ 添加 SDK 使用示例

### v2.0.0 (2025-11-18) - 会话隔离实现
- ✅ 实现基于 session_name 的会话隔离
- ✅ JWT + API payload 双重添加 session_name
- ✅ 完整测试验证

---

**文档更新**: 2025-11-19
