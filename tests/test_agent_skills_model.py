"""
AgentSkill 模型单元测试

验证坐席技能字段的标准化规则与数量限制。
"""

from pydantic import ValidationError
import pytest

from src.agent_auth import AgentSkill, AgentSkillLevel, UpdateAgentSkillsRequest


def test_agent_skill_normalizes_category_and_tags():
    """技能分类与标签应自动去除空白、统一为小写并去重"""
    skill = AgentSkill(
        category="  Product  ",
        level=AgentSkillLevel.SENIOR,
        tags=[" Battery ", "battery", "Motor", "  "]
    )

    assert skill.category == "product"
    assert skill.level == AgentSkillLevel.SENIOR
    assert skill.tags == ["battery", "motor"]


def test_update_agent_skills_request_limit():
    """技能条目超过上限时触发校验错误"""
    skills = [
        AgentSkill(category=f"category-{idx}", level=AgentSkillLevel.JUNIOR, tags=[f"tag{idx}"])
        for idx in range(21)
    ]

    with pytest.raises(ValidationError):
        UpdateAgentSkillsRequest(skills=skills)
