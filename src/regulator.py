"""
监管策略引擎模块
负责 AI 客服质量监控和人工接管触发决策

【核心功能】
1. 关键词检测 - 识别用户请求人工的意图
2. AI 失败检测 - 识别 AI 连续无法回答的情况
3. VIP 用户检测 - 识别 VIP 用户并提供优先服务
4. 优先级判断 - 按 VIP > 关键词 > 失败 的优先级触发接管

【设计原则】
- 所有规则可通过 .env 配置
- 返回统一的 EscalationResult 结构
- 无状态设计,依赖 SessionState 传入
"""

import os
import re
from typing import Optional, List, Set
from pydantic import BaseModel
from dotenv import load_dotenv

from src.session_state import (
    SessionState,
    EscalationReason,
    EscalationSeverity
)

# 加载环境变量
load_dotenv()


# ==================== 数据模型 ====================

class EscalationResult(BaseModel):
    """
    人工接管判断结果

    Attributes:
        should_escalate: 是否需要人工接管
        reason: 触发原因 (None 表示不需要接管)
        severity: 严重程度
        details: 详细说明
    """
    should_escalate: bool
    reason: Optional[EscalationReason] = None
    severity: EscalationSeverity = EscalationSeverity.LOW
    details: str = ""


# ==================== 配置加载 ====================

class RegulatorConfig:
    """监管策略配置"""

    def __init__(self):
        # 关键词配置 (用户请求人工的关键词)
        keywords_str = os.getenv(
            "REGULATOR_KEYWORDS",
            "人工,真人,客服,投诉,无法解决,转人工,接人工"
        )
        self.keywords: Set[str] = set(
            kw.strip() for kw in keywords_str.split(",") if kw.strip()
        )

        # AI 失败检测配置
        # AI 失败关键词 (AI 回复中出现这些词表示无法回答)
        fail_keywords_str = os.getenv(
            "REGULATOR_AI_FAIL_KEYWORDS",
            "抱歉,很抱歉,无法,不清楚,不太清楚,无法回答,不能确定"
        )
        self.ai_fail_keywords: Set[str] = set(
            kw.strip() for kw in fail_keywords_str.split(",") if kw.strip()
        )

        # 连续失败阈值
        self.fail_threshold: int = int(os.getenv("REGULATOR_FAIL_THRESHOLD", "3"))

        # VIP 配置
        self.vip_auto_escalate: bool = os.getenv("REGULATOR_VIP_AUTO_ESCALATE", "true").lower() == "true"

        # 严重程度配置
        self.keyword_severity: EscalationSeverity = EscalationSeverity.HIGH
        self.fail_severity: EscalationSeverity = EscalationSeverity.LOW
        self.vip_severity: EscalationSeverity = EscalationSeverity.HIGH

    def reload(self):
        """重新加载配置 (用于运行时更新)"""
        load_dotenv(override=True)
        self.__init__()


# 全局配置实例
_config = RegulatorConfig()


def get_config() -> RegulatorConfig:
    """获取全局配置实例"""
    return _config


# ==================== 监管策略引擎 ====================

class Regulator:
    """
    监管策略引擎

    提供三大检测功能:
    1. check_keyword - 检测用户消息中的关键词
    2. check_ai_failure - 检测 AI 连续失败
    3. check_vip - 检测 VIP 用户

    主方法:
    - evaluate - 综合评估是否需要人工接管 (按优先级)
    """

    def __init__(self, config: Optional[RegulatorConfig] = None):
        """
        初始化监管引擎

        Args:
            config: 配置对象 (None 则使用全局默认配置)
        """
        self.config = config or get_config()

    def check_keyword(self, user_message: str) -> Optional[EscalationResult]:
        """
        检测用户消息中的关键词

        Args:
            user_message: 用户输入的消息

        Returns:
            EscalationResult: 检测结果 (无命中则返回 None)
        """
        message_lower = user_message.lower()

        # 检测是否命中关键词
        matched_keywords = []
        for keyword in self.config.keywords:
            if keyword.lower() in message_lower:
                matched_keywords.append(keyword)

        if matched_keywords:
            return EscalationResult(
                should_escalate=True,
                reason=EscalationReason.KEYWORD,
                severity=self.config.keyword_severity,
                details=f"命中关键词: {', '.join(matched_keywords)}"
            )

        return None

    def check_ai_failure(self, session: SessionState, last_ai_response: Optional[str] = None) -> Optional[EscalationResult]:
        """
        检测 AI 连续失败

        Args:
            session: 当前会话状态
            last_ai_response: 最新的 AI 回复 (可选,用于实时检测)

        Returns:
            EscalationResult: 检测结果 (未达到阈值则返回 None)
        """
        # 如果提供了最新回复,检测是否包含失败关键词
        is_current_fail = False
        if last_ai_response:
            response_lower = last_ai_response.lower()
            for fail_keyword in self.config.ai_fail_keywords:
                if fail_keyword.lower() in response_lower:
                    is_current_fail = True
                    break

        # 计算失败次数 (考虑当前回复)
        fail_count = session.ai_fail_count
        if is_current_fail:
            fail_count += 1

        # 判断是否达到阈值
        if fail_count >= self.config.fail_threshold:
            return EscalationResult(
                should_escalate=True,
                reason=EscalationReason.FAIL_LOOP,
                severity=self.config.fail_severity,
                details=f"AI 连续失败 {fail_count} 次,已达阈值 {self.config.fail_threshold}"
            )

        return None

    def check_vip(self, session: SessionState, request_parameters: Optional[dict] = None) -> Optional[EscalationResult]:
        """
        检测 VIP 用户

        Args:
            session: 当前会话状态
            request_parameters: 请求参数 (可能包含 vip 字段)

        Returns:
            EscalationResult: 检测结果 (非 VIP 则返回 None)
        """
        if not self.config.vip_auto_escalate:
            return None

        # 检测 1: 会话中的 user_profile.vip
        is_vip = session.user_profile.vip

        # 检测 2: 请求参数中的 vip 字段
        if request_parameters and request_parameters.get("vip"):
            is_vip = True

        if is_vip:
            return EscalationResult(
                should_escalate=True,
                reason=EscalationReason.VIP,
                severity=self.config.vip_severity,
                details="VIP 用户,自动转人工"
            )

        return None

    def evaluate(
        self,
        session: SessionState,
        user_message: Optional[str] = None,
        ai_response: Optional[str] = None,
        request_parameters: Optional[dict] = None
    ) -> EscalationResult:
        """
        综合评估是否需要人工接管

        优先级: VIP > 关键词 > AI 失败

        Args:
            session: 当前会话状态
            user_message: 用户消息 (用于关键词检测)
            ai_response: AI 回复 (用于失败检测)
            request_parameters: 请求参数 (用于 VIP 检测)

        Returns:
            EscalationResult: 最终判断结果
        """
        # 优先级 1: VIP 用户
        vip_result = self.check_vip(session, request_parameters)
        if vip_result and vip_result.should_escalate:
            return vip_result

        # 优先级 2: 关键词
        if user_message:
            keyword_result = self.check_keyword(user_message)
            if keyword_result and keyword_result.should_escalate:
                return keyword_result

        # 优先级 3: AI 连续失败
        fail_result = self.check_ai_failure(session, ai_response)
        if fail_result and fail_result.should_escalate:
            return fail_result

        # 无需接管
        return EscalationResult(
            should_escalate=False,
            details="未触发任何监管规则"
        )

    def update_ai_fail_count(self, session: SessionState, ai_response: str) -> int:
        """
        更新 AI 失败计数器

        根据 AI 回复内容判断是否失败,并更新 session.ai_fail_count

        Args:
            session: 会话状态
            ai_response: AI 回复内容

        Returns:
            int: 更新后的失败次数
        """
        response_lower = ai_response.lower()

        # 检测是否包含失败关键词
        is_fail = False
        for fail_keyword in self.config.ai_fail_keywords:
            if fail_keyword.lower() in response_lower:
                is_fail = True
                break

        if is_fail:
            session.ai_fail_count += 1
        else:
            # 成功回复,重置计数器
            session.ai_fail_count = 0

        return session.ai_fail_count


# ==================== 便捷函数 ====================

def create_regulator(config: Optional[RegulatorConfig] = None) -> Regulator:
    """
    创建监管引擎实例

    Args:
        config: 自定义配置 (None 则使用全局配置)

    Returns:
        Regulator: 监管引擎实例
    """
    return Regulator(config=config)


# ==================== 导出 ====================

__all__ = [
    "Regulator",
    "RegulatorConfig",
    "EscalationResult",
    "create_regulator",
    "get_config"
]
