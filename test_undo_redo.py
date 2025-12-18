# test_undo_redo.py
# -*- coding: utf-8 -*-
"""
撤销/重做系统测试

运行此脚本测试撤销/重做功能是否正常工作
"""

import os
import sys
import tempfile
from core.undo_redo_manager import UndoRedoManager, Operation, OperationType, OperationGroup


def test_basic_undo_redo():
    """测试基本的撤销/重做功能"""
    print("测试1: 基本撤销/重做功能")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=False)
    
    # 记录操作
    op1 = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="Hello",
        new_value="Hello World"
    )
    manager.record_operation(op1)
    
    op2 = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="Hello World",
        new_value="Hello World!"
    )
    manager.record_operation(op2)
    
    print(f"记录了 {manager.get_undo_count()} 个操作")
    assert manager.get_undo_count() == 2, "应该有2个可撤销的操作"
    
    # 撤销
    undone = manager.undo()
    print(f"撤销操作: {undone.description}")
    assert manager.get_undo_count() == 1, "撤销后应该只有1个可撤销的操作"
    assert manager.get_redo_count() == 1, "应该有1个可重做的操作"
    
    # 重做
    redone = manager.redo()
    print(f"重做操作: {redone.description}")
    assert manager.get_undo_count() == 2, "重做后应该有2个可撤销的操作"
    assert manager.get_redo_count() == 0, "不应该有可重做的操作"
    
    print("✓ 基本撤销/重做功能测试通过\n")


def test_operation_merge():
    """测试操作合并功能"""
    print("测试2: 操作合并功能")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=True)
    
    # 记录多个相似操作（时间间隔很短）
    import time
    
    op1 = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="",
        new_value="你"
    )
    manager.record_operation(op1)
    
    time.sleep(0.1)  # 很短的时间间隔
    
    op2 = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="你",
        new_value="你好"
    )
    manager.record_operation(op2)
    
    # 操作应该被合并
    assert manager.get_undo_count() == 1, "操作应该被合并为1个"
    
    merged_op = manager.get_last_operation()
    assert merged_op.old_value == "", "合并后的旧值应该是空字符串"
    assert merged_op.new_value == "你好", "合并后的新值应该是'你好'"
    
    print(f"合并后的操作: {merged_op.description}")
    print("✓ 操作合并功能测试通过\n")


def test_operation_group():
    """测试操作组功能"""
    print("测试3: 操作组功能")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=False)
    
    # 开始操作组
    manager.begin_group("批量生成章节")
    
    # 记录多个操作
    for i in range(1, 6):
        op = Operation(
            operation_type=OperationType.GENERATE_CHAPTER,
            target=f"chapter_{i}",
            old_value=None,
            new_value=f"Chapter {i} content",
            metadata={'word_count': 1000}
        )
        manager.record_operation(op)
    
    # 结束操作组
    manager.end_group()
    
    # 应该只有1个操作（操作组）
    assert manager.get_undo_count() == 1, "操作组应该算作1个操作"
    
    # 撤销操作组
    undone = manager.undo()
    assert isinstance(undone, OperationGroup), "应该是操作组"
    assert len(undone.operations) == 5, "操作组应该包含5个操作"
    
    print(f"操作组包含 {len(undone.operations)} 个操作")
    print("✓ 操作组功能测试通过\n")


def test_branches():
    """测试分支功能"""
    print("测试4: 分支功能")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=False)
    
    # 在主分支记录操作
    op1 = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="A",
        new_value="B"
    )
    manager.record_operation(op1)
    
    # 创建分支
    assert manager.create_branch("version_a"), "应该能创建分支"
    assert "version_a" in manager.get_branches(), "分支应该存在"
    
    # 切换到新分支
    assert manager.switch_branch("version_a"), "应该能切换分支"
    assert manager.get_current_branch() == "version_a", "当前分支应该是version_a"
    
    # 切换回主分支
    assert manager.switch_branch("main"), "应该能切换回主分支"
    
    # 删除分支
    assert manager.delete_branch("version_a"), "应该能删除分支"
    assert "version_a" not in manager.get_branches(), "分支应该被删除"
    
    print("✓ 分支功能测试通过\n")


def test_persistence():
    """测试持久化功能"""
    print("测试5: 持久化功能")
    print("-" * 50)
    
    # 创建临时文件
    temp_file = tempfile.mktemp(suffix=".pkl")
    
    try:
        # 创建管理器并记录操作
        manager1 = UndoRedoManager(persistence_path=temp_file, auto_merge=False)
        
        op1 = Operation(
            operation_type=OperationType.EDIT_CHAPTER,
            target="chapter_1",
            old_value="A",
            new_value="B"
        )
        manager1.record_operation(op1)
        
        op2 = Operation(
            operation_type=OperationType.EDIT_CHAPTER,
            target="chapter_2",
            old_value="C",
            new_value="D"
        )
        manager1.record_operation(op2)
        
        assert manager1.get_undo_count() == 2, "应该有2个操作"
        
        # 创建新的管理器，应该加载之前的数据
        manager2 = UndoRedoManager(persistence_path=temp_file, auto_merge=False)
        
        assert manager2.get_undo_count() == 2, "应该从磁盘加载2个操作"
        
        print(f"从磁盘加载了 {manager2.get_undo_count()} 个操作")
        print("✓ 持久化功能测试通过\n")
        
    finally:
        # 清理临时文件
        if os.path.exists(temp_file):
            os.remove(temp_file)


def test_history():
    """测试历史记录功能"""
    print("测试6: 历史记录功能")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=False)
    
    # 记录多个操作
    for i in range(1, 11):
        op = Operation(
            operation_type=OperationType.EDIT_CHAPTER,
            target=f"chapter_{i}",
            old_value=f"Old {i}",
            new_value=f"New {i}"
        )
        manager.record_operation(op)
    
    # 获取历史
    history = manager.get_history(limit=5)
    assert len(history) == 5, "应该返回最近的5条历史"
    
    # 历史应该是逆序的（最新的在前）
    assert "chapter_10" in history[0][0], "第一条应该是最新的操作"
    
    print(f"获取了 {len(history)} 条历史记录")
    for desc, op_type, timestamp in history[:3]:
        print(f"  - {desc}")
    
    print("✓ 历史记录功能测试通过\n")


def test_observer_pattern():
    """测试观察者模式"""
    print("测试7: 观察者模式")
    print("-" * 50)
    
    manager = UndoRedoManager(max_history=100, auto_merge=False)
    
    # 记录事件
    events = []
    
    def observer(event_type, data):
        events.append(event_type)
    
    # 添加观察者
    manager.add_observer(observer)
    
    # 记录操作
    op = Operation(
        operation_type=OperationType.EDIT_CHAPTER,
        target="chapter_1",
        old_value="A",
        new_value="B"
    )
    manager.record_operation(op)
    
    # 应该收到事件
    assert "operation_recorded" in events, "应该收到operation_recorded事件"
    
    # 撤销操作
    manager.undo()
    assert "operation_undone" in events, "应该收到operation_undone事件"
    
    # 重做操作
    manager.redo()
    assert "operation_redone" in events, "应该收到operation_redone事件"
    
    print(f"收到了 {len(events)} 个事件")
    print("✓ 观察者模式测试通过\n")


def run_all_tests():
    """运行所有测试"""
    print("=" * 50)
    print("撤销/重做系统测试")
    print("=" * 50)
    print()
    
    try:
        test_basic_undo_redo()
        test_operation_merge()
        test_operation_group()
        test_branches()
        test_persistence()
        test_history()
        test_observer_pattern()
        
        print("=" * 50)
        print("✓ 所有测试通过！")
        print("=" * 50)
        return True
        
    except AssertionError as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n✗ 测试出错: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
