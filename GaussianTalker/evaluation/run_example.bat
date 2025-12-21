@echo off
REM GaussianTalker 评估系统运行示例 (Windows)

echo ==========================================
echo GaussianTalker 评估系统 - 运行示例
echo ==========================================
echo.

REM 设置路径（请根据实际情况修改）
set INPUT_DIR=D:\TFG\TFG_ui_GaussianTalker\testtt
set OUTPUT_DIR=D:\TFG\TFG_ui_GaussianTalker\evaluation_results

echo 输入目录: %INPUT_DIR%
echo 输出目录: %OUTPUT_DIR%
echo.

REM 创建输出目录
if not exist "%OUTPUT_DIR%" mkdir "%OUTPUT_DIR%"

REM 检查Docker镜像是否存在
docker image inspect gaussiantalker-eval:latest >nul 2>&1
if %errorlevel% neq 0 (
    echo 错误: Docker镜像不存在
    echo 请先运行 build.bat 构建镜像
    pause
    exit /b 1
)

echo 开始运行评估...
echo.

REM 运行评估（CPU版本）
docker run --rm ^
  -v "%INPUT_DIR%":/app/input ^
  -v "%OUTPUT_DIR%":/app/output ^
  gaussiantalker-eval:latest ^
  python evaluate_metrics.py ^
    --original_video /app/input/original.mp4 ^
    --generated_video /app/input/output.mp4 ^
    --output_dir /app/output

if %errorlevel% equ 0 (
    echo.
    echo ==========================================
    echo 评估完成！
    echo ==========================================
    echo.
    echo 结果保存在: %OUTPUT_DIR%\evaluation_results.json
    echo.
) else (
    echo.
    echo ==========================================
    echo 评估失败！
    echo ==========================================
    echo.
)

pause

