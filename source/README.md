# AutoGPT Trading System 最终备份

## 备份信息
- **备份时间**: 2026-02-20 22:27:42 (GMT+8)
- **备份位置**: `E:\TradingSystem\backup_20260220_2226\`
- **系统状态**: 最终版本，准备人工测试
- **重要修改**: 移除重试机制，优化等待时间

## 系统概述
这是一个基于Python的自动交易系统，集成了：
1. **MT5连接** - 获取市场数据和执行交易
2. **AutoGPT决策** - 基于技术信号进行交易决策
3. **Executor执行** - 通过PyAutoGUI控制MT5界面（快速失败机制）
4. **Web管理界面** - Flask Web界面进行配置和监控

## 核心文件说明

### 主要模块
1. **`autogpt_trading.py`** - 主应用程序
   - 连接Ollama LLM进行策略讨论
   - 计算技术指标和信号（MA交叉、RSI、MACD等）
   - **重要特性**: 输出具体价格数值（非百分比）
   - 示例输出: `做多 止损38300.50 止盈38800.50`

2. **`executor_agent.py`** - 执行器代理（**最终版本**）
   - 通过PyAutoGUI控制MT5界面
   - **最终修改** (22:24): 移除所有重试机制，快速失败
   - **窗口激活**: 0.05秒等待（用户手动确保MT5在前台）
   - **时间规则**: 严格遵守点击和等待时间
   - **执行逻辑**: 失败立即放弃，等待下次机会
   - **价格输入**: 直接复制粘贴计算好的价格到MT5

3. **`web_interface.py`** - Web管理界面
   - Flask服务器 (默认端口5000)
   - 配置交易策略和参数
   - 测试MT5连接和指标计算
   - 校准MT5按钮位置
   - 切换讨论/盯盘模式

### 配置文件
4. **`config.json`** - 系统配置
   - 交易品种: US30
   - 手数: 0.1
   - 监控间隔: 0.5秒
   - 做多/做空策略和百分比
   - 技术指标配置

5. **`mt5_positions.json`** - MT5位置校准
   - 存储MT5窗口按钮坐标
   - 包含: sl_input, tp_input, buy_btn, sell_btn等位置

### 启动和管理脚本
6. **`start_trading_fixed.bat`** - 修复版启动脚本
   - 尝试绕过UAC限制
   - 自动启动所有组件
   - 自动窗口布局调整

7. **`start_manual.bat`** - 手动启动脚本（**推荐**）
   - 逐步指导，100%避开UAC
   - 每步需要按任意键继续
   - 确保组件按正确顺序启动

8. **`window_manager.py`** - 窗口管理器
   - 自动定位MT5到屏幕左侧
   - 自动定位浏览器到屏幕右侧
   - 可单独运行: `python window_manager.py`

### 辅助文件
9. **`executor_changes_20260220_2224.txt`** - 修改记录
    - 记录了22:24对executor_agent.py的重要修改
    - 移除重试机制，减少等待时间

10. **`templates/`** - 按钮模板
    - OpenCV模板匹配用的按钮图片
    - 用于查找MT5界面元素

## 最终修改详情（2026-02-20 22:24）

### 修改原则
基于用户要求："一旦出错就直接取消，等待下次买卖的机会出现"

### 具体修改
1. **窗口激活等待时间优化**
   - 从0.3秒减少到 **0.05秒**
   - 用户会在开始盯盘后手动切回MT5，无需长时间等待
   - 移除二次激活检查和确认逻辑

2. **完全移除重试机制** ❌
   - **窗口激活失败重试** - 移除，失败立即放弃
   - **交易验证失败重试** - 移除，失败立即放弃  
   - **点击操作失败重试** - 移除，失败立即放弃
   - **异常情况重试** - 移除，失败立即放弃

3. **简化执行逻辑** - 快速失败机制
   ```python
   # 新逻辑（买入/卖出类似）
   if not self.activate_mt5_window():
       self.log("❌ 无法激活MT5窗口，放弃此次交易")
       return False
   
   success = self.execute_buy(...)
   if not success:
       self.log("❌ 操作失败，放弃此次交易")
       return False
   
   # 验证交易
   if not self.check_mt5_positions():
       self.log("❌ 交易验证失败，放弃此次交易")
       return False
   
   return True  # 成功
   ```

## 启动方式

### 推荐方式：手动启动（避开UAC）
```bash
cd E:\TradingSystem
start_manual.bat
```

### 备选方式：修复版自动启动
```bash
cd E:\TradingSystem
start_trading_fixed.bat
```

### 单独调整窗口位置
```bash
cd E:\TradingSystem
python window_manager.py
```

## 使用流程

### 1. 首次设置
1. 启动MT5并登录
2. 打开Web界面: `http://127.0.0.1:5000`
3. 设置交易品种和策略
4. 点击"校准"按钮，按提示点击MT5界面元素

### 2. 日常使用
1. 使用`start_manual.bat`启动系统
2. **手动切换到MT5窗口**（系统激活窗口只需0.05秒）
3. Web界面会自动打开在屏幕右侧
4. 在Web界面切换到"自动盯盘"模式

### 3. 交易流程（快速失败机制）
1. MT5连接 → Python计算技术信号 → AutoGPT决策 → Executor执行
2. Executor执行: 激活窗口(0.05s) → 按F9(0.8s) → 填价格 → 点击买卖
3. **任何一步失败立即放弃**，等待下次交易机会
4. 用户手动确保MT5窗口在前台

## 重要注意事项

### 最终版本特性
- **快速失败**: 出错立即放弃，不浪费时间重试
- **机会优先**: 错过本次交易，等待下次信号出现
- **用户控制**: 用户手动确保MT5在前台，系统快速响应
- **价格输出**: AutoGPT输出具体价格数值，Executor直接复制粘贴

### 系统要求
- Windows 10/11
- Python 3.8+
- MetaTrader 5 已安装并登录
- MT5快捷键F9设置为打开订单窗口

### 依赖包
```bash
pip install MetaTrader5 pyautogui flask requests opencv-python pillow pywin32 pygetwindow pyperclip
```

### 故障排除
1. **UAC问题**: 使用`start_manual.bat`手动启动
2. **MT5连接失败**: 检查MT5是否已启动并登录
3. **窗口位置错误**: 运行`python window_manager.py`
4. **校准问题**: 在Web界面重新校准MT5按钮位置
5. **交易失败**: 系统会立即放弃，等待下次机会

## 恢复备份
如需从备份恢复系统：
```bash
cd E:\TradingSystem\backup_20260220_2226
restore.bat
```
或手动复制文件回主目录。

## 版本历史
- **backup_20260220_2127**: 包含价格输出和窗口管理修改
- **backup_20260220_2220**: 包含重试机制和增强功能
- **backup_20260220_2226**: **最终版本** - 移除重试，快速失败机制

---
**备份完成时间**: 2026-02-20 22:27:42
**系统状态**: 最终版本，准备人工测试
**测试建议**: 使用`start_manual.bat`启动，观察快速失败机制是否符合预期