#!/bin/bash
# run_gaussiantalker.sh - GaussianTalker Docker 包装脚本

set -e  # 遇到错误立即退出

# 基础变量
IMAGE_NAME="gaussiantalker:latest"
WORKSPACE="/GaussianTalker"
GT_DIR="./GaussianTalker"  # 宿主机GaussianTalker目录

# 测试模式开关
TEST_MODE=${TEST_MODE:-0}

# 模拟Docker命令的函数
mock_docker() {
    if [ "$TEST_MODE" -eq 1 ]; then
        echo "[MOCK DOCKER] 模拟执行: $*"
        echo "  工作目录: $(pwd)"
        echo "  挂载点: $WORKSPACE"
        return 0
    else
        # 真实执行Docker命令
        docker "$@"
    fi
}

# 获取文件名（无扩展名）
get_basename() {
    local file_path="$1"
    local basename=$(basename "$file_path")
    echo "${basename%.*}"
}

# 智能解析GPU参数
parse_gpu_arg() {
    local gpu_arg="$1"
    
    # 转换为大写方便处理
    local upper_arg=$(echo "$gpu_arg" | tr '[:lower:]' '[:upper:]')
    
    # 处理CPU情况
    if [[ "$upper_arg" == "CPU" ]]; then
        echo ""
        return 0
    fi
    
    # 处理GPU情况（格式：GPU0, GPU1, GPU2...）
    if [[ "$upper_arg" =~ ^GPU[0-9]+$ ]]; then
        local gpu_num=$(echo "$upper_arg" | sed 's/GPU//')
        echo "--gpus device=$gpu_num"
    else
        # 默认使用GPU0
        echo "--gpus device=0"
    fi
}

# 确保GaussianTalker目录结构存在
ensure_gt_dirs() {
    mkdir -p "$GT_DIR/data"
    mkdir -p "$GT_DIR/output"
    echo "GaussianTalker目录结构已创建: $GT_DIR"
}

# 完整训练流程
train() {
    local video_path=""
    local gpu_arg="GPU0"
    local iterations="10000"
    local config="arguments/64_dim_1_transformer.py"
    local au_csv=""  # 用户手动提供的AU文件
    
    # 解析参数
    while [[ $# -gt 0 ]]; do
        case $1 in
            --video_path)
                video_path="$2"
                shift 2
                ;;
            --gpu)
                gpu_arg="$2"
                shift 2
                ;;
            --iterations)
                iterations="$2"
                shift 2
                ;;
            --config)
                config="$2"
                shift 2
                ;;
            --au_csv)
                au_csv="$2"
                shift 2
                ;;
            *)
                echo "未知参数: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    if [ -z "$video_path" ]; then
        echo "错误: 必须指定视频路径(--video_path)"
        usage
        exit 1
    fi
    
    if [ ! -f "$video_path" ]; then
        echo "错误: 视频文件不存在: $video_path"
        exit 1
    fi
    
    # 确保目录结构
    ensure_gt_dirs
    
    # 获取视频名称
    local video_name=$(get_basename "$video_path")
    local data_dir="$GT_DIR/data/${video_name}"
    local output_dir="$GT_DIR/output/${video_name}"
    
    # 解析GPU参数
    local gpu_param=$(parse_gpu_arg "$gpu_arg")
    
    echo "GaussianTalker开始训练..."
    echo "  - 输入视频: $video_path"
    echo "  - 视频名称: $video_name"
    echo "  - 数据目录: $data_dir"
    echo "  - 输出目录: $output_dir"
    echo "  - GPU设置: $gpu_arg -> $gpu_param"
    echo "  - 迭代次数: $iterations"
    echo "  - 配置文件: $config"
    
    # 创建数据目录
    mkdir -p "$data_dir"
    mkdir -p "$output_dir"
    
    # 复制视频到数据目录
    echo "复制视频文件..."
    cp "$video_path" "$data_dir/"
    
    # 如果用户提供了au.csv，复制到数据目录
    if [ -n "$au_csv" ] && [ -f "$au_csv" ]; then
        echo "使用用户提供的AU文件: $au_csv"
        cp "$au_csv" "$data_dir/au.csv"
        local skip_au="--skip_openface"
    else
        echo "将自动使用OpenFace提取AU特征"
        local skip_au=""
    fi
    
    # 获取GaussianTalker目录的绝对路径
    local gt_abs=$(realpath "$GT_DIR")
    
    # Step 1: 视频预处理（提取帧、音频、3DMM、DeepSpeech等）
    echo ""
    echo "===== 步骤1: 数据预处理 (process.py) ====="
    mock_docker run --rm $gpu_param \
        -v "$gt_abs/data:$WORKSPACE/data" \
        $IMAGE_NAME \
        python data_utils/process.py \
        "$WORKSPACE/data/${video_name}/$(basename "$video_path")"
    
    # Step 1.5: 提取AU特征（如果未提供au.csv）
    if [ -z "$skip_au" ]; then
        echo ""
        echo "===== 步骤1.5: 提取AU特征 (OpenFace) ====="
        echo "注意：这一步调用OpenFace，如果失败请手动提供au.csv"
        # OpenFace FeatureExtraction命令
        mock_docker run --rm $gpu_param \
            -v "$gt_abs/data:$WORKSPACE/data" \
            $IMAGE_NAME \
            bash -c "cd $WORKSPACE/data/${video_name} && FeatureExtraction -f $(basename "$video_path") -out_dir . && mv $(basename "$video_path" .mp4).csv au.csv"
        
        # 检查au.csv是否生成成功
        if [ ! -f "$data_dir/au.csv" ]; then
            echo "警告: OpenFace未能生成au.csv，训练可能受影响"
            echo "建议手动运行OpenFace或在前端上传预先提取的au.csv"
        fi
    fi
    
    # Step 2: 模型训练
    echo ""
    echo "===== 步骤2: 模型训练 (train.py) ====="
    mock_docker run --rm $gpu_param \
        -v "$gt_abs/data:$WORKSPACE/data" \
        -v "$gt_abs/output:$WORKSPACE/output" \
        $IMAGE_NAME \
        python train.py \
        -s "$WORKSPACE/data/${video_name}" \
        --model_path "$WORKSPACE/output/${video_name}" \
        --configs "$config" \
        --iterations $iterations
    
    echo ""
    echo "GaussianTalker训练完成!"
    echo "数据目录: $data_dir"
    echo "模型目录: $output_dir"
}

# 推理函数
infer() {
    local model_dir=""
    local audio_path=""
    local gpu_arg="GPU0"
    local batch_size="128"
    local iteration="10000"  # 用于指定加载哪个检查点
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --model_dir)
                model_dir="$2"
                shift 2
                ;;
            --audio_path)
                audio_path="$2"
                shift 2
                ;;
            --gpu)
                gpu_arg="$2"
                shift 2
                ;;
            --batch_size)
                batch_size="$2"
                shift 2
                ;;
            --iteration)
                iteration="$2"
                shift 2
                ;;
            *)
                echo "未知参数: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    if [ -z "$model_dir" ]; then
        echo "错误: 必须指定模型目录(--model_dir)"
        usage
        exit 1
    fi
    
    if [ -z "$audio_path" ]; then
        echo "错误: 必须指定音频路径(--audio_path)"
        usage
        exit 1
    fi
    
    if [ ! -f "$audio_path" ]; then
        echo "错误: 音频文件不存在: $audio_path"
        exit 1
    fi
    
    # 确保目录结构
    ensure_gt_dirs
    
    # 解析GPU参数
    local gpu_param=$(parse_gpu_arg "$gpu_arg")
    
    # 获取模型目录名称
    local model_name=$(basename "$model_dir")
    local data_dir="$GT_DIR/data/${model_name}"
    local output_dir="$GT_DIR/output/${model_name}"
    
    # 获取音频文件名称
    local audio_name=$(get_basename "$audio_path")
    
    if [ ! -d "$data_dir" ]; then
        echo "错误: 数据目录不存在: $data_dir"
        echo "请确保对应的训练数据存在"
        exit 1
    fi
    
    if [ ! -d "$output_dir" ]; then
        echo "错误: 模型目录不存在: $output_dir"
        echo "请确保模型已训练完成"
        exit 1
    fi
    
    echo "GaussianTalker开始推理..."
    echo "  - GPU设置: $gpu_arg -> $gpu_param"
    echo "  - 模型目录: $output_dir"
    echo "  - 数据目录: $data_dir"
    echo "  - 音频文件: $(basename "$audio_path")"
    echo "  - Batch Size: $batch_size"
    echo "  - Iteration: $iteration"
    
    # 复制音频到数据目录
    echo "复制音频文件到数据目录..."
    cp "$audio_path" "$data_dir/"
    
    # Step 1: 提取DeepSpeech特征
    echo ""
    echo "===== 步骤1: 提取音频DeepSpeech特征 ====="
    local gt_abs=$(realpath "$GT_DIR")
    
    mock_docker run --rm $gpu_param \
        -v "$gt_abs/data:$WORKSPACE/data" \
        $IMAGE_NAME \
        python data_utils/deepspeech_features/extract_ds_features.py \
        "$WORKSPACE/data/${model_name}/$(basename "$audio_path")" \
        "$WORKSPACE/data/${model_name}/${audio_name}.npy"
    
    # Step 2: 推理生成视频（使用render.py）
    echo ""
    echo "===== 步骤2: 推理生成数字人视频 (render.py) ====="
    mock_docker run --rm $gpu_param \
        -v "$gt_abs/data:$WORKSPACE/data" \
        -v "$gt_abs/output:$WORKSPACE/output" \
        $IMAGE_NAME \
        python render.py \
        -s "$WORKSPACE/data/${model_name}" \
        --model_path "$WORKSPACE/output/${model_name}" \
        --configs arguments/64_dim_1_transformer.py \
        --iteration $iteration \
        --batch $batch_size \
        --custom_aud "${audio_name}.npy" \
        --custom_wav "$(basename "$audio_path")" \
        --skip_train \
        --skip_test
    
    # 查找生成的视频
    local output_video=""
    if [ -f "$output_dir/output.mp4" ]; then
        output_video="$output_dir/output.mp4"
    elif [ -f "$output_dir/renders/output.mp4" ]; then
        output_video="$output_dir/renders/output.mp4"
    else
        # 查找任何mp4文件
        output_video=$(find "$output_dir" -name "*.mp4" -type f | head -1)
    fi
    
    if [ -n "$output_video" ] && [ -f "$output_video" ]; then
        echo ""
        echo "GaussianTalker推理完成!"
        echo "输出视频: $output_video"
    else
        echo ""
        echo "错误: 推理完成但未找到输出视频文件"
        echo "请检查模型目录: $output_dir"
        exit 1
    fi
}

# 评估函数
evaluate() {
    local generated_video=""
    local data_dir=""
    local output_json=""
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --generated_video)
                generated_video="$2"
                shift 2
                ;;
            --data_dir)
                data_dir="$2"
                shift 2
                ;;
            --output_json)
                output_json="$2"
                shift 2
                ;;
            *)
                echo "未知参数: $1"
                usage
                exit 1
                ;;
        esac
    done
    
    if [ -z "$generated_video" ]; then
        echo "错误: 必须指定生成视频路径(--generated_video)"
        usage
        exit 1
    fi
    
    if [ -z "$data_dir" ]; then
        echo "错误: 必须指定数据目录(--data_dir)"
        usage
        exit 1
    fi
    
    # 确保目录结构
    ensure_gt_dirs
    
    echo "GaussianTalker开始评估..."
    echo "  - 生成视频: $generated_video"
    echo "  - 数据目录: $data_dir"
    
    # 获取GaussianTalker目录的绝对路径
    local gt_abs=$(realpath "$GT_DIR")
    
    # 构建评估命令
    local eval_cmd="python evaluate.py --generated_video \"$generated_video\" --data_dir \"$data_dir\""
    
    if [ -n "$output_json" ]; then
        eval_cmd="$eval_cmd --output_json \"$output_json\""
    fi
    
    # 执行评估
    mock_docker run --rm \
        -v "$gt_abs:$WORKSPACE" \
        $IMAGE_NAME \
        bash -c "$eval_cmd"
    
    echo ""
    echo "评估完成!"
}

usage() {
    echo "用法: $0 <任务类型> [参数]"
    echo "可用任务:"
    echo "  train        - 完整训练流程（预处理+训练）"
    echo "  infer        - 推理生成视频"
    echo "  evaluate     - 评估生成视频质量（PSNR/SSIM）"
    echo ""
    echo "训练示例:"
    echo "  $0 train --video_path ./video.mp4 --gpu GPU0 --iterations 10000"
    echo "  $0 train --video_path ./video.mp4 --gpu GPU0 --iterations 15000 --config arguments/64_dim_1_transformer.py"
    echo "  $0 train --video_path ./video.mp4 --gpu GPU0 --au_csv ./au.csv  # 手动提供AU文件"
    echo ""
    echo "推理示例:"
    echo "  $0 infer --model_dir obama --audio_path speech.wav --gpu GPU0"
    echo "  $0 infer --model_dir obama --audio_path speech.wav --gpu GPU0 --batch_size 256 --iteration 15000"
    echo ""
    echo "评估示例:"
    echo "  $0 evaluate --generated_video ./GaussianTalker/output/obama/renders/output.mp4 --data_dir ./GaussianTalker/data/obama"
    echo "  $0 evaluate --generated_video ./output.mp4 --data_dir ./data/obama --output_json results.json"
}

# 主函数
main() {
    if [ $# -eq 0 ]; then
        usage
        exit 1
    fi
    
    case $1 in
        "train")
            shift
            train "$@"
            ;;
        "infer")
            shift
            infer "$@"
            ;;
        "evaluate")
            shift
            evaluate "$@"
            ;;
        "-h"|"--help")
            usage
            ;;
        *)
            echo "错误: 未知任务 '$1'"
            usage
            exit 1
            ;;
    esac
}

main "$@"
