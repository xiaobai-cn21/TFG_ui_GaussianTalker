import subprocess
import os
import time

def train_model(data, progress_callback=None):
    """
    模型训练逻辑。
    progress_callback: 可选的进度回调函数 (step, message, extra_data)
    """
    def report_progress(step, message, extra_data=None):
        if progress_callback:
            progress_callback(step, message, extra_data)
        print(f"[model_trainer] Step {step}: {message}")
    
    print("[backend.model_trainer] 收到数据：")
    for k, v in data.items():
        print(f"  {k}: {v}")
    
    video_path = data.get('ref_video', '')
    skip_preprocess = data.get('skip_preprocess', False)
    model_name = data.get('model_name', '')
    
    print(f"输入视频：{video_path}")
    print(f"跳过预处理：{skip_preprocess}")
    print(f"模型名称：{model_name}")

    report_progress(0, '正在初始化训练环境...')

    if data['model_choice'] == "SyncTalk":
        try:
            report_progress(1, '正在预处理视频数据...')
            
            # 构建命令
            cmd = [
                "./SyncTalk/run_synctalk.sh", "train",
                "--video_path", data['ref_video'],
                "--gpu", data['gpu_choice'],
                "--epochs", data['epoch']
            ]
            
            print(f"[backend.model_trainer] 执行命令: {' '.join(cmd)}")
            
            report_progress(5, '正在训练模型...')
            
            # 执行训练命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("[backend.model_trainer] 训练输出:", result.stdout)
            if result.stderr:
                print("[backend.model_trainer] 错误输出:", result.stderr)
            
            report_progress(7, '训练完成！')
                
        except subprocess.CalledProcessError as e:
            print(f"[backend.model_trainer] 训练失败，退出码: {e.returncode}")
            print(f"错误输出: {e.stderr}")
            return video_path
        except FileNotFoundError:
            print("[backend.model_trainer] 错误: 找不到训练脚本")
            return video_path
        except Exception as e:
            print(f"[backend.model_trainer] 训练过程中发生未知错误: {e}")
            return video_path

    elif data['model_choice'] == "GaussianTalker":
        gpu_choice = data.get('gpu_choice', 'GPU0')
        
        # 云端训练
        if gpu_choice == 'cloud':
            print("[backend.model_trainer] 使用云端训练")
            from backend.cloud_trainer import CloudTrainer
            
            try:
                trainer = CloudTrainer(
                    ssh_host="connect.bjb1.seetacloud.com",
                    ssh_port=data.get('ssh_port', 40258),
                    ssh_password=data.get('ssh_password', '83WncIL5CoYB')
                )
                
                report_progress(0, '正在连接云端服务器...')
                
                if not trainer.connect():
                    raise Exception("SSH连接失败")
                
                try:
                    # 如果跳过预处理
                    if skip_preprocess and model_name:
                        report_progress(1, '跳过预处理（使用已有数据）...')
                        time.sleep(0.5)
                        report_progress(2, '跳过特征提取...')
                        time.sleep(0.3)
                        report_progress(3, '跳过AU提取...')
                        time.sleep(0.3)
                        report_progress(4, '正在初始化模型...')
                        
                        # 直接训练
                        report_progress(5, '正在训练模型...')
                        remote_base = "/root/autodl-tmp/GaussianTalker"
                        remote_data_dir = f"{remote_base}/data/{model_name}"
                        
                        train_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && WANDB_MODE=disabled python train.py -s {remote_data_dir} --model_path output/{model_name} --configs {data.get('config', 'arguments/64_dim_1_transformer.py')} --iterations {data.get('iterations', 10000)}"
                        success, output = trainer.execute_command(train_cmd, cwd=remote_base)
                        
                        if not success:
                            raise Exception(f"训练失败: {output}")
                        
                        report_progress(6, '模型已保存到云端')
                        report_progress(7, '训练完成！')
                        
                        return video_path
                    
                    # 完整训练流程
                    # 从视频路径推断模型名称
                    inferred_model_name = os.path.splitext(os.path.basename(video_path))[0] if video_path else model_name
                    
                    report_progress(1, '正在上传视频到云端...')
                    
                    remote_base = "/root/autodl-tmp/GaussianTalker"
                    remote_data_dir = f"{remote_base}/data/{inferred_model_name}"
                    remote_video = f"{remote_data_dir}/{os.path.basename(video_path)}"
                    
                    if not trainer.upload_file(video_path, remote_video):
                        raise Exception("视频上传失败")
                    
                    # 上传AU文件
                    report_progress(2, '正在上传AU文件...')
                    au_csv_path = data.get('au_csv')
                    if au_csv_path and os.path.exists(au_csv_path):
                        remote_au = f"{remote_data_dir}/au.csv"
                        if not trainer.upload_file(au_csv_path, remote_au):
                            raise Exception("AU文件上传失败")
                    
                    # 预处理
                    report_progress(3, '正在进行数据预处理...')
                    preprocess_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && python data_utils/process.py {remote_video}"
                    success, output = trainer.execute_command(preprocess_cmd, cwd=remote_base)
                    if not success:
                        raise Exception(f"预处理失败: {output}")
                    
                    report_progress(4, '正在初始化模型...')
                    
                    # 训练
                    report_progress(5, '正在训练模型（这可能需要很长时间）...')
                    train_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && WANDB_MODE=disabled python train.py -s {remote_data_dir} --model_path output/{inferred_model_name} --configs {data.get('config', 'arguments/64_dim_1_transformer.py')} --iterations {data.get('iterations', 10000)}"
                    success, output = trainer.execute_command(train_cmd, cwd=remote_base)
                    
                    if not success:
                        raise Exception(f"训练失败: {output}")
                    
                    report_progress(6, '模型已保存到云端')
                    report_progress(7, '训练完成！')
                    
                    print(f"[backend.model_trainer] 云端训练成功")
                    return video_path
                    
                finally:
                    trainer.disconnect()
                    
            except Exception as e:
                print(f"[backend.model_trainer] 云端训练异常: {e}")
                import traceback
                traceback.print_exc()
                raise
        
        # 本地训练
        try:
            report_progress(1, '正在预处理视频数据...')
            
            # 构建命令
            cmd = [
                "./GaussianTalker/run_gaussiantalker.sh", "train",
                "--video_path", data['ref_video'],
                "--gpu", gpu_choice,
                "--iterations", data.get('iterations', '10000')
            ]
            
            # 如果提供了配置文件，添加config参数
            if 'config' in data and data['config']:
                cmd.extend(["--config", data['config']])
            
            # 如果提供了AU CSV文件，添加au_csv参数
            if 'au_csv' in data and data['au_csv'] and os.path.exists(data['au_csv']):
                print(f"[backend.model_trainer] 使用用户提供的AU文件: {data['au_csv']}")
                cmd.extend(["--au_csv", data['au_csv']])
            
            print(f"[backend.model_trainer] 执行命令: {' '.join(cmd)}")
            
            report_progress(5, '正在训练模型...')
            
            # 执行训练命令
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                check=True
            )
            
            print("[backend.model_trainer] 训练输出:", result.stdout)
            if result.stderr:
                print("[backend.model_trainer] 错误输出:", result.stderr)
            
            report_progress(7, '训练完成！')
                
        except subprocess.CalledProcessError as e:
            print(f"[backend.model_trainer] 训练失败，退出码: {e.returncode}")
            print(f"错误输出: {e.stderr}")
            return video_path
        except FileNotFoundError:
            print("[backend.model_trainer] 错误: 找不到训练脚本")
            return video_path
        except Exception as e:
            print(f"[backend.model_trainer] 训练过程中发生未知错误: {e}")
            return video_path

    print("[backend.model_trainer] 训练完成")
    return video_path


def train_model_with_progress(data, progress_callback):
    """带进度回调的训练接口（SSE 接口使用）"""
    return train_model(data, progress_callback)
