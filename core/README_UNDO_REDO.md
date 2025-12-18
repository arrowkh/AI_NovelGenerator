# 撤销/重做系统使用文档

## 概述

AI_NovelGenerator 现在支持完整的操作撤销/重做功能，让用户可以安全地进行各种创作操作。

## 功能特性

### 1. 基本操作

- **撤销 (Undo)**: `Ctrl+Z` - 撤销上一个操作
- **重做 (Redo)**: `Ctrl+Y` 或 `Ctrl+Shift+Z` - 重做被撤销的操作
- **操作历史**: `Ctrl+H` - 打开操作历史面板

### 2. 支持的操作类型

#### 内容编辑
- 修改章节内容
- 添加章节
- 删除章节
- 批量替换词汇
- 删除/恢复卷

#### 配置修改
- 修改项目配置
- 修改 LLM 参数
- 修改角色信息
- 修改风格档案

#### 生成操作
- 生成章节
- 生成设定
- 生成大纲
- 生成蓝图
- 风格检查和修复

#### 组织操作
- 移动章节
- 重新排序
- 修改标签

### 3. 操作历史面板

通过 `Ctrl+H` 或菜单 `编辑 > 操作历史` 打开操作历史面板，可以：

- 查看最近的操作历史（最多100条）
- 直接从历史面板执行撤销/重做
- 导出操作历史到文本文件
- 清空所有历史记录
- 查看统计信息（可撤销数、可重做数、当前分支）

### 4. 分支管理（时间旅行）

分支功能允许在同一个时间点尝试不同的修改方向：

```
主分支 (main)
├─ Op1 (创建项目)
├─ Op2 (生成设定)
├─ Op3 (生成大纲)
├─ Op4 (修改第1章)
│  ├─ Op5a (尝试版本A) ← 主分支
│  └─ Op5b (尝试版本B) ← 分支 1
```

#### 分支操作

- **创建分支**: 在操作历史面板中点击"分支管理" > "创建分支"
- **切换分支**: 在分支管理面板中选择并切换到其他分支
- **删除分支**: 删除不需要的分支（主分支和当前分支不可删除）

### 5. 操作合并优化

系统会自动合并相邻的相似操作：

```
原始操作: [输入"你"] [输入"好"] [输入"世"] [输入"界"]
合并后: [输入"你好世界"]
```

- 只有相同类型、相同目标、时间间隔小于2秒的操作才会合并
- 这可以避免频繁的小修改产生大量操作历史
- 用户按 Ctrl+Z 一次，整个单词被删除（而不是逐个字符）

### 6. 操作组（宏操作）

对于复杂的批量操作，可以使用操作组：

```python
# 开始操作组
self.undo_redo.begin_group("批量替换 '修为' → '境界'")

# 执行多个操作
for chapter in chapters:
    # ... 执行替换操作 ...
    self.undo_redo.record_chapter_edit(...)

# 结束操作组
self.undo_redo.end_group()
```

操作组中的所有操作会被作为一个单位进行撤销/重做。

## 使用示例

### 示例 1: 编辑章节并撤销

1. 打开 Chapters Manage 标签页
2. 选择一个章节进行编辑
3. 修改内容后点击"保存修改"
4. 如果不满意，按 `Ctrl+Z` 撤销修改
5. 如果想恢复修改，按 `Ctrl+Y` 重做

### 示例 2: 查看操作历史

1. 按 `Ctrl+H` 打开操作历史面板
2. 查看所有最近的操作
3. 可以直接从面板中点击"撤销"或"重做"按钮
4. 点击"导出历史"可以保存操作记录到文本文件

### 示例 3: 创建分支尝试不同方向

1. 在某个操作点，打开操作历史面板
2. 点击"分支管理"按钮
3. 点击"创建分支"，输入分支名称（如 "版本A"）
4. 在主分支上进行一些修改
5. 在分支管理面板中切换到"版本A"分支
6. 在版本A分支上进行另一些修改
7. 可以随时在两个分支间切换，比较不同的修改效果

### 示例 4: 批量操作

```python
# 在代码中使用操作组
self.undo_redo.begin_group("批量生成章节 1-10")

for i in range(1, 11):
    # 生成章节
    content = generate_chapter(i)
    self.undo_redo.record_chapter_generation(str(i), content, len(content))

self.undo_redo.end_group()
```

现在撤销一次就会撤销所有10个章节的生成。

## 技术细节

### 持久化

操作历史会自动保存到项目目录下的 `.undo_redo_history.pkl` 文件中。
这意味着：

- 关闭应用后再打开，操作历史会被保留
- 可以在不同的会话中继续撤销/重做操作
- 删除该文件会清空所有历史记录

### 性能优化

- 操作历史最多保留 1000 条记录
- 超过限制的旧操作会自动被清理
- 操作合并减少了内存占用
- 持久化使用 pickle 序列化，效率较高

### 观察者模式

撤销/重做系统使用观察者模式通知 UI 更新：

```python
def on_undo_redo_event(event_type, data):
    if event_type == "operation_recorded":
        print(f"操作已记录: {data.description}")
    elif event_type == "operation_undone":
        print(f"操作已撤销: {data.description}")

# 注册观察者
undo_redo_manager.add_observer(on_undo_redo_event)
```

## API 参考

### UndoRedoManager

主要的撤销/重做管理器类。

#### 方法

- `record_operation(operation)` - 记录一个操作
- `undo()` - 撤销上一个操作
- `redo()` - 重做被撤销的操作
- `can_undo()` - 判断是否可以撤销
- `can_redo()` - 判断是否可以重做
- `begin_group(description)` - 开始操作组
- `end_group()` - 结束操作组
- `create_branch(name)` - 创建分支
- `switch_branch(name)` - 切换分支
- `delete_branch(name)` - 删除分支
- `get_history(limit)` - 获取操作历史
- `clear_history()` - 清空历史记录

### Operation

表示单个操作的类。

#### 属性

- `operation_type` - 操作类型（OperationType 枚举）
- `target` - 操作目标
- `old_value` - 旧值
- `new_value` - 新值
- `timestamp` - 时间戳
- `metadata` - 元数据字典
- `description` - 操作描述

### UndoRedoIntegration

UI 集成类，连接撤销/重做系统和主界面。

#### 方法

- `record_chapter_edit(chapter_number, old_content, new_content)` - 记录章节编辑
- `record_chapter_add(chapter_number, content)` - 记录添加章节
- `record_chapter_delete(chapter_number, content)` - 记录删除章节
- `record_chapter_generation(chapter_number, content, word_count)` - 记录章节生成
- `record_setting_edit(setting_type, old_value, new_value)` - 记录设定编辑
- `record_batch_replace(old_word, new_word, count)` - 记录批量替换
- `undo()` - 执行撤销
- `redo()` - 执行重做
- `show_history_panel()` - 显示历史面板

## 最佳实践

1. **在修改前缓存内容**: 在加载内容到编辑器时自动缓存，以便记录操作时对比
2. **使用操作组**: 对于批量操作，使用 `begin_group` 和 `end_group` 包装
3. **定期导出历史**: 对于重要的编辑会话，可以导出操作历史作为备份
4. **使用分支**: 当不确定修改方向时，创建分支进行实验
5. **清理历史**: 当历史记录过多时，可以手动清空旧的历史

## 故障排除

### 问题：操作无法撤销

**可能原因**：
- 操作没有被正确记录
- 已经撤销到最早的操作点

**解决方法**：
- 检查 `hasattr(self, 'undo_redo')` 是否返回 True
- 查看操作历史面板确认操作是否被记录

### 问题：撤销后文件内容没有恢复

**可能原因**：
- 持久化路径未设置
- 文件权限问题

**解决方法**：
- 确保项目路径已设置
- 检查文件是否可写
- 查看日志文件了解详细错误信息

### 问题：历史记录丢失

**可能原因**：
- `.undo_redo_history.pkl` 文件被删除
- 持久化失败

**解决方法**：
- 检查项目目录中是否存在 `.undo_redo_history.pkl`
- 查看日志文件了解持久化错误

## 未来改进

计划中的功能：

1. **可视化时间线**: 图形化显示操作历史和分支
2. **智能合并**: 更智能的操作合并算法
3. **云端同步**: 将操作历史同步到云端
4. **协作功能**: 多人协作时的冲突解决
5. **操作回放**: 自动回放操作历史的动画演示

## 相关任务

- **Task 18 (版本管理)**: 撤销/重做系统与版本管理系统配合使用
  - 版本管理用于保存关键时刻的完整快照
  - 撤销系统用于快速回退小改动

## 贡献

如果您发现 bug 或有改进建议，请提交 issue 或 pull request。
