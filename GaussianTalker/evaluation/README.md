# GaussianTalker 评估指标系统

这是GaussianTalker的独立评估系统，支持6个核心评估指标的Docker封装输出。

## 📋 支持的评估指标

| 指标 | 说明 | 方向 | 良好值 |
|------|------|------|--------|
| **NIQE** | 自然图像质量评估 | ↓ 越低越好 | < 5.0 |
| **PSNR** | 峰值信噪比 | ↑ 越高越好 | > 27 dB |
| **FID** | 图像真实感距离 | ↓ 越低越好 | < 100 |
| **SSIM** | 结构相似性 | ↑ 越高越好 | > 0.80 |
| **LSE-C** | 音频同步置信度 | ↑ 越高越好 | > 0.7 |
| **LSE-D** | 音频同步距离 | ↓ 越低越好 | < 0.3 |

## 🚀 快速开始

### 方式一：Docker（推荐）

```bash
# 1. 构建Docker镜像
cd evaluation
docker build -t gaussiantalker-eval:latest .

# 2. 准备视频文件
# your_data/
# ├── original/
# │   └── video.mp4
# └── generated/
#     └── video.mp4

# 3. 运行评估
docker run --rm ^
  -v D:\path\to\your_data:/app/input ^
  -v D:\path\to\output:/app/output ^
  gaussiantalker-eval:latest
```

### 方式二：直接使用Python

```bash
# 1. 安装依赖
pip install -r requirements.txt

# 2. 运行评估
python evaluate_metrics.py ^
  --original_video original.mp4 ^
  --generated_video generated.mp4 ^
  --output_dir ./results
```

## 📊 输出格式

评估结果保存为JSON格式：

```json
{
  "psnr": {
    "mean": 28.45,
    "std": 2.31,
    "min": 24.12,
    "max": 32.67
  },
  "ssim": {
    "mean": 0.8523,
    "std": 0.0421
  },
  "fid": 45.23,
  "niqe": {
    "mean": 4.12,
    "std": 0.87
  },
  "lse_c": {
    "mean": 0.7834,
    "std": 0.1023
  },
  "lse_d": {
    "mean": 0.2166,
    "std": 0.1023
  }
}
```

## 📁 项目结构

```
evaluation/
├── Dockerfile              # Docker镜像定义
├── requirements.txt        # Python依赖
├── evaluate_metrics.py     # 核心评估脚本
├── README.md              # 本文档
├── build.bat              # Windows构建脚本
├── build.sh               # Linux构建脚本
└── run_example.bat        # Windows运行示例
```

## 🔧 技术细节

- **基础镜像**: pytorch/pytorch:2.0.1-cuda11.7-cudnn8-devel
- **Python版本**: 3.8
- **PyTorch版本**: 2.0.1
- **CUDA版本**: 11.7

### 核心依赖

- torch, torchvision - 深度学习框架
- pyiqa - NIQE指标
- librosa - 音频处理（LSE-C/LSE-D）
- scikit-image - PSNR/SSIM
- scipy - FID计算

## 📖 详细文档

更多详细信息请参考项目文档。

## 📝 许可证

本评估系统基于GaussianTalker项目，遵循相同的许可证。

