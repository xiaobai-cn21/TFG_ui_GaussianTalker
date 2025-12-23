import os
import subprocess
import speech_recognition as sr
from zhipuai import ZhipuAI
import pyttsx3
import shutil
import time
from backend.voice_cloner import synthesize_with_clone

# 尝试导入 Whisper（用于本地语音识别，不需要外网）
try:
    import whisper
    WHISPER_AVAILABLE = True
    print("[backend.chat_engine] Whisper 可用，将使用本地语音识别")
except ImportError:
    WHISPER_AVAILABLE = False
    print("[backend.chat_engine] Whisper 不可用，将使用 Google 语音识别（需要外网）")

def chat_response(data):
    """
    实时对话系统：ASR -> LLM -> TTS（本地）
    现阶段仍返回占位视频，后续可接入视频生成。
    """
    print("[backend.chat_engine] 收到数据：")
    for k, v in data.items():
        print(f"  {k}: {v}")

    # 确保目录存在
    os.makedirs('./static/audios', exist_ok=True)
    os.makedirs('./static/text', exist_ok=True)

    # 语音转文字（使用用户上传的录音）
    input_audio = "./static/audios/input.wav"
    input_text = "./static/text/input.txt"
    recognized_text = audio_to_text(input_audio, input_text)
    if not recognized_text:
        # 当识别失败时，写入一个默认文本，避免后续读取文件报错
        fallback_text = "你好，我的麦克风音频可能无效，请继续以文字方式交流。"
        with open(input_text, 'w', encoding='utf-8') as f:
            f.write(fallback_text)
        recognized_text = fallback_text

    # 大模型回答
    output_text = "./static/text/output.txt"
    api_key = "59086bcdaac941d18fd92545b7417739.OSRp1IXGkA3OMKAQ"
    model = "glm-4.5-flash"
    ai_response = get_ai_response(input_text, output_text, api_key, model)

    # 文本转语音（本地 TTS）
    output_audio = "./static/audios/ai_response.wav"
    text_to_speech(ai_response, output_audio)

    
    video_path = os.path.join("static", "videos", "chat_response.mp4")
    print(f"[backend.chat_engine] 生成视频路径：{video_path}")
    return video_path

def chat_pipeline(data):
    os.makedirs('./static/audios', exist_ok=True)
    os.makedirs('./static/text', exist_ok=True)

    input_audio = "./static/audios/input.wav"
    input_text = "./static/text/input.txt"
    recognized_text = audio_to_text(input_audio, input_text)
    
    # 🚫 禁用兜底逻辑：语音识别必须成功才继续
    if not recognized_text:
        raise Exception("语音识别失败：无法识别音频内容，请检查麦克风或上传有效音频文件")

    output_text = "./static/text/output.txt"
    api_key = "59086bcdaac941d18fd92545b7417739.OSRp1IXGkA3OMKAQ"
    model = "glm-4-flash"
    ai_response = get_ai_response(input_text, output_text, api_key, model)
    
    # 🚫 禁用兜底逻辑：大模型必须成功响应才继续
    if not ai_response or ai_response.strip() == "":
        raise Exception("大模型响应失败：未能获取有效回复，请检查API配置")

    # 选择TTS：如果提供了参考音频就使用语音克隆，否则使用默认TTS
    output_audio = "./static/audios/ai_response.wav"
    tts_audio_path = None

    # 检查是否上传了参考音频（用于语音克隆）
    ref_audio_path = data.get('ref_audio', '').strip() if isinstance(data, dict) else ''
    
    print(f"[backend.chat_engine] 🔍 检查参考音频参数: ref_audio='{ref_audio_path}'")
    
    if ref_audio_path and os.path.exists(ref_audio_path):
        print(f"[backend.chat_engine] ✅ 使用参考音频进行语音克隆: {ref_audio_path}")
        try:
            tts_audio_path = synthesize_with_clone(ai_response, ref_audio_path, output_audio, language='zh')
        except Exception as e:
            print(f"[backend.chat_engine] 语音克隆失败，将回退到本地TTS。原因: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("[backend.chat_engine] 未提供参考音频，使用默认TTS")

    if not tts_audio_path:
        tts_audio_path = text_to_speech(ai_response, output_audio)

    # ==== 新增：GaussianTalker数字人视频生成 ====
    video_path = os.path.join("static", "videos", "chat_response.mp4")
    
    # 获取数字人模型参数
    model_name = data.get('model_name', '')  # e.g., "GaussianTalker" or "SyncTalk"
    model_param = data.get('model_param', '')  # e.g., "obama"
    
    # 如果选择了数字人模型并提供了模型目录，则生成数字人视频
    if model_name and model_param and tts_audio_path and os.path.exists(tts_audio_path):
        print(f"[backend.chat_engine] 开始生成数字人视频：模型={model_name}, 目录={model_param}")
        try:
            from backend.video_generator import generate_video
            
            # 构造传递给generate_video的数据
            # 🔥 实时对话音频很短，降低batch_size避免OOM
            video_gen_data = {
                "model_name": model_name,
                "model_param": model_param,
                "ref_audio": tts_audio_path,
                "gpu_choice": data.get('gpu_choice', 'GPU0'),
                "batch_size": data.get('batch_size', '16'),  # 默认降低到16
                "iteration": data.get('iteration', '10000'),
                "ssh_host": data.get('ssh_host', 'connect.bjb1.seetacloud.com'),
                "ssh_port": data.get('ssh_port', 40258),
                "ssh_password": data.get('ssh_password', '83WncIL5CoYB')
            }
            
            video_gen_result = generate_video(video_gen_data)
            
            # generate_video返回的是视频路径字符串
            if video_gen_result and isinstance(video_gen_result, str) and os.path.exists(video_gen_result):
                video_path = video_gen_result
                print(f"[backend.chat_engine] 数字人视频生成成功：{video_path}")
            else:
                print(f"[backend.chat_engine] 数字人视频生成失败或文件不存在：{video_gen_result}")
                # 失败时使用占位视频（保持原有行为）
                
        except Exception as e:
            print(f"[backend.chat_engine] 数字人视频生成异常：{e}")
            import traceback
            traceback.print_exc()
            # 异常时使用占位视频（保持原有行为）
    else:
        print("[backend.chat_engine] 未启用数字人视频生成（未选择模型或音频不可用）")
    
    return {
        "recognized_text": recognized_text,
        "ai_text": ai_response,
        "tts_audio_path": tts_audio_path if tts_audio_path else (output_audio if os.path.exists(output_audio) else None),
        "video_path": video_path,
    }

def _ffmpeg_convert_to_pcm16_mono_16k(src_path, dst_path):
    """尝试用 ffmpeg 转为 16k/16bit mono PCM WAV。返回 True/False。"""
    try:
        cmd = [
            'ffmpeg', '-y', '-i', src_path,
            '-ac', '1', '-ar', '16000', '-c:a', 'pcm_s16le',
            dst_path
        ]
        result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if result.returncode == 0 and os.path.exists(dst_path) and os.path.getsize(dst_path) > 0:
            print('[backend.chat_engine] 已使用 ffmpeg 规范化音频为 PCM16 mono 16k')
            return True
        else:
            print('[backend.chat_engine] ffmpeg 转码失败:', result.stderr[-500:])
            return False
    except FileNotFoundError:
        print('[backend.chat_engine] 未找到 ffmpeg，请安装或加入 PATH 后再试')
        return False
    except Exception as e:
        print('[backend.chat_engine] ffmpeg 调用异常:', e)
        return False


def audio_to_text(input_audio, input_text):
    """
    使用 Whisper 本地模型进行语音识别（无需外网）
    优先使用 Whisper，如果不可用则回退到 Google 识别
    """
    try:
        if WHISPER_AVAILABLE:
            # 使用 Whisper 本地模型
            print("[backend.chat_engine] 使用 Whisper 进行语音识别...")
            
            # 设置模型下载路径到项目目录（非C盘）
            model_cache_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'whisper_models')
            os.makedirs(model_cache_dir, exist_ok=True)
            print(f"[backend.chat_engine] Whisper 模型缓存目录: {model_cache_dir}")
            
            # 加载模型（使用 medium 模型，准确率很高，约769MB）
            # 可选模型：tiny(39M), base(74M), small(244M), medium(769M, 推荐), large(1550M)
            model = whisper.load_model("medium", download_root=model_cache_dir)
            
            # 识别音频，添加优化参数
            result = model.transcribe(
                input_audio, 
                language='zh',           # 指定中文
                initial_prompt="以下是普通话的句子。",  # 提示词，提高中文识别率
                temperature=0.0,         # 降低随机性，提高准确性
                compression_ratio_threshold=2.4,
                logprob_threshold=-1.0,
                no_speech_threshold=0.6,
                beam_size=5,            # 使用束搜索，提高准确率
                best_of=5               # 从多个候选中选择最佳结果
            )
            text = result["text"].strip()
            
            if not text:
                print("[backend.chat_engine] Whisper 识别结果为空")
                return None
            
            # 保存结果
            with open(input_text, 'w', encoding='utf-8') as f:
                f.write(text)
            
            print(f"语音识别完成！结果已保存到: {input_text}")
            print(f"识别结果: {text}")
            return text
        else:
            # 回退到 Google 语音识别（需要外网）
            print("[backend.chat_engine] Whisper 不可用，使用 Google 语音识别（需要网络）...")
            recognizer = sr.Recognizer()
            
            def _recognize_from_file(path):
                with sr.AudioFile(path) as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio_data = recognizer.record(source)
                    print("正在识别语音...")
                    return recognizer.recognize_google(audio_data, language='zh-CN')

            # 第一次尝试直接读取
            try:
                text = _recognize_from_file(input_audio)
            except Exception as e:
                print('[backend.chat_engine] 直接读取音频失败，将尝试转码。原因:', e)
                tmp_converted = os.path.join(os.path.dirname(input_audio), '__converted_tmp__.wav')
                if _ffmpeg_convert_to_pcm16_mono_16k(input_audio, tmp_converted):
                    text = _recognize_from_file(tmp_converted)
                    try:
                        os.remove(tmp_converted)
                    except Exception:
                        pass
                else:
                    raise
            
            # 保存结果
            with open(input_text, 'w', encoding='utf-8') as f:
                f.write(text)
            print(f"语音识别完成！结果已保存到: {input_text}")
            print(f"识别结果: {text}")
            return text
            
    except sr.UnknownValueError:
        print("无法识别音频内容")
        return None
    except sr.RequestError as e:
        print(f"语音识别服务错误: {e}")
        return None
    except FileNotFoundError:
        print(f"音频文件不存在: {input_audio}")
        return None
    except Exception as e:
        print(f"语音识别发生错误: {e}")
        import traceback
        traceback.print_exc()
        return None

def get_ai_response(input_text, output_text, api_key, model):
    try:
        # 优先从环境变量读取密钥，若无则使用传入值
        api_key_env = os.getenv('ZHIPUAI_API_KEY')
        api_key_eff = (api_key_env if api_key_env else api_key or '').strip()
        # 关键校验：智谱密钥一般为 "{id}.{secret}" 两段形式
        if '.' not in api_key_eff or len(api_key_eff.split('.')) != 2:
            raise ValueError("无效的 ZHIPUAI_API_KEY：应为 id.secret 的两段形式，且不要包含引号/空格")
        client = ZhipuAI(api_key=api_key_eff)
        with open(input_text, 'r', encoding='utf-8') as file:
            content = file.read().strip()

        # 添加系统提示，限制回复长度
        system_prompt = """你是一个智能数字人模型，正在进行实时对话。请遵循以下规则：

1. 身份认同：用户可能会提及你的身份（如："你是奥巴马"、"你是某某明星"），你不应该否认这个身份，要自然地接受并扮演这个角色。

2. 个人偏好：当被问及偏好、喜好时，你必须给出具体的答案。如果你知道所扮演角色的真实偏好，请使用真实偏好；如果不知道，请合理编造一个符合角色设定的偏好。绝对不能回答"我是AI，没有偏好"或类似的推脱。

3. 回复风格：用简洁、自然、口语化的语言回答，回复控制在三句话以内，保持对话轻松友好。

4. 角色一致性：在整个对话过程中保持角色的一致性，不要打破角色设定。"""
        
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": content}
            ]
        )
        output = response.choices[0].message.content

        with open(output_text, 'w', encoding='utf-8') as file:
            file.write(output)

        print(f"答复已保存到: {output_text}")
        return output
    except Exception as e:
        # 失败兜底：直接把用户文本回声，避免整体 500
        print(f"[backend.chat_engine] 调用大模型失败，使用兜底回复。原因: {e}")
        try:
            with open(input_text, 'r', encoding='utf-8') as f:
                fallback = f.read().strip()
            if not fallback:
                fallback = "抱歉，目前无法连接大模型服务。"
        except Exception:
            fallback = "抱歉，目前无法连接大模型服务。"
        try:
            with open(output_text, 'w', encoding='utf-8') as f:
                f.write(fallback)
        except Exception:
            pass
        return fallback

def text_to_speech(text, output_audio_path):
    """
    使用本地 TTS 引擎（pyttsx3）将文本合成为语音文件。
    Windows 默认使用 SAPI5，无需联网。
    """
    try:
        if not text:
            print("[backend.chat_engine] TTS 跳过：文本为空")
            return None

        os.makedirs(os.path.dirname(output_audio_path), exist_ok=True)

        engine = pyttsx3.init()
        # 基础参数可按需调整
        engine.setProperty('rate', 160)
        engine.setProperty('volume', 0.9)

        engine.save_to_file(text, output_audio_path)
        engine.runAndWait()

        print(f"[backend.chat_engine] 语音合成成功: {output_audio_path}")
        return output_audio_path
    except Exception as e:
        print(f"[backend.chat_engine] TTS 错误: {e}")
        return None