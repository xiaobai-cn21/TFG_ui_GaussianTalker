#!/usr/bin/env python3
"""
GaussianTalker 评估脚本
评估生成视频的PSNR和SSIM指标
"""

import os
import cv2
import json
import argparse
import numpy as np
from skimage.metrics import structural_similarity as ssim
from skimage.metrics import peak_signal_noise_ratio as psnr


def load_transforms_val(transforms_val_path):
    """加载transforms_val.json获取验证集帧索引"""
    with open(transforms_val_path, 'r') as f:
        data = json.load(f)
    
    val_frames = []
    for frame in data['frames']:
        # 提取帧编号
        frame_path = frame['file_path']
        # 格式: './gt_imgs/0000' -> 0
        frame_idx = int(os.path.basename(frame_path))
        val_frames.append(frame_idx)
    
    return sorted(val_frames)


def load_video_frames(video_path, max_frames=None):
    """加载视频的所有帧"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frames.append(frame)
        
        if max_frames and len(frames) >= max_frames:
            break
    
    cap.release()
    return frames


def calculate_metrics(generated_video_path, gt_dir, transforms_val_path):
    """
    计算生成视频的PSNR和SSIM
    
    Args:
        generated_video_path: 生成的视频路径
        gt_dir: ground truth图像目录 (gt_imgs/)
        transforms_val_path: transforms_val.json路径
    """
    # 1. 加载验证集帧索引
    val_frame_indices = load_transforms_val(transforms_val_path)
    print(f"验证集包含 {len(val_frame_indices)} 帧")
    
    # 2. 加载生成的视频帧
    generated_frames = load_video_frames(generated_video_path)
    print(f"生成视频包含 {len(generated_frames)} 帧")
    
    # 3. 确保生成视频长度足够
    if len(generated_frames) < len(val_frame_indices):
        print(f"警告: 生成视频帧数 ({len(generated_frames)}) 少于验证集帧数 ({len(val_frame_indices)})")
        val_frame_indices = val_frame_indices[:len(generated_frames)]
    
    # 4. 逐帧计算PSNR和SSIM
    psnr_values = []
    ssim_values = []
    
    for i, gt_idx in enumerate(val_frame_indices):
        # 加载ground truth图像
        gt_path = os.path.join(gt_dir, f"{gt_idx}.jpg")
        if not os.path.exists(gt_path):
            # 尝试其他格式
            gt_path = os.path.join(gt_dir, f"{gt_idx:04d}.jpg")
            if not os.path.exists(gt_path):
                print(f"警告: 找不到GT图像 {gt_path}")
                continue
        
        gt_img = cv2.imread(gt_path)
        gen_img = generated_frames[i]
        
        # 确保尺寸一致
        if gt_img.shape != gen_img.shape:
            gen_img = cv2.resize(gen_img, (gt_img.shape[1], gt_img.shape[0]))
        
        # 计算PSNR
        psnr_val = psnr(gt_img, gen_img, data_range=255)
        psnr_values.append(psnr_val)
        
        # 计算SSIM (转为灰度)
        gt_gray = cv2.cvtColor(gt_img, cv2.COLOR_BGR2GRAY)
        gen_gray = cv2.cvtColor(gen_img, cv2.COLOR_BGR2GRAY)
        ssim_val = ssim(gt_gray, gen_gray, data_range=255)
        ssim_values.append(ssim_val)
        
        if (i + 1) % 50 == 0:
            print(f"已处理 {i + 1}/{len(val_frame_indices)} 帧...")
    
    # 5. 输出统计结果
    avg_psnr = np.mean(psnr_values)
    avg_ssim = np.mean(ssim_values)
    
    print("\n" + "="*50)
    print("评估结果:")
    print(f"  平均 PSNR: {avg_psnr:.2f} dB")
    print(f"  平均 SSIM: {avg_ssim:.4f}")
    print(f"  评估帧数: {len(psnr_values)}")
    print("="*50)
    
    return {
        "psnr": avg_psnr,
        "ssim": avg_ssim,
        "num_frames": len(psnr_values)
    }


def main():
    parser = argparse.ArgumentParser(description="评估GaussianTalker生成视频质量")
    parser.add_argument("--generated_video", type=str, required=True,
                        help="生成的视频路径 (如: output/obama/renders/output.mp4)")
    parser.add_argument("--data_dir", type=str, required=True,
                        help="数据目录 (如: data/obama)")
    parser.add_argument("--output_json", type=str, default=None,
                        help="输出结果的JSON文件路径")
    
    args = parser.parse_args()
    
    # 构建路径
    gt_dir = os.path.join(args.data_dir, "gt_imgs")
    transforms_val_path = os.path.join(args.data_dir, "transforms_val.json")
    
    # 检查文件是否存在
    if not os.path.exists(args.generated_video):
        print(f"错误: 生成视频不存在: {args.generated_video}")
        return
    
    if not os.path.exists(transforms_val_path):
        print(f"错误: transforms_val.json不存在: {transforms_val_path}")
        return
    
    if not os.path.exists(gt_dir):
        print(f"错误: GT图像目录不存在: {gt_dir}")
        return
    
    # 执行评估
    results = calculate_metrics(args.generated_video, gt_dir, transforms_val_path)
    
    # 保存结果
    if args.output_json:
        with open(args.output_json, 'w') as f:
            json.dump(results, f, indent=2)
        print(f"\n结果已保存到: {args.output_json}")


if __name__ == "__main__":
    main()

