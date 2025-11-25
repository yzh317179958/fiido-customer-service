# E-bike 知识库系统实施方案详解

> **版本**: v1.0
> **创建时间**: 2025-11-25
> **负责人**: Claude Code
> **状态**: 📝 方案待审核

---

## 📋 为什么需要知识库系统？

### 当前问题分析

**现状**: 当前 AI 客服依赖 Coze Workflow 的内置知识，但存在以下问题：

#### 问题1: 知识更新困难

**场景**:
```
新车型发布: Fiido X1（2025年新款）
- AI: "抱歉，我不了解 X1 车型"  ❌
- 原因: Coze Workflow 未更新知识

产品规格变更: C11 Pro 电池升级为 960Wh
- AI: "C11 Pro 电池容量是 696Wh"  ❌（旧数据）
- 原因: 知识库未同步最新规格
```

**问题**: 无法快速更新 AI 知识，导致回答过时、错误。

#### 问题2: 知识来源混乱

**场景**:
```
知识来源：
- 产品手册 PDF（德语版）
- Shopify 产品描述
- 客服邮件模板
- 技术团队经验
- 用户反馈的典型问题

问题：
- 分散在不同文档/系统
- 无版本控制
- 无审批流程
- 坐席/AI 无法快速查询
```

**问题**: 知识孤岛严重，无法形成统一的知识体系。

#### 问题3: 人工经验无法沉淀

**场景**:
```
坐席 A 解决了 50+ 电池问题
坐席 B 遇到相同问题时：
- 需要重新研究
- 无法查看 A 的解决方案
- 浪费时间，用户体验差

优秀的解决方案：
- 无法沉淀为 AI 知识
- 无法让其他坐席学习
```

**问题**: 人工经验无法转化为 AI 能力和团队知识。

### 业务价值

实施知识库系统后，可以实现：

1. **AI 能力提升**: 持续更新知识，提升 AI 回答准确率和覆盖率
2. **坐席效率提升**: 快速查询标准答案，减少重复研究时间
3. **知识沉淀**: 人工经验 → 知识库 → AI/坐席共享
4. **多语言支持**: 同一知识多语言版本（EN/DE/FR/IT/ES）
5. **质量管控**: 审批流程确保知识准确性

---

## 🔧 技术原理是什么？

### 核心概念

#### 1. 知识条目（Knowledge Article）

**定义**: 一个结构化的 FAQ 或产品信息单元

**结构**:
```json
{
  "article_id": "KB-001",
  "category": "product_specs",      // 分类（产品规格/售前/售后/合规）
  "sub_category": "c11_pro",        // 子分类（车型）
  "title": "C11 Pro 电池容量是多少？",
  "question_variants": [            // 问题变体（用于匹配）
    "C11 Pro 电池多大",
    "C11 Pro 续航多少公里",
    "C11 Pro 电量"
  ],
  "answer": "C11 Pro 配备 48V 14.5Ah (696Wh) 可拆卸锂电池，续航里程可达 80-100 公里（根据路况和骑行模式）。",
  "answer_metadata": {              // 答案元数据
    "key_points": ["48V 14.5Ah", "696Wh", "80-100km", "可拆卸"],
    "applicable_markets": ["EU", "UK"],
    "applicable_models": ["C11 Pro"]
  },
  "language": "zh",                 // 语言
  "translations": {                 // 多语言版本
    "en": {...},
    "de": {...}
  },
  "ai_enabled": true,               // 是否允许 AI 引用
  "agent_visible": true,            // 坐席是否可见
  "status": "published",            // 状态（草稿/审核中/已发布/已归档）
  "created_by": "agent_001",
  "approved_by": "admin_001",
  "created_at": "2025-11-25T10:00:00Z",
  "updated_at": "2025-11-25T10:00:00Z"
}
```

#### 2. 知识库层级结构

```
知识库
├── 产品规格（Product Specs）
│   ├── C 系列
│   │   ├── C11 Pro
│   │   ├── C11
│   │   └── C21
│   ├── T 系列
│   │   ├── T1 Pro
│   │   └── T2
│   └── 其他系列
│       ├── Titan
│       ├── Air
│       └── Nomads
│
├── 售前咨询（Presale）
│   ├── 产品对比
│   ├── 价格政策
│   ├── 合法性说明
│   └── 促销活动
│
├── 订单与物流（Order & Logistics）
│   ├── 订单操作
│   ├── 物流追踪
│   ├── 关税/VAT
│   └── 清关流程
│
├── 售后服务（Aftersale）
│   ├── 保修政策
│   ├── 退换货流程
│   ├── 常见故障
│   ├── 维修指南
│   └── 配件更换
│
└── 合规性（Compliance）
    ├── CE 认证
    ├── 电池法规
    └── GDPR
```

#### 3. 知识匹配算法

**多层匹配策略**:

```python
def search_knowledge(user_query: str, language: str = "zh"):
    """
    知识匹配算法
    """
    results = []

    # 第1层：精确匹配（完全相同）
    exact_matches = db.query(Article).filter(
        Article.title == user_query,
        Article.language == language,
        Article.status == "published"
    ).all()
    results.extend(exact_matches)

    # 第2层：关键词匹配（包含关键词）
    keywords = extract_keywords(user_query)  # 提取关键词
    keyword_matches = db.query(Article).filter(
        Article.answer_metadata["key_points"].overlap(keywords),  # PostgreSQL array overlap
        Article.language == language,
        Article.status == "published"
    ).all()
    results.extend(keyword_matches)

    # 第3层：语义匹配（向量相似度）
    query_embedding = embed_text(user_query)  # 使用 Coze/OpenAI Embedding
    semantic_matches = db.query(Article).filter(
        Article.embedding.cosine_distance(query_embedding) < 0.3,  # 相似度阈值
        Article.language == language,
        Article.status == "published"
    ).all()
    results.extend(semantic_matches)

    # 去重 + 排序（按匹配度）
    results = deduplicate_and_rank(results)

    return results[:5]  # 返回 Top 5
```

#### 4. 知识回流机制

**定义**: 将人工坐席的优质解决方案沉淀为知识库条目

**流程**:
```
1. 坐席解决问题 → 2. 坐席标记"沉淀为知识" → 3. 自动生成草稿 → 4. 审批 → 5. 发布 → 6. AI 引用
```

**实现**:
```python
@app.post("/api/tickets/{ticket_id}/extract-knowledge")
async def extract_knowledge_from_ticket(ticket_id: str):
    """从工单提取知识"""
    ticket = await db.get_ticket(ticket_id)

    # 1. 提取问题（从用户消息）
    question = extract_user_question(ticket.session_name)

    # 2. 提取答案（从坐席回复 + 解决方案）
    answer = extract_agent_solution(ticket)

    # 3. 生成知识库草稿
    draft = Article(
        category=auto_categorize(question),  # 自动分类
        title=question,
        answer=answer,
        status="draft",  # 草稿状态
        created_by=ticket.assigned_to,
        metadata={
            "source": "ticket",
            "ticket_id": ticket_id,
            "confidence": calculate_confidence(ticket)  # 自动评估质量
        }
    )

    await db.save(draft)

    # 4. 通知知识管理员审批
    await notify_knowledge_admin(draft)

    return {"article_id": draft.article_id}
```

---

## 🛠️ 需要什么工具和配置？

### 后端技术栈

| 技术 | 用途 | 原因 |
|------|------|------|
| **FastAPI** | Web 框架 | 已使用 |
| **PostgreSQL** | 数据库 | 支持全文搜索、JSONB、向量检索（pgvector 扩展）|
| **pgvector** | 向量检索 | 语义匹配（Embedding 向量相似度搜索）|
| **Coze Embedding API** | 文本向量化 | 将问题/答案转为向量 |
| **Redis** | 缓存 | 热门问题缓存，减少数据库查询 |

### 前端技术栈

| 技术 | 用途 |
|------|------|
| **Vue 3 + Element Plus** | 知识库管理后台 |
| **Markdown 编辑器** | 富文本编辑（支持图片、表格）|
| **搜索组件** | 快速查询知识 |

### Coze Workflow 集成

**目标**: 将知识库内容同步到 Coze Workflow

**方式1: 通过 Coze API 更新知识库**（推荐）

```python
import httpx

async def sync_to_coze(article: Article):
    """将知识库条目同步到 Coze"""
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{COZE_API_BASE}/v1/knowledge/documents",
            headers={"Authorization": f"Bearer {COZE_API_KEY}"},
            json={
                "knowledge_base_id": COZE_KNOWLEDGE_BASE_ID,
                "document_name": article.title,
                "content": article.answer,
                "metadata": article.answer_metadata
            }
        )
    return response.json()
```

**方式2: 导出为 CSV/JSON，手动上传**

```python
@app.get("/api/knowledge/export")
async def export_knowledge():
    """导出知识库为 CSV"""
    articles = await db.query(Article).filter(
        Article.ai_enabled == True,
        Article.status == "published"
    ).all()

    csv_content = generate_csv(articles)  # 生成 CSV
    return Response(content=csv_content, media_type="text/csv")
```

### 环境配置

```bash
# PostgreSQL 配置（已有）
DATABASE_URL=postgresql://user:pass@localhost:5432/fiido_kb

# pgvector 扩展（需安装）
# sudo apt install postgresql-14-pgvector
# psql -d fiido_kb -c "CREATE EXTENSION vector;"

# Coze Embedding API
COZE_EMBEDDING_API_KEY=your_api_key
COZE_KNOWLEDGE_BASE_ID=your_kb_id

# Redis（已有）
REDIS_URL=redis://localhost:6379/4
```

---

## 📐 数据模型设计

### 1. Article 表（知识条目）

```python
from sqlalchemy import Column, String, Integer, DateTime, Boolean, JSON, Enum
from pgvector.sqlalchemy import Vector

class Article(Base):
    __tablename__ = "knowledge_articles"

    # 主键
    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(50), unique=True, index=True)  # KB-001

    # 分类
    category = Column(Enum("product_specs", "presale", "order", "aftersale", "compliance"))
    sub_category = Column(String(50), nullable=True)  # 车型、问题类型

    # 内容
    title = Column(String(500))  # 问题标题
    question_variants = Column(JSON)  # 问题变体列表
    answer = Column(String(10000))  # 答案
    answer_metadata = Column(JSON)  # 元数据（关键点、适用市场等）

    # 向量（用于语义匹配）
    title_embedding = Column(Vector(1536))  # OpenAI/Coze Embedding 维度
    answer_embedding = Column(Vector(1536))

    # 多语言
    language = Column(String(5), default="zh")  # zh/en/de/fr/it/es
    translations = Column(JSON, nullable=True)  # 其他语言版本

    # 权限控制
    ai_enabled = Column(Boolean, default=True)  # AI 是否可引用
    agent_visible = Column(Boolean, default=True)  # 坐席是否可见
    user_visible = Column(Boolean, default=False)  # 用户端是否可见

    # 状态
    status = Column(Enum("draft", "pending_review", "published", "archived"))

    # 审批
    created_by = Column(String(100))  # 创建者
    approved_by = Column(String(100), nullable=True)  # 审批人
    approved_at = Column(DateTime, nullable=True)

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 统计
    view_count = Column(Integer, default=0)  # 查看次数
    usefulness_score = Column(Integer, default=0)  # 有用评分（+1/-1）
```

### 2. ArticleRevision 表（版本历史）

```python
class ArticleRevision(Base):
    __tablename__ = "article_revisions"

    id = Column(Integer, primary_key=True, autoincrement=True)
    article_id = Column(String(50), index=True)  # 关联条目

    # 版本信息
    revision_number = Column(Integer)  # 版本号（如 v1, v2）
    title = Column(String(500))
    answer = Column(String(10000))

    # 变更信息
    changed_by = Column(String(100))
    change_note = Column(String(500))  # 变更说明

    # 时间戳
    created_at = Column(DateTime, default=datetime.utcnow)
```

---

## 🔌 API 接口设计

### 1. 创建知识条目

```http
POST /api/knowledge/articles
Authorization: Bearer {JWT_TOKEN}
Content-Type: application/json

Body:
{
  "category": "product_specs",
  "sub_category": "c11_pro",
  "title": "C11 Pro 电池容量是多少？",
  "question_variants": ["C11 Pro 电池多大", "C11 Pro 续航"],
  "answer": "C11 Pro 配备 48V 14.5Ah (696Wh) 可拆卸锂电池，续航里程可达 80-100 公里。",
  "answer_metadata": {
    "key_points": ["48V 14.5Ah", "696Wh", "80-100km"],
    "applicable_markets": ["EU", "UK"],
    "applicable_models": ["C11 Pro"]
  },
  "language": "zh",
  "ai_enabled": true,
  "status": "draft"
}

Response 201:
{
  "success": true,
  "data": {
    "article_id": "KB-001",
    "status": "draft"
  }
}
```

### 2. 搜索知识（坐席/AI 使用）

```http
GET /api/knowledge/search?q=C11+Pro+电池&language=zh&limit=5

Response 200:
{
  "success": true,
  "data": {
    "results": [
      {
        "article_id": "KB-001",
        "title": "C11 Pro 电池容量是多少？",
        "answer": "...",
        "match_score": 0.95,  # 匹配度
        "match_type": "exact"  # 匹配类型（exact/keyword/semantic）
      }
    ]
  }
}
```

### 3. 审批知识条目

```http
POST /api/knowledge/articles/{article_id}/approve
Authorization: Bearer {JWT_TOKEN}  # role=admin
Body:
{
  "approved": true,
  "note": "内容准确，已审核通过"
}

Response 200:
{
  "success": true,
  "data": {
    "article_id": "KB-001",
    "status": "published",
    "approved_by": "admin_001",
    "approved_at": "2025-11-25T15:00:00Z"
  }
}
```

### 4. 同步到 Coze

```http
POST /api/knowledge/articles/{article_id}/sync-to-coze
Authorization: Bearer {JWT_TOKEN}

Response 200:
{
  "success": true,
  "data": {
    "coze_document_id": "doc_xxx",
    "sync_status": "success"
  }
}
```

### 5. 批量导出

```http
GET /api/knowledge/export?format=csv&language=zh&category=product_specs

Response 200:
Content-Type: text/csv
Content-Disposition: attachment; filename="knowledge_base_zh.csv"

category,title,answer,key_points,applicable_models
product_specs,"C11 Pro 电池容量是多少？","C11 Pro 配备...","48V 14.5Ah;696Wh","C11 Pro"
```

---

## 🔄 知识回流流程

### 场景1: 从工单提取知识

```python
# 坐席解决问题后，点击"沉淀为知识"
@app.post("/api/tickets/{ticket_id}/extract-knowledge")
async def extract_knowledge(ticket_id: str):
    ticket = await db.get_ticket(ticket_id)

    # 1. AI 自动提取问题和答案
    question = extract_user_question(ticket.session_name)
    answer = extract_agent_solution(ticket)

    # 2. 生成草稿
    draft = Article(
        title=question,
        answer=answer,
        category=ticket.category,
        status="draft",
        created_by=ticket.assigned_to,
        metadata={"source": "ticket", "ticket_id": ticket_id}
    )

    # 3. 计算向量
    draft.title_embedding = await get_embedding(question)
    draft.answer_embedding = await get_embedding(answer)

    await db.save(draft)

    # 4. 通知审批
    await notify_admin(f"新知识草稿 {draft.article_id} 待审批")

    return {"article_id": draft.article_id}
```

### 场景2: 坐席主动创建

```vue
<!-- agent-workbench 知识库管理 -->
<template>
  <el-dialog title="创建知识条目">
    <el-form>
      <el-form-item label="问题">
        <el-input v-model="form.title" placeholder="例如：C11 Pro 电池容量是多少？" />
      </el-form-item>

      <el-form-item label="答案">
        <markdown-editor v-model="form.answer" />
      </el-form-item>

      <el-form-item label="关键点">
        <el-tag v-for="tag in form.key_points" :key="tag">{{ tag }}</el-tag>
        <el-input v-model="newTag" @keyup.enter="addTag" />
      </el-form-item>

      <el-form-item label="适用车型">
        <el-checkbox-group v-model="form.applicable_models">
          <el-checkbox label="C11 Pro" />
          <el-checkbox label="C11" />
          <!-- ... -->
        </el-checkbox-group>
      </el-form-item>
    </el-form>

    <el-button type="primary" @click="submitDraft">提交草稿</el-button>
  </el-dialog>
</template>
```

### 场景3: 审批流程

**审批规则**:
- 草稿 → 审核中（自动）
- 审核中 → 已发布（管理员审批）
- 审核中 → 草稿（拒绝，返回修改）

**审批界面**:
```vue
<template>
  <el-card>
    <h3>{{ article.title }}</h3>
    <div v-html="markdown(article.answer)"></div>

    <el-form>
      <el-form-item label="审批意见">
        <el-input type="textarea" v-model="approvalNote" />
      </el-form-item>
    </el-form>

    <el-button type="success" @click="approve">通过</el-button>
    <el-button type="danger" @click="reject">拒绝</el-button>
  </el-card>
</template>
```

---

## ⏱️ 实施时间估算

### 阶段1: 基础架构（Week 1）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 数据库设计 | 4小时 | Article、Revision 表 |
| pgvector 配置 | 2小时 | 安装扩展、创建索引 |
| Coze Embedding 集成 | 4小时 | 文本向量化 API |
| **小计** | **10小时** | - |

### 阶段2: 核心功能（Week 2）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 创建知识 API | 3小时 | POST /api/knowledge/articles |
| 搜索知识 API | 6小时 | 三层匹配算法 |
| 审批流程 API | 4小时 | 审批/拒绝 |
| 版本历史 API | 3小时 | 查看历史版本 |
| **小计** | **16小时** | - |

### 阶段3: 知识回流（Week 3）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 从工单提取 API | 4小时 | 自动提取问题/答案 |
| AI 质量评估 | 4小时 | 评估知识置信度 |
| 通知系统 | 2小时 | 审批通知 |
| **小计** | **10小时** | - |

### 阶段4: Coze 集成（Week 4）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 同步到 Coze API | 6小时 | 调用 Coze Knowledge API |
| 批量导出 | 3小时 | CSV/JSON 导出 |
| 定时同步任务 | 3小时 | Celery 定时同步 |
| **小计** | **12小时** | - |

### 阶段5: 前端界面（Week 5-6）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 知识库列表页 | 6小时 | 列表、筛选、搜索 |
| 知识库详情页 | 4小时 | 查看、编辑 |
| 创建/编辑表单 | 6小时 | Markdown 编辑器 |
| 审批界面 | 4小时 | 审批工作流 |
| **小计** | **20小时** | - |

### 阶段6: 测试与文档（Week 7）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 单元测试 | 6小时 | API 测试 |
| 集成测试 | 6小时 | 端到端测试 |
| 用户手册 | 4小时 | 坐席使用指南 |
| **小计** | **16小时** | - |

### 总计: **84 小时** ≈ **10.5 个工作日**

---

## ❓ 常见问题 FAQ

### Q1: 如何保证知识库内容准确性？

**A**: 多层质量控制机制：

1. **审批流程**: 草稿 → 审核 → 发布
2. **版本管理**: 所有修改记录历史版本
3. **有用性评分**: 坐席/用户可评分（+1/-1）
4. **定期审计**: 每季度审核低分知识条目

### Q2: 知识库与 Coze Workflow 如何配合？

**A**: 双向配合：

- **方向1**: 知识库 → Coze（同步更新）
- **方向2**: Coze → 知识库（记录引用日志）

```python
# 记录 AI 引用知识
@app.post("/api/knowledge/articles/{article_id}/log-usage")
async def log_usage(article_id: str, session_name: str):
    article = await db.get_article(article_id)
    article.view_count += 1
    await db.save(article)

    # 记录引用日志（用于评估知识价值）
    await db.save(KnowledgeUsageLog(
        article_id=article_id,
        session_name=session_name,
        timestamp=datetime.utcnow()
    ))
```

### Q3: 如何支持多语言？

**A**: 三种方式：

1. **人工翻译**（推荐）: 坐席/翻译团队手动翻译
2. **机器翻译 + 人工校对**: DeepL API + 人工审核
3. **独立条目**: 每种语言创建独立条目

**实施**:
```python
class Article:
    language: str  # 主语言（zh）
    translations: dict = {
        "en": {"title": "...", "answer": "..."},
        "de": {"title": "...", "answer": "..."}
    }
```

### Q4: 知识库可以删除吗？

**A**: 不建议删除，建议归档。

```python
@app.post("/api/knowledge/articles/{article_id}/archive")
async def archive_article(article_id: str):
    article = await db.get_article(article_id)
    article.status = "archived"  # 不删除，只归档
    article.ai_enabled = False   # AI 不再引用
    await db.save(article)
```

**原因**:
- 保留历史记录
- 可能未来重新启用
- 用于数据分析

### Q5: 如何防止知识重复？

**A**: 创建时检测相似知识：

```python
async def create_article(article_data):
    # 1. 计算新知识向量
    new_embedding = await get_embedding(article_data.title)

    # 2. 搜索相似知识（向量距离 < 0.1）
    similar = await db.query(Article).filter(
        Article.title_embedding.cosine_distance(new_embedding) < 0.1
    ).all()

    if similar:
        raise HTTPException(
            status_code=409,
            detail=f"已存在相似知识: {similar[0].article_id}"
        )
```

---

## 📚 相关文档

- `prd/01_全局指导/PRD_COMPLETE_v3.0.md` - 第 5.1-5.2 节（知识库需求）
- `prd/02_约束与原则/coze.md` - Coze API 使用规范
- `CLAUDE.md` - 开发流程规范

---

## ✅ 下一步行动

### 用户确认事项

1. **Coze 集成方式**: 是否使用 Coze Knowledge Base API？（需 API Key）
2. **向量检索**: 是否安装 pgvector 扩展？
3. **多语言支持**: 是否需要多语言翻译功能？
4. **实施优先级**: 是否同意按 Week 1-7 顺序实施？

### 开发前准备

1. 安装 pgvector 扩展
2. 配置 Coze Embedding API
3. 准备初始知识库数据（产品手册、FAQ）

---

**文档维护者**: Fiido AI 客服开发团队
**最后更新**: 2025-11-25
**文档版本**: v1.0
**状态**: 📝 方案待审核
