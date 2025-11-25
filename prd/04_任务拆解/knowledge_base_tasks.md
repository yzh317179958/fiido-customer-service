# 知识库与学习回路 - 任务拆解文档

> 文档版本: v1.0
> 创建时间: 2025-11-25
> 优先级: P2
> 依赖: codex.md 第5节, Coze 知识库 API

---

## 📋 模块概述

构建E-bike领域专业知识库，实现知识回流机制，支持多语言管理，打通AI学习闭环，持续提升AI回答质量和覆盖率。

### 核心目标

1. **E-bike 专业知识库**：车型参数、技术规格、故障诊断、维修指南、合规法规
2. **知识回流机制**：从人工对话中提取优质QA，反哺知识库
3. **多语言支持**：en/de/fr/it/es 五语言知识管理
4. **AI 持续学习**：知识库版本管理、A/B测试、效果评估

---

## 🎯 功能需求（基于 codex.md 第5节）

### 5.1 E-bike 知识库架构

**优先级**: P2
**预计工时**: 12小时

#### 知识库分类

```typescript
enum KnowledgeCategory {
  PRODUCT = 'product',               // 产品介绍
  TECHNICAL = 'technical',           // 技术规格
  TROUBLESHOOTING = 'troubleshooting', // 故障诊断
  MAINTENANCE = 'maintenance',       // 维护保养
  COMPLIANCE = 'compliance',         // 合规法规
  WARRANTY = 'warranty',             // 保修政策
  SHIPPING = 'shipping',             // 物流配送
  PAYMENT = 'payment',               // 支付方式
  RETURNS = 'returns',               // 退换货
  ACCESSORIES = 'accessories'        // 配件与升级
}

interface KnowledgeEntry {
  // 基础信息
  knowledge_id: string
  title: string
  content: string
  category: KnowledgeCategory
  tags: string[]
  language: string                   // en/de/fr/it/es

  // 版本管理
  version: string                    // v1.0, v1.1, etc.
  status: 'draft' | 'published' | 'archived'
  created_at: number
  updated_at: number
  created_by: string                 // 创建者

  // 关联信息
  related_products: string[]         // 关联车型
  related_knowledge: string[]        // 相关知识条目

  // 质量评估
  usage_count: number                // 被引用次数
  positive_feedback: number          // 用户好评数
  negative_feedback: number          // 用户差评数
  avg_rating: number                 // 平均评分

  // 多语言支持
  translations: {
    [lang: string]: {
      title: string
      content: string
      translated_by: string
      translated_at: number
    }
  }

  // 来源追踪
  source_type: 'manual' | 'auto_extracted' | 'imported'
  source_session_id?: string         // 来自哪个会话
  source_ticket_id?: string          // 来自哪个工单
}
```

#### 知识库内容结构

**产品知识 (Product)**:
```markdown
# C11 Pro - 产品介绍

## 基本信息
- 车型系列: C系列（城市通勤）
- 定位: 中高端折叠电助力车
- 目标市场: 欧洲城市通勤用户

## 核心参数
- 电机: 250W/500W 后轮电机（可选）
- 电池: 48V 14.5Ah 可拆卸电池
- 续航: 80-120km（PAS 1-3档）
- 最大速度: 25km/h（欧盟合规）
- 车重: 23kg
- 最大承重: 120kg

## 适用场景
- 城市通勤（10-20km）
- 地铁接驳
- 周末郊游
- 不适合：越野、长途骑行

## 常见问题
Q: C11 Pro 和 C11 有什么区别？
A: C11 Pro 采用更大容量电池（14.5Ah vs 10.4Ah），续航提升 40%...
```

**技术规格 (Technical)**:
```markdown
# C11 Pro - 技术规格

## 电机参数
- 型号: Fiido Rear Hub Motor
- 功率: 250W（欧盟版）/ 500W（非欧盟版）
- 扭矩: 42Nm
- 位置: 后轮中置

## 电池参数
- 类型: 锂离子电池
- 电压: 48V
- 容量: 14.5Ah (696Wh)
- 充电时间: 4-6小时（标准充电器）
- 充电循环: 800+ 次
- 可拆卸: 是
- 防水等级: IP54

## 辅助系统
- 档位: 5档电助力（PAS 1-5）
- 传感器: 力矩传感器 + 速度传感器
- 显示屏: LCD彩色显示屏
- 灯光: 前LED灯 + 后刹车灯

## 刹车系统
- 前刹: 液压碟刹（160mm）
- 后刹: 液压碟刹（140mm）
- 刹车传感器: 电子刹车断电

## 合规认证
- CE 认证: ✅
- EN 15194: ✅（欧盟电助力车标准）
- RoHS: ✅
- 最大速度限制: 25km/h（欧盟）
```

**故障诊断 (Troubleshooting)**:
```markdown
# 电池续航不足 - 故障诊断

## 症状描述
客户反馈电池续航明显低于官方宣传值

## 可能原因（按概率排序）

### 1. 使用习惯问题（60%）
- 高档位使用（PAS 4-5）
- 频繁加速/刹车
- 载重超过建议值
- 逆风/上坡路段多

**解决方案**:
- 建议使用 PAS 1-3 档
- 保持匀速骑行
- 检查轮胎气压（建议 50-65 PSI）

### 2. 环境因素（20%）
- 低温环境（< 0°C）
- 湿度过高

**解决方案**:
- 电池在室温环境充电
- 低温下续航会降低 20-30%（正常现象）

### 3. 电池老化（15%）
- 充电循环 > 500 次
- 电池健康度 < 80%

**解决方案**:
- 检查电池循环次数（固件查询）
- 建议更换电池（保修期内免费）

### 4. 固件问题（5%）
- 固件版本过旧
- BMS 校准偏差

**解决方案**:
- 升级到最新固件
- 执行电池校准程序

## 诊断流程
1. 获取客户使用数据（里程、档位、载重）
2. 查询电池健康度（`GET /api/devices/{vin}/battery`）
3. 检查固件版本
4. 根据上述排查顺序逐一验证

## 坐席处理建议
- 首先询问使用习惯（避免直接判断为故障）
- 查看设备数据确认电池健康度
- 提供节能骑行建议
- 必要时创建售后工单
```

---

### 5.2 知识回流机制

**优先级**: P2
**预计工时**: 10小时

#### 回流触发场景

```typescript
enum KnowledgeExtractionTrigger {
  MANUAL_RESOLVE = 'manual_resolve',     // 人工成功解决
  HIGH_RATING = 'high_rating',           // 用户高评分（>4星）
  FREQUENT_QUESTION = 'frequent_question', // 频繁出现问题
  NEW_SCENARIO = 'new_scenario'          // AI 无法回答的新场景
}

interface KnowledgeExtractionTask {
  task_id: string
  session_id: string
  trigger: KnowledgeExtractionTrigger
  created_at: number
  status: 'pending' | 'extracted' | 'reviewed' | 'published'

  // 提取的内容
  question: string                       // 用户问题
  answer: string                         // 坐席回答
  context: string                        // 对话上下文

  // AI 分析
  suggested_category: KnowledgeCategory
  suggested_tags: string[]
  suggested_related_products: string[]
  confidence: number                     // 置信度 (0-1)

  // 人工审核
  reviewed_by?: string                   // 审核者
  reviewed_at?: number
  review_comments?: string
  approved: boolean

  // 发布信息
  published_knowledge_id?: string
  published_at?: number
}
```

#### 回流工作流

```
用户对话 → AI无法回答 → 人工接管 → 坐席解决 → 用户好评
                ↓
        标记为"可提取知识"
                ↓
        AI自动生成知识条目草稿
                ↓
        运营人员审核 → 编辑 → 发布
                ↓
        知识库更新 → AI学习 → 下次自动回答
```

#### UI 界面要求

**布局位置**: 坐席工作台 > "知识回流" Tab

**知识提取面板**:
```vue
<KnowledgeExtractionPanel>
  <!-- 待提取队列 -->
  <ExtractionQueue>
    <QueueFilters>
      <FilterSelect v-model="filterTrigger" :options="triggers" />
      <FilterSelect v-model="filterCategory" :options="categories" />
      <DateRangePicker v-model="dateRange" />
    </QueueFilters>

    <ExtractionList>
      <ExtractionCard v-for="task in tasks" :key="task.task_id">
        <Header>
          <TriggerBadge :trigger="task.trigger" />
          <ConfidenceBadge :score="task.confidence" />
          <Date>{{ formatDate(task.created_at) }}</Date>
        </Header>

        <Content>
          <Question>{{ task.question }}</Question>
          <Answer>{{ task.answer }}</Answer>
          <Context>{{ task.context }}</Context>
        </Content>

        <AISuggestion>
          <CategoryTag :category="task.suggested_category" />
          <TagList :tags="task.suggested_tags" />
          <ProductList :products="task.suggested_related_products" />
        </AISuggestion>

        <Actions>
          <Button @click="handleReview(task)">审核</Button>
          <Button @click="handleReject(task)">拒绝</Button>
        </Actions>
      </ExtractionCard>
    </ExtractionList>
  </ExtractionQueue>

  <!-- 知识编辑器 -->
  <KnowledgeEditor v-if="currentTask">
    <FormFields>
      <Input v-model="knowledge.title" label="标题" />
      <CategorySelect v-model="knowledge.category" />
      <TagInput v-model="knowledge.tags" />
      <ProductSelect v-model="knowledge.related_products" />
      <MarkdownEditor v-model="knowledge.content" />
    </FormFields>

    <PreviewPane>
      <MarkdownRenderer :content="knowledge.content" />
    </PreviewPane>

    <Actions>
      <Button @click="saveDraft">保存草稿</Button>
      <Button @click="publish" type="primary">发布</Button>
    </Actions>
  </KnowledgeEditor>
</KnowledgeExtractionPanel>
```

---

### 5.3 多语言知识管理

**优先级**: P2
**预计工时**: 8小时

#### 翻译工作流

```
原始知识（英文）→ AI自动翻译（de/fr/it/es）→ 人工校对 → 发布多语言版本
```

#### 翻译质量评估

```typescript
interface TranslationQuality {
  knowledge_id: string
  source_lang: string
  target_lang: string

  // 自动评估
  bleu_score: number              // 机器翻译质量评分
  fluency_score: number           // 流畅度评分
  accuracy_score: number          // 准确度评分

  // 人工评估
  human_reviewed: boolean
  reviewed_by?: string
  reviewed_at?: number
  issues: TranslationIssue[]

  // 使用反馈
  usage_count: number
  user_feedback_score: number     // 用户反馈评分
}

interface TranslationIssue {
  issue_type: 'terminology' | 'grammar' | 'context' | 'cultural'
  description: string
  suggested_fix: string
}
```

#### 术语库管理

```typescript
interface TerminologyEntry {
  term_id: string
  source_term: string              // 原始术语（英文）
  category: string                 // 分类（技术/营销/法律）

  // 多语言翻译
  translations: {
    [lang: string]: {
      term: string
      context: string              // 使用场景
      approved_by: string
      approved_at: number
    }
  }

  // 示例
  examples: {
    source: string
    translations: { [lang: string]: string }
  }[]
}
```

**示例术语库**:
```json
{
  "term_id": "term_001",
  "source_term": "electric assist",
  "category": "technical",
  "translations": {
    "de": { "term": "elektrische Unterstützung", "context": "技术文档" },
    "fr": { "term": "assistance électrique", "context": "技术文档" },
    "it": { "term": "assistenza elettrica", "context": "技术文档" },
    "es": { "term": "asistencia eléctrica", "context": "技术文档" }
  },
  "examples": [
    {
      "source": "The bike provides 5 levels of electric assist.",
      "translations": {
        "de": "Das Fahrrad bietet 5 Stufen elektrischer Unterstützung.",
        "fr": "Le vélo offre 5 niveaux d'assistance électrique.",
        "it": "La bici offre 5 livelli di assistenza elettrica.",
        "es": "La bicicleta ofrece 5 niveles de asistencia eléctrica."
      }
    }
  ]
}
```

---

### 5.4 知识库版本管理

**优先级**: P2
**预计工时**: 6小时

#### 版本控制

```typescript
interface KnowledgeVersion {
  version_id: string
  knowledge_id: string
  version_number: string          // v1.0, v1.1, v2.0

  // 变更信息
  change_type: 'create' | 'update' | 'delete' | 'merge'
  changed_by: string
  changed_at: number
  change_reason: string

  // 快照
  snapshot: KnowledgeEntry

  // 差异
  diff: {
    added: string[]
    removed: string[]
    modified: { field: string, old_value: any, new_value: any }[]
  }
}
```

#### A/B 测试

```typescript
interface KnowledgeABTest {
  test_id: string
  test_name: string
  start_date: number
  end_date: number
  status: 'running' | 'completed' | 'cancelled'

  // 版本对比
  version_a: string               // 当前版本
  version_b: string               // 新版本

  // 流量分配
  traffic_split: {
    version_a: number             // 50%
    version_b: number             // 50%
  }

  // 评估指标
  metrics: {
    version_a: KnowledgeMetrics
    version_b: KnowledgeMetrics
  }

  // 测试结论
  winner?: 'version_a' | 'version_b'
  conclusion?: string
}

interface KnowledgeMetrics {
  usage_count: number             // 使用次数
  resolution_rate: number         // 问题解决率
  avg_rating: number              // 平均评分
  escalation_rate: number         // 升级人工比例
  avg_response_time: number       // 平均响应时间
}
```

---

## 📝 API 接口设计

### 知识库 CRUD

```http
# 创建知识条目
POST /api/knowledge
Authorization: Bearer {admin_token}
Content-Type: application/json

{
  "title": "C11 Pro 电池续航优化指南",
  "content": "...",
  "category": "maintenance",
  "tags": ["battery", "range", "c11-pro"],
  "language": "en",
  "related_products": ["c11-pro"],
  "status": "draft"
}

# 获取知识列表
GET /api/knowledge?category={category}&language={lang}&status={status}

# 获取知识详情
GET /api/knowledge/{knowledge_id}

# 更新知识
PATCH /api/knowledge/{knowledge_id}

# 删除知识
DELETE /api/knowledge/{knowledge_id}

# 发布知识
POST /api/knowledge/{knowledge_id}/publish

# 归档知识
POST /api/knowledge/{knowledge_id}/archive
```

### 知识回流

```http
# 标记会话可提取知识
POST /api/knowledge/extract/mark
{
  "session_id": "session_123",
  "trigger": "manual_resolve"
}

# 获取待提取队列
GET /api/knowledge/extract/queue?trigger={trigger}&status={status}

# 审核提取任务
POST /api/knowledge/extract/{task_id}/review
{
  "approved": true,
  "review_comments": "内容准确，可以发布"
}

# 拒绝提取任务
POST /api/knowledge/extract/{task_id}/reject
{
  "reason": "内容不完整，需要补充"
}
```

### 多语言管理

```http
# 请求自动翻译
POST /api/knowledge/{knowledge_id}/translate
{
  "target_languages": ["de", "fr", "it", "es"]
}

# 更新翻译
PATCH /api/knowledge/{knowledge_id}/translations/{lang}
{
  "title": "...",
  "content": "..."
}

# 获取术语库
GET /api/terminology?category={category}

# 创建术语
POST /api/terminology
{
  "source_term": "electric assist",
  "category": "technical",
  "translations": {...}
}
```

### 版本管理

```http
# 获取版本历史
GET /api/knowledge/{knowledge_id}/versions

# 回滚到指定版本
POST /api/knowledge/{knowledge_id}/rollback
{
  "version_id": "version_456"
}

# 创建 A/B 测试
POST /api/knowledge/ab-test
{
  "test_name": "电池续航指南优化",
  "knowledge_id": "kb_123",
  "version_a": "v1.0",
  "version_b": "v2.0",
  "traffic_split": { "version_a": 50, "version_b": 50 },
  "duration_days": 7
}

# 获取 A/B 测试结果
GET /api/knowledge/ab-test/{test_id}/results
```

---

## 🔌 系统集成

### Coze 知识库 API 集成

```python
# ✅ 正确 - 使用 Coze 知识库 API
import httpx

async def sync_knowledge_to_coze(knowledge: KnowledgeEntry):
    """同步知识到 Coze 平台"""

    # 1. 格式化知识内容
    formatted_content = format_knowledge_for_coze(knowledge)

    # 2. 调用 Coze 知识库 API
    async with httpx.AsyncClient() as client:
        response = await client.post(
            f"{COZE_API_BASE}/knowledge/documents",
            headers={
                "Authorization": f"Bearer {COZE_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "dataset_id": COZE_DATASET_ID,
                "document_name": knowledge.title,
                "document_content": formatted_content,
                "language": knowledge.language,
                "metadata": {
                    "category": knowledge.category,
                    "tags": knowledge.tags,
                    "related_products": knowledge.related_products
                }
            }
        )

    # 3. 记录同步结果
    if response.status_code == 200:
        coze_doc_id = response.json()["document_id"]
        await db.update_knowledge(
            knowledge.knowledge_id,
            {"coze_document_id": coze_doc_id}
        )
```

### AI 自动翻译集成

```python
# 使用 Azure Translator 或 DeepL API
async def auto_translate(
    text: str,
    source_lang: str,
    target_langs: List[str]
) -> Dict[str, str]:
    """自动翻译知识内容"""

    translations = {}

    for target_lang in target_langs:
        # 调用翻译 API
        response = await translator_client.translate(
            text=text,
            from_lang=source_lang,
            to_lang=target_lang
        )

        translations[target_lang] = response["translation"]

    return translations
```

---

## 📊 知识库质量指标

| 指标 | 目标值 | 说明 |
|------|-------|------|
| 知识覆盖率 | > 80% | AI 能回答的问题占比 |
| 知识准确率 | > 95% | 用户反馈准确的比例 |
| 知识使用率 | > 70% | 被实际引用的知识条目比例 |
| 回流转化率 | > 30% | 人工对话转化为知识的比例 |
| 翻译质量分 | > 4.0/5.0 | 人工校对评分 |
| A/B 测试提升 | > 10% | 新版本相比旧版本的改进幅度 |

---

## 📝 开发任务清单

### 后端任务 (20小时)

- [ ] Task 1: 知识库数据模型设计 (3h)
  - [ ] 定义 TypeScript/Python 类型
  - [ ] 设计数据库表结构
  - [ ] 编写 ORM 模型

- [ ] Task 2: 知识库 CRUD API (5h)
  - [ ] 创建/更新/删除接口
  - [ ] 查询与搜索接口
  - [ ] 版本管理接口

- [ ] Task 3: 知识回流引擎 (6h)
  - [ ] 提取触发器实现
  - [ ] AI 自动分析与分类
  - [ ] 审核工作流

- [ ] Task 4: 多语言翻译集成 (4h)
  - [ ] 集成翻译 API（Azure/DeepL）
  - [ ] 术语库管理
  - [ ] 翻译质量评估

- [ ] Task 5: Coze 知识库同步 (2h)
  - [ ] 同步接口实现
  - [ ] 错误处理与重试
  - [ ] 同步状态追踪

### 前端任务 (16小时)

- [ ] Task 6: 知识库管理页面 (5h)
  - [ ] 知识列表组件
  - [ ] 知识编辑器（Markdown）
  - [ ] 分类与标签管理

- [ ] Task 7: 知识回流面板 (5h)
  - [ ] 待提取队列组件
  - [ ] 审核界面
  - [ ] AI 建议展示

- [ ] Task 8: 多语言管理界面 (4h)
  - [ ] 翻译编辑器
  - [ ] 术语库组件
  - [ ] 翻译质量对比

- [ ] Task 9: 版本与 A/B 测试 (2h)
  - [ ] 版本历史组件
  - [ ] A/B 测试配置
  - [ ] 效果对比仪表板

### 测试任务 (4h)

- [ ] Task 10: 单元测试 (2h)
  - [ ] API 测试
  - [ ] 组件测试

- [ ] Task 11: 集成测试 (2h)
  - [ ] 知识回流端到端测试
  - [ ] Coze 同步测试
  - [ ] 多语言翻译测试

**预计总工时**: 40小时

---

## 📚 相关文档

- 📘 [codex.md](../../codex.md) - 第5节：知识库与学习回路
- 📘 [CLAUDE.md](../../CLAUDE.md) - 开发流程规范
- 📘 [Coze 知识库 API 文档](https://www.coze.com/docs/developer_guides/knowledge_base)
- 📘 [Azure Translator API 文档](https://docs.microsoft.com/azure/cognitive-services/translator/)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-25
**预计总工时**: 40小时
