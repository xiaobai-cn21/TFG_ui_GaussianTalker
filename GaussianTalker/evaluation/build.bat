@echo off
REM GaussianTalker 评估系统构建脚本 (Windows)

echo ==========================================
echo GaussianTalker 评估系统 - Docker构建
echo ==========================================

REM 检查Docker是否安装
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker未安装
    echo 请先安装Docker Desktop: https://docs.docker.com/desktop/install/windows-install/
    pause
    exit /b 1
)

REM 构建镜像
echo.
echo 开始构建Docker镜像...
echo.

docker build -t gaussiantalker-eval:latest .

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo 构建成功！
    echo ==========================================
    echo.
    echo 使用方法：
    echo.
    echo 1. 准备视频文件：
    echo    your_data\
    echo    ├── original\
    echo    │   └── video.mp4
    echo    └── generated\
    echo        └── video.mp4
    echo.
    echo 2. 运行评估：
    echo    docker run --rm ^
    echo      -v D:\path\to\your_data:/app/input ^
    echo      -v D:\path\to\output:/app/output ^
    echo      gaussiantalker-eval:latest
    echo.
    echo 3. GPU加速（如果有NVIDIA GPU）：
    echo    docker run --rm --gpus all ^
    echo      -v D:\path\to\your_data:/app/input ^
    echo      -v D:\path\to\output:/app/output ^
    echo      gaussiantalker-eval:latest
    echo.
    echo ==========================================
) else (
    echo.
    echo ==========================================
    echo 构建失败！
    echo ==========================================
    echo.
    echo 请检查错误信息并重试
    pause
    exit /b 1
)

pause

