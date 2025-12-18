# ui/configuration_simplifier.py
# -*- coding: utf-8 -*-
"""
配置简化和渐进式学习系统
提供三层配置模式（基础、高级、专家），让用户根据自己的水平逐步学习和掌握系统
"""

import json
import os
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple, Any
from dataclasses import dataclass, asdict


class ConfigMode(Enum):
    """配置模式枚举"""
    BASIC = "基础"
    ADVANCED = "高级"
    EXPERT = "专家"


class ConfigPreset(Enum):
    """配置预设枚举"""
    FAST = "快速"
    BALANCED = "平衡"
    HIGH_QUALITY = "高质量"
    CREATIVE = "创意模式"
    CUSTOM = "自定义"


@dataclass
class ConfigSnapshot:
    """配置快照，用于历史记录"""
    timestamp: str
    mode: str
    preset: str
    config_data: Dict
    description: str
    user_satisfaction: Optional[str] = None  # "满意", "能接受", "不满意"
    impact_notes: Optional[str] = None


@dataclass
class ValidationIssue:
    """配置验证问题"""
    level: str  # "warning", "error", "info"
    title: str
    description: str
    suggestion: str
    auto_fix_available: bool = False
    auto_fix_data: Optional[Dict] = None


class ConfigurationSimplifier:
    """
    配置简化器主类
    管理配置的分层展示、验证、历史记录和智能建议
    """
    
    def __init__(self, config_file: str):
        """
        初始化配置简化器
        
        Args:
            config_file: 配置文件路径
        """
        self.config_file = config_file
        self.history_file = config_file.replace('.json', '_history.json')
        self.current_mode = ConfigMode.BASIC
        self.current_preset = ConfigPreset.BALANCED
        self.history: List[ConfigSnapshot] = []
        self._load_history()
        
    # ==================== 模式管理 ====================
    
    def get_mode(self) -> ConfigMode:
        """获取当前配置模式"""
        return self.current_mode
    
    def set_mode(self, mode: ConfigMode) -> None:
        """设置配置模式"""
        self.current_mode = mode
        
    def get_mode_description(self, mode: ConfigMode) -> str:
        """获取模式描述"""
        descriptions = {
            ConfigMode.BASIC: "适合新手，只显示核心配置，使用推荐预设",
            ConfigMode.ADVANCED: "适合中级用户，显示常用配置项，支持细节调整",
            ConfigMode.EXPERT: "适合高级用户，显示所有配置项，完全控制"
        }
        return descriptions.get(mode, "")
    
    def get_next_mode_tip(self) -> Optional[str]:
        """获取下一模式的提示"""
        if self.current_mode == ConfigMode.BASIC:
            return "💡 想了解更多吗？切换到高级模式查看更多配置选项"
        elif self.current_mode == ConfigMode.ADVANCED:
            return "💡 想完全掌控吗？切换到专家模式获得完整配置权限"
        elif self.current_mode == ConfigMode.EXPERT:
            return "💡 需要简化界面？随时可以切换回基础模式"
        return None
    
    # ==================== 预设管理 ====================
    
    def get_preset_config(self, preset: ConfigPreset) -> Dict:
        """
        获取预设配置
        
        Args:
            preset: 预设类型
            
        Returns:
            预设配置字典
        """
        presets = {
            ConfigPreset.FAST: {
                "description": "成本低，生成快，质量还可以",
                "model_name": "gpt-3.5-turbo",
                "temperature": 0.7,
                "max_tokens": 4096,
                "timeout": 300,
                "estimated_time_per_chapter": "1 分钟",
                "estimated_cost_per_chapter": "$0.02",
                "use_cases": ["快速原型", "初稿生成", "大量章节"]
            },
            ConfigPreset.BALANCED: {
                "description": "成本适中，质量和速度平衡（推荐）",
                "model_name": "gpt-4",
                "temperature": 0.75,
                "max_tokens": 8192,
                "timeout": 600,
                "estimated_time_per_chapter": "2 分钟",
                "estimated_cost_per_chapter": "$0.05",
                "use_cases": ["日常写作", "标准质量", "平衡成本"]
            },
            ConfigPreset.HIGH_QUALITY: {
                "description": "成本高，质量最好",
                "model_name": "gpt-4-turbo",
                "temperature": 0.65,
                "max_tokens": 16384,
                "timeout": 900,
                "estimated_time_per_chapter": "3-4 分钟",
                "estimated_cost_per_chapter": "$0.12",
                "use_cases": ["重要章节", "高质量要求", "专业出版"]
            },
            ConfigPreset.CREATIVE: {
                "description": "高创意度，适合奇幻/科幻",
                "model_name": "gpt-4",
                "temperature": 0.90,
                "max_tokens": 8192,
                "timeout": 600,
                "estimated_time_per_chapter": "2-3 分钟",
                "estimated_cost_per_chapter": "$0.06",
                "use_cases": ["创意写作", "奇幻小说", "科幻设定"]
            }
        }
        return presets.get(preset, presets[ConfigPreset.BALANCED])
    
    def apply_preset(self, preset: ConfigPreset, current_config: Dict) -> Dict:
        """
        应用预设到当前配置
        
        Args:
            preset: 预设类型
            current_config: 当前配置
            
        Returns:
            应用预设后的配置
        """
        preset_data = self.get_preset_config(preset)
        
        # 更新主要配置项
        if "llm_configs" in current_config:
            for config_name, config in current_config["llm_configs"].items():
                config["temperature"] = preset_data["temperature"]
                config["max_tokens"] = preset_data["max_tokens"]
                config["timeout"] = preset_data["timeout"]
                # 可选：更新模型名称（如果用户想要）
                # config["model_name"] = preset_data["model_name"]
        
        self.current_preset = preset
        return current_config
    
    def get_preset_comparison(self) -> List[Dict]:
        """获取所有预设的对比信息"""
        comparison = []
        for preset in [ConfigPreset.FAST, ConfigPreset.BALANCED, 
                      ConfigPreset.HIGH_QUALITY, ConfigPreset.CREATIVE]:
            config = self.get_preset_config(preset)
            comparison.append({
                "name": preset.value,
                "description": config["description"],
                "time": config["estimated_time_per_chapter"],
                "cost": config["estimated_cost_per_chapter"],
                "use_cases": config["use_cases"]
            })
        return comparison
    
    # ==================== 配置验证 ====================
    
    def validate_config(self, config: Dict) -> List[ValidationIssue]:
        """
        验证配置并返回问题列表
        
        Args:
            config: 要验证的配置
            
        Returns:
            验证问题列表
        """
        issues = []
        
        # 检查 LLM 配置
        if "llm_configs" in config:
            for config_name, llm_config in config["llm_configs"].items():
                # 检查温度值
                temp = llm_config.get("temperature", 0.7)
                if temp > 0.9:
                    issues.append(ValidationIssue(
                        level="warning",
                        title=f"配置 '{config_name}': 温度值过高 ({temp})",
                        description="高温度值会增加创意度，但可能降低一致性和稳定性",
                        suggestion="建议：仅在创意优先的项目中使用，或同时启用一致性检查",
                        auto_fix_available=True,
                        auto_fix_data={"temperature": 0.85}
                    ))
                elif temp < 0.3:
                    issues.append(ValidationIssue(
                        level="info",
                        title=f"配置 '{config_name}': 温度值较低 ({temp})",
                        description="低温度值会提高一致性，但可能降低创意性",
                        suggestion="适合需要严格控制输出的场景",
                        auto_fix_available=False
                    ))
                
                # 检查 max_tokens
                max_tokens = llm_config.get("max_tokens", 8192)
                if max_tokens < 2000:
                    issues.append(ValidationIssue(
                        level="warning",
                        title=f"配置 '{config_name}': Max Tokens 过低 ({max_tokens})",
                        description="可能无法生成足够长度的章节内容",
                        suggestion="建议：至少设置为 4096",
                        auto_fix_available=True,
                        auto_fix_data={"max_tokens": 4096}
                    ))
                elif max_tokens > 50000:
                    issues.append(ValidationIssue(
                        level="warning",
                        title=f"配置 '{config_name}': Max Tokens 过高 ({max_tokens})",
                        description="可能导致成本过高和响应时间过长",
                        suggestion="建议：根据实际需求调整到合理范围（4096-16384）",
                        auto_fix_available=True,
                        auto_fix_data={"max_tokens": 16384}
                    ))
                
                # 检查 API Key
                api_key = llm_config.get("api_key", "")
                if not api_key or api_key.strip() == "":
                    issues.append(ValidationIssue(
                        level="error",
                        title=f"配置 '{config_name}': API Key 未设置",
                        description="没有 API Key 将无法调用 LLM 服务",
                        suggestion="请在配置中填入有效的 API Key",
                        auto_fix_available=False
                    ))
                
                # 检查超时设置
                timeout = llm_config.get("timeout", 600)
                if timeout < 60:
                    issues.append(ValidationIssue(
                        level="warning",
                        title=f"配置 '{config_name}': 超时时间过短 ({timeout}秒)",
                        description="可能导致请求在完成前超时",
                        suggestion="建议：至少设置为 300 秒",
                        auto_fix_available=True,
                        auto_fix_data={"timeout": 300}
                    ))
        
        # 检查嵌入配置
        if "embedding_configs" in config:
            for emb_name, emb_config in config["embedding_configs"].items():
                api_key = emb_config.get("api_key", "")
                if not api_key or api_key.strip() == "":
                    issues.append(ValidationIssue(
                        level="error",
                        title=f"Embedding配置 '{emb_name}': API Key 未设置",
                        description="没有 API Key 将无法使用向量检索功能",
                        suggestion="请在配置中填入有效的 API Key",
                        auto_fix_available=False
                    ))
        
        # 检查配置冲突
        issues.extend(self._check_config_conflicts(config))
        
        return issues
    
    def _check_config_conflicts(self, config: Dict) -> List[ValidationIssue]:
        """检查配置冲突"""
        conflicts = []
        
        # 这里可以添加更多的冲突检查逻辑
        # 例如：检查并行度与 API 速率限制的冲突
        
        return conflicts
    
    def auto_fix_issue(self, issue: ValidationIssue, config: Dict, 
                       config_name: str) -> Dict:
        """
        自动修复配置问题
        
        Args:
            issue: 验证问题
            config: 配置字典
            config_name: 配置名称
            
        Returns:
            修复后的配置
        """
        if not issue.auto_fix_available or not issue.auto_fix_data:
            return config
        
        if config_name in config.get("llm_configs", {}):
            config["llm_configs"][config_name].update(issue.auto_fix_data)
        
        return config
    
    # ==================== 智能建议 ====================
    
    def get_parameter_impact(self, param_name: str, 
                            old_value: Any, new_value: Any) -> Dict:
        """
        获取参数变更的影响分析
        
        Args:
            param_name: 参数名称
            old_value: 旧值
            new_value: 新值
            
        Returns:
            影响分析字典
        """
        impact = {
            "parameter": param_name,
            "old_value": old_value,
            "new_value": new_value,
            "changes": []
        }
        
        if param_name == "temperature":
            if new_value > old_value:
                impact["changes"] = [
                    {"aspect": "创意度", "change": "↑↑" if new_value - old_value > 0.2 else "↑"},
                    {"aspect": "一致性", "change": "↓↓" if new_value - old_value > 0.2 else "↓"},
                    {"aspect": "预计成本", "change": "→" if abs(new_value - old_value) < 0.1 else "↑"},
                ]
            else:
                impact["changes"] = [
                    {"aspect": "创意度", "change": "↓↓" if old_value - new_value > 0.2 else "↓"},
                    {"aspect": "一致性", "change": "↑↑" if old_value - new_value > 0.2 else "↑"},
                    {"aspect": "预计成本", "change": "→"},
                ]
            
            # 添加建议
            if new_value > 0.9:
                impact["warning"] = "⚠️ 警告: 这个温度值很高！"
                impact["recommendations"] = [
                    "仅在'创意优先'的项目中使用",
                    "同时启用'一致性检查'来弥补",
                    "考虑使用创意模式预设"
                ]
            elif new_value < 0.3:
                impact["info"] = "ℹ️ 提示: 这个温度值很低"
                impact["recommendations"] = [
                    "适合需要严格一致性的项目",
                    "输出会更加保守和可预测"
                ]
        
        elif param_name == "max_tokens":
            token_change_pct = ((new_value - old_value) / old_value) * 100
            if new_value > old_value:
                impact["changes"] = [
                    {"aspect": "章节长度", "change": f"↑ (约{token_change_pct:.0f}%)"},
                    {"aspect": "生成时间", "change": "↑"},
                    {"aspect": "成本", "change": f"↑ (约{token_change_pct:.0f}%)"},
                ]
            else:
                impact["changes"] = [
                    {"aspect": "章节长度", "change": f"↓ (约{abs(token_change_pct):.0f}%)"},
                    {"aspect": "生成时间", "change": "↓"},
                    {"aspect": "成本", "change": f"↓ (约{abs(token_change_pct):.0f}%)"},
                ]
        
        elif param_name == "timeout":
            if new_value < 300:
                impact["warning"] = "⚠️ 警告: 超时时间可能过短"
                impact["recommendations"] = [
                    "可能导致长章节生成被中断",
                    "建议至少设置为 300 秒"
                ]
        
        return impact
    
    # ==================== 历史记录 ====================
    
    def _load_history(self) -> None:
        """从文件加载历史记录"""
        if os.path.exists(self.history_file):
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.history = [
                        ConfigSnapshot(**item) for item in data
                    ]
            except Exception as e:
                print(f"加载历史记录失败: {e}")
                self.history = []
        else:
            self.history = []
    
    def _save_history(self) -> None:
        """保存历史记录到文件"""
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(
                    [asdict(snapshot) for snapshot in self.history],
                    f, ensure_ascii=False, indent=2
                )
        except Exception as e:
            print(f"保存历史记录失败: {e}")
    
    def add_history_snapshot(self, config_data: Dict, 
                            description: str) -> None:
        """
        添加配置快照到历史记录
        
        Args:
            config_data: 配置数据
            description: 变更描述
        """
        snapshot = ConfigSnapshot(
            timestamp=datetime.now().isoformat(),
            mode=self.current_mode.value,
            preset=self.current_preset.value,
            config_data=config_data.copy(),
            description=description
        )
        self.history.append(snapshot)
        
        # 只保留最近 50 条记录
        if len(self.history) > 50:
            self.history = self.history[-50:]
        
        self._save_history()
    
    def get_history(self, limit: int = 10) -> List[ConfigSnapshot]:
        """
        获取历史记录
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            历史记录列表
        """
        return self.history[-limit:][::-1]  # 返回最近的记录，倒序
    
    def restore_from_history(self, timestamp: str) -> Optional[Dict]:
        """
        从历史记录恢复配置
        
        Args:
            timestamp: 时间戳
            
        Returns:
            配置数据，如果未找到返回 None
        """
        for snapshot in self.history:
            if snapshot.timestamp == timestamp:
                return snapshot.config_data.copy()
        return None
    
    def update_snapshot_satisfaction(self, timestamp: str, 
                                    satisfaction: str, 
                                    impact_notes: str = "") -> None:
        """
        更新历史快照的满意度反馈
        
        Args:
            timestamp: 时间戳
            satisfaction: 满意度（"满意", "能接受", "不满意"）
            impact_notes: 影响说明
        """
        for snapshot in self.history:
            if snapshot.timestamp == timestamp:
                snapshot.user_satisfaction = satisfaction
                snapshot.impact_notes = impact_notes
                self._save_history()
                break
    
    # ==================== 配置导入导出 ====================
    
    def export_config(self, config: Dict, export_path: str) -> bool:
        """
        导出配置到文件
        
        Args:
            config: 配置数据
            export_path: 导出路径
            
        Returns:
            是否成功
        """
        try:
            export_data = {
                "version": "1.0",
                "exported_at": datetime.now().isoformat(),
                "mode": self.current_mode.value,
                "preset": self.current_preset.value,
                "config": config
            }
            with open(export_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            print(f"导出配置失败: {e}")
            return False
    
    def import_config(self, import_path: str) -> Optional[Dict]:
        """
        从文件导入配置
        
        Args:
            import_path: 导入路径
            
        Returns:
            配置数据，失败返回 None
        """
        try:
            with open(import_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if "config" in data:
                    return data["config"]
                return data  # 兼容旧格式
        except Exception as e:
            print(f"导入配置失败: {e}")
            return None
    
    # ==================== UI 辅助方法 ====================
    
    def get_visible_fields(self, mode: ConfigMode) -> Dict[str, List[str]]:
        """
        获取不同模式下应该显示的字段
        
        Args:
            mode: 配置模式
            
        Returns:
            字段分组字典
        """
        if mode == ConfigMode.BASIC:
            return {
                "llm": ["preset_selector", "temperature"],
                "generation": ["estimated_info"],
                "actions": ["save", "reset"]
            }
        elif mode == ConfigMode.ADVANCED:
            return {
                "llm": ["model_name", "api_key", "base_url", "max_tokens", 
                       "temperature", "top_p"],
                "optimization": ["consistency_check", "style_check", 
                               "quality_score", "auto_fix"],
                "performance": ["parallel_generation", "vector_cache"],
                "actions": ["save", "reset", "test"]
            }
        else:  # EXPERT
            return {
                "llm": ["all"],
                "embedding": ["all"],
                "generation": ["all"],
                "optimization": ["all"],
                "performance": ["all"],
                "advanced": ["all"],
                "actions": ["save", "reset", "test", "import", "export", "validate"]
            }
    
    def get_field_tooltip(self, field_name: str, mode: ConfigMode) -> str:
        """
        获取字段的工具提示（根据模式调整详细程度）
        
        Args:
            field_name: 字段名称
            mode: 配置模式
            
        Returns:
            工具提示文本
        """
        tooltips = {
            "temperature": {
                ConfigMode.BASIC: "控制创意度：低值更保守，高值更有创意",
                ConfigMode.ADVANCED: "Temperature (0.0-2.0): 控制输出的随机性。较低的值使输出更确定，较高的值使输出更多样化",
                ConfigMode.EXPERT: "Temperature 参数控制 softmax 函数的温度，影响 token 选择的概率分布。范围 0.0-2.0，推荐 0.7-0.9"
            },
            "max_tokens": {
                ConfigMode.BASIC: "控制生成内容的最大长度",
                ConfigMode.ADVANCED: "Max Tokens: 限制单次生成的最大 token 数量，影响章节长度和成本",
                ConfigMode.EXPERT: "Max Tokens: API 调用的 token 上限。注意：实际消耗 = prompt tokens + completion tokens"
            }
        }
        
        field_tooltips = tooltips.get(field_name, {})
        return field_tooltips.get(mode, "")
    
    def should_show_field(self, field_name: str, group: str, 
                         mode: ConfigMode) -> bool:
        """
        判断某个字段在当前模式下是否应该显示
        
        Args:
            field_name: 字段名称
            group: 字段分组
            mode: 配置模式
            
        Returns:
            是否显示
        """
        visible_fields = self.get_visible_fields(mode)
        
        if group not in visible_fields:
            return False
        
        fields = visible_fields[group]
        
        # 如果是 "all"，显示所有字段
        if "all" in fields:
            return True
        
        return field_name in fields
    
    # ==================== 学习路径 ====================
    
    def get_learning_resources(self, field_name: str) -> Dict:
        """
        获取字段的学习资源
        
        Args:
            field_name: 字段名称
            
        Returns:
            学习资源字典
        """
        resources = {
            "temperature": {
                "quick_tutorial": "Temperature 是什么？\n\n它控制 AI 的创意程度。想象一下写作时的灵感状态：\n• 低温度(0.3)：像严谨的技术写作，每个词都很确定\n• 中温度(0.7)：像正常的创作，既有逻辑又有创意\n• 高温度(1.2+)：像头脑风暴，充满惊喜但可能不太连贯",
                "advanced_guide": "如何根据项目选择温度？\n\n• 技术文档、历史小说：0.5-0.7（需要准确性）\n• 现代小说、传记：0.7-0.8（平衡）\n• 科幻、奇幻：0.8-1.0（需要想象力）\n• 实验性创作：1.0+（追求独特性）",
                "video_url": "https://example.com/temperature-tutorial",
                "community_discussions": "https://example.com/community/temperature"
            },
            "max_tokens": {
                "quick_tutorial": "Max Tokens 控制生成长度\n\n1 token ≈ 0.75 个英文单词 ≈ 1-2 个中文字符\n\n常见设置：\n• 短章节（1000字）：2000-3000 tokens\n• 中等章节（3000字）：6000-8000 tokens\n• 长章节（5000字+）：10000+ tokens",
                "advanced_guide": "优化 Token 使用：\n\n• 预留 20-30% 给 prompt（系统提示、上下文等）\n• 监控实际使用量，避免浪费\n• 考虑成本：tokens 越多，成本越高",
            }
        }
        return resources.get(field_name, {})
    
    def get_usage_statistics(self) -> Dict:
        """
        获取使用统计信息
        
        Returns:
            统计信息字典
        """
        if not self.history:
            return {
                "total_configs": 0,
                "most_used_preset": "无",
                "most_used_mode": "无"
            }
        
        # 统计最常用的预设
        preset_counts = {}
        mode_counts = {}
        
        for snapshot in self.history:
            preset_counts[snapshot.preset] = preset_counts.get(snapshot.preset, 0) + 1
            mode_counts[snapshot.mode] = mode_counts.get(snapshot.mode, 0) + 1
        
        most_used_preset = max(preset_counts.items(), key=lambda x: x[1])[0] if preset_counts else "无"
        most_used_mode = max(mode_counts.items(), key=lambda x: x[1])[0] if mode_counts else "无"
        
        # 计算满意度
        satisfaction_counts = {
            "满意": 0,
            "能接受": 0,
            "不满意": 0
        }
        
        for snapshot in self.history:
            if snapshot.user_satisfaction:
                satisfaction_counts[snapshot.user_satisfaction] = \
                    satisfaction_counts.get(snapshot.user_satisfaction, 0) + 1
        
        return {
            "total_configs": len(self.history),
            "most_used_preset": most_used_preset,
            "most_used_mode": most_used_mode,
            "satisfaction_stats": satisfaction_counts
        }


# ==================== 全局工具函数 ====================

def format_time_ago(timestamp_str: str) -> str:
    """
    格式化时间为相对时间（例如：2小时前）
    
    Args:
        timestamp_str: ISO 格式的时间字符串
        
    Returns:
        相对时间字符串
    """
    try:
        timestamp = datetime.fromisoformat(timestamp_str)
        now = datetime.now()
        delta = now - timestamp
        
        if delta.days > 0:
            return f"{delta.days} 天前"
        elif delta.seconds >= 3600:
            return f"{delta.seconds // 3600} 小时前"
        elif delta.seconds >= 60:
            return f"{delta.seconds // 60} 分钟前"
        else:
            return "刚刚"
    except:
        return timestamp_str


def estimate_cost_and_time(config: Dict) -> Tuple[str, str]:
    """
    估算配置的成本和时间
    
    Args:
        config: 配置字典
        
    Returns:
        (预计成本, 预计时间) 元组
    """
    # 这里可以根据模型和 token 数量进行更精确的估算
    # 简化版本：基于 max_tokens
    
    if "llm_configs" not in config:
        return ("未知", "未知")
    
    # 取第一个配置进行估算
    first_config = list(config["llm_configs"].values())[0]
    max_tokens = first_config.get("max_tokens", 8192)
    model_name = first_config.get("model_name", "").lower()
    
    # 简单的成本估算（这些是示例值，实际应根据 API 定价调整）
    if "gpt-4" in model_name:
        cost_per_1k = 0.03
        time_factor = 3
    elif "gpt-3.5" in model_name:
        cost_per_1k = 0.002
        time_factor = 1
    else:
        cost_per_1k = 0.01
        time_factor = 2
    
    estimated_cost = (max_tokens / 1000) * cost_per_1k
    estimated_time = (max_tokens / 1000) * time_factor
    
    return (f"${estimated_cost:.2f}", f"{estimated_time:.1f} 分钟")
