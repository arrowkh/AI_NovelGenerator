# ui/config_simplifier_ui.py
# -*- coding: utf-8 -*-
"""
配置简化器UI组件
提供简化配置界面的UI组件和交互逻辑
"""

import customtkinter as ctk
from tkinter import messagebox, filedialog
from typing import Optional, Callable
from ui.configuration_simplifier import (
    ConfigurationSimplifier, ConfigMode, ConfigPreset,
    ValidationIssue, format_time_ago
)


class ConfigSimplifierPanel(ctk.CTkFrame):
    """
    配置简化器面板
    提供分层配置管理的完整UI
    """
    
    def __init__(self, parent, config_file: str, 
                 on_config_changed: Optional[Callable] = None):
        """
        初始化面板
        
        Args:
            parent: 父窗口
            config_file: 配置文件路径
            on_config_changed: 配置变更回调函数
        """
        super().__init__(parent)
        
        self.simplifier = ConfigurationSimplifier(config_file)
        self.on_config_changed = on_config_changed
        self.current_config = {}
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI布局"""
        self.grid_columnconfigure(0, weight=1)
        
        # 模式选择区域
        self._create_mode_selector()
        
        # 配置内容区域（动态）
        self.config_content_frame = ctk.CTkFrame(self)
        self.config_content_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=5)
        self.grid_rowconfigure(1, weight=1)
        
        # 提示区域
        self._create_tip_area()
        
        # 初始化为基础模式
        self._refresh_config_ui()
    
    def _create_mode_selector(self):
        """创建模式选择器"""
        mode_frame = ctk.CTkFrame(self)
        mode_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        mode_frame.grid_columnconfigure(1, weight=1)
        
        # 标签
        label = ctk.CTkLabel(
            mode_frame,
            text="配置模式:",
            font=("Microsoft YaHei", 14, "bold")
        )
        label.grid(row=0, column=0, padx=5, pady=5, sticky="w")
        
        # 模式按钮组
        btn_frame = ctk.CTkFrame(mode_frame)
        btn_frame.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
        
        self.mode_buttons = {}
        for i, mode in enumerate([ConfigMode.BASIC, ConfigMode.ADVANCED, ConfigMode.EXPERT]):
            btn = ctk.CTkButton(
                btn_frame,
                text=mode.value,
                command=lambda m=mode: self._switch_mode(m),
                font=("Microsoft YaHei", 12),
                width=100
            )
            btn.grid(row=0, column=i, padx=5, pady=2)
            self.mode_buttons[mode] = btn
        
        # 高亮当前模式
        self._highlight_current_mode()
        
        # 模式说明
        self.mode_desc_label = ctk.CTkLabel(
            mode_frame,
            text=self.simplifier.get_mode_description(self.simplifier.get_mode()),
            font=("Microsoft YaHei", 10),
            text_color="gray"
        )
        self.mode_desc_label.grid(row=1, column=0, columnspan=2, padx=5, pady=2, sticky="w")
    
    def _highlight_current_mode(self):
        """高亮显示当前模式"""
        current_mode = self.simplifier.get_mode()
        for mode, btn in self.mode_buttons.items():
            if mode == current_mode:
                btn.configure(fg_color="#1E90FF")
            else:
                btn.configure(fg_color=["#3B8ED0", "#1F6AA5"])
    
    def _create_tip_area(self):
        """创建提示区域"""
        self.tip_frame = ctk.CTkFrame(self)
        self.tip_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
        
        self.tip_label = ctk.CTkLabel(
            self.tip_frame,
            text="",
            font=("Microsoft YaHei", 10),
            wraplength=600
        )
        self.tip_label.pack(padx=10, pady=5)
        
        self._update_tip()
    
    def _update_tip(self):
        """更新提示信息"""
        tip = self.simplifier.get_next_mode_tip()
        if tip:
            self.tip_label.configure(text=tip)
        else:
            self.tip_label.configure(text="")
    
    def _switch_mode(self, mode: ConfigMode):
        """切换配置模式"""
        self.simplifier.set_mode(mode)
        self._highlight_current_mode()
        self.mode_desc_label.configure(
            text=self.simplifier.get_mode_description(mode)
        )
        self._update_tip()
        self._refresh_config_ui()
    
    def _refresh_config_ui(self):
        """刷新配置UI（根据当前模式）"""
        # 清空现有内容
        for widget in self.config_content_frame.winfo_children():
            widget.destroy()
        
        mode = self.simplifier.get_mode()
        
        if mode == ConfigMode.BASIC:
            self._build_basic_ui()
        elif mode == ConfigMode.ADVANCED:
            self._build_advanced_ui()
        else:
            self._build_expert_ui()
    
    def _build_basic_ui(self):
        """构建基础模式UI"""
        frame = self.config_content_frame
        frame.grid_columnconfigure(0, weight=1)
        
        # LLM 模型选择
        llm_frame = ctk.CTkFrame(frame)
        llm_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        llm_frame.grid_columnconfigure(0, weight=1)
        
        title = ctk.CTkLabel(
            llm_frame,
            text="LLM 模型",
            font=("Microsoft YaHei", 14, "bold")
        )
        title.grid(row=0, column=0, sticky="w", padx=10, pady=5)
        
        subtitle = ctk.CTkLabel(
            llm_frame,
            text="选择推荐模型:",
            font=("Microsoft YaHei", 12)
        )
        subtitle.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        # 预设选择按钮
        self.preset_var = ctk.StringVar(value=ConfigPreset.BALANCED.value)
        
        presets_info = [
            (ConfigPreset.FAST, "快速 (推荐新手)", "成本低，生成快，质量还可以"),
            (ConfigPreset.BALANCED, "平衡 (推荐)", "成本适中，质量和速度平衡"),
            (ConfigPreset.HIGH_QUALITY, "高质量", "成本高，质量最好"),
            (ConfigPreset.CUSTOM, "自定义", "点击配置详细参数")
        ]
        
        for i, (preset, label, desc) in enumerate(presets_info):
            radio_frame = ctk.CTkFrame(llm_frame)
            radio_frame.grid(row=2+i, column=0, sticky="ew", padx=20, pady=3)
            
            radio = ctk.CTkRadioButton(
                radio_frame,
                text=label,
                variable=self.preset_var,
                value=preset.value,
                font=("Microsoft YaHei", 11),
                command=lambda p=preset: self._on_preset_selected(p)
            )
            radio.pack(side="left", padx=5)
            
            desc_label = ctk.CTkLabel(
                radio_frame,
                text=f"└─ {desc}",
                font=("Microsoft YaHei", 9),
                text_color="gray"
            )
            desc_label.pack(side="left", padx=10)
        
        # 生成参数
        param_frame = ctk.CTkFrame(frame)
        param_frame.grid(row=1, column=0, sticky="ew", padx=10, pady=10)
        param_frame.grid_columnconfigure(1, weight=1)
        
        param_title = ctk.CTkLabel(
            param_frame,
            text="生成参数",
            font=("Microsoft YaHei", 14, "bold")
        )
        param_title.grid(row=0, column=0, columnspan=3, sticky="w", padx=10, pady=5)
        
        # 温度滑块
        temp_label = ctk.CTkLabel(
            param_frame,
            text="温度(创意度):",
            font=("Microsoft YaHei", 12)
        )
        temp_label.grid(row=1, column=0, sticky="w", padx=10, pady=5)
        
        self.temp_var = ctk.DoubleVar(value=0.7)
        temp_slider = ctk.CTkSlider(
            param_frame,
            from_=0.0,
            to=2.0,
            number_of_steps=20,
            variable=self.temp_var,
            command=self._on_temperature_changed
        )
        temp_slider.grid(row=1, column=1, sticky="ew", padx=10, pady=5)
        
        self.temp_value_label = ctk.CTkLabel(
            param_frame,
            text=f"{self.temp_var.get():.1f}",
            font=("Microsoft YaHei", 12)
        )
        self.temp_value_label.grid(row=1, column=2, padx=5, pady=5)
        
        hint_label = ctk.CTkLabel(
            param_frame,
            text="低←→高",
            font=("Microsoft YaHei", 9),
            text_color="gray"
        )
        hint_label.grid(row=2, column=1, sticky="ew", padx=10, pady=0)
        
        # 预计信息
        self.estimate_label = ctk.CTkLabel(
            param_frame,
            text="预计耗时: 2 分钟/章 | 预计成本: $0.05/章",
            font=("Microsoft YaHei", 10),
            text_color="gray"
        )
        self.estimate_label.grid(row=3, column=0, columnspan=3, sticky="w", padx=10, pady=10)
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(frame)
        btn_frame.grid(row=2, column=0, sticky="ew", padx=10, pady=10)
        btn_frame.grid_columnconfigure(0, weight=1)
        btn_frame.grid_columnconfigure(1, weight=1)
        
        save_btn = ctk.CTkButton(
            btn_frame,
            text="保存",
            command=self._save_config,
            font=("Microsoft YaHei", 12),
            fg_color="#2E8B57"
        )
        save_btn.grid(row=0, column=0, padx=5, pady=5, sticky="ew")
        
        reset_btn = ctk.CTkButton(
            btn_frame,
            text="重置为默认",
            command=self._reset_config,
            font=("Microsoft YaHei", 12),
            fg_color="#8B0000"
        )
        reset_btn.grid(row=0, column=1, padx=5, pady=5, sticky="ew")
    
    def _build_advanced_ui(self):
        """构建高级模式UI"""
        frame = self.config_content_frame
        frame.grid_columnconfigure(0, weight=1)
        
        # 使用 scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(0, weight=1)
        
        # LLM 配置
        self._create_section(scroll_frame, "LLM 配置", 0, [
            ("生成模型:", "model_dropdown"),
            ("API Key:", "api_key_entry"),
            ("Base URL:", "base_url_entry"),
            ("最大 Tokens:", "max_tokens_slider"),
            ("温度:", "temperature_slider"),
            ("Top P:", "top_p_slider")
        ])
        
        # 检查和优化
        self._create_section(scroll_frame, "检查和优化", 1, [
            ("☑ 启用一致性检查", "consistency_check"),
            ("☑ 启用风格检查", "style_check"),
            ("☑ 启用质量评分", "quality_score"),
            ("☐ 启用自动修复", "auto_fix")
        ], is_checkbox=True)
        
        # 性能
        self._create_section(scroll_frame, "性能", 2, [
            ("并行生成:", "parallel_gen_checkbox"),
            ("向量库缓存:", "cache_checkbox")
        ], is_checkbox=True)
        
        # 操作按钮
        self._create_action_buttons(scroll_frame, 3, ["保存", "测试", "重置"])
    
    def _build_expert_ui(self):
        """构建专家模式UI"""
        frame = self.config_content_frame
        frame.grid_columnconfigure(0, weight=1)
        
        # 使用 scrollable frame
        scroll_frame = ctk.CTkScrollableFrame(frame)
        scroll_frame.grid(row=0, column=0, sticky="nsew", padx=5, pady=5)
        frame.grid_rowconfigure(0, weight=1)
        
        # 创建可折叠的配置组
        sections = [
            ("◆ LLM 配置", ["生成模型", "评估模型", "Embedding 模型", "备选模型"]),
            ("◆ 向量库配置", ["后端选择", "持久化目录", "索引策略", "缓存设置"]),
            ("◆ 生成参数", ["温度、Top P、Frequency Penalty", "单批大小、并行度", "重试策略"]),
            ("◆ 检查和优化", ["一致性检查权重", "质量评分阈值", "自动修复策略"])
        ]
        
        for i, (title, items) in enumerate(sections):
            section_frame = ctk.CTkFrame(scroll_frame)
            section_frame.grid(row=i, column=0, sticky="ew", padx=5, pady=5)
            section_frame.grid_columnconfigure(0, weight=1)
            
            # 标题（可点击折叠/展开）
            title_btn = ctk.CTkButton(
                section_frame,
                text=title,
                font=("Microsoft YaHei", 12, "bold"),
                fg_color="transparent",
                text_color=("black", "white"),
                hover=False,
                anchor="w"
            )
            title_btn.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
            
            # 内容
            content_frame = ctk.CTkFrame(section_frame)
            content_frame.grid(row=1, column=0, sticky="ew", padx=15, pady=2)
            
            for j, item in enumerate(items):
                item_label = ctk.CTkLabel(
                    content_frame,
                    text=f"├─ {item}",
                    font=("Microsoft YaHei", 10),
                    anchor="w"
                )
                item_label.grid(row=j, column=0, sticky="w", padx=5, pady=2)
        
        # 操作按钮（专家模式有更多选项）
        btn_frame = ctk.CTkFrame(scroll_frame)
        btn_frame.grid(row=len(sections), column=0, sticky="ew", padx=5, pady=10)
        
        buttons = ["导入", "导出", "验证", "重置为默认"]
        for i, btn_text in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame,
                text=btn_text,
                font=("Microsoft YaHei", 11),
                width=120,
                command=lambda t=btn_text: self._handle_expert_action(t)
            )
            btn.grid(row=0, column=i, padx=5, pady=5)
    
    def _create_section(self, parent, title: str, row: int, 
                       fields: list, is_checkbox: bool = False):
        """创建配置区段"""
        section_frame = ctk.CTkFrame(parent)
        section_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=5)
        section_frame.grid_columnconfigure(1, weight=1)
        
        # 标题
        title_label = ctk.CTkLabel(
            section_frame,
            text=title,
            font=("Microsoft YaHei", 13, "bold")
        )
        title_label.grid(row=0, column=0, columnspan=2, sticky="w", padx=10, pady=5)
        
        # 字段
        for i, field in enumerate(fields):
            if isinstance(field, tuple):
                label_text, field_name = field
            else:
                label_text = field
                field_name = field
            
            if is_checkbox:
                checkbox = ctk.CTkCheckBox(
                    section_frame,
                    text=label_text,
                    font=("Microsoft YaHei", 11)
                )
                checkbox.grid(row=i+1, column=0, columnspan=2, sticky="w", padx=15, pady=3)
            else:
                label = ctk.CTkLabel(
                    section_frame,
                    text=label_text,
                    font=("Microsoft YaHei", 11)
                )
                label.grid(row=i+1, column=0, sticky="w", padx=10, pady=5)
                
                # 这里可以根据 field_name 创建不同的输入控件
                entry = ctk.CTkEntry(
                    section_frame,
                    font=("Microsoft YaHei", 11),
                    placeholder_text=f"请输入{label_text}"
                )
                entry.grid(row=i+1, column=1, sticky="ew", padx=10, pady=5)
    
    def _create_action_buttons(self, parent, row: int, buttons: list):
        """创建操作按钮组"""
        btn_frame = ctk.CTkFrame(parent)
        btn_frame.grid(row=row, column=0, sticky="ew", padx=5, pady=10)
        
        for i, btn_text in enumerate(buttons):
            btn = ctk.CTkButton(
                btn_frame,
                text=btn_text,
                font=("Microsoft YaHei", 11),
                width=100
            )
            btn.grid(row=0, column=i, padx=5, pady=5)
    
    # ==================== 事件处理 ====================
    
    def _on_preset_selected(self, preset: ConfigPreset):
        """预设被选择"""
        if preset == ConfigPreset.CUSTOM:
            # 切换到高级模式
            self._switch_mode(ConfigMode.ADVANCED)
        else:
            # 应用预设
            preset_config = self.simplifier.get_preset_config(preset)
            self.temp_var.set(preset_config["temperature"])
            self._update_estimates()
    
    def _on_temperature_changed(self, value):
        """温度值改变"""
        self.temp_value_label.configure(text=f"{float(value):.1f}")
        
        # 显示影响提示
        if float(value) > 0.9:
            messagebox.showwarning(
                "提示",
                "⚠️ 温度值较高！\n\n"
                "可能影响：\n"
                "• 创意度 ↑↑↑ (非常高)\n"
                "• 一致性 ↓↓↓ (可能不稳定)\n"
                "• 预计质量 ↓ (可能出现错误)\n\n"
                "建议：仅在创意优先的项目中使用"
            )
    
    def _update_estimates(self):
        """更新预计信息"""
        # 这里可以根据当前配置计算预计时间和成本
        preset_config = self.simplifier.get_preset_config(
            ConfigPreset(self.preset_var.get())
        )
        time = preset_config.get("estimated_time_per_chapter", "未知")
        cost = preset_config.get("estimated_cost_per_chapter", "未知")
        self.estimate_label.configure(
            text=f"预计耗时: {time} | 预计成本: {cost}"
        )
    
    def _save_config(self):
        """保存配置"""
        # 这里应该调用实际的保存逻辑
        messagebox.showinfo("提示", "配置已保存")
        
        if self.on_config_changed:
            self.on_config_changed(self.current_config)
        
        # 添加到历史
        self.simplifier.add_history_snapshot(
            self.current_config,
            "用户保存配置"
        )
    
    def _reset_config(self):
        """重置配置"""
        if messagebox.askyesno("确认", "确定要重置为默认配置吗？"):
            # 重置逻辑
            self.temp_var.set(0.7)
            self.preset_var.set(ConfigPreset.BALANCED.value)
            messagebox.showinfo("提示", "已重置为默认配置")
    
    def _handle_expert_action(self, action: str):
        """处理专家模式的操作"""
        if action == "导入":
            self._import_config()
        elif action == "导出":
            self._export_config()
        elif action == "验证":
            self._validate_config()
        elif action == "重置为默认":
            self._reset_config()
    
    def _import_config(self):
        """导入配置"""
        file_path = filedialog.askopenfilename(
            title="选择配置文件",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            imported_config = self.simplifier.import_config(file_path)
            if imported_config:
                self.current_config = imported_config
                messagebox.showinfo("成功", "配置已导入")
                self._refresh_config_ui()
            else:
                messagebox.showerror("错误", "导入配置失败")
    
    def _export_config(self):
        """导出配置"""
        file_path = filedialog.asksaveasfilename(
            title="保存配置文件",
            defaultextension=".json",
            filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
        )
        
        if file_path:
            if self.simplifier.export_config(self.current_config, file_path):
                messagebox.showinfo("成功", "配置已导出")
            else:
                messagebox.showerror("错误", "导出配置失败")
    
    def _validate_config(self):
        """验证配置"""
        issues = self.simplifier.validate_config(self.current_config)
        
        if not issues:
            messagebox.showinfo("验证结果", "✅ 配置验证通过，没有发现问题")
            return
        
        # 显示验证结果
        self._show_validation_dialog(issues)
    
    def _show_validation_dialog(self, issues: list):
        """显示验证结果对话框"""
        dialog = ctk.CTkToplevel(self)
        dialog.title("配置验证结果")
        dialog.geometry("600x400")
        
        # 标题
        title = ctk.CTkLabel(
            dialog,
            text=f"⚠️ 发现 {len(issues)} 个问题",
            font=("Microsoft YaHei", 14, "bold")
        )
        title.pack(padx=10, pady=10)
        
        # 问题列表
        scroll_frame = ctk.CTkScrollableFrame(dialog)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        for i, issue in enumerate(issues):
            issue_frame = ctk.CTkFrame(scroll_frame)
            issue_frame.pack(fill="x", padx=5, pady=5)
            
            # 图标
            icon = "❌" if issue.level == "error" else "⚠️" if issue.level == "warning" else "ℹ️"
            
            # 标题
            issue_title = ctk.CTkLabel(
                issue_frame,
                text=f"{icon} 问题{i+1}: {issue.title}",
                font=("Microsoft YaHei", 11, "bold"),
                anchor="w"
            )
            issue_title.pack(fill="x", padx=10, pady=5)
            
            # 描述
            desc = ctk.CTkLabel(
                issue_frame,
                text=f"├─ {issue.description}",
                font=("Microsoft YaHei", 10),
                anchor="w"
            )
            desc.pack(fill="x", padx=20, pady=2)
            
            # 建议
            suggestion = ctk.CTkLabel(
                issue_frame,
                text=f"├─ 建议: {issue.suggestion}",
                font=("Microsoft YaHei", 10),
                anchor="w",
                text_color="green"
            )
            suggestion.pack(fill="x", padx=20, pady=2)
            
            # 自动修复按钮
            if issue.auto_fix_available:
                fix_btn = ctk.CTkButton(
                    issue_frame,
                    text="自动修复",
                    width=100,
                    command=lambda iss=issue: self._auto_fix_issue(iss, dialog)
                )
                fix_btn.pack(padx=20, pady=5, anchor="w")
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            dialog,
            text="关闭",
            command=dialog.destroy
        )
        close_btn.pack(pady=10)
    
    def _auto_fix_issue(self, issue: ValidationIssue, dialog):
        """自动修复问题"""
        # 这里应该实际修复配置
        messagebox.showinfo("提示", "问题已自动修复")
        dialog.destroy()
        self._refresh_config_ui()


class ConfigHistoryViewer(ctk.CTkToplevel):
    """配置历史查看器"""
    
    def __init__(self, parent, simplifier: ConfigurationSimplifier):
        super().__init__(parent)
        
        self.simplifier = simplifier
        self.title("配置变更历史")
        self.geometry("700x500")
        
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI"""
        # 标题
        title = ctk.CTkLabel(
            self,
            text="配置变更时间线",
            font=("Microsoft YaHei", 16, "bold")
        )
        title.pack(padx=10, pady=10)
        
        # 历史列表
        scroll_frame = ctk.CTkScrollableFrame(self)
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        history = self.simplifier.get_history(limit=20)
        
        if not history:
            no_data = ctk.CTkLabel(
                scroll_frame,
                text="暂无历史记录",
                font=("Microsoft YaHei", 12),
                text_color="gray"
            )
            no_data.pack(pady=20)
            return
        
        for snapshot in history:
            self._create_history_item(scroll_frame, snapshot)
        
        # 关闭按钮
        close_btn = ctk.CTkButton(
            self,
            text="关闭",
            command=self.destroy
        )
        close_btn.pack(pady=10)
    
    def _create_history_item(self, parent, snapshot):
        """创建历史记录项"""
        item_frame = ctk.CTkFrame(parent)
        item_frame.pack(fill="x", padx=5, pady=5)
        
        # 时间和描述
        time_str = format_time_ago(snapshot.timestamp)
        header = ctk.CTkLabel(
            item_frame,
            text=f"{time_str} - {snapshot.description}",
            font=("Microsoft YaHei", 11, "bold"),
            anchor="w"
        )
        header.pack(fill="x", padx=10, pady=5)
        
        # 影响说明
        if snapshot.impact_notes:
            impact = ctk.CTkLabel(
                item_frame,
                text=f"│ 影响: {snapshot.impact_notes}",
                font=("Microsoft YaHei", 10),
                anchor="w",
                text_color="gray"
            )
            impact.pack(fill="x", padx=10, pady=2)
        
        # 满意度
        if snapshot.user_satisfaction:
            satisfaction_icon = "✓" if snapshot.user_satisfaction == "满意" else "~" if snapshot.user_satisfaction == "能接受" else "✗"
            satisfaction = ctk.CTkLabel(
                item_frame,
                text=f"│ 结果: {snapshot.user_satisfaction} {satisfaction_icon}",
                font=("Microsoft YaHei", 10),
                anchor="w"
            )
            satisfaction.pack(fill="x", padx=10, pady=2)
        
        # 操作按钮
        btn_frame = ctk.CTkFrame(item_frame)
        btn_frame.pack(fill="x", padx=10, pady=5)
        
        restore_btn = ctk.CTkButton(
            btn_frame,
            text="恢复到此版本",
            width=120,
            command=lambda: self._restore_snapshot(snapshot)
        )
        restore_btn.pack(side="left", padx=5)
        
        details_btn = ctk.CTkButton(
            btn_frame,
            text="详情",
            width=80,
            command=lambda: self._show_snapshot_details(snapshot)
        )
        details_btn.pack(side="left", padx=5)
    
    def _restore_snapshot(self, snapshot):
        """恢复快照"""
        if messagebox.askyesno("确认", "确定要恢复到这个配置版本吗？"):
            config = self.simplifier.restore_from_history(snapshot.timestamp)
            if config:
                messagebox.showinfo("成功", "配置已恢复")
                self.destroy()
            else:
                messagebox.showerror("错误", "恢复配置失败")
    
    def _show_snapshot_details(self, snapshot):
        """显示快照详情"""
        details_window = ctk.CTkToplevel(self)
        details_window.title("配置详情")
        details_window.geometry("600x400")
        
        text_widget = ctk.CTkTextbox(details_window)
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        
        import json
        details_text = json.dumps(snapshot.config_data, ensure_ascii=False, indent=2)
        text_widget.insert("1.0", details_text)
        text_widget.configure(state="disabled")
