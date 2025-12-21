#!/bin/bash
# GaussianTalker 评估系统构建脚本

echo "=========================================="
echo "GaussianTalker 评估系统 - Docker构建"
echo "=========================================="

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "错误: Docker未安装"
    echo "请先安装Docker: https://docs.docker.com/get-docker/"
    exit 1
fi

# 构建镜像
echo ""
echo "开始构建Docker镜像..."
echo ""

docker build -f Dockerfile.evaluation -t gaussiantalker-evaluation:latest .

if [ $? -eq 0 ]; then
    echo ""
    echo "=========================================="
    echo "构建成功！"
    echo "=========================================="
    echo ""
    echo "使用方法："
    echo ""
    echo "1. 准备视频文件："
    echo "   your_data/"
    echo "   ├── original/"
    echo "   │   └── video.mp4"
    echo "   └── generated/"
    echo "       └── video.mp4"
    echo ""
    echo "2. 运行评估："
    echo "   docker run --rm \\"
    echo "     -v /path/to/your_data:/app/input \\"
    echo "     -v /path/to/output:/app/output \\"
    echo "     gaussiantalker-evaluation:latest"
    echo ""
    echo "3. GPU加速（如果有NVIDIA GPU）："
    echo "   docker run --rm --gpus all \\"
    echo "     -v /path/to/your_data:/app/input \\"
    echo "     -v /path/to/output:/app/output \\"
    echo "     gaussiantalker-evaluation:latest"
    echo ""
    echo "=========================================="
else
    echo ""
    echo "=========================================="
    echo "构建失败！"
    echo "=========================================="
    echo ""
    echo "请检查错误信息并重试"
    exit 1
fi

