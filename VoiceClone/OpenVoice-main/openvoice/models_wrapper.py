# OpenVoice-main/openvoice/models_wrapper.py

import torch
import numpy as np
import os
import re
import soundfile
import librosa

from . import utils
from . import commons
from .mel_processing import spectrogram_torch
from .models import SynthesizerTrn
# openvoice/utils.py
from .text import cleaners, symbols

# 这个函数从官方 repo 中摘取
def text_to_sequence(text, symbol_set, text_cleaners):
    """
    将文本转为模型可用的序列
    text          : 输入文本
    symbol_set    : 模型 symbols 列表
    text_cleaners : 文本清理器列表
    """
    from .text import cleaners as cleaner_module
    from .text.symbols import _symbol_to_id

    # 调用官方 cleaners
    for cleaner_name in text_cleaners:
        if hasattr(cleaner_module, cleaner_name):
            cleaner_func = getattr(cleaner_module, cleaner_name)
            text = cleaner_func(text)
        else:
            print(f"Warning: cleaner {cleaner_name} not found.")

    sequence = []
    for c in text:
        if c in _symbol_to_id:
            sequence.append(_symbol_to_id[c])
    return sequence


class BaseSpeakerTTS:
    language_marks = {
        "english": "EN",
        "chinese": "ZH",
    }

    def __init__(self, config_path, device='cuda:0'):
        if 'cuda' in device:
            assert torch.cuda.is_available()
        self.device = device
        self.hps = utils.get_hparams_from_file(config_path)

        self.model = SynthesizerTrn(
            len(getattr(self.hps, 'symbols', [])),
            self.hps.data.filter_length // 2 + 1,
            n_speakers=self.hps.data.n_speakers,
            **self.hps.model,
        ).to(device)
        self.model.eval()

    def load_ckpt(self, ckpt_path):
        checkpoint_dict = torch.load(ckpt_path, map_location=torch.device(self.device))
        a, b = self.model.load_state_dict(checkpoint_dict['model'], strict=False)
        print(f"Loaded checkpoint '{ckpt_path}'")
        print('missing/unexpected keys:', a, b)

    @staticmethod
    def get_text(text, hps, is_symbol=False):
        text_norm = utils.text_to_sequence(text, hps.symbols, [] if is_symbol else hps.data.text_cleaners)
        if getattr(hps.data, 'add_blank', False):
            text_norm = commons.intersperse(text_norm, 0)
        return torch.LongTensor(text_norm)

    @staticmethod
    def audio_numpy_concat(segment_data_list, sr, speed=1.):
        audio_segments = []
        for segment_data in segment_data_list:
            audio_segments += segment_data.reshape(-1).tolist()
            audio_segments += [0] * int((sr * 0.05)/speed)
        return np.array(audio_segments).astype(np.float32)

    def tts(self, text, output_path, speaker, language='English', speed=1.0):
        mark = self.language_marks.get(language.lower())
        assert mark is not None, f"language {language} is not supported"

        text_formatted = f'[{mark}]{text}[{mark}]'
        stn_tst = self.get_text(text_formatted, self.hps, False)

        with torch.no_grad():
            x_tst = stn_tst.unsqueeze(0).to(self.device)
            x_tst_lengths = torch.LongTensor([stn_tst.size(0)]).to(self.device)
            speaker_id = self.hps.speakers[speaker]
            sid = torch.LongTensor([speaker_id]).to(self.device)
            audio = self.model.infer(
                x_tst, x_tst_lengths, sid=sid,
                noise_scale=0.667, noise_scale_w=0.6,
                length_scale=1.0/speed
            )[0][0, 0].cpu().numpy()

        audio_out = self.audio_numpy_concat([audio], sr=self.hps.data.sampling_rate, speed=speed)
        soundfile.write(output_path, audio_out, self.hps.data.sampling_rate)
        return output_path


class ToneColorConverter(BaseSpeakerTTS):
    def __init__(self, config_path, device='cuda:0', enable_watermark=False):
        super().__init__(config_path, device=device)
        self.enable_watermark = enable_watermark
        self.watermark_model = None
        if enable_watermark:
            import wavmark
            self.watermark_model = wavmark.load_model().to(device)

    def extract_se(self, ref_wav_list, se_save_path=None):
        if isinstance(ref_wav_list, str):
            ref_wav_list = [ref_wav_list]

        gs = []
        for fname in ref_wav_list:
            audio_ref, sr = librosa.load(fname, sr=self.hps.data.sampling_rate)
            y = torch.FloatTensor(audio_ref).unsqueeze(0).to(self.device)
            y = spectrogram_torch(y, self.hps.data.filter_length,
                                  self.hps.data.sampling_rate,
                                  self.hps.data.hop_length,
                                  self.hps.data.win_length,
                                  center=False).to(self.device)
            with torch.no_grad():
                g = self.model.ref_enc(y.transpose(1, 2)).unsqueeze(-1)
                gs.append(g.detach())

        gs = torch.stack(gs).mean(0)

        if se_save_path:
            os.makedirs(os.path.dirname(se_save_path), exist_ok=True)
            torch.save(gs.cpu(), se_save_path)

        return gs

    def convert(self, audio_src_path, src_se, tgt_se, output_path=None, tau=0.3, message="default"):
        audio, _ = librosa.load(audio_src_path, sr=self.hps.data.sampling_rate)
        y = torch.FloatTensor(audio).unsqueeze(0).to(self.device)
        spec = spectrogram_torch(y, self.hps.data.filter_length,
                                 self.hps.data.sampling_rate,
                                 self.hps.data.hop_length,
                                 self.hps.data.win_length,
                                 center=False).to(self.device)
        spec_lengths = torch.LongTensor([spec.size(-1)]).to(self.device)

        with torch.no_grad():
            audio_out = self.model.voice_conversion(spec, spec_lengths, sid_src=src_se, sid_tgt=tgt_se, tau=tau)[0][0, 0].cpu().numpy()

        if output_path:
            soundfile.write(output_path, audio_out, self.hps.data.sampling_rate)
        return audio_out
