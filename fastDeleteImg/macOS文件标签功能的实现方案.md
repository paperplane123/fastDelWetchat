# 标签颜色映射
```python
TAGS = {
    '1': ('Red', '\033[31m●\033[0m'),     # 红色
    '2': ('Orange', '\033[33m●\033[0m'),  # 橙色
    '3': ('Yellow', '\033[33m●\033[0m'),  # 黄色
    # ... 其他颜色
}
```
这个映射定义了数字键与颜色的对应关系，方便在UI和后端之间传递标签信息。
# 核心实现方法 我们使用了macOS的AppleScript来设置标签，主要代码如下：
```python
script = '''
tell application "Finder"
    if exists POSIX file "{file_path}" then
        set theFile to POSIX file "{file_path}" as alias
        set label index of theFile to {tag_key}
    end if
end tell
'''
```
关键点:

- 使用label index而不是tag名称，这是macOS Finder的原生属性
- 直接使用数字索引（1-7）对应不同颜色
- 通过osascript -e命令执行AppleScript

# 刷新机制 为了确保标签变更立即可见，添加了Finder刷新功能：
```python
def _refresh_finder(file_path: str):
    script = '''
    tell application "Finder"
        if exists POSIX file "{file_path}" then
            update POSIX file "{file_path}"
        end if
    end tell
    '''
```
# 错误处理
- 检查文件是否存在
- 检查文件权限
- 捕获并记录所有可能的错误

这个实现方案的优点是：

- 使用macOS的原生功能，可靠性高
- 不依赖第三方命令行工具
- 变更立即可见
- 错误处理完善
使用示例：
```python
MacOSUtils.set_tag(file_path, '1')  # 设置红色标签
```
这个实现比之前使用tag命令行工具的方案更可靠，因为它直接使用了macOS的原生功能。标签会立即显示在Finder中，并且与系统的其他部分（如Spotlight搜索）完全兼容。