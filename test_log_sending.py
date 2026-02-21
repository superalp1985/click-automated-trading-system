"""测试AutoGPT日志发送到Web界面"""
import requests
import json
import time

def test_log_sending():
    """测试日志发送功能"""
    print("测试AutoGPT日志发送到Web界面...")
    
    # 测试web界面是否响应
    try:
        response = requests.get('http://127.0.0.1:5000/get_logs', timeout=5)
        print(f"[OK] Web界面响应: HTTP {response.status_code}")
    except Exception as e:
        print(f"[ERR] Web界面无法访问: {e}")
        return False
    
    # 发送测试日志
    test_message = f"测试日志 - {time.strftime('%H:%M:%S')}"
    try:
        response = requests.post(
            'http://127.0.0.1:5000/save_log',
            json={'type': 'log', 'message': test_message},
            timeout=5
        )
        if response.status_code == 200:
            print(f"[OK] 日志发送成功: '{test_message}'")
        else:
            print(f"[ERR] 日志发送失败: HTTP {response.status_code}")
            return False
    except Exception as e:
        print(f"[ERR] 日志发送异常: {e}")
        return False
    
    # 验证日志是否已保存
    time.sleep(1)
    try:
        response = requests.get('http://127.0.0.1:5000/get_logs', timeout=5)
        logs = response.json().get('logs', [])
        last_log = logs[-1] if logs else None
        if last_log and test_message in last_log.get('message', ''):
            print(f"[OK] 日志确认已保存到Web界面")
            return True
        else:
            print(f"[ERR] 日志未在Web界面中找到")
            return False
    except Exception as e:
        print(f"[ERR] 获取日志失败: {e}")
        return False

def check_autogpt_log():
    """检查AutoGPT日志文件"""
    import os
    log_file = "E:\\TradingSystem\\autogpt.log"
    if os.path.exists(log_file):
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            last_lines = lines[-5:] if len(lines) >= 5 else lines
            print(f"\nAutoGPT日志文件最后{len(last_lines)}行:")
            for line in last_lines:
                print(f"  {line.strip()}")
        return True
    else:
        print(f"\nAutoGPT日志文件不存在: {log_file}")
        return False

if __name__ == '__main__':
    print("=" * 60)
    print("AutoGPT-Web界面日志集成测试")
    print("=" * 60)
    
    success = test_log_sending()
    
    print("\n" + "=" * 60)
    print("检查本地日志文件...")
    check_autogpt_log()
    
    print("\n" + "=" * 60)
    if success:
        print("[PASS] 测试通过: 日志系统正常工作")
    else:
        print("[FAIL] 测试失败: 日志系统存在问题")
    print("=" * 60)