# ui/undo_redo_integration.py
# -*- coding: utf-8 -*-
"""
撤销/重做系统与UI的集成

负责：
- 将操作记录到撤销/重做管理器
- 应用撤销/重做操作
- 管理菜单和快捷键
"""

import os
import logging
from tkinter import messagebox
from typing import TYPE_CHECKING
from core.undo_redo_manager import UndoRedoManager, Operation, OperationType, OperationGroup
from utils import read_file, save_string_to_txt, clear_file_content

if TYPE_CHECKING:
    from ui.main_window import NovelGeneratorGUI


class UndoRedoIntegration:
    """撤销/重做系统集成类"""
    
    def __init__(self, gui: 'NovelGeneratorGUI'):
        """
        初始化集成
        
        Args:
            gui: 主GUI实例
        """
        self.gui = gui
        
        # 创建撤销/重做管理器
        persistence_path = None
        if hasattr(gui, 'filepath_var'):
            filepath = gui.filepath_var.get().strip()
            if filepath:
                persistence_path = os.path.join(filepath, ".undo_redo_history.pkl")
        
        self.manager = UndoRedoManager(
            max_history=1000,
            auto_merge=True,
            persistence_path=persistence_path
        )
        
        # 注册观察者
        self.manager.add_observer(self._on_manager_event)
        
        # 内容缓存，用于记录操作前的状态
        self.content_cache = {}
        
        logging.info("UndoRedoIntegration initialized")
    
    def setup_shortcuts(self):
        """设置快捷键"""
        # Ctrl+Z 撤销
        self.gui.master.bind("<Control-z>", lambda e: self.undo())
        self.gui.master.bind("<Control-Z>", lambda e: self.undo())
        
        # Ctrl+Y 重做
        self.gui.master.bind("<Control-y>", lambda e: self.redo())
        self.gui.master.bind("<Control-Y>", lambda e: self.redo())
        
        # Ctrl+Shift+Z 也可以重做
        self.gui.master.bind("<Control-Shift-z>", lambda e: self.redo())
        self.gui.master.bind("<Control-Shift-Z>", lambda e: self.redo())
        
        # Ctrl+H 显示历史面板
        self.gui.master.bind("<Control-h>", lambda e: self.show_history_panel())
        self.gui.master.bind("<Control-H>", lambda e: self.show_history_panel())
    
    def update_persistence_path(self):
        """更新持久化路径"""
        filepath = self.gui.filepath_var.get().strip()
        if filepath:
            persistence_path = os.path.join(filepath, ".undo_redo_history.pkl")
            self.manager.persistence_path = persistence_path
    
    # ==================== 操作记录 ====================
    
    def record_chapter_edit(self, chapter_number: str, old_content: str, new_content: str):
        """
        记录章节编辑操作
        
        Args:
            chapter_number: 章节号
            old_content: 旧内容
            new_content: 新内容
        """
        if old_content == new_content:
            return
        
        operation = Operation(
            operation_type=OperationType.EDIT_CHAPTER,
            target=f"chapter_{chapter_number}",
            old_value=old_content,
            new_value=new_content,
            description=f"修改第{chapter_number}章内容"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded chapter edit: chapter_{chapter_number}")
    
    def record_chapter_add(self, chapter_number: str, content: str):
        """
        记录添加章节操作
        
        Args:
            chapter_number: 章节号
            content: 章节内容
        """
        operation = Operation(
            operation_type=OperationType.ADD_CHAPTER,
            target=f"chapter_{chapter_number}",
            old_value=None,
            new_value=content,
            description=f"添加第{chapter_number}章"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded chapter add: chapter_{chapter_number}")
    
    def record_chapter_delete(self, chapter_number: str, content: str):
        """
        记录删除章节操作
        
        Args:
            chapter_number: 章节号
            content: 被删除的内容
        """
        operation = Operation(
            operation_type=OperationType.DELETE_CHAPTER,
            target=f"chapter_{chapter_number}",
            old_value=content,
            new_value=None,
            description=f"删除第{chapter_number}章"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded chapter delete: chapter_{chapter_number}")
    
    def record_chapter_generation(self, chapter_number: str, content: str, word_count: int):
        """
        记录章节生成操作
        
        Args:
            chapter_number: 章节号
            content: 生成的内容
            word_count: 字数
        """
        operation = Operation(
            operation_type=OperationType.GENERATE_CHAPTER,
            target=f"chapter_{chapter_number}",
            old_value=None,
            new_value=content,
            metadata={'word_count': word_count},
            description=f"生成第{chapter_number}章 ({word_count}字)"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded chapter generation: chapter_{chapter_number}")
    
    def record_setting_edit(self, setting_type: str, old_value: str, new_value: str):
        """
        记录设定编辑操作
        
        Args:
            setting_type: 设定类型 (architecture/blueprint/character/summary)
            old_value: 旧值
            new_value: 新值
        """
        if old_value == new_value:
            return
        
        operation = Operation(
            operation_type=OperationType.GENERATE_SETTING,
            target=setting_type,
            old_value=old_value,
            new_value=new_value,
            description=f"修改{setting_type}设定"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded setting edit: {setting_type}")
    
    def record_batch_replace(self, old_word: str, new_word: str, count: int):
        """
        记录批量替换操作
        
        Args:
            old_word: 旧词
            new_word: 新词
            count: 替换次数
        """
        operation = Operation(
            operation_type=OperationType.BATCH_REPLACE,
            target="batch_replace",
            old_value=old_word,
            new_value=new_word,
            metadata={'count': count},
            description=f"批量替换 '{old_word}' → '{new_word}' ({count}处)"
        )
        
        self.manager.record_operation(operation)
        logging.debug(f"Recorded batch replace: {old_word} -> {new_word}")
    
    def begin_group(self, description: str):
        """开始操作组"""
        self.manager.begin_group(description)
    
    def end_group(self):
        """结束操作组"""
        self.manager.end_group()
    
    # ==================== 缓存章节内容 ====================
    
    def cache_chapter_content(self, chapter_number: str):
        """
        缓存章节内容（在编辑前调用）
        
        Args:
            chapter_number: 章节号
        """
        filepath = self.gui.filepath_var.get().strip()
        if not filepath:
            return
        
        chapter_file = os.path.join(filepath, "chapters", f"chapter_{chapter_number}.txt")
        if os.path.exists(chapter_file):
            content = read_file(chapter_file)
            self.content_cache[f"chapter_{chapter_number}"] = content
    
    def get_cached_content(self, chapter_number: str) -> str:
        """
        获取缓存的章节内容
        
        Args:
            chapter_number: 章节号
            
        Returns:
            缓存的内容，如果没有则返回空字符串
        """
        return self.content_cache.get(f"chapter_{chapter_number}", "")
    
    def clear_cache(self):
        """清空缓存"""
        self.content_cache.clear()
    
    # ==================== 撤销/重做应用 ====================
    
    def undo(self):
        """执行撤销"""
        if not self.manager.can_undo():
            self.gui.safe_log("没有可撤销的操作")
            return
        
        operation = self.manager.undo()
        if operation:
            self._apply_operation(operation, is_undo=True)
            self.gui.safe_log(f"已撤销: {self._get_operation_description(operation)}")
    
    def redo(self):
        """执行重做"""
        if not self.manager.can_redo():
            self.gui.safe_log("没有可重做的操作")
            return
        
        operation = self.manager.redo()
        if operation:
            self._apply_operation(operation, is_undo=False)
            self.gui.safe_log(f"已重做: {self._get_operation_description(operation)}")
    
    def _get_operation_description(self, operation) -> str:
        """获取操作描述"""
        if isinstance(operation, Operation):
            return operation.description
        elif isinstance(operation, OperationGroup):
            return operation.description
        return "未知操作"
    
    def _apply_operation(self, operation, is_undo: bool):
        """
        应用操作（撤销或重做）
        
        Args:
            operation: 操作对象
            is_undo: 是否为撤销操作
        """
        # 处理操作组
        if isinstance(operation, OperationGroup):
            operations = reversed(operation.operations) if is_undo else operation.operations
            for op in operations:
                self._apply_single_operation(op, is_undo)
        else:
            self._apply_single_operation(operation, is_undo)
    
    def _apply_single_operation(self, operation: Operation, is_undo: bool):
        """
        应用单个操作
        
        Args:
            operation: 操作对象
            is_undo: 是否为撤销操作
        """
        filepath = self.gui.filepath_var.get().strip()
        if not filepath:
            logging.warning("No filepath set, cannot apply operation")
            return
        
        # 根据操作类型应用
        if operation.operation_type in [OperationType.EDIT_CHAPTER, OperationType.GENERATE_CHAPTER]:
            self._apply_chapter_operation(operation, is_undo, filepath)
        
        elif operation.operation_type == OperationType.ADD_CHAPTER:
            self._apply_add_chapter_operation(operation, is_undo, filepath)
        
        elif operation.operation_type == OperationType.DELETE_CHAPTER:
            self._apply_delete_chapter_operation(operation, is_undo, filepath)
        
        elif operation.operation_type == OperationType.GENERATE_SETTING:
            self._apply_setting_operation(operation, is_undo, filepath)
    
    def _apply_chapter_operation(self, operation: Operation, is_undo: bool, filepath: str):
        """应用章节编辑/生成操作"""
        chapter_number = operation.target.replace("chapter_", "")
        chapter_file = os.path.join(filepath, "chapters", f"chapter_{chapter_number}.txt")
        
        # 确定要恢复的内容
        content = operation.old_value if is_undo else operation.new_value
        
        if content is not None:
            # 保存内容
            clear_file_content(chapter_file)
            save_string_to_txt(content, chapter_file)
            
            # 如果当前正在查看这个章节，更新显示
            if hasattr(self.gui, 'chapter_select_var'):
                current_chapter = self.gui.chapter_select_var.get()
                if current_chapter == chapter_number:
                    self.gui.chapter_view_text.delete("0.0", "end")
                    self.gui.chapter_view_text.insert("0.0", content)
            
            logging.debug(f"Applied chapter operation: {operation.target}")
    
    def _apply_add_chapter_operation(self, operation: Operation, is_undo: bool, filepath: str):
        """应用添加章节操作"""
        chapter_number = operation.target.replace("chapter_", "")
        chapter_file = os.path.join(filepath, "chapters", f"chapter_{chapter_number}.txt")
        
        if is_undo:
            # 撤销添加 = 删除章节
            if os.path.exists(chapter_file):
                os.remove(chapter_file)
                logging.debug(f"Removed chapter file: {chapter_file}")
        else:
            # 重做添加 = 恢复章节
            if operation.new_value:
                clear_file_content(chapter_file)
                save_string_to_txt(operation.new_value, chapter_file)
                logging.debug(f"Restored chapter file: {chapter_file}")
        
        # 刷新章节列表
        if hasattr(self.gui, 'refresh_chapters_list'):
            self.gui.refresh_chapters_list()
    
    def _apply_delete_chapter_operation(self, operation: Operation, is_undo: bool, filepath: str):
        """应用删除章节操作"""
        chapter_number = operation.target.replace("chapter_", "")
        chapter_file = os.path.join(filepath, "chapters", f"chapter_{chapter_number}.txt")
        
        if is_undo:
            # 撤销删除 = 恢复章节
            if operation.old_value:
                clear_file_content(chapter_file)
                save_string_to_txt(operation.old_value, chapter_file)
                logging.debug(f"Restored deleted chapter: {chapter_file}")
        else:
            # 重做删除 = 删除章节
            if os.path.exists(chapter_file):
                os.remove(chapter_file)
                logging.debug(f"Re-deleted chapter file: {chapter_file}")
        
        # 刷新章节列表
        if hasattr(self.gui, 'refresh_chapters_list'):
            self.gui.refresh_chapters_list()
    
    def _apply_setting_operation(self, operation: Operation, is_undo: bool, filepath: str):
        """应用设定编辑操作"""
        setting_type = operation.target
        content = operation.old_value if is_undo else operation.new_value
        
        # 根据设定类型保存到相应文件
        file_map = {
            'architecture': 'novel_architecture.txt',
            'blueprint': 'chapter_blueprint.txt',
            'character': 'character_state.txt',
            'summary': 'global_summary.txt'
        }
        
        if setting_type in file_map:
            file_path = os.path.join(filepath, file_map[setting_type])
            clear_file_content(file_path)
            save_string_to_txt(content, file_path)
            
            # 刷新对应的UI
            if setting_type == 'architecture' and hasattr(self.gui, 'load_novel_architecture'):
                self.gui.load_novel_architecture()
            elif setting_type == 'blueprint' and hasattr(self.gui, 'load_chapter_blueprint'):
                self.gui.load_chapter_blueprint()
            elif setting_type == 'character' and hasattr(self.gui, 'load_character_state'):
                self.gui.load_character_state()
            elif setting_type == 'summary' and hasattr(self.gui, 'load_global_summary'):
                self.gui.load_global_summary()
            
            logging.debug(f"Applied setting operation: {setting_type}")
    
    # ==================== UI方法 ====================
    
    def show_history_panel(self):
        """显示历史面板"""
        from ui.undo_redo_panel import UndoRedoPanel
        
        panel = UndoRedoPanel(
            self.gui.master,
            self.manager,
            apply_undo_callback=lambda op: self._apply_operation(op, is_undo=True),
            apply_redo_callback=lambda op: self._apply_operation(op, is_undo=False)
        )
    
    def get_status_text(self) -> str:
        """
        获取状态文本
        
        Returns:
            状态文本，如 "撤销(5) | 重做(2)"
        """
        undo_count = self.manager.get_undo_count()
        redo_count = self.manager.get_redo_count()
        return f"撤销({undo_count}) | 重做({redo_count})"
    
    def _on_manager_event(self, event_type: str, data):
        """响应管理器事件"""
        # 可以在这里添加UI更新逻辑
        pass
    
    def cleanup(self):
        """清理资源"""
        self.manager.remove_observer(self._on_manager_event)
