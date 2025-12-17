# GaussianTalker Docker 调用说明

## 构建Docker镜像

```bash
cd GaussianTalker
# 将Dockerfile.final重命名为Dockerfile
cp Dockerfile.final Dockerfile

# 将5个预训练模型文件放置到GaussianTalker/目录下：
# - 01_MorphableModel.mat
# - epoch_20.pth
# - resnet50-19c8e357.pth
# - shape_predictor_68_face_landmarks.dat
# - s3fd-619a316812.pth

# 构建Docker镜像（需要较长时间，约30-60分钟）
docker build -t gaussiantalker:latest .
```

## 打包Docker镜像

```bash
docker save -o gaussiantalker.tar gaussiantalker:latest
```

## 从tar导入Docker镜像

```bash
docker load -i gaussiantalker.tar
```

## 脚本文件

`run_gaussiantalker.sh`

## 目录结构

```
当前工作目录/
└── GaussianTalker/              # 自动创建的工作目录
    ├── data/                    # 数据目录
    │   └── {视频名称}/          # 预处理数据文件夹
    │       ├── {视频名称}.mp4   # 原始视频
    │       ├── ori_imgs/        # 视频帧
    │       ├── gt_imgs/         # 裁剪后的人脸图像
    │       ├── parsing/         # 人脸分割
    │       ├── aud.wav          # 提取的音频
    │       ├── aud.npy          # DeepSpeech音频特征
    │       ├── au.csv           # Action Unit特征
    │       └── transforms_*.json # 3DMM参数
    └── output/                  # 输出目录
        └── {视频名称}/          # 训练好的模型
            ├── point_cloud/     # 3D高斯点云
            ├── checkpoints/     # 模型检查点
            └── renders/         # 推理结果
                └── output.mp4   # 生成的视频
```

## 脚本调用命令

### train - 完整训练流程

```bash
./run_gaussiantalker.sh train \
    --video_path <视频文件路径> \
    --gpu <GPU设备> \
    --iterations <迭代次数> \
    [--config <配置文件>] \
    [--au_csv <AU文件>]
```

**参数说明：**
- `--video_path`: 输入视频文件路径（必需）
- `--gpu`: GPU设备（默认: GPU0）
  - `GPU0`, `GPU1`, `GPU2`, ... - 指定GPU
  - `CPU` - 使用CPU
- `--iterations`: 训练迭代次数（默认: 10000）
- `--config`: 配置文件路径（可选，默认: arguments/64_dim_1_transformer.py）
- `--au_csv`: 手动提供的AU文件（可选，如果OpenFace封装失败）

**示例：**
```bash
# 基础训练
./run_gaussiantalker.sh train --video_path ./obama.mp4 --gpu GPU0 --iterations 10000

# 使用自定义配置
./run_gaussiantalker.sh train --video_path ./obama.mp4 --gpu GPU0 --iterations 15000 --config arguments/64_dim_1_transformer.py

# 手动提供AU文件（如果OpenFace失败）
./run_gaussiantalker.sh train --video_path ./obama.mp4 --gpu GPU0 --au_csv ./au.csv
```

### infer - 视频推理

```bash
./run_gaussiantalker.sh infer \
    --model_dir <模型目录名称> \
    --audio_path <音频文件路径> \
    --gpu <GPU设备> \
    [--batch_size <批大小>] \
    [--iteration <检查点迭代次数>]
```

**参数说明：**
- `--model_dir`: 模型目录名称（如：obama）
- `--audio_path`: 驱动音频文件路径
- `--gpu`: GPU设备
- `--batch_size`: 批处理大小（可选，默认: 128）
- `--iteration`: 使用的检查点迭代次数（可选，默认: 10000）

**示例：**
```bash
# 基础推理
./run_gaussiantalker.sh infer \
    --model_dir obama \
    --audio_path speech.wav \
    --gpu GPU0

# 指定batch_size和iteration
./run_gaussiantalker.sh infer \
    --model_dir obama \
    --audio_path speech.wav \
    --gpu GPU0 \
    --batch_size 256 \
    --iteration 15000
```

## 输出文件说明

### 训练完成后
- **数据目录**: `GaussianTalker/data/{视频名称}/`
- **模型目录**: `GaussianTalker/output/{视频名称}/`

### 推理完成后
- **输出视频**: `GaussianTalker/output/{视频名称}/renders/output.mp4`
  - 或: `GaussianTalker/output/{视频名称}/custom/ours_{iteration}/renders/output.mp4`

## 测试模式

在不构建 Docker 镜像的情况下测试脚本逻辑：

```bash
# 启用测试模式
TEST_MODE=1 ./run_gaussiantalker.sh train --video_path ./test.mp4 --gpu GPU0 --iterations 10000
TEST_MODE=1 ./run_gaussiantalker.sh infer --model_dir test --audio_path ./test.wav
```

**示例：**
```
GaussianTalker/data/obama/
GaussianTalker/output/obama/
GaussianTalker/output/obama/renders/output.mp4
```

## 前后端集成说明

### 前端界面

1. **模型训练页面** (`model_training.html`):
   - 选择模型: `GaussianTalker`
   - 输入参数: 视频路径、GPU、迭代次数、配置文件
   - 可选: 手动上传AU文件

2. **视频生成页面** (`video_generation.html`):
   - 选择模型: `GaussianTalker`
   - 输入参数: 模型目录、音频路径、GPU、Batch Size、Iteration

3. **实时对话页面** (`chat_system.html`):
   - 选择模型: `GaussianTalker`
   - 自动调用: ASR -> LLM -> TTS -> GaussianTalker视频生成

### 后端逻辑

- **`app.py`**: 处理HTTP请求和文件上传
- **`backend/model_trainer.py`**: 调用 `run_gaussiantalker.sh train`
- **`backend/video_generator.py`**: 调用 `run_gaussiantalker.sh infer`
- **`backend/chat_engine.py`**: 整合ASR、LLM、TTS、GaussianTalker完整流程

### 工作流程

**训练:**
1. 用户在前端选择GaussianTalker并上传视频
2. 后端接收请求 -> `model_trainer.py`
3. 调用 `run_gaussiantalker.sh train`
4. Docker容器内执行预处理和训练
5. 训练完成，模型保存到 `GaussianTalker/output/`

**推理:**
1. 用户在前端选择模型和上传音频
2. 后端接收请求 -> `video_generator.py`
3. 调用 `run_gaussiantalker.sh infer`
4. Docker容器内提取DeepSpeech特征并推理
5. 生成视频复制到 `static/videos/` 供前端显示

**实时对话:**
1. 用户录音 -> ASR识别文本
2. LLM生成回复文本
3. TTS合成语音（支持语音克隆）
4. GaussianTalker生成数字人视频
5. 前端同时播放音频和视频

## 注意事项

1. **首次使用**需要先构建 Docker 镜像（时间较长）
2. **预训练模型**必须放置在正确位置（详见构建说明）
3. **OpenFace集成**: 如果封装失败，用户可手动上传AU文件绕过
4. **视频格式**: 建议使用常见格式（mp4, avi）
5. **音频格式**: 支持 wav, mp3 等常见格式
6. **GPU要求**: 推荐使用NVIDIA GPU with CUDA 11.7+

## 性能参考

- **训练时间**: 10K iterations约需30-60分钟（取决于视频长度和GPU性能）
- **推理时间**: 约10-30秒/10秒音频（batch_size=128）
- **显存需求**: 至少8GB（推荐12GB+）
- **评估指标**: PSNR 30+, SSIM 0.90+（良好训练）

## 故障排除

### 问题1: OpenFace提取AU失败
**解决方案**: 在前端勾选"手动上传AU文件"，提供预先提取的au.csv

### 问题2: 推理时找不到输出视频
**检查**:
- 模型是否训练完成
- 检查点文件是否存在（`output/{model_name}/checkpoints/`）
- 检查日志输出中的错误信息

### 问题3: 训练过程中断
**解决方案**: GaussianTalker支持从检查点恢复，重新运行train命令即可

### 问题4: Docker镜像构建失败
**检查**:
- 预训练模型是否都已放置
- 网络连接是否正常（需下载依赖包）
- 磁盘空间是否充足（至少20GB+）
