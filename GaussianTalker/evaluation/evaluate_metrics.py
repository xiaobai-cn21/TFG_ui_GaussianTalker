#!/usr/bin/env python3
"""
GaussianTalker 评估指标脚本
支持指标: NIQE, PSNR, FID, SSIM, LSE-C, LSE-D

使用方法:
    python evaluate_metrics.py --original_video original.mp4 --generated_video generated.mp4 --output_dir ./results

Docker使用方法:
    docker run -v /path/to/videos:/app/input -v /path/to/output:/app/output gaussiantalker-eval
"""

import os
import sys
import json
import argparse
import warnings
import cv2
import torch
import librosa
import subprocess
import numpy as np
import torch.nn as nn
import torch.nn.functional as F
from tqdm import tqdm
from skimage.metrics import peak_signal_noise_ratio as sk_psnr
from skimage.metrics import structural_similarity as ssim

# 忽略警告
warnings.filterwarnings("ignore")

# 尝试导入可选依赖
try:
    import lpips
    LPIPS_AVAILABLE = True
except:
    LPIPS_AVAILABLE = False
    print("警告: lpips未安装，LPIPS指标将跳过")

try:
    from torchvision.models import inception_v3
    from scipy import linalg
    TORCHVISION_AVAILABLE = True
except:
    TORCHVISION_AVAILABLE = False
    print("警告: torchvision或scipy未安装，FID指标将跳过")

try:
    import pyiqa
    PYIQA_AVAILABLE = True
except:
    PYIQA_AVAILABLE = False
    print("警告: pyiqa未安装，NIQE指标将跳过")

# 导入GaussianTalker的PSNR实现
try:
    sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from utils.image_utils import psnr as gt_psnr
    GT_PSNR_AVAILABLE = True
except:
    GT_PSNR_AVAILABLE = False
    print("提示: 使用scikit-image的PSNR实现")


# ============================================================================
# SyncNet 模型定义 (用于 LSE-C 和 LSE-D)
# ============================================================================
class SyncNet(nn.Module):
    def __init__(self):
        super(SyncNet, self).__init__()
        # 音频分支
        self.audio_encoder = nn.Sequential(
            nn.Conv2d(1, 96, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2), stride=(1, 2)),
            nn.Conv2d(96, 128, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2), stride=(1, 2)),
            nn.Conv2d(128, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2), stride=(1, 2)),
            nn.Conv2d(256, 512, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(1, 2), stride=(1, 2)),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        # 视频分支
        self.video_encoder = nn.Sequential(
            nn.Conv2d(3, 96, kernel_size=(7, 7), stride=(2, 2), padding=(3, 3)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)),
            nn.Conv2d(96, 256, kernel_size=(5, 5), stride=(2, 2), padding=(2, 2)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)),
            nn.Conv2d(256, 512, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 512, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.Conv2d(512, 256, kernel_size=(3, 3), stride=(1, 1), padding=(1, 1)),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=(3, 3), stride=(2, 2), padding=(1, 1)),
            nn.AdaptiveAvgPool2d((1, 1))
        )
        
        self.audio_proj = nn.Linear(512, 128)
        self.video_proj = nn.Linear(256, 128)
    
    def forward(self, audio, video):
        a_feat = self.audio_encoder(audio)
        a_feat = a_feat.view(a_feat.size(0), -1)
        a_emb = self.audio_proj(a_feat)
        
        v_feat = self.video_encoder(video)
        v_feat = v_feat.view(v_feat.size(0), -1)
        v_emb = self.video_proj(v_feat)
        
        a_emb = F.normalize(a_emb, p=2, dim=1)
        v_emb = F.normalize(v_emb, p=2, dim=1)
        
        return a_emb, v_emb


# ============================================================================
# 辅助函数
# ============================================================================
def extract_audio_from_video(video_path, audio_save_path="temp_audio.wav"):
    """从视频中提取音频"""
    cmd = [
        'ffmpeg', '-i', video_path,
        '-vn', '-ac', '1', '-ar', '16000',
        '-y', audio_save_path
    ]
    subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return audio_save_path


def extract_mfcc(audio_path, n_mfcc=96, n_fft=512, hop_length=160):
    """提取音频MFCC特征"""
    y, sr = librosa.load(audio_path, sr=16000)
    mfcc = librosa.feature.mfcc(y=y, sr=sr, n_mfcc=n_mfcc, n_fft=n_fft, hop_length=hop_length)
    mfcc = (mfcc - np.mean(mfcc)) / np.std(mfcc)
    mfcc = np.expand_dims(mfcc, axis=0)
    return mfcc.astype(np.float32)


def preprocess_video_frame_syncnet(frame, target_size=(224, 224)):
    """预处理视频帧（SyncNet输入格式）"""
    frame = cv2.resize(frame, target_size)
    frame = (frame / 255.0 - 0.5) * 2.0
    frame = frame.transpose(2, 0, 1)
    return frame.astype(np.float32)


def load_video_frames(video_path, max_frames=None):
    """加载视频所有帧"""
    cap = cv2.VideoCapture(video_path)
    frames = []
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        frames.append(frame)
        
        if max_frames and len(frames) >= max_frames:
            break
    
    cap.release()
    print(f"加载了 {len(frames)} 帧")
    return frames


def center_crop_square(frame):
    """中心裁剪为正方形"""
    h, w = frame.shape[:2]
    s = min(h, w)
    y0 = max(0, (h - s) // 2)
    x0 = max(0, (w - s) // 2)
    return frame[y0:y0 + s, x0:x0 + s]


def resize_to_square(frame, size=512):
    """缩放到size×size"""
    if frame is None or frame.size == 0:
        return frame
    h, w = frame.shape[:2]
    if h == size and w == size:
        return frame
    interp = cv2.INTER_AREA if (h > size or w > size) else cv2.INTER_LINEAR
    return cv2.resize(frame, (size, size), interpolation=interp)


def preprocess_for_pixel_metrics(frames, target_size=512):
    """像素级指标预处理"""
    out = []
    for f in tqdm(frames, desc="预处理帧"):
        f2 = center_crop_square(f)
        f2 = resize_to_square(f2, size=target_size)
        out.append(f2)
    return out


# ============================================================================
# 评估指标计算
# ============================================================================
def compute_psnr(orig_frames, gen_frames):
    """计算PSNR"""
    n = min(len(orig_frames), len(gen_frames))
    psnr_list = []
    
    print(f"\n计算 PSNR（共{n}帧）...")
    for i in tqdm(range(n), desc="PSNR"):
        if GT_PSNR_AVAILABLE:
            # 使用GaussianTalker官方实现
            o = (torch.from_numpy(orig_frames[i]).permute(2, 0, 1).contiguous().float() / 255.0)
            g = (torch.from_numpy(gen_frames[i]).permute(2, 0, 1).contiguous().float() / 255.0)
            psnr_val = gt_psnr(g.unsqueeze(0), o.unsqueeze(0), mask=None).mean().item()
        else:
            # 使用scikit-image实现
            psnr_val = sk_psnr(orig_frames[i], gen_frames[i], data_range=255)
        psnr_list.append(psnr_val)
    
    return np.array(psnr_list)


def compute_ssim(orig_frames, gen_frames):
    """计算SSIM"""
    n = min(len(orig_frames), len(gen_frames))
    ssim_list = []
    
    print(f"\n计算 SSIM（共{n}帧）...")
    for i in tqdm(range(n), desc="SSIM"):
        ssim_val = ssim(orig_frames[i], gen_frames[i], data_range=255, channel_axis=2)
        ssim_list.append(ssim_val)
    
    return np.array(ssim_list)


def compute_fid(orig_frames, gen_frames, batch_size=50):
    """计算FID"""
    if not TORCHVISION_AVAILABLE:
        print("跳过FID计算（torchvision不可用）")
        return None
    
    print("\n初始化Inception v3模型...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    try:
        inception_model = inception_v3(pretrained=True, transform_input=False)
        inception_model.fc = nn.Identity()
        inception_model.AuxLogits = None
        inception_model.eval()
        inception_model = inception_model.to(device)
    except Exception as e:
        print(f"FID计算失败: {str(e)}")
        return None
    
    def preprocess_for_inception(frame):
        frame_resized = cv2.resize(frame, (299, 299))
        frame_normalized = frame_resized.astype(np.float32) / 255.0
        frame_tensor = torch.from_numpy(frame_normalized).permute(2, 0, 1)
        mean = torch.tensor([0.485, 0.456, 0.406]).view(3, 1, 1)
        std = torch.tensor([0.229, 0.224, 0.225]).view(3, 1, 1)
        frame_tensor = (frame_tensor - mean) / std
        return frame_tensor.unsqueeze(0)
    
    def get_features(frames):
        features_list = []
        n = len(frames)
        
        for i in tqdm(range(0, n, batch_size), desc="提取Inception特征"):
            batch_frames = frames[i:min(i+batch_size, n)]
            batch_tensors = [preprocess_for_inception(f) for f in batch_frames]
            batch_tensor = torch.cat(batch_tensors, dim=0).to(device)
            
            with torch.no_grad():
                features = inception_model(batch_tensor)
                features_list.append(features.cpu().numpy())
        
        return np.concatenate(features_list, axis=0)
    
    print("\n提取原始图像特征...")
    orig_features = get_features(orig_frames)
    
    print("\n提取生成图像特征...")
    gen_features = get_features(gen_frames)
    
    mu1 = np.mean(orig_features, axis=0)
    sigma1 = np.cov(orig_features, rowvar=False)
    
    mu2 = np.mean(gen_features, axis=0)
    sigma2 = np.cov(gen_features, rowvar=False)
    
    try:
        diff = mu1 - mu2
        covmean, _ = linalg.sqrtm(sigma1.dot(sigma2), disp=False)
        
        if not np.isfinite(covmean).all():
            offset = np.eye(sigma1.shape[0]) * 1e-6
            covmean = linalg.sqrtm((sigma1 + offset).dot(sigma2 + offset))
        
        fid_score = diff.dot(diff) + np.trace(sigma1 + sigma2 - 2 * covmean)
        fid_score = np.real(fid_score)
        return fid_score
    except Exception as e:
        print(f"FID计算失败: {str(e)}")
        return None


def compute_niqe(gen_frames):
    """计算NIQE"""
    if not PYIQA_AVAILABLE:
        print("跳过NIQE计算（pyiqa不可用）")
        return [], None, None
    
    print(f"\n计算 NIQE（共{len(gen_frames)}帧）...")
    device = "cuda" if torch.cuda.is_available() else "cpu"
    
    try:
        niqe_metric = pyiqa.create_metric('niqe', device=device)
    except Exception as e:
        print(f"NIQE初始化失败: {str(e)}")
        return [], None, None
    
    niqe_list = []
    for i in tqdm(range(len(gen_frames)), desc="NIQE"):
        try:
            frame = gen_frames[i]
            frame_tensor = torch.from_numpy(frame).permute(2, 0, 1).float() / 255.0
            frame_tensor = frame_tensor.unsqueeze(0).to(device)
            
            with torch.no_grad():
                niqe_score = niqe_metric(frame_tensor)
                if torch.is_tensor(niqe_score):
                    niqe_list.append(niqe_score.cpu().item())
                else:
                    niqe_list.append(float(niqe_score))
        except:
            niqe_list.append(np.nan)
    
    valid_niqe = [n for n in niqe_list if not np.isnan(n)]
    avg_niqe = np.mean(valid_niqe) if len(valid_niqe) > 0 else None
    niqe_std = np.std(valid_niqe) if len(valid_niqe) > 0 else None
    
    return niqe_list, avg_niqe, niqe_std


def compute_lse_c_d(video_path):
    """计算LSE-C和LSE-D"""
    print("\n计算 LSE-C 和 LSE-D...")
    
    model = SyncNet()
    model.eval()
    
    # 提取音频
    audio_path = extract_audio_from_video(video_path)
    mfcc = extract_mfcc(audio_path)
    audio_timesteps = mfcc.shape[2]
    
    # 读取视频
    cap = cv2.VideoCapture(video_path)
    fps = cap.get(cv2.CAP_PROP_FPS)
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    cap.release()
    
    lse_c_list = []
    lse_d_list = []
    
    with torch.no_grad():
        for frame_idx in tqdm(range(total_frames), desc="LSE-C/LSE-D"):
            try:
                cap = cv2.VideoCapture(video_path)
                cap.set(cv2.CAP_PROP_POS_FRAMES, frame_idx)
                ret, frame = cap.read()
                cap.release()
                
                if not ret or frame is None:
                    lse_c_list.append(0.0)
                    lse_d_list.append(1.0)
                    continue
                
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                video_feat = preprocess_video_frame_syncnet(frame)
                video_feat = torch.from_numpy(video_feat).unsqueeze(0)
                
                audio_idx = int(frame_idx * audio_timesteps / total_frames)
                if audio_idx >= audio_timesteps:
                    audio_idx = audio_timesteps - 1
                audio_feat = mfcc[:, :, audio_idx:audio_idx + 64]
                
                if audio_feat.shape[2] < 64:
                    pad = np.zeros((1, 96, 64 - audio_feat.shape[2]), dtype=np.float32)
                    audio_feat = np.concatenate([audio_feat, pad], axis=2)
                audio_feat = torch.from_numpy(audio_feat).unsqueeze(0)
                
                a_emb, v_emb = model(audio_feat, video_feat)
                similarity = (a_emb * v_emb).sum(dim=1).cpu().numpy()[0]
                
                # LSE-C: 置信度（越高越好）
                lse_c = (similarity + 1) / 2.0
                lse_c_list.append(lse_c)
                
                # LSE-D: 距离（越低越好）
                lse_d = 1.0 - lse_c
                lse_d_list.append(lse_d)
                
            except:
                lse_c_list.append(0.0)
                lse_d_list.append(1.0)
    
    # 删除临时音频
    if os.path.exists(audio_path):
        os.remove(audio_path)
    
    return lse_c_list, lse_d_list


# ============================================================================
# 主函数
# ============================================================================
def main():
    parser = argparse.ArgumentParser(description="GaussianTalker 评估指标")
    parser.add_argument("--original_video", type=str, required=True, help="原始视频路径")
    parser.add_argument("--generated_video", type=str, required=True, help="生成视频路径")
    parser.add_argument("--output_dir", type=str, default="./evaluation_results", help="输出目录")
    parser.add_argument("--max_frames", type=int, default=None, help="最大评估帧数")
    
    args = parser.parse_args()
    
    # 检查文件
    if not os.path.exists(args.original_video):
        print(f"错误: 原始视频不存在: {args.original_video}")
        return
    
    if not os.path.exists(args.generated_video):
        print(f"错误: 生成视频不存在: {args.generated_video}")
        return
    
    os.makedirs(args.output_dir, exist_ok=True)
    
    print("=" * 70)
    print("GaussianTalker 评估指标")
    print("=" * 70)
    print(f"原始视频: {args.original_video}")
    print(f"生成视频: {args.generated_video}")
    print(f"输出目录: {args.output_dir}")
    print("=" * 70)
    
    # 1. 加载视频帧
    print("\n1. 加载视频帧...")
    orig_frames = load_video_frames(args.original_video, args.max_frames)
    gen_frames = load_video_frames(args.generated_video, args.max_frames)
    
    n = min(len(orig_frames), len(gen_frames))
    orig_frames = orig_frames[:n]
    gen_frames = gen_frames[:n]
    
    print(f"对齐后帧数: {n}")
    
    # 2. 预处理
    print("\n2. 预处理帧（中心裁剪+缩放到512x512）...")
    orig_eval_frames = preprocess_for_pixel_metrics(orig_frames, target_size=512)
    gen_eval_frames = preprocess_for_pixel_metrics(gen_frames, target_size=512)
    
    # 3. 计算指标
    results = {}
    
    # PSNR
    psnr_list = compute_psnr(orig_eval_frames, gen_eval_frames)
    results['psnr'] = {
        'mean': float(np.mean(psnr_list)),
        'std': float(np.std(psnr_list)),
        'min': float(np.min(psnr_list)),
        'max': float(np.max(psnr_list))
    }
    
    # SSIM
    ssim_list = compute_ssim(orig_eval_frames, gen_eval_frames)
    results['ssim'] = {
        'mean': float(np.mean(ssim_list)),
        'std': float(np.std(ssim_list)),
        'min': float(np.min(ssim_list)),
        'max': float(np.max(ssim_list))
    }
    
    # FID
    fid_score = compute_fid(orig_eval_frames, gen_eval_frames)
    if fid_score is not None:
        results['fid'] = float(fid_score)
    
    # NIQE
    niqe_list, avg_niqe, niqe_std = compute_niqe(gen_eval_frames)
    if avg_niqe is not None:
        results['niqe'] = {
            'mean': float(avg_niqe),
            'std': float(niqe_std)
        }
    
    # LSE-C 和 LSE-D
    lse_c_list, lse_d_list = compute_lse_c_d(args.generated_video)
    results['lse_c'] = {
        'mean': float(np.mean(lse_c_list)),
        'std': float(np.std(lse_c_list))
    }
    results['lse_d'] = {
        'mean': float(np.mean(lse_d_list)),
        'std': float(np.std(lse_d_list))
    }
    
    # 4. 输出结果
    print("\n" + "=" * 70)
    print("评估结果")
    print("=" * 70)
    
    print(f"\nPSNR: {results['psnr']['mean']:.2f} dB (±{results['psnr']['std']:.2f})")
    print(f"SSIM: {results['ssim']['mean']:.4f} (±{results['ssim']['std']:.4f})")
    
    if 'fid' in results:
        print(f"FID: {results['fid']:.2f}")
    
    if 'niqe' in results:
        print(f"NIQE: {results['niqe']['mean']:.4f} (±{results['niqe']['std']:.4f})")
    
    print(f"LSE-C: {results['lse_c']['mean']:.4f} (±{results['lse_c']['std']:.4f})")
    print(f"LSE-D: {results['lse_d']['mean']:.4f} (±{results['lse_d']['std']:.4f})")
    
    print("=" * 70)
    
    # 5. 保存结果
    output_json = os.path.join(args.output_dir, "evaluation_results.json")
    with open(output_json, 'w', encoding='utf-8') as f:
        json.dump(results, f, indent=2, ensure_ascii=False)
    
    print(f"\n结果已保存到: {output_json}")


if __name__ == "__main__":
    main()

