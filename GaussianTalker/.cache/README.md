# 预训练模型缓存目录

此目录用于存储预训练模型，避免在Docker构建时重复下载。

## 目录结构

```
.cache/
└── torch/
    └── hub/
        └── checkpoints/
            ├── resnet18-5c106cde.pth
            ├── alexnet-owt-7be5be79.pth
            ├── vgg16-397923af.pth
            ├── s3fd-619a316812.pth
            └── lpips/
                └── alex.pth
```

## 使用说明

1. 运行 `download_pretrained.sh` 会自动下载这些模型到此目录
2. Docker构建时会将这些模型复制到镜像中
3. 如果目录为空，Docker构建仍可成功，但首次运行时会下载模型

## 注意

- 此目录已在 `.gitignore` 中排除，不会被提交到Git
- 模型文件总大小约 500MB-1GB

