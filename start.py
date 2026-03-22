#!/usr/bin/env python3
"""
视频下载器 - 一键启动脚本
支持 macOS、Windows、Linux
"""

import os
import sys
import subprocess
import platform

def get_script_dir():
    """获取脚本所在目录"""
    return os.path.dirname(os.path.abspath(__file__))

def check_python_version():
    """检查 Python 版本"""
    if sys.version_info < (3, 10):
        print("错误: 需要 Python 3.10 或更高版本")
        print(f"当前版本: {sys.version_info.major}.{sys.version_info.minor}")
        return False
    return True

def install_dependencies(venv_path):
    """安装依赖"""
    print("正在安装依赖...")

    # 检查 pip 命令
    pip_cmd = [sys.executable, "-m", "pip"]

    try:
        subprocess.run(
            pip_cmd + ["install", "-r", "requirements.txt"],
            cwd=os.path.join(get_script_dir(), "backend"),
            check=True,
            capture_output=True
        )
        print("依赖安装完成!")
        return True
    except subprocess.CalledProcessError as e:
        print(f"安装依赖时出错: {e}")
        print("请尝试手动运行:")
        print(f"  cd {os.path.join(get_script_dir(), 'backend')}")
        print("  source venv/bin/activate  # 或 venv\\Scripts\\activate")
        print("  pip install -r requirements.txt")
        return False

def create_venv(venv_path):
    """创建虚拟环境"""
    print("正在创建虚拟环境...")
    try:
        subprocess.run(
            [sys.executable, "-m", "venv", venv_path],
            cwd=os.path.join(get_script_dir(), "backend"),
            check=True,
            capture_output=True
        )
        return True
    except subprocess.CalledProcessError:
        print("创建虚拟环境失败，请检查 Python 安装")
        return False

def get_activate_cmd():
    """获取虚拟环境激活命令"""
    system = platform.system()
    venv_path = os.path.join(get_script_dir(), "backend", "venv")

    if system == "Windows":
        return os.path.join(venv_path, "Scripts", "python.exe")
    else:
        return os.path.join(venv_path, "bin", "python")

def kill_port_8000():
    """关闭占用 8000 端口的进程"""
    system = platform.system()
    try:
        if system == "Darwin" or system == "Linux":
            # macOS/Linux
            result = subprocess.run(
                ["lsof", "-ti:8000"],
                capture_output=True,
                text=True
            )
            if result.stdout.strip():
                pids = result.stdout.strip().split("\n")
                for pid in pids:
                    try:
                        subprocess.run(["kill", "-9", pid], check=False)
                    except:
                        pass
                print("已关闭占用 8000 端口的进程")
        elif system == "Windows":
            result = subprocess.run(
                ["netstat", "-ano"],
                capture_output=True,
                text=True
            )
            for line in result.stdout.split("\n"):
                if ":8000" in line:
                    parts = line.split()
                    if len(parts) > 4:
                        try:
                            pid = parts[-1]
                            subprocess.run(["taskkill", "/F", "/PID", pid], check=False)
                        except:
                            pass
            print("已关闭占用 8000 端口的进程")
    except:
        pass  # 忽略错误，继续启动

def main():
    if not check_python_version():
        input("\n按回车键退出...")
        sys.exit(1)

    script_dir = get_script_dir()
    venv_path = os.path.join(script_dir, "backend", "venv")
    python_path = get_activate_cmd() if os.path.exists(venv_path) else sys.executable

    # 检查虚拟环境是否存在
    if not os.path.exists(venv_path):
        print("首次启动，正在配置环境...")
        if not create_venv(venv_path):
            input("\n按回车键退出...")
            sys.exit(1)
        if not install_dependencies(venv_path):
            input("\n按回车键退出...")
            sys.exit(1)

    # 关闭占用端口的进程
    kill_port_8000()

    # 启动服务
    print("\n" + "="*50)
    print("正在启动视频下载器...")
    print("="*50)

    backend_dir = os.path.join(script_dir, "backend")

    try:
        subprocess.run(
            [python_path, "main.py"],
            cwd=backend_dir
        )
    except KeyboardInterrupt:
        print("\n\n服务已停止")
    except Exception as e:
        print(f"启动失败: {e}")
        input("\n按回车键退出...")
        sys.exit(1)

if __name__ == "__main__":
    main()
