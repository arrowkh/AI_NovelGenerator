# config_simplifier_integration_example.py
# -*- coding: utf-8 -*-
"""
配置简化器集成示例
展示如何将配置简化器集成到现有的 config_tab.py 中
"""

# ==================== 方法 1: 添加新的标签页 ====================

# 在 ui/config_tab.py 的 build_config_tabview 函数中添加：

def build_config_tabview(self):
    """
    创建包含 LLM Model settings 和 Embedding settings 的选项卡。
    """
    self.config_tabview = ctk.CTkTabview(self.config_frame)
    self.config_tabview.grid(row=0, column=0, sticky="we", padx=5, pady=5)

    self.ai_config_tab = self.config_tabview.add("LLM Model settings")
    self.embeddings_config_tab = self.config_tabview.add("Embedding settings")
    self.config_choose = self.config_tabview.add("Config choose")
    self.proxy_setting_tab = self.config_tabview.add("Proxy setting")
    
    # ⭐ 添加配置简化器标签页
    self.simplifier_tab = self.config_tabview.add("🎓 配置向导")

    build_ai_config_tab(self)
    build_embeddings_config_tab(self)
    build_config_choose_tab(self)
    build_proxy_setting_tab(self)
    
    # ⭐ 构建配置简化器标签页
    build_simplifier_tab(self)


# ⭐ 新增函数：构建配置简化器标签页
def build_simplifier_tab(self):
    """构建配置简化器标签页"""
    from ui.config_simplifier_ui import ConfigSimplifierPanel
    
    # 创建简化器面板
    self.simplifier_panel = ConfigSimplifierPanel(
        self.simplifier_tab,
        self.config_file,
        on_config_changed=self._on_simplifier_config_changed
    )
    self.simplifier_panel.pack(fill="both", expand=True, padx=5, pady=5)


# ⭐ 新增回调函数：处理简化器的配置变更
def _on_simplifier_config_changed(self, config):
    """当配置简化器修改配置时调用"""
    # 更新主配置
    self.loaded_config.update(config)
    
    # 刷新其他标签页的显示
    # 例如，如果用户在简化器中修改了 LLM 配置，应该同步到 LLM 标签页
    if "llm_configs" in config:
        # 刷新 LLM 配置显示
        self._refresh_llm_config_display()
    
    if "embedding_configs" in config:
        # 刷新 Embedding 配置显示
        self._refresh_embedding_config_display()
    
    # 保存配置到文件
    from config_manager import save_config
    save_config(self.loaded_config, self.config_file)
    
    # 显示提示
    from tkinter import messagebox
    messagebox.showinfo("提示", "配置已从向导更新")


# ==================== 方法 2: 添加工具栏按钮 ====================

# 在 ui/main_window.py 中添加：

def create_toolbar(self):
    """创建工具栏"""
    self.toolbar = ctk.CTkFrame(self)
    self.toolbar.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
    
    # ... 其他工具栏按钮 ...
    
    # ⭐ 添加配置向导按钮
    wizard_btn = ctk.CTkButton(
        self.toolbar,
        text="🎓 配置向导",
        command=self.open_config_wizard,
        font=("Microsoft YaHei", 12),
        width=120
    )
    wizard_btn.pack(side="left", padx=5)


# ⭐ 新增方法：打开配置向导窗口
def open_config_wizard(self):
    """打开配置向导对话框"""
    from ui.config_simplifier_ui import ConfigSimplifierPanel
    import customtkinter as ctk
    
    # 创建对话框窗口
    wizard_window = ctk.CTkToplevel(self)
    wizard_window.title("配置向导 - 渐进式学习")
    wizard_window.geometry("850x650")
    
    # 创建简化器面板
    panel = ConfigSimplifierPanel(
        wizard_window,
        self.config_file,
        on_config_changed=self._on_wizard_config_changed
    )
    panel.pack(fill="both", expand=True, padx=10, pady=10)
    
    # 使窗口模态
    wizard_window.focus()
    wizard_window.grab_set()


def _on_wizard_config_changed(self, config):
    """向导配置变更处理"""
    # 更新主窗口的配置
    self.config = config
    
    # 刷新相关 UI
    self._refresh_all_config_displays()
    
    # 保存配置
    from config_manager import save_config
    save_config(config, self.config_file)


# ==================== 方法 3: 添加帮助菜单项 ====================

# 在主窗口的菜单栏中添加：

def create_menu_bar(self):
    """创建菜单栏"""
    # ... 其他菜单 ...
    
    # 帮助菜单
    help_menu = tk.Menu(menubar, tearoff=0)
    menubar.add_cascade(label="帮助", menu=help_menu)
    
    # ⭐ 添加配置向导菜单项
    help_menu.add_command(
        label="🎓 配置向导",
        command=self.open_config_wizard
    )
    help_menu.add_command(
        label="📜 配置历史",
        command=self.open_config_history
    )
    help_menu.add_separator()
    help_menu.add_command(label="关于", command=self.show_about)


# ⭐ 新增方法：打开配置历史
def open_config_history(self):
    """打开配置历史查看器"""
    from ui.config_simplifier_ui import ConfigHistoryViewer
    from ui.configuration_simplifier import ConfigurationSimplifier
    
    simplifier = ConfigurationSimplifier(self.config_file)
    viewer = ConfigHistoryViewer(self, simplifier)
    viewer.focus()


# ==================== 方法 4: 首次启动向导 ====================

# 在主窗口初始化时检查是否首次启动：

def __init__(self):
    super().__init__()
    
    # ... 其他初始化代码 ...
    
    # ⭐ 检查是否首次启动
    self._check_first_launch()


def _check_first_launch(self):
    """检查是否首次启动，如果是则显示配置向导"""
    import os
    from ui.configuration_simplifier import ConfigurationSimplifier
    
    simplifier = ConfigurationSimplifier(self.config_file)
    history = simplifier.get_history()
    
    # 如果没有配置历史，说明是首次启动
    if len(history) == 0:
        # 延迟显示（等窗口完全加载）
        self.after(500, self._show_first_launch_wizard)


def _show_first_launch_wizard(self):
    """显示首次启动向导"""
    from tkinter import messagebox
    
    result = messagebox.askyesno(
        "欢迎使用 AI小说生成器",
        "检测到这是您第一次使用本系统。\n\n"
        "我们提供了配置向导帮助您快速上手，\n"
        "向导会根据您的经验水平提供不同的配置方式。\n\n"
        "是否现在打开配置向导？"
    )
    
    if result:
        self.open_config_wizard()


# ==================== 方法 5: 快捷键绑定 ====================

# 在主窗口中添加快捷键：

def setup_key_bindings(self):
    """设置快捷键"""
    # ... 其他快捷键 ...
    
    # ⭐ Ctrl+W 打开配置向导
    self.bind("<Control-w>", lambda e: self.open_config_wizard())
    
    # ⭐ Ctrl+H 打开配置历史
    self.bind("<Control-h>", lambda e: self.open_config_history())


# ==================== 方法 6: 状态栏提示 ====================

# 在状态栏中添加提示：

def update_status_bar(self):
    """更新状态栏"""
    from ui.configuration_simplifier import ConfigurationSimplifier
    
    simplifier = ConfigurationSimplifier(self.config_file)
    mode = simplifier.get_mode()
    
    # 显示当前配置模式
    self.status_label.configure(
        text=f"当前配置模式: {mode.value} | 按 Ctrl+W 打开配置向导"
    )


# ==================== 使用示例 ====================

"""
完整的集成步骤：

1. 在 config_tab.py 中添加新标签页
   - 添加 self.simplifier_tab = self.config_tabview.add("🎓 配置向导")
   - 调用 build_simplifier_tab(self)

2. 在 main_window.py 中添加工具栏按钮
   - 创建 "配置向导" 按钮
   - 绑定 open_config_wizard 方法

3. 添加菜单项（可选）
   - 在帮助菜单添加 "配置向导" 和 "配置历史"

4. 添加首次启动检测（可选）
   - 检测配置历史，首次使用时显示向导

5. 添加快捷键（可选）
   - Ctrl+W 打开向导
   - Ctrl+H 打开历史

6. 更新状态栏（可选）
   - 显示当前配置模式

测试集成：

1. 运行主程序
2. 点击 "配置向导" 标签页或按钮
3. 切换不同的配置模式
4. 应用预设配置
5. 查看配置历史
6. 验证配置是否正确保存和同步

注意事项：

- 确保 config_file 路径正确
- 配置变更后要同步更新其他标签页的显示
- 历史记录文件会自动创建和管理
- 可以根据实际需求选择集成方式
"""
