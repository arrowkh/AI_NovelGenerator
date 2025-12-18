# core/undo_redo_manager.py
# -*- coding: utf-8 -*-
"""
完整的操作撤销/重做系统

支持功能：
- 操作堆栈管理（撤销/重做）
- 分支管理（时间旅行）
- 操作合并优化
- 操作持久化
- 观察者模式通知UI更新
"""

import os
import pickle
import logging
import time
from collections import deque
from datetime import datetime
from typing import Any, Dict, List, Optional, Callable, Tuple
from enum import Enum
from dataclasses import dataclass, field


class OperationType(Enum):
    """操作类型枚举"""
    # 内容编辑
    EDIT_CHAPTER = "edit_chapter"
    ADD_CHAPTER = "add_chapter"
    DELETE_CHAPTER = "delete_chapter"
    BATCH_REPLACE = "batch_replace"
    DELETE_VOLUME = "delete_volume"
    RESTORE_VOLUME = "restore_volume"
    
    # 配置修改
    MODIFY_CONFIG = "modify_config"
    MODIFY_LLM_PARAMS = "modify_llm_params"
    MODIFY_CHARACTER = "modify_character"
    MODIFY_STYLE_PROFILE = "modify_style_profile"
    
    # 生成操作
    GENERATE_CHAPTER = "generate_chapter"
    GENERATE_SETTING = "generate_setting"
    GENERATE_ARCHITECTURE = "generate_architecture"
    GENERATE_BLUEPRINT = "generate_blueprint"
    STYLE_CHECK_FIX = "style_check_fix"
    
    # 组织操作
    MOVE_CHAPTER = "move_chapter"
    REORDER = "reorder"
    MODIFY_TAG = "modify_tag"
    
    # 知识库操作
    IMPORT_KNOWLEDGE = "import_knowledge"
    CLEAR_VECTORSTORE = "clear_vectorstore"


@dataclass
class Operation:
    """单个操作的数据结构"""
    operation_type: OperationType
    target: str  # 操作的目标对象标识符
    old_value: Any  # 操作前的值
    new_value: Any  # 操作后的值
    timestamp: float = field(default_factory=time.time)
    metadata: Dict[str, Any] = field(default_factory=dict)  # 额外信息
    description: str = ""  # 操作描述
    
    def __post_init__(self):
        if not self.description:
            self.description = self._generate_description()
    
    def _generate_description(self) -> str:
        """生成操作描述"""
        op_type = self.operation_type.value
        if self.operation_type == OperationType.EDIT_CHAPTER:
            return f"修改章节 {self.target}"
        elif self.operation_type == OperationType.ADD_CHAPTER:
            return f"添加章节 {self.target}"
        elif self.operation_type == OperationType.DELETE_CHAPTER:
            return f"删除章节 {self.target}"
        elif self.operation_type == OperationType.GENERATE_CHAPTER:
            word_count = self.metadata.get('word_count', '未知')
            return f"生成章节 {self.target} ({word_count}字)"
        elif self.operation_type == OperationType.BATCH_REPLACE:
            count = self.metadata.get('count', 0)
            return f"批量替换 '{self.old_value}' → '{self.new_value}' ({count}处)"
        else:
            return f"{op_type}: {self.target}"
    
    def can_merge_with(self, other: 'Operation') -> bool:
        """判断是否可以与另一个操作合并"""
        if self.operation_type != other.operation_type:
            return False
        if self.target != other.target:
            return False
        
        # 只有编辑类操作可以合并
        if self.operation_type not in [OperationType.EDIT_CHAPTER, OperationType.MODIFY_CHARACTER]:
            return False
        
        # 时间间隔小于2秒的操作可以合并
        time_diff = other.timestamp - self.timestamp
        if time_diff > 2.0:
            return False
        
        return True
    
    def merge_with(self, other: 'Operation') -> 'Operation':
        """与另一个操作合并"""
        return Operation(
            operation_type=self.operation_type,
            target=self.target,
            old_value=self.old_value,  # 保留最早的旧值
            new_value=other.new_value,  # 使用最新的新值
            timestamp=self.timestamp,  # 保留最早的时间戳
            metadata=self.metadata,
            description=self._generate_description()
        )


@dataclass
class OperationGroup:
    """操作组，用于将多个操作作为一个单位进行撤销/重做"""
    operations: List[Operation] = field(default_factory=list)
    description: str = ""
    timestamp: float = field(default_factory=time.time)
    
    def add_operation(self, operation: Operation):
        """添加操作到组"""
        self.operations.append(operation)
    
    def is_empty(self) -> bool:
        """判断操作组是否为空"""
        return len(self.operations) == 0


class OperationBranch:
    """操作分支，用于管理操作的分支"""
    def __init__(self, name: str, parent_branch: Optional[str] = None, 
                 branch_point: int = 0):
        self.name = name
        self.parent_branch = parent_branch
        self.branch_point = branch_point  # 从哪个操作点分支出来的
        self.operations: deque = deque(maxlen=1000)  # 操作历史
        self.created_at = time.time()


class UndoRedoManager:
    """
    撤销/重做管理器
    
    功能：
    - 操作堆栈管理
    - 分支管理
    - 操作合并
    - 持久化
    - 观察者通知
    """
    
    def __init__(self, max_history: int = 1000, auto_merge: bool = True,
                 persistence_path: Optional[str] = None):
        """
        初始化撤销/重做管理器
        
        Args:
            max_history: 最大历史记录数
            auto_merge: 是否自动合并相邻的相似操作
            persistence_path: 持久化存储路径
        """
        self.max_history = max_history
        self.auto_merge = auto_merge
        self.persistence_path = persistence_path
        
        # 操作堆栈
        self.undo_stack: deque = deque(maxlen=max_history)
        self.redo_stack: deque = deque(maxlen=max_history)
        
        # 分支管理
        self.branches: Dict[str, OperationBranch] = {}
        self.current_branch = "main"
        self.branches["main"] = OperationBranch("main")
        
        # 操作组管理
        self.current_group: Optional[OperationGroup] = None
        self.is_grouping = False
        
        # 观察者列表
        self.observers: List[Callable] = []
        
        # 加载持久化数据
        if persistence_path:
            self._load_from_disk()
        
        logging.info("UndoRedoManager initialized")
    
    # ==================== 基本操作 ====================
    
    def record_operation(self, operation: Operation):
        """
        记录一个操作
        
        Args:
            operation: 操作对象
        """
        # 如果正在进行操作分组，添加到当前组
        if self.is_grouping and self.current_group:
            self.current_group.add_operation(operation)
            return
        
        # 尝试与上一个操作合并
        if self.auto_merge and len(self.undo_stack) > 0:
            last_op = self.undo_stack[-1]
            if isinstance(last_op, Operation) and last_op.can_merge_with(operation):
                merged_op = last_op.merge_with(operation)
                self.undo_stack[-1] = merged_op
                self._notify_observers("operation_merged", merged_op)
                return
        
        # 添加新操作到撤销栈
        self.undo_stack.append(operation)
        
        # 清空重做栈（因为进行了新操作）
        self.redo_stack.clear()
        
        # 添加到当前分支
        current_branch = self.branches[self.current_branch]
        current_branch.operations.append(operation)
        
        # 通知观察者
        self._notify_observers("operation_recorded", operation)
        
        # 持久化
        if self.persistence_path:
            self._save_to_disk()
        
        logging.debug(f"Operation recorded: {operation.description}")
    
    def undo(self) -> Optional[Operation]:
        """
        撤销上一个操作
        
        Returns:
            被撤销的操作，如果没有可撤销的操作则返回None
        """
        if not self.can_undo():
            logging.warning("No operation to undo")
            return None
        
        operation = self.undo_stack.pop()
        
        # 处理操作组
        if isinstance(operation, OperationGroup):
            # 撤销组内所有操作（逆序）
            for op in reversed(operation.operations):
                self._apply_undo(op)
        else:
            self._apply_undo(operation)
        
        # 移动到重做栈
        self.redo_stack.append(operation)
        
        # 通知观察者
        self._notify_observers("operation_undone", operation)
        
        # 持久化
        if self.persistence_path:
            self._save_to_disk()
        
        logging.info(f"Operation undone: {operation.description if isinstance(operation, Operation) else operation.description}")
        return operation
    
    def redo(self) -> Optional[Operation]:
        """
        重做上一个被撤销的操作
        
        Returns:
            被重做的操作，如果没有可重做的操作则返回None
        """
        if not self.can_redo():
            logging.warning("No operation to redo")
            return None
        
        operation = self.redo_stack.pop()
        
        # 处理操作组
        if isinstance(operation, OperationGroup):
            # 重做组内所有操作
            for op in operation.operations:
                self._apply_redo(op)
        else:
            self._apply_redo(operation)
        
        # 移动回撤销栈
        self.undo_stack.append(operation)
        
        # 通知观察者
        self._notify_observers("operation_redone", operation)
        
        # 持久化
        if self.persistence_path:
            self._save_to_disk()
        
        logging.info(f"Operation redone: {operation.description if isinstance(operation, Operation) else operation.description}")
        return operation
    
    def _apply_undo(self, operation: Operation):
        """应用撤销操作"""
        # 这里只是记录，实际的撤销逻辑由外部实现
        # 通过观察者模式通知外部系统执行实际的撤销
        pass
    
    def _apply_redo(self, operation: Operation):
        """应用重做操作"""
        # 这里只是记录，实际的重做逻辑由外部实现
        # 通过观察者模式通知外部系统执行实际的重做
        pass
    
    def can_undo(self) -> bool:
        """判断是否可以撤销"""
        return len(self.undo_stack) > 0
    
    def can_redo(self) -> bool:
        """判断是否可以重做"""
        return len(self.redo_stack) > 0
    
    def get_undo_count(self) -> int:
        """获取可撤销的操作数量"""
        return len(self.undo_stack)
    
    def get_redo_count(self) -> int:
        """获取可重做的操作数量"""
        return len(self.redo_stack)
    
    def get_last_operation(self) -> Optional[Operation]:
        """获取最后一个操作"""
        if len(self.undo_stack) > 0:
            return self.undo_stack[-1]
        return None
    
    # ==================== 操作组管理 ====================
    
    def begin_group(self, description: str = ""):
        """开始一个操作组"""
        if self.is_grouping:
            logging.warning("Already in a group, ending previous group")
            self.end_group()
        
        self.is_grouping = True
        self.current_group = OperationGroup(description=description)
        logging.debug(f"Operation group started: {description}")
    
    def end_group(self):
        """结束当前操作组"""
        if not self.is_grouping or not self.current_group:
            logging.warning("No active group to end")
            return
        
        self.is_grouping = False
        
        # 如果操作组不为空，添加到撤销栈
        if not self.current_group.is_empty():
            self.undo_stack.append(self.current_group)
            self.redo_stack.clear()
            
            # 通知观察者
            self._notify_observers("group_recorded", self.current_group)
            
            logging.debug(f"Operation group ended: {self.current_group.description}, {len(self.current_group.operations)} operations")
        
        self.current_group = None
        
        # 持久化
        if self.persistence_path:
            self._save_to_disk()
    
    # ==================== 分支管理 ====================
    
    def create_branch(self, branch_name: str) -> bool:
        """
        创建一个新分支
        
        Args:
            branch_name: 分支名称
            
        Returns:
            是否创建成功
        """
        if branch_name in self.branches:
            logging.warning(f"Branch {branch_name} already exists")
            return False
        
        # 当前操作点
        branch_point = len(self.undo_stack)
        
        # 创建新分支
        new_branch = OperationBranch(
            name=branch_name,
            parent_branch=self.current_branch,
            branch_point=branch_point
        )
        
        self.branches[branch_name] = new_branch
        
        # 通知观察者
        self._notify_observers("branch_created", branch_name)
        
        logging.info(f"Branch created: {branch_name}")
        return True
    
    def switch_branch(self, branch_name: str) -> bool:
        """
        切换到指定分支
        
        Args:
            branch_name: 分支名称
            
        Returns:
            是否切换成功
        """
        if branch_name not in self.branches:
            logging.warning(f"Branch {branch_name} does not exist")
            return False
        
        if branch_name == self.current_branch:
            logging.info(f"Already on branch {branch_name}")
            return True
        
        old_branch = self.current_branch
        self.current_branch = branch_name
        
        # 通知观察者
        self._notify_observers("branch_switched", (old_branch, branch_name))
        
        logging.info(f"Switched from branch {old_branch} to {branch_name}")
        return True
    
    def delete_branch(self, branch_name: str) -> bool:
        """
        删除指定分支
        
        Args:
            branch_name: 分支名称
            
        Returns:
            是否删除成功
        """
        if branch_name == "main":
            logging.warning("Cannot delete main branch")
            return False
        
        if branch_name not in self.branches:
            logging.warning(f"Branch {branch_name} does not exist")
            return False
        
        if branch_name == self.current_branch:
            logging.warning("Cannot delete current branch, switch to another branch first")
            return False
        
        del self.branches[branch_name]
        
        # 通知观察者
        self._notify_observers("branch_deleted", branch_name)
        
        logging.info(f"Branch deleted: {branch_name}")
        return True
    
    def get_branches(self) -> List[str]:
        """获取所有分支名称"""
        return list(self.branches.keys())
    
    def get_current_branch(self) -> str:
        """获取当前分支名称"""
        return self.current_branch
    
    # ==================== 历史记录 ====================
    
    def get_history(self, limit: int = 50) -> List[Tuple[str, str, float]]:
        """
        获取操作历史
        
        Args:
            limit: 返回的最大记录数
            
        Returns:
            操作历史列表 [(描述, 类型, 时间戳)]
        """
        history = []
        for item in list(self.undo_stack)[-limit:]:
            if isinstance(item, Operation):
                history.append((
                    item.description,
                    item.operation_type.value,
                    item.timestamp
                ))
            elif isinstance(item, OperationGroup):
                history.append((
                    item.description,
                    "group",
                    item.timestamp
                ))
        return list(reversed(history))
    
    def jump_to_operation(self, index: int) -> bool:
        """
        跳转到指定的操作点
        
        Args:
            index: 操作索引（0为最早的操作）
            
        Returns:
            是否跳转成功
        """
        current_index = len(self.undo_stack)
        
        if index < 0 or index > current_index:
            logging.warning(f"Invalid operation index: {index}")
            return False
        
        # 撤销到目标点
        while len(self.undo_stack) > index:
            self.undo()
        
        # 重做到目标点
        while len(self.undo_stack) < index:
            self.redo()
        
        logging.info(f"Jumped to operation {index}")
        return True
    
    def clear_history(self):
        """清空所有历史记录"""
        self.undo_stack.clear()
        self.redo_stack.clear()
        
        # 清空所有分支
        for branch in self.branches.values():
            branch.operations.clear()
        
        # 通知观察者
        self._notify_observers("history_cleared", None)
        
        # 持久化
        if self.persistence_path:
            self._save_to_disk()
        
        logging.info("History cleared")
    
    # ==================== 观察者模式 ====================
    
    def add_observer(self, observer: Callable):
        """
        添加观察者
        
        Args:
            observer: 观察者函数，接收两个参数：event_type 和 data
        """
        if observer not in self.observers:
            self.observers.append(observer)
            logging.debug(f"Observer added: {observer}")
    
    def remove_observer(self, observer: Callable):
        """
        移除观察者
        
        Args:
            observer: 观察者函数
        """
        if observer in self.observers:
            self.observers.remove(observer)
            logging.debug(f"Observer removed: {observer}")
    
    def _notify_observers(self, event_type: str, data: Any):
        """
        通知所有观察者
        
        Args:
            event_type: 事件类型
            data: 事件数据
        """
        for observer in self.observers:
            try:
                observer(event_type, data)
            except Exception as e:
                logging.error(f"Error notifying observer: {e}")
    
    # ==================== 持久化 ====================
    
    def _save_to_disk(self):
        """保存到磁盘"""
        if not self.persistence_path:
            return
        
        try:
            os.makedirs(os.path.dirname(self.persistence_path), exist_ok=True)
            
            data = {
                'undo_stack': list(self.undo_stack),
                'redo_stack': list(self.redo_stack),
                'current_branch': self.current_branch,
                'branches': self.branches
            }
            
            with open(self.persistence_path, 'wb') as f:
                pickle.dump(data, f)
            
            logging.debug("Undo/redo data saved to disk")
        except Exception as e:
            logging.error(f"Error saving undo/redo data: {e}")
    
    def _load_from_disk(self):
        """从磁盘加载"""
        if not self.persistence_path or not os.path.exists(self.persistence_path):
            return
        
        try:
            with open(self.persistence_path, 'rb') as f:
                data = pickle.load(f)
            
            self.undo_stack = deque(data['undo_stack'], maxlen=self.max_history)
            self.redo_stack = deque(data['redo_stack'], maxlen=self.max_history)
            self.current_branch = data['current_branch']
            self.branches = data['branches']
            
            logging.info(f"Undo/redo data loaded from disk: {len(self.undo_stack)} operations")
        except Exception as e:
            logging.error(f"Error loading undo/redo data: {e}")
    
    # ==================== 工具方法 ====================
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return {
            'undo_count': self.get_undo_count(),
            'redo_count': self.get_redo_count(),
            'branches': len(self.branches),
            'current_branch': self.current_branch,
            'max_history': self.max_history,
            'auto_merge': self.auto_merge
        }
    
    def __repr__(self) -> str:
        return f"UndoRedoManager(undo={self.get_undo_count()}, redo={self.get_redo_count()}, branch={self.current_branch})"
