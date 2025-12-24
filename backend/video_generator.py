import os
import time
import subprocess
import shutil

def generate_video(data, progress_callback=None):
    """
    视频生成逻辑：接收来自前端的参数，并返回一个视频路径。
    支持：1. 直接使用上传的音频  2. 使用TTS语音克隆生成音频
    progress_callback: 可选的进度回调函数 (step, message, extra_data)
    """
    def report_progress(step, message, extra_data=None):
        if progress_callback:
            progress_callback(step, message, extra_data)
        print(f"[video_generator] Step {step}: {message}")
    
    print("[backend.video_generator] 收到数据：")
    for k, v in data.items():
        print(f"  {k}: {v}")
    
    report_progress(0, '正在初始化...')
    
    # 🔥 步骤1: 如果启用了TTS语音克隆，先生成音频
    if data.get('use_tts'):
        report_progress(1, '正在进行语音克隆...')
        print("[backend.video_generator] 启用TTS语音克隆")
        tts_text = data.get('tts_text', '').strip()
        tts_ref_audio = data.get('tts_ref_audio', '').strip()
        
        if not tts_text:
            print("[backend.video_generator] TTS文字为空，跳过")
            return {'status': 'error', 'message': '请提供要转换为语音的文字'}
        
        if not tts_ref_audio or not os.path.exists(tts_ref_audio):
            print("[backend.video_generator] TTS参考音频不存在，跳过")
            return {'status': 'error', 'message': '请提供语音克隆参考音频'}
        
        try:
            from backend.voice_cloner import synthesize_with_clone
            
            # 生成TTS音频
            os.makedirs('./static/audios', exist_ok=True)
            tts_output_audio = "./static/audios/tts_generated.wav"
            
            print(f"[backend.video_generator] 开始TTS合成：文字='{tts_text[:50]}...', 参考音频={tts_ref_audio}")
            synthesize_with_clone(
                text=tts_text,
                ref_audio_path=tts_ref_audio,
                out_path=tts_output_audio,
                language='zh-cn'
            )
            
            # 用生成的TTS音频替换ref_audio
            data['ref_audio'] = tts_output_audio
            print(f"[backend.video_generator] TTS合成成功：{tts_output_audio}")
            report_progress(2, '语音克隆完成')
            
        except Exception as e:
            print(f"[backend.video_generator] TTS合成失败：{e}")
            import traceback
            traceback.print_exc()
            return {'status': 'error', 'message': f'TTS合成失败: {e}'}
    else:
        report_progress(1, '跳过语音克隆（使用上传音频）')

    if data['model_name'] == "SyncTalk":
        try:
            report_progress(2, '正在加载 SyncTalk 模型...')
            
            # 构建命令
            cmd = [
                './SyncTalk/run_synctalk.sh', 'infer',
                '--model_dir', data['model_param'],
                '--audio_path', data['ref_audio'],
                '--gpu', data['gpu_choice']
            ]

            print(f"[backend.video_generator] 执行命令: {' '.join(cmd)}")
            
            report_progress(3, '正在进行音频特征提取...')
            report_progress(4, '正在生成视频帧...')

            # 执行命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True
            )
            
            print("命令标准输出:", result.stdout)
            if result.stderr:
                print("命令标准错误:", result.stderr)
            
            report_progress(5, '正在合成视频...')
            
            # 文件原路径与目的路径 
            model_dir_name = os.path.basename(data['model_param'])
            source_path = os.path.join("SyncTalk", "model", model_dir_name, "results", "test_audio.mp4")
            audio_name = os.path.splitext(os.path.basename(data['ref_audio']))[0]
            video_filename = f"{model_dir_name}_{audio_name}.mp4"
            destination_path = os.path.join("static", "videos", video_filename)
            
            # 检查文件是否存在
            if os.path.exists(source_path):
                shutil.copy(source_path, destination_path)
                print(f"[backend.video_generator] 视频生成完成，路径：{destination_path}")
                report_progress(6, '视频生成完成！')
                return destination_path
            else:
                print(f"[backend.video_generator] 视频文件不存在: {source_path}")
                # 尝试查找任何新生成的mp4文件
                results_dir = os.path.join("SyncTalk", "model", model_dir_name, "results")
                if os.path.exists(results_dir):
                    mp4_files = [f for f in os.listdir(results_dir) if f.endswith('.mp4')]
                    if mp4_files:
                        latest_file = max(mp4_files, key=lambda f: os.path.getctime(os.path.join(results_dir, f)))
                        source_path = os.path.join(results_dir, latest_file)
                        shutil.copy(source_path, destination_path)
                        print(f"[backend.video_generator] 找到最新视频文件: {destination_path}")
                        report_progress(6, '视频生成完成！')
                        return destination_path
                
                return os.path.join("static", "videos", "out.mp4")
            
        except subprocess.CalledProcessError as e:
            print(f"[backend.video_generator] 命令执行失败: {e}")
            print("错误输出:", e.stderr)
            return os.path.join("static", "videos", "out.mp4")
        except Exception as e:
            print(f"[backend.video_generator] 其他错误: {e}")
            return os.path.join("static", "videos", "out.mp4")
    
    elif data['model_name'] == "GaussianTalker":
        gpu_choice = data.get('gpu_choice', 'GPU0')
        
        # 云端渲染
        if gpu_choice == 'cloud':
            print("[backend.video_generator] 使用云端渲染")
            from backend.cloud_trainer import CloudTrainer
            
            try:
                trainer = CloudTrainer(
                    ssh_host="connect.bjb1.seetacloud.com",
                    ssh_port=data.get('ssh_port', 40258),
                    ssh_password=data.get('ssh_password', '83WncIL5CoYB')
                )
                
                report_progress(2, '正在连接云端服务器...')
                
                if not trainer.connect():
                    raise Exception("SSH连接失败")
                
                try:
                    model_name = data.get('model_param')
                    audio_path = data.get('ref_audio')
                    batch_size = int(data.get('batch_size', 128))
                    iteration = int(data.get('iteration', 10000))
                    
                    remote_base = "/root/autodl-tmp/GaussianTalker"
                    remote_data_dir = f"{remote_base}/data/{model_name}"
                    
                    # 如果有音频，上传
                    if audio_path and audio_path.strip() and os.path.exists(audio_path):
                        report_progress(3, '正在上传音频到云端...')
                        audio_filename = os.path.basename(audio_path)
                        audio_name = os.path.splitext(audio_filename)[0]
                        remote_audio = f"{remote_data_dir}/{audio_filename}"
                        
                        if not trainer.upload_file(audio_path, remote_audio):
                            raise Exception("音频上传失败")
                        
                        report_progress(4, '正在提取音频特征...')
                        extract_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && python data_utils/deepspeech_features/extract_ds_features.py --input {remote_audio} --output {remote_data_dir}/{audio_name}.npy"
                        success, output = trainer.execute_command(extract_cmd, cwd=remote_base)
                        if not success:
                            raise Exception(f"音频特征提取失败: {output}")
                        
                        custom_aud = f"{audio_name}.npy"
                        custom_wav = audio_filename
                    else:
                        report_progress(3, '使用训练时的音频...')
                        custom_aud = "aud_ds.npy"
                        custom_wav = "aud.wav"
                    
                    report_progress(5, '正在渲染视频（这可能需要几分钟）...')
                    render_cmd = (
                        f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && ulimit -n 65535 && python render.py "
                        f"-s {remote_data_dir} "
                        f"--model_path output/{model_name} "
                        f"--configs arguments/64_dim_1_transformer.py "
                        f"--iteration {iteration} "
                        f"--batch {batch_size} "
                        f"--skip_train --skip_test "
                        f"--custom_aud {custom_aud} "
                        f"--custom_wav {custom_wav}"
                    )
                    success, output = trainer.execute_command(render_cmd, cwd=remote_base)
                    if not success:
                        raise Exception(f"渲染失败: {output}")
                    
                    report_progress(6, '正在下载生成的视频...')
                    remote_video = f"{remote_base}/output/{model_name}/custom/ours_{iteration}/renders/output_custom_{iteration}iter_renders.mov"
                    local_video = f"./static/videos/cloud_{model_name}_{iteration}.mov"
                    
                    if not trainer.download_file(remote_video, local_video):
                        remote_video_alt = f"{remote_base}/output/{model_name}/renders/output.mp4"
                        local_video = f"./static/videos/cloud_{model_name}_{iteration}.mp4"
                        if not trainer.download_file(remote_video_alt, local_video):
                            raise Exception("视频下载失败")
                    
                    report_progress(7, '视频生成完成！')
                    print(f"[backend.video_generator] 云端渲染成功: {local_video}")
                    return local_video
                    
                finally:
                    trainer.disconnect()
                    
            except Exception as e:
                print(f"[backend.video_generator] 云端渲染异常: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # 本地渲染
        try:
            report_progress(2, '正在加载 GaussianTalker 模型...')
            
            # 构建命令
            cmd = [
                './GaussianTalker/run_gaussiantalker.sh', 'infer',
                '--model_dir', data['model_param'],
                '--audio_path', data['ref_audio'],
                '--gpu', gpu_choice
            ]
            
            # 添加batch_size和iteration参数（使用默认值）
            batch_size = data.get('batch_size', '128')
            iteration = data.get('iteration', '10000')
            cmd.extend(['--batch_size', str(batch_size)])
            cmd.extend(['--iteration', str(iteration)])

            print(f"[backend.video_generator] 执行GaussianTalker推理命令: {' '.join(cmd)}")
            
            report_progress(3, '正在提取音频特征...')
            report_progress(4, '正在渲染视频帧...')

            # 执行命令（使用check=True确保错误时抛出异常）
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("[backend.video_generator] 推理标准输出:", result.stdout)
            if result.stderr:
                print("[backend.video_generator] 推理标准错误:", result.stderr)
            
            report_progress(5, '正在合成最终视频...')
            
            # 确定输出视频路径（run_gaussiantalker.sh会将视频生成到GaussianTalker/output/目录）
            model_dir_name = os.path.basename(data['model_param'])
            output_dir = os.path.join("GaussianTalker", "output", model_dir_name)
            
            # 可能的视频路径
            possible_paths = [
                os.path.join(output_dir, "output.mp4"),
                os.path.join(output_dir, "renders", "output.mp4"),
                os.path.join(output_dir, "custom", f"ours_{iteration}", "renders", "output.mp4"),
            ]
            
            # 尝试查找生成的视频
            source_path = None
            for path in possible_paths:
                if os.path.exists(path):
                    source_path = path
                    print(f"[backend.video_generator] 找到输出视频: {source_path}")
                    break
            
            # 如果找不到预期路径，搜索整个output目录
            if not source_path:
                print(f"[backend.video_generator] 未找到预期路径，搜索整个输出目录: {output_dir}")
                for root, dirs, files in os.walk(output_dir):
                    mp4_files = [f for f in files if f.endswith('.mp4')]
                    if mp4_files:
                        # 使用最新生成的视频
                        latest_file = max(mp4_files, key=lambda f: os.path.getctime(os.path.join(root, f)))
                        source_path = os.path.join(root, latest_file)
                        print(f"[backend.video_generator] 找到最新视频: {source_path}")
                        break
            
            # 复制到static/videos目录
            if source_path and os.path.exists(source_path):
                audio_name = os.path.splitext(os.path.basename(data['ref_audio']))[0]
                video_filename = f"gt_{model_dir_name}_{audio_name}.mp4"
                destination_path = os.path.join("static", "videos", video_filename)
                
                os.makedirs(os.path.dirname(destination_path), exist_ok=True)
                shutil.copy(source_path, destination_path)
                print(f"[backend.video_generator] GaussianTalker视频生成完成: {destination_path}")
                report_progress(6, '视频生成完成！')
                return destination_path
            else:
                print(f"[backend.video_generator] 错误: 未找到GaussianTalker输出视频")
                return os.path.join("static", "videos", "out.mp4")
            
        except subprocess.CalledProcessError as e:
            print(f"[backend.video_generator] GaussianTalker推理失败，退出码: {e.returncode}")
            print(f"错误输出: {e.stderr}")
            return os.path.join("static", "videos", "out.mp4")
        except Exception as e:
            print(f"[backend.video_generator] GaussianTalker推理出现异常: {e}")
            import traceback
            traceback.print_exc()
            return os.path.join("static", "videos", "out.mp4")
    
    video_path = os.path.join("static", "videos", "out.mp4")
    print(f"[backend.video_generator] 视频生成完成，路径：{video_path}")
    report_progress(6, '视频生成完成！')
    return video_path


def generate_video_with_progress(data, progress_callback):
    """带进度回调的视频生成接口（SSE 接口使用）"""
    return generate_video(data, progress_callback)
