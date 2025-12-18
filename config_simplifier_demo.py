#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置简化器演示程序
展示如何使用配置简化和渐进式学习系统
"""

import customtkinter as ctk
from ui.config_simplifier_ui import ConfigSimplifierPanel, ConfigHistoryViewer
from ui.configuration_simplifier import ConfigurationSimplifier, ConfigMode, ConfigPreset
import os


class ConfigSimplifierDemo(ctk.CTk):
    """配置简化器演示主窗口"""
    
    def __init__(self):
        super().__init__()
        
        self.title("配置简化器 - 演示程序")
        self.geometry("900x700")
        
        # 设置主题
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 配置文件路径
        self.config_file = "config.json"
        
        # 创建UI
        self._setup_ui()
    
    def _setup_ui(self):
        """设置UI布局"""
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)
        
        # 标题栏
        title_frame = ctk.CTkFrame(self)
        title_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=10)
        
        title = ctk.CTkLabel(
            title_frame,
            text="🎓 配置简化和渐进式学习系统",
            font=("Microsoft YaHei", 18, "bold")
        )
        title.pack(side="left", padx=10, pady=10)
        
        # 工具按钮
        btn_frame = ctk.CTkFrame(title_frame)
        btn_frame.pack(side="right", padx=10, pady=10)
        
        history_btn = ctk.CTkButton(
            btn_frame,
            text="📜 查看历史",
            command=self._show_history,
            width=120
        )
        history_btn.pack(side="left", padx=5)
        
        stats_btn = ctk.CTkButton(
            btn_frame,
            text="📊 使用统计",
            command=self._show_statistics,
            width=120
        )
        stats_btn.pack(side="left", padx=5)
        
        help_btn = ctk.CTkButton(
            btn_frame,
            text="❓ 帮助",
            command=self._show_help,
            width=100
        )
        help_btn.pack(side="left", padx=5)
        
        # 主配置面板
        self.config_panel = ConfigSimplifierPanel(
            self,
            self.config_file,
            on_config_changed=self._on_config_changed
        )
        self.config_panel.grid(row=1, column=0, sticky="nsew", padx=10, pady=10)
        
        # 状态栏
        self.status_bar = ctk.CTkLabel(
            self,
            text="就绪",
            font=("Microsoft YaHei", 10),
            anchor="w"
        )
        self.status_bar.grid(row=2, column=0, sticky="ew", padx=10, pady=5)
    
    def _on_config_changed(self, config):
        """配置变更回调"""
        self.status_bar.configure(text="配置已更新")
        print("配置已变更:", config)
    
    def _show_history(self):
        """显示配置历史"""
        simplifier = ConfigurationSimplifier(self.config_file)
        viewer = ConfigHistoryViewer(self, simplifier)
        viewer.focus()
    
    def _show_statistics(self):
        """显示使用统计"""
        simplifier = ConfigurationSimplifier(self.config_file)
        stats = simplifier.get_usage_statistics()
        
        # 创建统计对话框
        dialog = ctk.CTkToplevel(self)
        dialog.title("使用统计")
        dialog.geometry("500x400")
        
        title = ctk.CTkLabel(
            dialog,
            text="📊 配置使用统计",
            font=("Microsoft YaHei", 16, "bold")
        )
        title.pack(padx=10, pady=10)
        
        stats_frame = ctk.CTkFrame(dialog)
        stats_frame.pack(fill="both", expand=True, padx=20, pady=10)
        
        # 显示统计信息
        stats_items = [
            ("总配置次数:", str(stats["total_configs"])),
            ("最常用预设:", stats["most_used_preset"]),
            ("最常用模式:", stats["most_used_mode"]),
        ]
        
        for i, (label, value) in enumerate(stats_items):
            label_widget = ctk.CTkLabel(
                stats_frame,
                text=label,
                font=("Microsoft YaHei", 12),
                anchor="w"
            )
            label_widget.grid(row=i, column=0, sticky="w", padx=10, pady=5)
            
            value_widget = ctk.CTkLabel(
                stats_frame,
                text=value,
                font=("Microsoft YaHei", 12, "bold"),
                anchor="e"
            )
            value_widget.grid(row=i, column=1, sticky="e", padx=10, pady=5)
        
        # 满意度统计
        if stats["satisfaction_stats"]:
            satisfaction_label = ctk.CTkLabel(
                stats_frame,
                text="满意度统计:",
                font=("Microsoft YaHei", 12),
                anchor="w"
            )
            satisfaction_label.grid(row=len(stats_items), column=0, columnspan=2, 
                                   sticky="w", padx=10, pady=10)
            
            for j, (satisfaction, count) in enumerate(stats["satisfaction_stats"].items()):
                sat_text = f"  {satisfaction}: {count} 次"
                sat_label = ctk.CTkLabel(
                    stats_frame,
                    text=sat_text,
                    font=("Microsoft YaHei", 11),
                    anchor="w"
                )
                sat_label.grid(row=len(stats_items)+1+j, column=0, columnspan=2,
                             sticky="w", padx=20, pady=2)
        
        close_btn = ctk.CTkButton(
            dialog,
            text="关闭",
            command=dialog.destroy
        )
        close_btn.pack(pady=10)
    
    def _show_help(self):
        """显示帮助信息"""
        help_text = """
        🎓 配置简化和渐进式学习系统 - 使用指南
        
        ═══════════════════════════════════════════
        
        📌 三种配置模式：
        
        1️⃣ 基础模式（推荐新手）
           • 只显示核心配置选项
           • 使用推荐的预设配置
           • 快速上手，无需了解技术细节
        
        2️⃣ 高级模式（中级用户）
           • 显示常用配置项
           • 支持细节调整
           • 查看性能和优化选项
        
        3️⃣ 专家模式（高级用户）
           • 显示所有配置项
           • 完全控制所有参数
           • 支持导入/导出配置
        
        ═══════════════════════════════════════════
        
        🎯 推荐的学习路径：
        
        第1天：从基础模式开始
        └─ 了解基本概念，使用推荐预设
        
        第1周：切换到高级模式
        └─ 开始微调参数，优化生成效果
        
        第1月+：尝试专家模式
        └─ 完全掌握所有配置选项
        
        💡 随时可以切换回简单模式！
        
        ═══════════════════════════════════════════
        
        🚀 快速预设：
        
        • 快速：适合快速原型和初稿，成本低
        • 平衡：推荐使用，质量和成本平衡
        • 高质量：适合重要章节，质量最好
        • 创意模式：适合奇幻/科幻，高创意度
        
        ═══════════════════════════════════════════
        
        ⚠️ 智能提示：
        
        • 系统会自动检测配置问题
        • 参数变更时显示影响分析
        • 提供自动修复建议
        • 记录配置历史，随时恢复
        
        ═══════════════════════════════════════════
        
        💾 配置历史：
        
        • 点击"查看历史"查看所有配置变更
        • 可以恢复到任意历史版本
        • 记录每次变更的影响和满意度
        
        ═══════════════════════════════════════════
        
        📤 导入/导出（专家模式）：
        
        • 导出配置分享给朋友
        • 导入他人的优秀配置
        • 备份重要配置
        
        ═══════════════════════════════════════════
        
        需要更多帮助？
        
        • 每个配置项都有"?"按钮
        • 点击查看详细说明
        • 包含教程链接和最佳实践
        
        ═══════════════════════════════════════════
        """
        
        dialog = ctk.CTkToplevel(self)
        dialog.title("帮助")
        dialog.geometry("700x600")
        
        text_widget = ctk.CTkTextbox(
            dialog,
            font=("Microsoft YaHei", 11),
            wrap="word"
        )
        text_widget.pack(fill="both", expand=True, padx=10, pady=10)
        text_widget.insert("1.0", help_text)
        text_widget.configure(state="disabled")
        
        close_btn = ctk.CTkButton(
            dialog,
            text="关闭",
            command=dialog.destroy
        )
        close_btn.pack(pady=10)


def main():
    """主函数"""
    app = ConfigSimplifierDemo()
    app.mainloop()


if __name__ == "__main__":
    main()
