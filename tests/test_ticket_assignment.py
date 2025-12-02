"""
SmartAssignmentEngine 单元测试

覆盖场景：
- 技能匹配优先
- 负载均衡（已有会话的坐席权重更高）
"""

import asyncio
import pytest

from src.agent_auth import Agent, AgentRole, AgentStatus, AgentSkill, AgentSkillLevel
from src.session_state import SessionState, InMemorySessionStore, AgentInfo, SessionStatus
from src.ticket_assignment import SmartAssignmentEngine


class FakeAgentManager:
    """测试专用的坐席管理器"""

    def __init__(self, agents):
        self._agents = agents

    def get_all_agents(self):
        return self._agents


def _make_agent(agent_id: str, *, status: AgentStatus = AgentStatus.ONLINE, skills=None) -> Agent:
    return Agent(
        id=agent_id,
        username=f"{agent_id}_user",
        password_hash="hash",
        name=f"Agent {agent_id}",
        role=AgentRole.AGENT,
        status=status,
        skills=skills or []
    )


def test_assign_prefers_skill_match():
    """当存在技能匹配的坐席时，应优先分配"""
    store = InMemorySessionStore()
    agents = [
        _make_agent("agent_a", skills=[AgentSkill(category="battery", level=AgentSkillLevel.SENIOR, tags=["battery"])]),
        _make_agent("agent_b", skills=[AgentSkill(category="logistics", level=AgentSkillLevel.INTERMEDIATE, tags=["shipping"])])
    ]
    engine = SmartAssignmentEngine(agent_manager=FakeAgentManager(agents), session_store=store)

    session = SessionState(session_name="session_1")
    session.user_profile.metadata["category"] = "Battery"

    assigned = asyncio.run(engine.assign_session(session))
    assert assigned is not None
    assert assigned.agent.id == "agent_a"


def test_assign_balances_existing_load():
    """已有人工会话的坐席负载更高，应优先选择空闲坐席"""
    store = InMemorySessionStore()
    agents = [
        _make_agent("agent_busy", skills=[AgentSkill(category="battery", level=AgentSkillLevel.INTERMEDIATE, tags=["battery"])]),
        _make_agent("agent_free", skills=[AgentSkill(category="battery", level=AgentSkillLevel.INTERMEDIATE, tags=["battery"])])
    ]
    engine = SmartAssignmentEngine(agent_manager=FakeAgentManager(agents), session_store=store)

    # 模拟 agent_busy 正在处理人工会话
    session_live = SessionState(session_name="existing_session")
    session_live.status = SessionStatus.MANUAL_LIVE
    session_live.assigned_agent = AgentInfo(id="agent_busy", name="Agent Busy")
    asyncio.run(store.save(session_live))

    # 新增一个待分配会话
    new_session = SessionState(session_name="new_session")
    new_session.user_profile.metadata["category"] = "battery"

    assigned = asyncio.run(engine.assign_session(new_session))
    assert assigned is not None
    assert assigned.agent.id == "agent_free"
