# AI表现与运营分析 - 任务拆解文档

> 文档版本: v1.0
> 创建时间: 2025-11-25
> 优先级: P2
> 依赖: codex.md 第6节, session_state.py, regulator.py

---

## 📋 模块概述

构建全方位的AI质量分析和运营指标体系，帮助运营团队监控AI表现、优化坐席效率、提升客户体验，实现数据驱动的持续改进。

### 核心目标

1. **AI 质量分析**：回答准确率、知识覆盖率、升级率、响应时间
2. **坐席效率统计**：处理量、平均处理时长、满意度、负载分布
3. **客户体验指标**：满意度、解决率、等待时长、多轮对话率
4. **运营决策支持**：趋势分析、异常告警、优化建议、A/B测试

---

## 🎯 功能需求（基于 codex.md 第6节）

### 6.1 AI 质量分析

**优先级**: P2
**预计工时**: 10小时

#### 核心指标

```typescript
interface AIQualityMetrics {
  // 时间范围
  time_range: {
    start_date: number
    end_date: number
    granularity: 'hour' | 'day' | 'week' | 'month'
  }

  // 准确率指标
  accuracy: {
    total_conversations: number
    ai_handled: number                // AI 完全处理
    escalated_to_human: number        // 升级人工
    ai_success_rate: number           // AI 成功率 (%)
    avg_confidence: number            // 平均置信度
  }

  // 知识覆盖率
  knowledge_coverage: {
    total_questions: number
    matched_knowledge: number         // 匹配知识库
    no_match: number                  // 无匹配
    coverage_rate: number             // 覆盖率 (%)
    top_missing_topics: {             // 最缺失主题
      topic: string
      count: number
    }[]
  }

  // 升级原因分析
  escalation_reasons: {
    keyword_trigger: number           // 关键词触发
    ai_fail_threshold: number         // AI 连续失败
    high_value_order: number          // 高价值订单
    manual_request: number            // 用户主动要求
    complex_issue: number             // 复杂问题
    off_hours: number                 // 非工作时间
  }

  // 响应时间
  response_time: {
    avg_first_response: number        // 平均首次响应(ms)
    avg_completion_time: number       // 平均完成时间(s)
    p50: number
    p90: number
    p99: number
  }

  // 多轮对话分析
  conversation_depth: {
    single_turn: number               // 单轮解决
    multi_turn_2_5: number            // 2-5轮
    multi_turn_6_10: number           // 6-10轮
    multi_turn_10_plus: number        // 10轮以上
    avg_turns: number                 // 平均轮数
  }

  // 错误分析
  errors: {
    timeout: number                   // 超时错误
    api_error: number                 // API 错误
    parse_error: number               // 解析错误
    unknown_error: number             // 未知错误
  }
}
```

#### AI 表现趋势

```typescript
interface AIPerformanceTrend {
  metric_name: string                 // 指标名称
  data_points: {
    timestamp: number
    value: number
    baseline: number                  // 基线值
    target: number                    // 目标值
  }[]

  // 趋势分析
  trend: 'improving' | 'declining' | 'stable'
  change_rate: number                 // 变化率 (%)
  anomalies: {                        // 异常点
    timestamp: number
    value: number
    reason: string
  }[]
}
```

---

### 6.2 坐席效率统计

**优先级**: P2
**预计工时**: 8小时

#### 坐席绩效指标

```typescript
interface AgentPerformanceMetrics {
  agent_id: string
  agent_name: string
  time_range: { start_date: number, end_date: number }

  // 工作量指标
  workload: {
    total_sessions: number            // 总接入会话数
    avg_sessions_per_day: number      // 日均接入量
    concurrent_peak: number           // 并发峰值
    avg_concurrent: number            // 平均并发数
    utilization_rate: number          // 利用率 (%)
  }

  // 效率指标
  efficiency: {
    avg_handle_time: number           // 平均处理时长(s)
    avg_response_time: number         // 平均响应时间(s)
    avg_first_response: number        // 平均首次响应(s)
    resolution_rate: number           // 一次解决率 (%)
    escalation_to_ticket: number      // 升级工单数
  }

  // 质量指标
  quality: {
    avg_csat: number                  // 平均满意度(1-5)
    positive_rate: number             // 好评率 (%)
    negative_rate: number             // 差评率 (%)
    complaint_count: number           // 投诉数
    quality_score: number             // 综合质量分(1-100)
  }

  // 时间分布
  time_distribution: {
    working_hours: number             // 工作时长(小时)
    available_hours: number           // 在线时长(小时)
    busy_hours: number                // 忙碌时长(小时)
    break_hours: number               // 休息时长(小时)
  }

  // 技能标签
  skill_tags: {
    tag: string                       // 技能标签
    session_count: number             // 处理次数
    avg_rating: number                // 平均评分
  }[]

  // 排名
  rank: {
    handle_time_rank: number          // 处理时长排名
    csat_rank: number                 // 满意度排名
    resolution_rank: number           // 解决率排名
    workload_rank: number             // 工作量排名
  }
}
```

#### 团队统计

```typescript
interface TeamStatistics {
  team_name: string
  time_range: { start_date: number, end_date: number }

  // 团队概览
  overview: {
    total_agents: number              // 总坐席数
    online_agents: number             // 在线坐席数
    total_sessions: number            // 总会话数
    avg_csat: number                  // 平均满意度
  }

  // 负载分布
  load_distribution: {
    agent_id: string
    agent_name: string
    session_count: number
    avg_handle_time: number
    load_percentage: number           // 负载占比 (%)
  }[]

  // 技能分布
  skill_distribution: {
    skill: string
    agent_count: number               // 具备该技能的坐席数
    session_count: number             // 该技能处理会话数
    avg_rating: number                // 平均评分
  }[]

  // 工作时间覆盖
  shift_coverage: {
    hour: number                      // 小时(0-23)
    avg_online_agents: number         // 平均在线坐席数
    avg_queue_length: number          // 平均队列长度
    avg_wait_time: number             // 平均等待时长(s)
  }[]
}
```

---

### 6.3 客户体验指标

**优先级**: P2
**预计工时**: 6小时

#### 客户满意度 (CSAT)

```typescript
interface CustomerSatisfactionMetrics {
  time_range: { start_date: number, end_date: number }

  // 总体满意度
  overall: {
    total_surveys: number             // 总调查数
    response_rate: number             // 响应率 (%)
    avg_rating: number                // 平均评分(1-5)
    nps_score: number                 // NPS 净推荐值(-100 to 100)
  }

  // 评分分布
  rating_distribution: {
    rating_5: number                  // 5星数量
    rating_4: number
    rating_3: number
    rating_2: number
    rating_1: number
  }

  // 渠道满意度
  by_channel: {
    channel: string                   // web/mobile/whatsapp
    avg_rating: number
    response_count: number
  }[]

  // 问题类型满意度
  by_category: {
    category: string                  // 问题分类
    avg_rating: number
    response_count: number
  }[]

  // 服务类型满意度
  by_service_type: {
    service_type: 'ai_only' | 'ai_then_human' | 'human_only'
    avg_rating: number
    response_count: number
  }[]

  // 负面反馈分析
  negative_feedback: {
    reason: string                    // 不满意原因
    count: number
    percentage: number
  }[]
}
```

#### 客户体验旅程

```typescript
interface CustomerJourneyMetrics {
  // 等待体验
  waiting_experience: {
    avg_queue_time: number            // 平均排队时长(s)
    max_queue_time: number            // 最大排队时长(s)
    abandon_rate: number              // 放弃率 (%)
    avg_queue_position: number        // 平均排队位置
  }

  // 响应体验
  response_experience: {
    avg_first_response: number        // 平均首次响应(s)
    avg_subsequent_response: number   // 平均后续响应(s)
    response_sla_compliance: number   // SLA 达标率 (%)
  }

  // 解决体验
  resolution_experience: {
    first_contact_resolution: number  // 一次解决率 (%)
    avg_resolution_time: number       // 平均解决时长(s)
    multi_contact_rate: number        // 多次联系率 (%)
    self_service_rate: number         // 自助解决率 (%)
  }

  // 多渠道体验
  omnichannel_experience: {
    channel_switch_rate: number       // 渠道切换率 (%)
    avg_channels_per_session: number  // 平均使用渠道数
    seamless_transition_rate: number  // 无缝切换率 (%)
  }
}
```

---

### 6.4 运营决策仪表板

**优先级**: P2
**预计工时**: 12小时

#### 实时监控仪表板

```vue
<RealtimeDashboard>
  <!-- 顶部关键指标 -->
  <MetricsBar>
    <MetricCard title="在线坐席" :value="onlineAgents" icon="users" color="blue" />
    <MetricCard title="队列长度" :value="queueLength" icon="list" color="orange"
                :alert="queueLength > 10" />
    <MetricCard title="AI成功率" :value="`${aiSuccessRate}%`" icon="robot" color="green"
                :trend="aiSuccessTrend" />
    <MetricCard title="平均CSAT" :value="avgCSAT" icon="smile" color="purple"
                :trend="csatTrend" />
  </MetricsBar>

  <!-- 实时会话列表 -->
  <ActiveSessionsPanel>
    <SessionCard v-for="session in activeSessions" :key="session.session_id">
      <Header>
        <StatusBadge :status="session.status" />
        <AgentInfo v-if="session.assigned_agent" :agent="session.assigned_agent" />
        <Duration :start="session.created_at" />
      </Header>
      <Content>
        <Customer :info="session.customer" />
        <LastMessage :message="session.last_message" />
      </Content>
    </SessionCard>
  </ActiveSessionsPanel>

  <!-- 趋势图表 -->
  <ChartsSection>
    <LineChart
      title="今日会话量趋势"
      :data="sessionTrendData"
      :series="['AI处理', '人工处理', '总计']"
    />
    <BarChart
      title="坐席负载分布"
      :data="agentLoadData"
    />
    <PieChart
      title="升级原因分布"
      :data="escalationReasonData"
    />
  </ChartsSection>

  <!-- 告警列表 -->
  <AlertPanel v-if="alerts.length">
    <AlertItem v-for="alert in alerts" :key="alert.id" :severity="alert.severity">
      <Icon :type="alert.type" />
      <Message>{{ alert.message }}</Message>
      <Action @click="handleAlert(alert)">处理</Action>
    </AlertItem>
  </AlertPanel>
</RealtimeDashboard>
```

#### 历史分析仪表板

```vue
<AnalyticsDashboard>
  <!-- 时间选择器 -->
  <TimeRangeSelector v-model="timeRange" :presets="presets" />

  <!-- 综合指标概览 -->
  <MetricsSummary>
    <Section title="AI 表现">
      <Metric label="AI成功率" :value="`${metrics.ai.success_rate}%`" :trend="trends.ai_success" />
      <Metric label="知识覆盖率" :value="`${metrics.ai.coverage_rate}%`" :trend="trends.coverage" />
      <Metric label="平均响应" :value="`${metrics.ai.avg_response}ms`" :trend="trends.response" />
    </Section>

    <Section title="坐席效率">
      <Metric label="平均处理时长" :value="`${metrics.agent.avg_handle_time}s`" />
      <Metric label="一次解决率" :value="`${metrics.agent.resolution_rate}%`" />
      <Metric label="利用率" :value="`${metrics.agent.utilization_rate}%`" />
    </Section>

    <Section title="客户体验">
      <Metric label="平均CSAT" :value="metrics.customer.avg_csat" :trend="trends.csat" />
      <Metric label="NPS" :value="metrics.customer.nps" :trend="trends.nps" />
      <Metric label="首次解决率" :value="`${metrics.customer.fcr}%`" />
    </Section>
  </MetricsSummary>

  <!-- 详细分析图表 -->
  <DetailedCharts>
    <TabView>
      <Tab title="AI 分析">
        <AIAnalysisCharts :data="aiMetrics" />
      </Tab>
      <Tab title="坐席分析">
        <AgentAnalysisCharts :data="agentMetrics" />
      </Tab>
      <Tab title="客户体验">
        <CustomerAnalysisCharts :data="customerMetrics" />
      </Tab>
      <Tab title="趋势对比">
        <TrendComparisonCharts :data="trendData" />
      </Tab>
    </TabView>
  </DetailedCharts>

  <!-- 排行榜 -->
  <RankingsPanel>
    <Leaderboard title="坐席满意度 TOP 10" :data="topAgentsByCSAT" />
    <Leaderboard title="高频问题 TOP 10" :data="topQuestions" />
    <Leaderboard title="缺失知识 TOP 10" :data="topMissingKnowledge" />
  </RankingsPanel>

  <!-- 导出功能 -->
  <ExportSection>
    <Button @click="exportPDF">导出 PDF 报告</Button>
    <Button @click="exportExcel">导出 Excel 数据</Button>
    <Button @click="scheduleReport">定时报告</Button>
  </ExportSection>
</AnalyticsDashboard>
```

---

### 6.5 智能告警系统

**优先级**: P2
**预计工时**: 4小时

#### 告警规则

```typescript
interface AlertRule {
  rule_id: string
  rule_name: string
  category: 'ai' | 'agent' | 'customer' | 'system'
  enabled: boolean

  // 触发条件
  condition: {
    metric: string                    // 指标名称
    operator: '>' | '<' | '=' | '>=' | '<='
    threshold: number                 // 阈值
    duration: number                  // 持续时长(秒)
  }

  // 严重级别
  severity: 'critical' | 'warning' | 'info'

  // 通知方式
  notification: {
    channels: ('email' | 'slack' | 'wechat' | 'sms')[]
    recipients: string[]
  }

  // 冷却时间
  cooldown: number                    // 避免重复告警(秒)
}
```

**预设告警规则**:
```json
[
  {
    "rule_name": "队列积压告警",
    "category": "agent",
    "condition": {
      "metric": "queue_length",
      "operator": ">",
      "threshold": 10,
      "duration": 300
    },
    "severity": "critical",
    "notification": {
      "channels": ["slack", "wechat"],
      "recipients": ["team_lead"]
    }
  },
  {
    "rule_name": "AI成功率下降",
    "category": "ai",
    "condition": {
      "metric": "ai_success_rate",
      "operator": "<",
      "threshold": 70,
      "duration": 1800
    },
    "severity": "warning",
    "notification": {
      "channels": ["email", "slack"],
      "recipients": ["ai_team", "ops_team"]
    }
  },
  {
    "rule_name": "CSAT异常下降",
    "category": "customer",
    "condition": {
      "metric": "avg_csat",
      "operator": "<",
      "threshold": 4.0,
      "duration": 3600
    },
    "severity": "critical",
    "notification": {
      "channels": ["email", "slack", "wechat"],
      "recipients": ["service_manager", "team_lead"]
    }
  }
]
```

---

## 📝 API 接口设计

### AI 质量分析

```http
# 获取 AI 质量指标
GET /api/analytics/ai/quality
  ?start_date={timestamp}
  &end_date={timestamp}
  &granularity=day
Authorization: Bearer {admin_token}

# 获取 AI 趋势
GET /api/analytics/ai/trend
  ?metric={metric_name}
  &start_date={timestamp}
  &end_date={timestamp}

# 获取升级原因分析
GET /api/analytics/ai/escalation-reasons
  ?start_date={timestamp}
  &end_date={timestamp}
```

### 坐席效率统计

```http
# 获取坐席绩效
GET /api/analytics/agents/{agent_id}/performance
  ?start_date={timestamp}
  &end_date={timestamp}

# 获取团队统计
GET /api/analytics/team/statistics
  ?start_date={timestamp}
  &end_date={timestamp}

# 获取坐席排行榜
GET /api/analytics/agents/leaderboard
  ?metric={metric_name}
  &limit=10
```

### 客户体验指标

```http
# 获取 CSAT 指标
GET /api/analytics/customer/csat
  ?start_date={timestamp}
  &end_date={timestamp}

# 获取客户旅程指标
GET /api/analytics/customer/journey
  ?start_date={timestamp}
  &end_date={timestamp}

# 获取负面反馈分析
GET /api/analytics/customer/negative-feedback
  ?start_date={timestamp}
  &end_date={timestamp}
```

### 实时监控

```http
# 获取实时指标
GET /api/analytics/realtime/metrics

# 获取活跃会话列表
GET /api/analytics/realtime/sessions

# 获取告警列表
GET /api/analytics/alerts?status=active&severity={severity}

# 处理告警
POST /api/analytics/alerts/{alert_id}/acknowledge
{
  "action": "resolved",
  "comment": "已联系团队处理"
}
```

### 报告导出

```http
# 生成 PDF 报告
POST /api/analytics/reports/pdf
{
  "report_type": "weekly_summary",
  "start_date": 1700000000,
  "end_date": 1700604800,
  "sections": ["ai_quality", "agent_performance", "customer_satisfaction"]
}

# 导出 Excel 数据
POST /api/analytics/reports/excel
{
  "data_type": "agent_performance",
  "start_date": 1700000000,
  "end_date": 1700604800
}

# 配置定时报告
POST /api/analytics/reports/schedule
{
  "report_type": "daily_summary",
  "frequency": "daily",
  "time": "09:00",
  "recipients": ["manager@example.com"],
  "format": "pdf"
}
```

---

## 📊 数据存储设计

### 时序数据库 (InfluxDB/TimescaleDB)

用于存储时间序列指标：
```sql
-- AI 质量指标时序表
CREATE TABLE ai_quality_metrics (
  timestamp TIMESTAMPTZ NOT NULL,
  ai_success_rate DOUBLE PRECISION,
  knowledge_coverage_rate DOUBLE PRECISION,
  avg_confidence DOUBLE PRECISION,
  avg_response_time DOUBLE PRECISION,
  PRIMARY KEY (timestamp)
);

-- 坐席绩效时序表
CREATE TABLE agent_performance_metrics (
  timestamp TIMESTAMPTZ NOT NULL,
  agent_id VARCHAR(50),
  session_count INT,
  avg_handle_time DOUBLE PRECISION,
  avg_csat DOUBLE PRECISION,
  PRIMARY KEY (timestamp, agent_id)
);

-- 创建时序索引
CREATE INDEX idx_ai_metrics_time ON ai_quality_metrics (timestamp DESC);
CREATE INDEX idx_agent_metrics_time ON agent_performance_metrics (timestamp DESC, agent_id);
```

### 聚合数据表 (PostgreSQL)

用于存储预聚合的统计数据：
```sql
-- 每日汇总表
CREATE TABLE daily_summary (
  date DATE PRIMARY KEY,
  total_sessions INT,
  ai_handled_sessions INT,
  human_handled_sessions INT,
  avg_ai_success_rate DOUBLE PRECISION,
  avg_csat DOUBLE PRECISION,
  total_agents INT,
  avg_handle_time DOUBLE PRECISION
);

-- 坐席月度绩效表
CREATE TABLE agent_monthly_performance (
  month DATE,
  agent_id VARCHAR(50),
  total_sessions INT,
  avg_handle_time DOUBLE PRECISION,
  avg_csat DOUBLE PRECISION,
  quality_score DOUBLE PRECISION,
  PRIMARY KEY (month, agent_id)
);
```

---

## 🔄 数据采集与处理

### 实时数据流

```python
# 使用 Redis Streams 实时采集指标
async def collect_realtime_metrics():
    """实时采集指标数据"""

    # 1. 从会话状态收集
    sessions = await session_store.get_all_sessions()

    # 2. 计算实时指标
    online_agents = len([s for s in sessions if s.status == "manual_live"])
    queue_length = len([s for s in sessions if s.status == "pending_manual"])
    avg_wait_time = calculate_avg_wait_time(sessions)

    # 3. 推送到 Redis Stream
    await redis.xadd(
        "analytics:realtime",
        {
            "timestamp": time.time(),
            "online_agents": online_agents,
            "queue_length": queue_length,
            "avg_wait_time": avg_wait_time
        }
    )

    # 4. 触发告警检查
    await check_alert_rules({
        "queue_length": queue_length,
        "avg_wait_time": avg_wait_time
    })
```

### 定时聚合任务

```python
# 使用 Celery 定时任务聚合数据
from celery import Celery
from celery.schedules import crontab

app = Celery('analytics')

@app.task
def aggregate_daily_metrics():
    """每天凌晨聚合前一天数据"""

    yesterday = datetime.now() - timedelta(days=1)
    start_date = yesterday.replace(hour=0, minute=0, second=0)
    end_date = yesterday.replace(hour=23, minute=59, second=59)

    # 1. 查询原始数据
    sessions = session_store.query_by_date_range(start_date, end_date)

    # 2. 计算汇总指标
    summary = {
        "date": yesterday.date(),
        "total_sessions": len(sessions),
        "ai_handled_sessions": count_ai_handled(sessions),
        "avg_ai_success_rate": calculate_ai_success_rate(sessions),
        "avg_csat": calculate_avg_csat(sessions)
    }

    # 3. 保存到汇总表
    await db.save_daily_summary(summary)

# 配置定时任务
app.conf.beat_schedule = {
    'aggregate-daily': {
        'task': 'aggregate_daily_metrics',
        'schedule': crontab(hour=1, minute=0)  # 每天凌晨1点执行
    }
}
```

---

## 📈 可视化技术栈

### 前端图表库

**推荐使用 ECharts**:
```typescript
import * as echarts from 'echarts'

// 折线图 - AI 成功率趋势
const lineChartOption = {
  title: { text: 'AI 成功率趋势' },
  xAxis: {
    type: 'time',
    data: timestamps
  },
  yAxis: {
    type: 'value',
    name: '成功率 (%)',
    min: 0,
    max: 100
  },
  series: [
    {
      name: 'AI 成功率',
      type: 'line',
      data: aiSuccessRateData,
      smooth: true,
      lineStyle: { color: '#4ECDC4' }
    }
  ],
  tooltip: { trigger: 'axis' }
}

// 柱状图 - 坐席负载分布
const barChartOption = {
  title: { text: '坐席负载分布' },
  xAxis: {
    type: 'category',
    data: agentNames
  },
  yAxis: {
    type: 'value',
    name: '会话数'
  },
  series: [
    {
      name: '会话数',
      type: 'bar',
      data: sessionCounts,
      itemStyle: { color: '#52C7B8' }
    }
  ]
}

// 饼图 - 升级原因分布
const pieChartOption = {
  title: { text: '升级原因分布' },
  series: [
    {
      name: '升级原因',
      type: 'pie',
      radius: '50%',
      data: [
        { value: 40, name: '关键词触发' },
        { value: 30, name: 'AI连续失败' },
        { value: 20, name: '高价值订单' },
        { value: 10, name: '用户主动要求' }
      ]
    }
  ]
}
```

---

## 📝 开发任务清单

### 后端任务 (18小时)

- [ ] Task 1: 数据模型设计 (3h)
  - [ ] 定义 TypeScript/Python 类型
  - [ ] 设计时序数据库表结构
  - [ ] 设计聚合数据表结构

- [ ] Task 2: 数据采集模块 (5h)
  - [ ] 实时指标采集
  - [ ] 会话数据追踪
  - [ ] 坐席行为记录

- [ ] Task 3: 数据聚合引擎 (4h)
  - [ ] 定时聚合任务（Celery）
  - [ ] 多维度汇总
  - [ ] 趋势计算

- [ ] Task 4: 分析 API (4h)
  - [ ] AI 质量分析接口
  - [ ] 坐席效率接口
  - [ ] 客户体验接口

- [ ] Task 5: 告警系统 (2h)
  - [ ] 告警规则引擎
  - [ ] 通知发送（Email/Slack）
  - [ ] 告警管理

### 前端任务 (14小时)

- [ ] Task 6: 实时监控仪表板 (5h)
  - [ ] 关键指标卡片
  - [ ] 活跃会话列表
  - [ ] 实时图表

- [ ] Task 7: 历史分析仪表板 (5h)
  - [ ] 时间选择器
  - [ ] 综合指标概览
  - [ ] 详细分析图表（ECharts）

- [ ] Task 8: 排行榜与对比 (2h)
  - [ ] 坐席排行榜
  - [ ] 问题排行榜
  - [ ] 趋势对比

- [ ] Task 9: 报告导出 (2h)
  - [ ] PDF 报告生成
  - [ ] Excel 数据导出
  - [ ] 定时报告配置

### 测试任务 (4h)

- [ ] Task 10: 单元测试 (2h)
  - [ ] 数据采集测试
  - [ ] 聚合逻辑测试
  - [ ] API 测试

- [ ] Task 11: 性能测试 (2h)
  - [ ] 大数据量查询测试
  - [ ] 实时更新延迟测试
  - [ ] 图表渲染性能测试

**预计总工时**: 36小时

---

## 📊 关键性能指标 (KPI)

### AI 质量目标

| 指标 | 目标值 | 优秀值 |
|------|-------|-------|
| AI 成功率 | > 70% | > 80% |
| 知识覆盖率 | > 80% | > 90% |
| 平均响应时间 | < 2s | < 1s |
| 升级率 | < 30% | < 20% |

### 坐席效率目标

| 指标 | 目标值 | 优秀值 |
|------|-------|-------|
| 平均处理时长 | < 5分钟 | < 3分钟 |
| 一次解决率 | > 80% | > 90% |
| 利用率 | 60-80% | 70-85% |
| CSAT | > 4.0 | > 4.5 |

### 客户体验目标

| 指标 | 目标值 | 优秀值 |
|------|-------|-------|
| 平均 CSAT | > 4.0 | > 4.5 |
| NPS | > 30 | > 50 |
| 首次解决率 | > 70% | > 85% |
| 平均等待时长 | < 2分钟 | < 1分钟 |

---

## 📚 相关文档

- 📘 [codex.md](../../codex.md) - 第6节：AI表现与运营分析
- 📘 [CLAUDE.md](../../CLAUDE.md) - 开发流程规范
- 📘 [ECharts 文档](https://echarts.apache.org/)
- 📘 [InfluxDB 文档](https://docs.influxdata.com/)
- 📘 [Celery 文档](https://docs.celeryproject.org/)

---

**文档维护者**: Claude Code
**最后更新**: 2025-11-25
**预计总工时**: 36小时
