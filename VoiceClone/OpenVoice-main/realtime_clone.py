import os
import torch
from openvoice.models_wrapper import ToneColorConverter

device = 'cuda:0' if torch.cuda.is_available() else 'cpu'

converter_ckpt = "checkpoints/converter/checkpoint.pth"
converter_config = "checkpoints/converter/config.json"

converter = ToneColorConverter(config_path=converter_config, device=device)
converter.load_ckpt(converter_ckpt)

# reference.wav 是你想克隆的人的声音
ref_wav = "resources/example_reference.mp3"

# 提取音色 embedding
speaker_emb = converter.extract_se(
    ref_wav,
    se_save_path="Save/target_se.pt"
)
# speaker_emb 是 torch.Tensor，可以直接用作转换

# input.wav 是你想转换的原始音频
input_wav = "resources/demo_speaker2.mp3"
output_dir = "outputs"
os.makedirs(output_dir, exist_ok=True)  # 如果文件夹不存在就创建

# 输出文件完整路径
output_wav = os.path.join(output_dir, "output_clone.wav")

converter.convert(input_wav, src_se=speaker_emb, tgt_se=speaker_emb, output_path=output_wav, tau=0.1)
print("音色克隆完成！输出文件：", output_wav)
