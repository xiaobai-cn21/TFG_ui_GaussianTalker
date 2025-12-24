#
# Copyright (C) 2023, Inria
# GRAPHDECO research group, https://team.inria.fr/graphdeco
# All rights reserved.
#
# This software is free for non-commercial, research and evaluation use 
# under the terms of the LICENSE.md file.
#
# For inquiries contact  george.drettakis@inria.fr
#

import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.autograd import Variable
from math import exp
import lpips
import torchvision

def lpips_loss(img1, img2, lpips_model):
    loss = lpips_model(img1,img2)
    return loss.mean()

def l1_loss(network_output, gt):
    return torch.abs((network_output - gt)).mean()


# ==================== 改进1: 时序一致性损失 ====================
def temporal_consistency_loss(current_frame, prev_frame, weight=0.1):
    """
    时序一致性损失：约束相邻帧之间的变化平滑
    
    数学原理：
    L_temporal = ||I_t - I_{t-1}||_1 * w
    
    这里使用L1损失来惩罚帧间的剧烈变化，促进视频的时序平滑性。
    对于说话人头像，可以减少闪烁和抖动问题。
    
    Args:
        current_frame: 当前帧 [B, C, H, W]
        prev_frame: 前一帧 [B, C, H, W]
        weight: 损失权重
    
    Returns:
        temporal loss value
    """
    if prev_frame is None:
        return torch.tensor(0.0, device=current_frame.device)
    
    # 基础时序损失
    diff = torch.abs(current_frame - prev_frame)
    
    # 使用梯度加权，对边缘区域给予更高容忍度
    # 因为边缘区域在运动时自然会有更大变化
    sobel_x = torch.tensor([[-1, 0, 1], [-2, 0, 2], [-1, 0, 1]], 
                           dtype=torch.float32, device=current_frame.device).view(1, 1, 3, 3)
    sobel_y = torch.tensor([[-1, -2, -1], [0, 0, 0], [1, 2, 1]], 
                           dtype=torch.float32, device=current_frame.device).view(1, 1, 3, 3)
    
    # 计算当前帧的边缘强度
    if current_frame.shape[1] == 3:
        gray = 0.299 * current_frame[:, 0:1] + 0.587 * current_frame[:, 1:2] + 0.114 * current_frame[:, 2:3]
    else:
        gray = current_frame[:, 0:1]
    
    edge_x = F.conv2d(gray, sobel_x, padding=1)
    edge_y = F.conv2d(gray, sobel_y, padding=1)
    edge_magnitude = torch.sqrt(edge_x**2 + edge_y**2 + 1e-6)
    
    # 边缘区域权重降低 (1 / (1 + edge_magnitude))
    edge_weight = 1.0 / (1.0 + edge_magnitude * 2.0)
    edge_weight = edge_weight.expand_as(diff)
    
    weighted_diff = diff * edge_weight
    
    return weighted_diff.mean() * weight


def temporal_gradient_loss(current_deform, prev_deform, weight=0.05):
    """
    变形场的时序梯度损失
    
    数学原理：
    L_deform_temporal = ||D_t - D_{t-1}||_2^2
    
    约束高斯点的变形在时间上平滑变化，避免突变
    
    Args:
        current_deform: 当前帧的变形量 [B, N, 3] 或 [N, 3]
        prev_deform: 前一帧的变形量
        weight: 损失权重
    
    Returns:
        deformation temporal loss
    """
    if prev_deform is None:
        return torch.tensor(0.0, device=current_deform.device)
    
    # L2损失更适合约束连续变化
    diff = (current_deform - prev_deform) ** 2
    return diff.mean() * weight


# ==================== 改进2: 嘴唇区域增强损失 ====================
def lip_weighted_loss(pred, target, lip_rect, base_weight=1.0, lip_weight=3.0):
    """
    嘴唇区域加权损失
    
    数学原理：
    L = w_base * L1(pred, target) + w_lip * L1(pred_lip, target_lip)
    
    对嘴唇区域给予更高权重，因为嘴唇运动是语音驱动的关键
    
    Args:
        pred: 预测图像 [B, C, H, W]
        target: 目标图像 [B, C, H, W]
        lip_rect: 嘴唇区域 (y1, y2, x1, x2)
        base_weight: 基础损失权重
        lip_weight: 嘴唇区域额外权重
    
    Returns:
        weighted loss value
    """
    # 基础L1损失
    base_loss = torch.abs(pred - target).mean() * base_weight
    
    if lip_rect is not None:
        y1, y2, x1, x2 = lip_rect
        # 嘴唇区域损失
        pred_lip = pred[:, :, y1:y2, x1:x2]
        target_lip = target[:, :, y1:y2, x1:x2]
        lip_loss = torch.abs(pred_lip - target_lip).mean() * lip_weight
        return base_loss + lip_loss
    
    return base_loss


def lip_structure_loss(pred, target, lip_rect, weight=0.5):
    """
    嘴唇结构损失 - 使用SSIM保持嘴唇的结构特征
    
    数学原理：
    L_struct = 1 - SSIM(pred_lip, target_lip)
    
    SSIM考虑了亮度、对比度和结构三个方面，
    对于保持嘴唇的形状和纹理细节很有效
    
    Args:
        pred: 预测图像 [B, C, H, W]
        target: 目标图像 [B, C, H, W]
        lip_rect: 嘴唇区域 (y1, y2, x1, x2)
        weight: 损失权重
    
    Returns:
        lip structure loss value
    """
    if lip_rect is None:
        return torch.tensor(0.0, device=pred.device)
    
    y1, y2, x1, x2 = lip_rect
    pred_lip = pred[:, :, y1:y2, x1:x2]
    target_lip = target[:, :, y1:y2, x1:x2]
    
    # 确保嘴唇区域足够大以计算SSIM
    if pred_lip.shape[2] < 11 or pred_lip.shape[3] < 11:
        return torch.abs(pred_lip - target_lip).mean() * weight
    
    lip_ssim = ssim(pred_lip, target_lip)
    return (1.0 - lip_ssim) * weight


# ==================== 改进3: 自适应损失权重 ====================
class AdaptiveLossWeights(nn.Module):
    """
    自适应损失权重 - 基于不确定性加权
    
    数学原理 (Kendall et al., 2018):
    L_total = Σ (exp(-s_i) * L_i + s_i)
    
    其中s_i是可学习的log方差参数。
    这允许网络自动学习每个损失项的最优权重，
    而不是使用固定的超参数。
    
    优点：
    1. 自动平衡不同量级的损失
    2. 减少超参数调优的工作量
    3. 可以适应训练过程中的动态变化
    """
    def __init__(self, num_losses=4):
        super().__init__()
        # 初始化log方差参数为0（即初始权重为1）
        self.log_vars = nn.Parameter(torch.zeros(num_losses))
    
    def forward(self, losses):
        """
        Args:
            losses: list of individual loss values [L1, L2, L3, ...]
        
        Returns:
            weighted total loss
        """
        total = 0
        for i, loss in enumerate(losses):
            # precision = 1 / σ² = exp(-log(σ²)) = exp(-s)
            precision = torch.exp(-self.log_vars[i])
            # L = precision * L_i + log(σ²) = precision * L_i + s
            total += precision * loss + self.log_vars[i]
        return total
    
    def get_weights(self):
        """返回当前的损失权重用于日志记录"""
        return torch.exp(-self.log_vars).detach().cpu().numpy()

def l2_loss(network_output, gt):
    return ((network_output - gt) ** 2).mean()

def gaussian(window_size, sigma):
    gauss = torch.Tensor([exp(-(x - window_size // 2) ** 2 / float(2 * sigma ** 2)) for x in range(window_size)])
    return gauss / gauss.sum()

def create_window(window_size, channel):
    _1D_window = gaussian(window_size, 1.5).unsqueeze(1)
    _2D_window = _1D_window.mm(_1D_window.t()).float().unsqueeze(0).unsqueeze(0)
    window = Variable(_2D_window.expand(channel, 1, window_size, window_size).contiguous())
    return window

def ssim(img1, img2, window_size=11, size_average=True):
    channel = img1.size(-3)
    window = create_window(window_size, channel)

    if img1.is_cuda:
        window = window.cuda(img1.get_device())
    window = window.type_as(img1)

    return _ssim(img1, img2, window, window_size, channel, size_average)

def _ssim(img1, img2, window, window_size, channel, size_average=True):
    mu1 = F.conv2d(img1, window, padding=window_size // 2, groups=channel)
    mu2 = F.conv2d(img2, window, padding=window_size // 2, groups=channel)

    mu1_sq = mu1.pow(2)
    mu2_sq = mu2.pow(2)
    mu1_mu2 = mu1 * mu2

    sigma1_sq = F.conv2d(img1 * img1, window, padding=window_size // 2, groups=channel) - mu1_sq
    sigma2_sq = F.conv2d(img2 * img2, window, padding=window_size // 2, groups=channel) - mu2_sq
    sigma12 = F.conv2d(img1 * img2, window, padding=window_size // 2, groups=channel) - mu1_mu2

    C1 = 0.01 ** 2
    C2 = 0.03 ** 2

    ssim_map = ((2 * mu1_mu2 + C1) * (2 * sigma12 + C2)) / ((mu1_sq + mu2_sq + C1) * (sigma1_sq + sigma2_sq + C2))

    if size_average:
        return ssim_map.mean()
    else:
        return ssim_map.mean(1).mean(1).mean(1)

class VGGPerceptualLoss(torch.nn.Module):
    def __init__(self, resize=True):
        super(VGGPerceptualLoss, self).__init__()
        blocks = []
        blocks.append(torchvision.models.vgg16(weights=True).features[:4].eval())
        blocks.append(torchvision.models.vgg16(weights=True).features[4:9].eval())
        blocks.append(torchvision.models.vgg16(weights=True).features[9:16].eval())
        blocks.append(torchvision.models.vgg16(weights=True).features[16:23].eval())
        for bl in blocks:
            for p in bl.parameters():
                p.requires_grad = False
        self.blocks = torch.nn.ModuleList(blocks)
        self.transform = torch.nn.functional.interpolate
        self.resize = resize
        self.register_buffer("mean", torch.tensor([0.485, 0.456, 0.406]).view(1, 3, 1, 1))
        self.register_buffer("std", torch.tensor([0.229, 0.224, 0.225]).view(1, 3, 1, 1))

    def forward(self, input, target, feature_layers=[0, 1, 2, 3], style_layers=[]):
        if input.shape[1] != 3:
            input = input.repeat(1, 3, 1, 1)
            target = target.repeat(1, 3, 1, 1)
        input = (input-self.mean) / self.std
        target = (target-self.mean) / self.std
        if self.resize:
            input = self.transform(input, mode='bilinear', size=(224, 224), align_corners=False)
            target = self.transform(target, mode='bilinear', size=(224, 224), align_corners=False)
        loss = 0.0
        x = input
        y = target
        for i, block in enumerate(self.blocks):
            x = block(x)
            y = block(y)
            if i in feature_layers:
                loss += torch.nn.functional.l1_loss(x, y)
            if i in style_layers:
                act_x = x.reshape(x.shape[0], x.shape[1], -1)
                act_y = y.reshape(y.shape[0], y.shape[1], -1)
                gram_x = act_x @ act_x.permute(0, 2, 1)
                gram_y = act_y @ act_y.permute(0, 2, 1)
                loss += torch.nn.functional.l1_loss(gram_x, gram_y)
        return loss