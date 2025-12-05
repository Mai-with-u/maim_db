@echo off
REM MaiMBot数据库启动脚本
REM Windows可执行启动脚本

setlocal enabledelayedexpansion

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
cd /d "%SCRIPT_DIR%"

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python未安装或不在PATH中
    pause
    exit /b 1
)

REM 检查是否在正确的目录
if not exist "db_manager.py" (
    echo ❌ 请在maim_db目录下运行此脚本
    pause
    exit /b 1
)

if not exist "start_db.py" (
    echo ❌ 请在maim_db目录下运行此脚本
    pause
    exit /b 1
)

echo 🚀 MaiMBot数据库启动器
echo ==================================

REM 执行Python启动脚本
python start_db.py %*

pause