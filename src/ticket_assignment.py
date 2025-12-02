"""
智能分配算法核心模块

实现思路：
- 过滤在线坐席
- 优先匹配技能标签
- 统计当前工作负载（人工会话+已分配待接入会话）
- 结合历史偏好（同一客户优先安排熟悉坐席）
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Dict, List, Optional, Set

from src.agent_auth import Agent, AgentManager, AgentStatus, AgentSkill
from src.session_state import (
    AgentInfo,
    SessionState,
    SessionStateStore,
    SessionStatus,
)


@dataclass
class AgentSnapshot:
    """坐席快照，包含技能和负载信息"""
    agent: Agent
    manual_sessions: int = 0
    pending_sessions: int = 0

    @property
    def load_score(self) -> float:
        """人工会话权重更高"""
        return self.manual_sessions * 2 + self.pending_sessions

    def skill_tags(self) -> Set[str]:
        tags: Set[str] = set()
        for skill in self.agent.skills or []:
            tags.add(skill.category)
            tags.update(skill.tags)
        return tags


@dataclass
class AssignmentDecision:
    """智能分配结果"""
    agent: AgentInfo
    matched_tags: List[str]
    manual_sessions: int
    pending_sessions: int
    load_score: float


class SmartAssignmentEngine:
    """坐席智能分配引擎"""

    STATUS_PRIORITY = {
        AgentStatus.ONLINE: 0,
        AgentStatus.BUSY: 1,
        AgentStatus.BREAK: 2,
        AgentStatus.LUNCH: 2,
        AgentStatus.TRAINING: 3,
        AgentStatus.OFFLINE: 4,
    }

    def __init__(
        self,
        agent_manager: AgentManager,
        session_store: SessionStateStore,
    ):
        self.agent_manager = agent_manager
        self.session_store = session_store
        # 最近一次成功分配的客户 -> 坐席映射，用于简单的历史偏好
        self._customer_agent_cache: Dict[str, str] = {}

    async def assign_session(
        self,
        session_state: SessionState,
        remember_choice: bool = True
    ) -> Optional[AssignmentDecision]:
        """根据会话状态选择最合适的坐席"""
        if not self.agent_manager:
            return None

        available_agents = self._get_available_agents()
        if not available_agents:
            return None

        loads = await self._calculate_agent_loads()
        context_tags = self._collect_session_tags(session_state)

        candidates = self._filter_by_skills(available_agents, context_tags)
        if not candidates:
            candidates = available_agents

        snapshots = self._build_snapshots(candidates, loads)

        preferred_agent_id = self._find_preferred_agent(session_state, snapshots)
        if preferred_agent_id:
            chosen = next((snap for snap in snapshots if snap.agent.id == preferred_agent_id), None)
            if chosen:
                decision = self._build_decision(chosen, context_tags)
                if remember_choice:
                    self._remember_customer(session_state, decision.agent.id)
                return decision

        sorted_candidates = sorted(
            snapshots,
            key=lambda snap: (
                self.STATUS_PRIORITY.get(snap.agent.status, 5),
                snap.load_score,
                snap.manual_sessions,
                snap.pending_sessions,
                snap.agent.id
            )
        )

        if not sorted_candidates:
            return None

        decision = self._build_decision(sorted_candidates[0], context_tags)
        if remember_choice:
            self._remember_customer(session_state, decision.agent.id)
        return decision

    def remember_assignment(self, session_state: SessionState, agent_id: str):
        """
        记录人工接入的坐席，供后续历史偏好使用
        """
        self._remember_customer(session_state, agent_id)

    async def _calculate_agent_loads(self) -> Dict[str, Dict[str, int]]:
        loads: Dict[str, Dict[str, int]] = defaultdict(lambda: {"manual": 0, "pending": 0})

        manual_sessions = await self.session_store.list_by_status(SessionStatus.MANUAL_LIVE, limit=1000)
        for session in manual_sessions:
            if session.assigned_agent:
                loads[session.assigned_agent.id]["manual"] += 1

        pending_sessions = await self.session_store.list_by_status(SessionStatus.PENDING_MANUAL, limit=1000)
        for session in pending_sessions:
            if session.assigned_agent:
                loads[session.assigned_agent.id]["pending"] += 1

        return loads

    def _get_available_agents(self) -> List[Agent]:
        """
        获取可用坐席（在线或忙碌状态）
        """
        candidates: List[Agent] = []
        for agent in self.agent_manager.get_all_agents():
            status = agent.status if isinstance(agent.status, AgentStatus) else AgentStatus(agent.status)
            if status in {AgentStatus.ONLINE, AgentStatus.BUSY}:
                candidates.append(agent)
        return candidates

    def _filter_by_skills(self, agents: List[Agent], tags: Set[str]) -> List[Agent]:
        if not tags:
            return agents

        matched: List[Agent] = []
        for agent in agents:
            skill_tags = set()
            for skill in agent.skills or []:
                skill_tags.add(skill.category)
                skill_tags.update(skill.tags)

            if skill_tags.intersection(tags):
                matched.append(agent)

        return matched

    def _build_snapshots(
        self,
        agents: List[Agent],
        loads: Dict[str, Dict[str, int]]
    ) -> List[AgentSnapshot]:
        snapshots: List[AgentSnapshot] = []
        for agent in agents:
            agent_load = loads.get(agent.id, {"manual": 0, "pending": 0})
            snapshots.append(
                AgentSnapshot(
                    agent=agent,
                    manual_sessions=agent_load["manual"],
                    pending_sessions=agent_load["pending"]
                )
            )
        return snapshots

    def _build_decision(
        self,
        snapshot: AgentSnapshot,
        context_tags: Set[str]
    ) -> AssignmentDecision:
        matched = sorted(list(snapshot.skill_tags().intersection(context_tags)))
        return AssignmentDecision(
            agent=AgentInfo(id=snapshot.agent.id, name=snapshot.agent.name),
            matched_tags=matched,
            manual_sessions=snapshot.manual_sessions,
            pending_sessions=snapshot.pending_sessions,
            load_score=snapshot.load_score
        )

    def _collect_session_tags(self, session_state: SessionState) -> Set[str]:
        tags: Set[str] = set()

        profile = session_state.user_profile
        if profile.metadata:
            for key in ("category", "product", "issue_type", "tags"):
                value = profile.metadata.get(key)
                self._normalize_tags(value, tags)

        if session_state.priority and session_state.priority.urgent_keywords:
            self._normalize_tags(session_state.priority.urgent_keywords, tags)

        if session_state.escalation:
            tags.add(session_state.escalation.reason.value)

        return tags

    def _normalize_tags(self, value, output: Set[str]):
        if not value:
            return
        if isinstance(value, str):
            normalized = value.strip().lower()
            if normalized:
                output.add(normalized)
        elif isinstance(value, (list, tuple, set)):
            for item in value:
                self._normalize_tags(item, output)
        elif isinstance(value, dict):
            for item in value.values():
                self._normalize_tags(item, output)

    def _find_preferred_agent(
        self,
        session_state: SessionState,
        snapshots: List[AgentSnapshot]
    ) -> Optional[str]:
        """
        根据历史缓存寻找优先坐席
        """
        customer_key = self._customer_key(session_state)
        if not customer_key:
            return None

        preferred = self._customer_agent_cache.get(customer_key)
        if not preferred:
            return None

        if any(snap.agent.id == preferred for snap in snapshots):
            return preferred

        return None

    def _remember_customer(self, session_state: SessionState, agent_id: str):
        key = self._customer_key(session_state)
        if key:
            self._customer_agent_cache[key] = agent_id

    def _customer_key(self, session_state: SessionState) -> Optional[str]:
        """
        生成客户唯一标识（优先使用邮箱）
        """
        profile = session_state.user_profile
        if profile and profile.email:
            return profile.email.strip().lower()

        metadata = profile.metadata if profile and profile.metadata else {}
        potential = metadata.get("customer_id") or metadata.get("phone")
        if isinstance(potential, str) and potential.strip():
            return potential.strip().lower()

        return None
