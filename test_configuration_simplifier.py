# test_configuration_simplifier.py
# -*- coding: utf-8 -*-
"""
配置简化器单元测试
测试配置管理、验证、历史记录等功能
"""

import unittest
import os
import json
import tempfile
from datetime import datetime
from ui.configuration_simplifier import (
    ConfigurationSimplifier,
    ConfigMode,
    ConfigPreset,
    ValidationIssue,
    ConfigSnapshot,
    format_time_ago,
    estimate_cost_and_time
)


class TestConfigurationSimplifier(unittest.TestCase):
    """测试 ConfigurationSimplifier 类"""
    
    def setUp(self):
        """测试前准备"""
        # 创建临时配置文件
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = os.path.join(self.temp_dir, "test_config.json")
        
        # 创建测试配置
        self.test_config = {
            "llm_configs": {
                "test_config": {
                    "api_key": "test_key",
                    "base_url": "https://api.test.com",
                    "model_name": "gpt-4",
                    "temperature": 0.7,
                    "max_tokens": 8192,
                    "timeout": 600,
                    "interface_format": "OpenAI"
                }
            },
            "embedding_configs": {
                "test_embedding": {
                    "api_key": "embed_key",
                    "base_url": "https://api.test.com",
                    "model_name": "text-embedding-ada-002",
                    "retrieval_k": 4,
                    "interface_format": "OpenAI"
                }
            }
        }
        
        # 保存测试配置
        with open(self.config_file, 'w', encoding='utf-8') as f:
            json.dump(self.test_config, f)
        
        # 创建 simplifier 实例
        self.simplifier = ConfigurationSimplifier(self.config_file)
    
    def tearDown(self):
        """测试后清理"""
        # 删除临时文件
        if os.path.exists(self.config_file):
            os.remove(self.config_file)
        
        history_file = self.config_file.replace('.json', '_history.json')
        if os.path.exists(history_file):
            os.remove(history_file)
        
        os.rmdir(self.temp_dir)
    
    # ==================== 模式管理测试 ====================
    
    def test_get_set_mode(self):
        """测试模式的获取和设置"""
        # 默认应该是基础模式
        self.assertEqual(self.simplifier.get_mode(), ConfigMode.BASIC)
        
        # 设置为高级模式
        self.simplifier.set_mode(ConfigMode.ADVANCED)
        self.assertEqual(self.simplifier.get_mode(), ConfigMode.ADVANCED)
        
        # 设置为专家模式
        self.simplifier.set_mode(ConfigMode.EXPERT)
        self.assertEqual(self.simplifier.get_mode(), ConfigMode.EXPERT)
    
    def test_get_mode_description(self):
        """测试模式描述"""
        for mode in [ConfigMode.BASIC, ConfigMode.ADVANCED, ConfigMode.EXPERT]:
            desc = self.simplifier.get_mode_description(mode)
            self.assertIsInstance(desc, str)
            self.assertTrue(len(desc) > 0)
    
    def test_get_next_mode_tip(self):
        """测试下一模式提示"""
        # 基础模式应该提示高级模式
        self.simplifier.set_mode(ConfigMode.BASIC)
        tip = self.simplifier.get_next_mode_tip()
        self.assertIn("高级", tip)
        
        # 高级模式应该提示专家模式
        self.simplifier.set_mode(ConfigMode.ADVANCED)
        tip = self.simplifier.get_next_mode_tip()
        self.assertIn("专家", tip)
        
        # 专家模式应该提示基础模式
        self.simplifier.set_mode(ConfigMode.EXPERT)
        tip = self.simplifier.get_next_mode_tip()
        self.assertIn("基础", tip)
    
    # ==================== 预设管理测试 ====================
    
    def test_get_preset_config(self):
        """测试获取预设配置"""
        for preset in [ConfigPreset.FAST, ConfigPreset.BALANCED, 
                      ConfigPreset.HIGH_QUALITY, ConfigPreset.CREATIVE]:
            config = self.simplifier.get_preset_config(preset)
            
            # 检查必需的字段
            self.assertIn("description", config)
            self.assertIn("model_name", config)
            self.assertIn("temperature", config)
            self.assertIn("max_tokens", config)
            self.assertIn("timeout", config)
            self.assertIn("estimated_time_per_chapter", config)
            self.assertIn("estimated_cost_per_chapter", config)
    
    def test_apply_preset(self):
        """测试应用预设"""
        config = self.test_config.copy()
        
        # 应用快速预设
        updated_config = self.simplifier.apply_preset(ConfigPreset.FAST, config)
        
        # 检查温度是否已更新
        preset_data = self.simplifier.get_preset_config(ConfigPreset.FAST)
        self.assertEqual(
            updated_config["llm_configs"]["test_config"]["temperature"],
            preset_data["temperature"]
        )
    
    def test_get_preset_comparison(self):
        """测试获取预设对比"""
        comparison = self.simplifier.get_preset_comparison()
        
        # 应该有 4 个预设
        self.assertEqual(len(comparison), 4)
        
        # 每个预设应该有必需的字段
        for preset_info in comparison:
            self.assertIn("name", preset_info)
            self.assertIn("description", preset_info)
            self.assertIn("time", preset_info)
            self.assertIn("cost", preset_info)
            self.assertIn("use_cases", preset_info)
    
    # ==================== 配置验证测试 ====================
    
    def test_validate_config_success(self):
        """测试验证成功的配置"""
        issues = self.simplifier.validate_config(self.test_config)
        
        # 应该没有错误（可能有警告）
        errors = [i for i in issues if i.level == "error"]
        self.assertEqual(len(errors), 0)
    
    def test_validate_high_temperature(self):
        """测试高温度值的验证"""
        config = self.test_config.copy()
        config["llm_configs"]["test_config"]["temperature"] = 1.5
        
        issues = self.simplifier.validate_config(config)
        
        # 应该有温度警告
        temp_issues = [i for i in issues if "温度" in i.title]
        self.assertTrue(len(temp_issues) > 0)
    
    def test_validate_low_max_tokens(self):
        """测试低 max_tokens 的验证"""
        config = self.test_config.copy()
        config["llm_configs"]["test_config"]["max_tokens"] = 1000
        
        issues = self.simplifier.validate_config(config)
        
        # 应该有 max_tokens 警告
        token_issues = [i for i in issues if "Max Tokens" in i.title]
        self.assertTrue(len(token_issues) > 0)
    
    def test_validate_missing_api_key(self):
        """测试缺少 API Key 的验证"""
        config = self.test_config.copy()
        config["llm_configs"]["test_config"]["api_key"] = ""
        
        issues = self.simplifier.validate_config(config)
        
        # 应该有 API Key 错误
        key_issues = [i for i in issues if "API Key" in i.title and i.level == "error"]
        self.assertTrue(len(key_issues) > 0)
    
    def test_validate_short_timeout(self):
        """测试过短的超时时间"""
        config = self.test_config.copy()
        config["llm_configs"]["test_config"]["timeout"] = 30
        
        issues = self.simplifier.validate_config(config)
        
        # 应该有超时警告
        timeout_issues = [i for i in issues if "超时" in i.title]
        self.assertTrue(len(timeout_issues) > 0)
    
    def test_auto_fix_issue(self):
        """测试自动修复问题"""
        config = self.test_config.copy()
        
        # 创建一个可自动修复的问题
        issue = ValidationIssue(
            level="warning",
            title="测试问题",
            description="测试描述",
            suggestion="测试建议",
            auto_fix_available=True,
            auto_fix_data={"temperature": 0.8}
        )
        
        # 修复问题
        fixed_config = self.simplifier.auto_fix_issue(
            issue, config, "test_config"
        )
        
        # 检查是否已修复
        self.assertEqual(
            fixed_config["llm_configs"]["test_config"]["temperature"],
            0.8
        )
    
    # ==================== 智能建议测试 ====================
    
    def test_get_parameter_impact_temperature(self):
        """测试温度参数的影响分析"""
        # 测试温度升高
        impact = self.simplifier.get_parameter_impact(
            "temperature", 0.7, 0.9
        )
        
        self.assertEqual(impact["parameter"], "temperature")
        self.assertEqual(impact["old_value"], 0.7)
        self.assertEqual(impact["new_value"], 0.9)
        self.assertTrue(len(impact["changes"]) > 0)
        
        # 应该有创意度增加的提示
        creativity_change = next(
            (c for c in impact["changes"] if "创意度" in c["aspect"]),
            None
        )
        self.assertIsNotNone(creativity_change)
        self.assertIn("↑", creativity_change["change"])
    
    def test_get_parameter_impact_max_tokens(self):
        """测试 max_tokens 参数的影响分析"""
        impact = self.simplifier.get_parameter_impact(
            "max_tokens", 4096, 8192
        )
        
        self.assertEqual(impact["parameter"], "max_tokens")
        self.assertTrue(len(impact["changes"]) > 0)
        
        # 应该有成本增加的提示
        cost_change = next(
            (c for c in impact["changes"] if "成本" in c["aspect"]),
            None
        )
        self.assertIsNotNone(cost_change)
    
    # ==================== 历史记录测试 ====================
    
    def test_add_history_snapshot(self):
        """测试添加历史快照"""
        config = self.test_config.copy()
        
        # 添加快照
        self.simplifier.add_history_snapshot(config, "测试快照")
        
        # 获取历史
        history = self.simplifier.get_history(limit=10)
        
        # 应该有一条记录
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0].description, "测试快照")
    
    def test_get_history(self):
        """测试获取历史记录"""
        # 添加多个快照
        for i in range(5):
            config = self.test_config.copy()
            self.simplifier.add_history_snapshot(config, f"快照 {i}")
        
        # 获取历史
        history = self.simplifier.get_history(limit=3)
        
        # 应该返回最近的 3 条
        self.assertEqual(len(history), 3)
        
        # 应该是倒序（最新的在前）
        self.assertEqual(history[0].description, "快照 4")
        self.assertEqual(history[1].description, "快照 3")
        self.assertEqual(history[2].description, "快照 2")
    
    def test_restore_from_history(self):
        """测试从历史恢复配置"""
        # 添加快照
        config = self.test_config.copy()
        config["llm_configs"]["test_config"]["temperature"] = 0.9
        self.simplifier.add_history_snapshot(config, "高温度配置")
        
        # 获取时间戳
        history = self.simplifier.get_history(limit=1)
        timestamp = history[0].timestamp
        
        # 恢复配置
        restored_config = self.simplifier.restore_from_history(timestamp)
        
        # 检查是否正确恢复
        self.assertIsNotNone(restored_config)
        self.assertEqual(
            restored_config["llm_configs"]["test_config"]["temperature"],
            0.9
        )
    
    def test_update_snapshot_satisfaction(self):
        """测试更新快照满意度"""
        # 添加快照
        config = self.test_config.copy()
        self.simplifier.add_history_snapshot(config, "测试配置")
        
        # 获取时间戳
        history = self.simplifier.get_history(limit=1)
        timestamp = history[0].timestamp
        
        # 更新满意度
        self.simplifier.update_snapshot_satisfaction(
            timestamp, "满意", "效果很好"
        )
        
        # 检查是否已更新
        history = self.simplifier.get_history(limit=1)
        self.assertEqual(history[0].user_satisfaction, "满意")
        self.assertEqual(history[0].impact_notes, "效果很好")
    
    # ==================== 导入导出测试 ====================
    
    def test_export_import_config(self):
        """测试配置的导出和导入"""
        export_file = os.path.join(self.temp_dir, "export.json")
        
        # 导出配置
        success = self.simplifier.export_config(self.test_config, export_file)
        self.assertTrue(success)
        self.assertTrue(os.path.exists(export_file))
        
        # 导入配置
        imported_config = self.simplifier.import_config(export_file)
        self.assertIsNotNone(imported_config)
        
        # 检查配置是否一致
        self.assertEqual(
            imported_config["llm_configs"]["test_config"]["temperature"],
            self.test_config["llm_configs"]["test_config"]["temperature"]
        )
        
        # 清理
        os.remove(export_file)
    
    # ==================== UI 辅助方法测试 ====================
    
    def test_get_visible_fields(self):
        """测试获取可见字段"""
        # 基础模式
        basic_fields = self.simplifier.get_visible_fields(ConfigMode.BASIC)
        self.assertIn("llm", basic_fields)
        self.assertIn("temperature", basic_fields["llm"])
        
        # 高级模式
        advanced_fields = self.simplifier.get_visible_fields(ConfigMode.ADVANCED)
        self.assertIn("llm", advanced_fields)
        self.assertIn("optimization", advanced_fields)
        
        # 专家模式
        expert_fields = self.simplifier.get_visible_fields(ConfigMode.EXPERT)
        self.assertIn("llm", expert_fields)
        self.assertEqual(expert_fields["llm"], ["all"])
    
    def test_should_show_field(self):
        """测试字段显示判断"""
        # 基础模式下应该显示 temperature
        self.assertTrue(
            self.simplifier.should_show_field("temperature", "llm", ConfigMode.BASIC)
        )
        
        # 基础模式下不应该显示 top_p
        self.assertFalse(
            self.simplifier.should_show_field("top_p", "llm", ConfigMode.BASIC)
        )
        
        # 专家模式下应该显示所有字段
        self.simplifier.set_mode(ConfigMode.EXPERT)
        self.assertTrue(
            self.simplifier.should_show_field("any_field", "llm", ConfigMode.EXPERT)
        )
    
    def test_get_field_tooltip(self):
        """测试获取字段工具提示"""
        # 基础模式的提示应该简单
        basic_tooltip = self.simplifier.get_field_tooltip("temperature", ConfigMode.BASIC)
        self.assertIsInstance(basic_tooltip, str)
        
        # 专家模式的提示应该详细
        expert_tooltip = self.simplifier.get_field_tooltip("temperature", ConfigMode.EXPERT)
        self.assertIsInstance(expert_tooltip, str)
    
    def test_get_learning_resources(self):
        """测试获取学习资源"""
        resources = self.simplifier.get_learning_resources("temperature")
        
        self.assertIn("quick_tutorial", resources)
        self.assertIsInstance(resources["quick_tutorial"], str)
    
    def test_get_usage_statistics(self):
        """测试获取使用统计"""
        # 添加一些历史记录
        for i in range(3):
            config = self.test_config.copy()
            self.simplifier.add_history_snapshot(config, f"测试 {i}")
        
        stats = self.simplifier.get_usage_statistics()
        
        self.assertIn("total_configs", stats)
        self.assertIn("most_used_preset", stats)
        self.assertIn("most_used_mode", stats)
        self.assertEqual(stats["total_configs"], 3)


class TestUtilityFunctions(unittest.TestCase):
    """测试工具函数"""
    
    def test_format_time_ago(self):
        """测试时间格式化"""
        # 当前时间
        now = datetime.now().isoformat()
        result = format_time_ago(now)
        self.assertEqual(result, "刚刚")
        
        # 无效时间字符串
        result = format_time_ago("invalid")
        self.assertEqual(result, "invalid")
    
    def test_estimate_cost_and_time(self):
        """测试成本和时间估算"""
        config = {
            "llm_configs": {
                "test": {
                    "model_name": "gpt-4",
                    "max_tokens": 8192
                }
            }
        }
        
        cost, time = estimate_cost_and_time(config)
        
        self.assertIsInstance(cost, str)
        self.assertIsInstance(time, str)
        self.assertIn("$", cost)
        self.assertIn("分钟", time)


if __name__ == "__main__":
    unittest.main()
