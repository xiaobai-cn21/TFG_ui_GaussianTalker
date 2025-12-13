# OpenVoice-main/main.py

import os
import torch
from openvoice.models_wrapper import BaseSpeakerTTS, ToneColorConverter

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# ===== 官方 TTS 模型（必须有 config.json）=====
en_tts_dir = os.path.join(BASE_DIR, "checkpoints", "base_speakers", "EN")
zh_tts_dir = os.path.join(BASE_DIR, "checkpoints", "base_speakers", "ZH")

# ===== 音色转换模型 =====
converter_dir = os.path.join(BASE_DIR, "checkpoints", "converter")

# ===== checkpoints_v2 音色 =====
SE_V2_DIR = os.path.join(
    BASE_DIR, "checkpoints_v2", "base_speakers", "ses"
)

device = "cuda" if torch.cuda.is_available() else "cpu"

# ===== 初始化模型 =====
en_tts = BaseSpeakerTTS(
    os.path.join(en_tts_dir, "config.json"),
    device=device
)
en_tts.load_ckpt(os.path.join(en_tts_dir, "checkpoint.pth"))

zh_tts = BaseSpeakerTTS(
    os.path.join(zh_tts_dir, "config.json"),
    device=device
)
zh_tts.load_ckpt(os.path.join(zh_tts_dir, "checkpoint.pth"))

tone_converter = ToneColorConverter(
    os.path.join(converter_dir, "config.json"),
    device=device
)
tone_converter.load_ckpt(
    os.path.join(converter_dir, "checkpoint.pth")
)


# ======================================================
# 对外接口：用 checkpoints_v2 的 en-default.pth 做声音克隆
# ======================================================
def synthesize(
    text,
    language="en",
    output_path="outputs/output.wav",
    ref_audio=None,                 # 👈 新增：参考音频
    v2_se_name="en-default.pth",    # 👈 兜底方案
):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    ref_audio = os.path.join(BASE_DIR, ref_audio)
    # ===== 选择 TTS 模型 =====
    if language.lower() in ["en", "english"]:
        tts_model = en_tts
        src_se = torch.load(
            os.path.join(en_tts_dir, "en_default_se.pth"),
            map_location=device
        )
        lang_flag = "english"
    elif language.lower() in ["zh", "chinese"]:
        tts_model = zh_tts
        src_se = torch.load(
            os.path.join(zh_tts_dir, "zh_default_se.pth"),
            map_location=device
        )
        lang_flag = "chinese"
    else:
        raise ValueError("Unsupported language")

    tmp_wav = output_path.replace(".wav", "_tmp.wav")

    # ===== 1️⃣ TTS 生成基础语音 =====
    speaker = list(tts_model.hps.speakers.keys())[0]
    tts_model.tts(
        text=text,
        output_path=tmp_wav,
        speaker=speaker,
        language=lang_flag,
    )

    # ===== 2️⃣ 获取目标音色（重点）=====
    if ref_audio is not None:
        if not os.path.isfile(ref_audio):
            raise FileNotFoundError(ref_audio)

        print(f"🎤 Using reference audio: {ref_audio}")
        tgt_se = tone_converter.extract_se(ref_audio)

    else:
        print(f"🎭 Using v2 preset voice: {v2_se_name}")
        tgt_se_path = os.path.join(SE_V2_DIR, v2_se_name)
        if not os.path.isfile(tgt_se_path):
            raise FileNotFoundError(tgt_se_path)
        tgt_se = torch.load(tgt_se_path, map_location=device)

    # ===== 3️⃣ 音色转换 =====
    tone_converter.convert(
        audio_src_path=tmp_wav,
        src_se=src_se.to(device),
        tgt_se=tgt_se.to(device),
        output_path=output_path,
    )

    os.remove(tmp_wav)
    print(f"✅ Audio saved to {output_path}")

