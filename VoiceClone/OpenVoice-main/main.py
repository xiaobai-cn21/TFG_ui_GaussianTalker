# OpenVoice-main/main.py

import os
import torch
from openvoice.models_wrapper import BaseSpeakerTTS, ToneColorConverter
from openvoice import utils

# ===============================
# 自动获取 VoiceClone 根目录
# ===============================
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))


en_ckpt_base = os.path.join(BASE_DIR, 'checkpoints', 'base_speakers', 'EN')
zh_ckpt_base = os.path.join(BASE_DIR, 'checkpoints', 'base_speakers', 'ZH')
ckpt_converter = os.path.join(BASE_DIR, 'checkpoints', 'converter')

device = 'cuda' if torch.cuda.is_available() else 'cpu'

# ===============================
# 初始化模型
# ===============================
en_base_speaker_tts = BaseSpeakerTTS(os.path.join(en_ckpt_base, 'config.json'), device=device)
en_base_speaker_tts.load_ckpt(os.path.join(en_ckpt_base, 'checkpoint.pth'))

zh_base_speaker_tts = BaseSpeakerTTS(os.path.join(zh_ckpt_base, 'config.json'), device=device)
zh_base_speaker_tts.load_ckpt(os.path.join(zh_ckpt_base, 'checkpoint.pth'))

tone_color_converter = ToneColorConverter(os.path.join(ckpt_converter, 'config.json'), device=device)
tone_color_converter.load_ckpt(os.path.join(ckpt_converter, 'checkpoint.pth'))

# ===============================
# 定义语音克隆接口
# ===============================
def synthesize(text, speaker='default', language='en', ref_audio=None, output_path='outputs/output.wav'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    if language.lower() in ['en', 'english']:
        model = en_base_speaker_tts
        source_se_path = os.path.join(en_ckpt_base, 'en_default_se.pth')
        model_language = 'english'
    elif language.lower() in ['zh', 'chinese']:
        model = zh_base_speaker_tts
        source_se_path = os.path.join(zh_ckpt_base, 'zh_default_se.pth')
        model_language = 'chinese'
    else:
        raise ValueError(f"Language {language} not supported")

    source_se = torch.load(source_se_path).to(device)
    tmp_path = os.path.join(os.path.dirname(output_path), 'tmp.wav')

    # TTS
    model.tts(text, tmp_path, speaker=speaker, language=model_language)

    # 如果提供参考音频，进行声色克隆
    if ref_audio is not None:
        tgt_se = tone_color_converter.extract_se(ref_audio)
        tone_color_converter.convert(tmp_path, source_se, tgt_se, output_path)
        os.remove(tmp_path)
    else:
        os.rename(tmp_path, output_path)

    print(f"Audio saved to {output_path}")
    return output_path
