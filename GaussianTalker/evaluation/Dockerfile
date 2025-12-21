# =================================================================
# GaussianTalker 评估指标 Dockerfile
# 支持指标: NIQE, PSNR, FID, SSIM, LSE-C, LSE-D
# 环境: Python 3.8 | PyTorch 2.0.1 | CUDA 11.7
# =================================================================

FROM pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel

# 环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    TZ=Asia/Shanghai \
    PYTHONPATH=/app \
    PYTHONUNBUFFERED=1

WORKDIR /app

# 安装系统依赖
RUN apt-get update
RUN apt-get install -y \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    wget \
    git
RUN apt-get clean
RUN rm -rf /var/lib/apt/lists/*

# 升级pip
RUN pip install --upgrade pip setuptools wheel

# 复制依赖文件
COPY requirements.txt /app/

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制评估脚本
COPY evaluate_metrics.py /app/
COPY ../utils/image_utils.py /app/utils/

# 创建输入输出目录
RUN mkdir -p /app/input/original
RUN mkdir -p /app/input/generated
RUN mkdir -p /app/output

# 设置工作目录权限
RUN chmod -R 777 /app

# 默认命令：运行评估
CMD ["python", "evaluate_metrics.py", \
     "--original_video", "/app/input/original/video.mp4", \
     "--generated_video", "/app/input/generated/video.mp4", \
     "--output_dir", "/app/output"]

