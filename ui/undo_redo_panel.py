# ui/undo_redo_panel.py
# -*- coding: utf-8 -*-
"""
撤销/重做UI面板

功能：
- 操作历史面板
- 分支管理面板
- 快捷键支持
"""

import customtkinter as ctk
import tkinter as tk
from tkinter import messagebox
from datetime import datetime
from typing import Optional, Callable
from core.undo_redo_manager import UndoRedoManager, Operation, OperationGroup


class UndoRedoPanel(ctk.CTkToplevel):
    """操作历史面板"""
    
    def __init__(self, master, undo_redo_manager: UndoRedoManager, 
                 apply_undo_callback: Optional[Callable] = None,
                 apply_redo_callback: Optional[Callable] = None):
        """
        初始化操作历史面板
        
        Args:
            master: 父窗口
            undo_redo_manager: 撤销/重做管理器
            apply_undo_callback: 应用撤销的回调函数
            apply_redo_callback: 应用重做的回调函数
        """
        super().__init__(master)
        
        self.undo_redo_manager = undo_redo_manager
        self.apply_undo_callback = apply_undo_callback
        self.apply_redo_callback = apply_redo_callback
        
        self.title("操作历史")
        self.geometry("800x600")
        
        # 设置为临时窗口
        self.transient(master)
        
        self._build_ui()
        self._refresh_history()
        
        # 注册观察者
        self.undo_redo_manager.add_observer(self._on_manager_event)
    
    def _build_ui(self):
        """构建UI"""
        # 主框架
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部工具栏
        toolbar = ctk.CTkFrame(main_frame)
        toolbar.pack(fill="x", pady=(0, 10))
        
        # 统计信息
        stats = self.undo_redo_manager.get_statistics()
        self.stats_label = ctk.CTkLabel(
            toolbar,
            text=f"可撤销: {stats['undo_count']} | 可重做: {stats['redo_count']} | 分支: {stats['current_branch']}",
            font=("Microsoft YaHei", 12)
        )
        self.stats_label.pack(side="left", padx=10)
        
        # 刷新按钮
        btn_refresh = ctk.CTkButton(
            toolbar,
            text="刷新",
            width=80,
            command=self._refresh_history
        )
        btn_refresh.pack(side="right", padx=5)
        
        # 清空历史按钮
        btn_clear = ctk.CTkButton(
            toolbar,
            text="清空历史",
            width=80,
            command=self._clear_history,
            fg_color="red"
        )
        btn_clear.pack(side="right", padx=5)
        
        # 导出历史按钮
        btn_export = ctk.CTkButton(
            toolbar,
            text="导出历史",
            width=80,
            command=self._export_history
        )
        btn_export.pack(side="right", padx=5)
        
        # 分支管理按钮
        btn_branches = ctk.CTkButton(
            toolbar,
            text="分支管理",
            width=80,
            command=self._show_branch_panel
        )
        btn_branches.pack(side="right", padx=5)
        
        # 历史列表框架
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # 创建滚动文本框显示历史
        self.history_text = ctk.CTkTextbox(list_frame, font=("Consolas", 11))
        self.history_text.pack(fill="both", expand=True)
        
        # 底部按钮框架
        bottom_frame = ctk.CTkFrame(main_frame)
        bottom_frame.pack(fill="x", pady=(10, 0))
        
        # 撤销按钮
        self.btn_undo = ctk.CTkButton(
            bottom_frame,
            text="撤销 (Ctrl+Z)",
            command=self._undo_operation
        )
        self.btn_undo.pack(side="left", padx=5, expand=True, fill="x")
        
        # 重做按钮
        self.btn_redo = ctk.CTkButton(
            bottom_frame,
            text="重做 (Ctrl+Y)",
            command=self._redo_operation
        )
        self.btn_redo.pack(side="left", padx=5, expand=True, fill="x")
        
        # 关闭按钮
        btn_close = ctk.CTkButton(
            bottom_frame,
            text="关闭",
            command=self.destroy
        )
        btn_close.pack(side="left", padx=5, expand=True, fill="x")
        
        self._update_button_states()
    
    def _refresh_history(self):
        """刷新历史列表"""
        history = self.undo_redo_manager.get_history(limit=100)
        
        self.history_text.configure(state="normal")
        self.history_text.delete("0.0", "end")
        
        if not history:
            self.history_text.insert("0.0", "暂无操作历史\n")
        else:
            self.history_text.insert("0.0", "=" * 80 + "\n")
            self.history_text.insert("end", f"操作历史 (最近 {len(history)} 条)\n")
            self.history_text.insert("end", "=" * 80 + "\n\n")
            
            for i, (description, op_type, timestamp) in enumerate(history, 1):
                time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                line = f"{i:3d}. [{time_str}] {description}\n"
                self.history_text.insert("end", line)
                
                if i % 5 == 0:
                    self.history_text.insert("end", "\n")
        
        self.history_text.configure(state="disabled")
        
        # 更新统计信息
        stats = self.undo_redo_manager.get_statistics()
        self.stats_label.configure(
            text=f"可撤销: {stats['undo_count']} | 可重做: {stats['redo_count']} | 分支: {stats['current_branch']}"
        )
        
        self._update_button_states()
    
    def _update_button_states(self):
        """更新按钮状态"""
        if self.undo_redo_manager.can_undo():
            self.btn_undo.configure(state="normal")
        else:
            self.btn_undo.configure(state="disabled")
        
        if self.undo_redo_manager.can_redo():
            self.btn_redo.configure(state="normal")
        else:
            self.btn_redo.configure(state="disabled")
    
    def _undo_operation(self):
        """撤销操作"""
        if not self.undo_redo_manager.can_undo():
            messagebox.showinfo("提示", "没有可撤销的操作")
            return
        
        operation = self.undo_redo_manager.undo()
        
        if operation and self.apply_undo_callback:
            self.apply_undo_callback(operation)
        
        self._refresh_history()
    
    def _redo_operation(self):
        """重做操作"""
        if not self.undo_redo_manager.can_redo():
            messagebox.showinfo("提示", "没有可重做的操作")
            return
        
        operation = self.undo_redo_manager.redo()
        
        if operation and self.apply_redo_callback:
            self.apply_redo_callback(operation)
        
        self._refresh_history()
    
    def _clear_history(self):
        """清空历史"""
        result = messagebox.askyesno(
            "确认",
            "确定要清空所有操作历史吗？\n此操作不可撤销！"
        )
        
        if result:
            self.undo_redo_manager.clear_history()
            self._refresh_history()
            messagebox.showinfo("完成", "操作历史已清空")
    
    def _export_history(self):
        """导出历史"""
        from tkinter import filedialog
        
        file_path = filedialog.asksaveasfilename(
            title="导出操作历史",
            defaultextension=".txt",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")]
        )
        
        if file_path:
            history = self.undo_redo_manager.get_history(limit=1000)
            
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write("操作历史\n")
                f.write("=" * 80 + "\n\n")
                
                for i, (description, op_type, timestamp) in enumerate(history, 1):
                    time_str = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    f.write(f"{i}. [{time_str}] {description}\n")
                
                stats = self.undo_redo_manager.get_statistics()
                f.write("\n" + "=" * 80 + "\n")
                f.write("统计信息\n")
                f.write(f"可撤销操作数: {stats['undo_count']}\n")
                f.write(f"可重做操作数: {stats['redo_count']}\n")
                f.write(f"当前分支: {stats['current_branch']}\n")
                f.write(f"总分支数: {stats['branches']}\n")
            
            messagebox.showinfo("完成", f"历史已导出到：\n{file_path}")
    
    def _show_branch_panel(self):
        """显示分支管理面板"""
        BranchManagementPanel(self, self.undo_redo_manager)
    
    def _on_manager_event(self, event_type: str, data):
        """响应管理器事件"""
        if self.winfo_exists():
            self.after(0, self._refresh_history)
    
    def destroy(self):
        """销毁窗口"""
        # 移除观察者
        self.undo_redo_manager.remove_observer(self._on_manager_event)
        super().destroy()


class BranchManagementPanel(ctk.CTkToplevel):
    """分支管理面板"""
    
    def __init__(self, master, undo_redo_manager: UndoRedoManager):
        """
        初始化分支管理面板
        
        Args:
            master: 父窗口
            undo_redo_manager: 撤销/重做管理器
        """
        super().__init__(master)
        
        self.undo_redo_manager = undo_redo_manager
        
        self.title("分支管理")
        self.geometry("600x400")
        
        # 设置为临时窗口
        self.transient(master)
        self.grab_set()
        
        self._build_ui()
        self._refresh_branches()
    
    def _build_ui(self):
        """构建UI"""
        # 主框架
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 顶部标签
        label = ctk.CTkLabel(
            main_frame,
            text="时间旅行 - 分支管理",
            font=("Microsoft YaHei", 14, "bold")
        )
        label.pack(pady=(0, 10))
        
        # 分支列表框架
        list_frame = ctk.CTkFrame(main_frame)
        list_frame.pack(fill="both", expand=True)
        
        # 分支列表
        self.branch_text = ctk.CTkTextbox(list_frame, font=("Consolas", 11))
        self.branch_text.pack(fill="both", expand=True)
        
        # 操作按钮框架
        btn_frame = ctk.CTkFrame(main_frame)
        btn_frame.pack(fill="x", pady=(10, 0))
        
        # 创建分支按钮
        btn_create = ctk.CTkButton(
            btn_frame,
            text="创建分支",
            command=self._create_branch
        )
        btn_create.pack(side="left", padx=5, expand=True, fill="x")
        
        # 切换分支按钮
        btn_switch = ctk.CTkButton(
            btn_frame,
            text="切换分支",
            command=self._switch_branch
        )
        btn_switch.pack(side="left", padx=5, expand=True, fill="x")
        
        # 删除分支按钮
        btn_delete = ctk.CTkButton(
            btn_frame,
            text="删除分支",
            command=self._delete_branch,
            fg_color="red"
        )
        btn_delete.pack(side="left", padx=5, expand=True, fill="x")
        
        # 关闭按钮
        btn_close = ctk.CTkButton(
            btn_frame,
            text="关闭",
            command=self.destroy
        )
        btn_close.pack(side="left", padx=5, expand=True, fill="x")
    
    def _refresh_branches(self):
        """刷新分支列表"""
        branches = self.undo_redo_manager.get_branches()
        current = self.undo_redo_manager.get_current_branch()
        
        self.branch_text.configure(state="normal")
        self.branch_text.delete("0.0", "end")
        
        self.branch_text.insert("0.0", "=" * 60 + "\n")
        self.branch_text.insert("end", f"当前分支: {current}\n")
        self.branch_text.insert("end", "=" * 60 + "\n\n")
        
        for branch_name in branches:
            branch_obj = self.undo_redo_manager.branches[branch_name]
            op_count = len(branch_obj.operations)
            created_time = datetime.fromtimestamp(branch_obj.created_at).strftime("%Y-%m-%d %H:%M:%S")
            
            marker = "★ " if branch_name == current else "  "
            line = f"{marker}{branch_name}\n"
            line += f"    操作数: {op_count}\n"
            line += f"    创建时间: {created_time}\n"
            
            if branch_obj.parent_branch:
                line += f"    父分支: {branch_obj.parent_branch}\n"
            
            line += "\n"
            
            self.branch_text.insert("end", line)
        
        self.branch_text.configure(state="disabled")
    
    def _create_branch(self):
        """创建分支"""
        dialog = ctk.CTkInputDialog(
            text="请输入新分支名称:",
            title="创建分支"
        )
        branch_name = dialog.get_input()
        
        if branch_name:
            if self.undo_redo_manager.create_branch(branch_name):
                messagebox.showinfo("成功", f"分支 '{branch_name}' 创建成功")
                self._refresh_branches()
            else:
                messagebox.showerror("错误", f"分支 '{branch_name}' 已存在")
    
    def _switch_branch(self):
        """切换分支"""
        branches = self.undo_redo_manager.get_branches()
        current = self.undo_redo_manager.get_current_branch()
        
        # 创建分支选择对话框
        dialog = ctk.CTkToplevel(self)
        dialog.title("切换分支")
        dialog.geometry("300x400")
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text="请选择要切换到的分支:")
        label.pack(pady=10)
        
        # 分支列表
        frame = ctk.CTkScrollableFrame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        selected_branch = tk.StringVar(value=current)
        
        for branch_name in branches:
            radio = ctk.CTkRadioButton(
                frame,
                text=branch_name,
                variable=selected_branch,
                value=branch_name
            )
            radio.pack(anchor="w", pady=2)
        
        # 按钮
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        def do_switch():
            target = selected_branch.get()
            if target != current:
                if self.undo_redo_manager.switch_branch(target):
                    messagebox.showinfo("成功", f"已切换到分支 '{target}'")
                    self._refresh_branches()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "切换分支失败")
            else:
                dialog.destroy()
        
        btn_ok = ctk.CTkButton(btn_frame, text="确定", command=do_switch)
        btn_ok.pack(side="left", expand=True, padx=5)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="取消", command=dialog.destroy)
        btn_cancel.pack(side="left", expand=True, padx=5)
    
    def _delete_branch(self):
        """删除分支"""
        branches = self.undo_redo_manager.get_branches()
        current = self.undo_redo_manager.get_current_branch()
        
        # 可删除的分支（排除main和当前分支）
        deletable = [b for b in branches if b != "main" and b != current]
        
        if not deletable:
            messagebox.showinfo("提示", "没有可删除的分支")
            return
        
        # 创建分支选择对话框
        dialog = ctk.CTkToplevel(self)
        dialog.title("删除分支")
        dialog.geometry("300x400")
        dialog.transient(self)
        dialog.grab_set()
        
        label = ctk.CTkLabel(dialog, text="请选择要删除的分支:")
        label.pack(pady=10)
        
        # 分支列表
        frame = ctk.CTkScrollableFrame(dialog)
        frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        selected_branch = tk.StringVar(value=deletable[0] if deletable else "")
        
        for branch_name in deletable:
            radio = ctk.CTkRadioButton(
                frame,
                text=branch_name,
                variable=selected_branch,
                value=branch_name
            )
            radio.pack(anchor="w", pady=2)
        
        # 按钮
        btn_frame = ctk.CTkFrame(dialog)
        btn_frame.pack(fill="x", padx=10, pady=10)
        
        def do_delete():
            target = selected_branch.get()
            result = messagebox.askyesno(
                "确认",
                f"确定要删除分支 '{target}' 吗？\n此操作不可撤销！"
            )
            
            if result:
                if self.undo_redo_manager.delete_branch(target):
                    messagebox.showinfo("成功", f"分支 '{target}' 已删除")
                    self._refresh_branches()
                    dialog.destroy()
                else:
                    messagebox.showerror("错误", "删除分支失败")
        
        btn_ok = ctk.CTkButton(btn_frame, text="删除", command=do_delete, fg_color="red")
        btn_ok.pack(side="left", expand=True, padx=5)
        
        btn_cancel = ctk.CTkButton(btn_frame, text="取消", command=dialog.destroy)
        btn_cancel.pack(side="left", expand=True, padx=5)


def setup_undo_redo_shortcuts(widget, undo_callback: Callable, redo_callback: Callable):
    """
    为窗口设置撤销/重做快捷键
    
    Args:
        widget: 要绑定快捷键的窗口组件
        undo_callback: 撤销回调函数
        redo_callback: 重做回调函数
    """
    # Ctrl+Z 撤销
    widget.bind("<Control-z>", lambda e: undo_callback())
    widget.bind("<Control-Z>", lambda e: undo_callback())
    
    # Ctrl+Y 重做
    widget.bind("<Control-y>", lambda e: redo_callback())
    widget.bind("<Control-Y>", lambda e: redo_callback())
    
    # Ctrl+Shift+Z 也可以重做
    widget.bind("<Control-Shift-z>", lambda e: redo_callback())
    widget.bind("<Control-Shift-Z>", lambda e: redo_callback())
