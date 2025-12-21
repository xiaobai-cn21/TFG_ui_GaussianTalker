"""
云端训练模块 - 通过SSH连接到AutoDL服务器进行训练
"""
import os
import paramiko
from scp import SCPClient
import time


class CloudTrainer:
    """AutoDL云端训练器"""
    
    def __init__(self, ssh_host, ssh_port, ssh_password):
        self.ssh_host = ssh_host
        self.ssh_port = int(ssh_port)
        self.ssh_password = ssh_password
        self.ssh_username = "root"
        self.remote_base = "/root/autodl-tmp/GaussianTalker"
        self.ssh_client = None
        
    def connect(self):
        """建立SSH连接"""
        print(f"[CloudTrainer] 连接到 {self.ssh_host}:{self.ssh_port}")
        self.ssh_client = paramiko.SSHClient()
        self.ssh_client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        
        try:
            self.ssh_client.connect(
                hostname=self.ssh_host,
                port=self.ssh_port,
                username=self.ssh_username,
                password=self.ssh_password,
                timeout=30
            )
            print("[CloudTrainer] SSH连接成功")
            return True
        except Exception as e:
            print(f"[CloudTrainer] SSH连接失败: {e}")
            return False
    
    def disconnect(self):
        """断开SSH连接"""
        if self.ssh_client:
            self.ssh_client.close()
            print("[CloudTrainer] SSH连接已关闭")
    
    def execute_command(self, command, cwd=None):
        """执行远程命令"""
        if cwd:
            command = f"cd {cwd} && {command}"
        
        print(f"[CloudTrainer] 执行命令: {command}")
        stdin, stdout, stderr = self.ssh_client.exec_command(command, get_pty=True)
        
        # 实时输出
        for line in stdout:
            print(f"[REMOTE] {line.strip()}")
        
        exit_status = stdout.channel.recv_exit_status()
        
        if exit_status != 0:
            error_output = stderr.read().decode()
            print(f"[CloudTrainer] 命令执行失败 (退出码: {exit_status})")
            print(f"[CloudTrainer] 错误输出: {error_output}")
            return False, error_output
        
        return True, stdout.read().decode()
    
    def upload_file(self, local_path, remote_path):
        """上传文件到云端"""
        print(f"[CloudTrainer] 上传文件: {local_path} -> {remote_path}")
        
        try:
            with SCPClient(self.ssh_client.get_transport()) as scp:
                # 确保远程目录存在
                remote_dir = os.path.dirname(remote_path)
                self.execute_command(f"mkdir -p {remote_dir}")
                
                # 上传文件
                scp.put(local_path, remote_path)
            print(f"[CloudTrainer] 文件上传成功")
            return True
        except Exception as e:
            print(f"[CloudTrainer] 文件上传失败: {e}")
            return False
    
    def download_file(self, remote_path, local_path):
        """从云端下载文件"""
        print(f"[CloudTrainer] 下载文件: {remote_path} -> {local_path}")
        
        try:
            # 确保本地目录存在
            os.makedirs(os.path.dirname(local_path), exist_ok=True)
            
            with SCPClient(self.ssh_client.get_transport()) as scp:
                scp.get(remote_path, local_path)
            print(f"[CloudTrainer] 文件下载成功")
            return True
        except Exception as e:
            print(f"[CloudTrainer] 文件下载失败: {e}")
            return False
    
    def train_model(self, model_name, video_path, au_csv_path, iterations=10000, config="arguments/64_dim_1_transformer.py"):
        """
        完整训练流程
        
        Args:
            model_name: 模型名称（如：May）
            video_path: 本地视频路径
            au_csv_path: 本地au.csv路径
            iterations: 训练迭代次数
            config: 配置文件路径
        """
        print(f"[CloudTrainer] 开始云端训练: {model_name}")
        
        # 远程路径
        remote_data_dir = f"{self.remote_base}/data/{model_name}"
        remote_video = f"{remote_data_dir}/{os.path.basename(video_path)}"
        remote_au_csv = f"{remote_data_dir}/au.csv"
        
        # 1. 上传视频
        print("\n===== 步骤1: 上传视频 =====")
        if not self.upload_file(video_path, remote_video):
            return False, "视频上传失败"
        
        # 2. 上传au.csv
        print("\n===== 步骤2: 上传AU文件 =====")
        if not self.upload_file(au_csv_path, remote_au_csv):
            return False, "AU文件上传失败"
        
        # 3. 预处理
        print("\n===== 步骤3: 数据预处理 =====")
        preprocess_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && python data_utils/process.py {remote_data_dir}/{os.path.basename(video_path)}"
        success, output = self.execute_command(preprocess_cmd, cwd=self.remote_base)
        if not success:
            return False, f"预处理失败: {output}"
        
        # 4. 训练
        print("\n===== 步骤4: 模型训练 =====")
        train_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && WANDB_MODE=disabled python train.py -s {remote_data_dir} --model_path output/{model_name} --configs {config} --iterations {iterations}"
        success, output = self.execute_command(train_cmd, cwd=self.remote_base)
        if not success:
            return False, f"训练失败: {output}"
        
        print(f"[CloudTrainer] 云端训练完成: {model_name}")
        return True, f"训练成功完成，模型保存在云端: {self.remote_base}/output/{model_name}"
    
    def render_video(self, model_name, audio_path=None, batch_size=128, iteration=10000, config="arguments/64_dim_1_transformer.py"):
        """
        渲染视频
        
        Args:
            model_name: 模型名称
            audio_path: 本地音频路径（可选，不提供则使用训练时的音频）
            batch_size: 批大小
            iteration: 使用的检查点迭代次数
            config: 配置文件路径
        """
        print(f"[CloudTrainer] 开始云端渲染: {model_name}")
        
        remote_data_dir = f"{self.remote_base}/data/{model_name}"
        
        # 1. 如果提供了音频，上传音频并提取特征
        if audio_path and audio_path.strip() and os.path.exists(audio_path):
            print("\n===== 步骤1: 上传音频并提取特征 =====")
            audio_filename = os.path.basename(audio_path)
            audio_name = os.path.splitext(audio_filename)[0]
            remote_audio = f"{remote_data_dir}/{audio_filename}"
            
            # 上传音频
            if not self.upload_file(audio_path, remote_audio):
                return False, "音频上传失败"
            
            # 提取DeepSpeech特征
            extract_cmd = f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && python data_utils/deepspeech_features/extract_ds_features.py --input {remote_audio} --output {remote_data_dir}/{audio_name}.npy"
            success, output = self.execute_command(extract_cmd, cwd=self.remote_base)
            if not success:
                return False, f"音频特征提取失败: {output}"
            
            custom_aud = f"{audio_name}.npy"
            custom_wav = audio_filename
        else:
            # 使用训练时的音频
            print("\n===== 步骤1: 使用训练时的音频（未提供新音频）=====")
            custom_aud = "aud_ds.npy"
            custom_wav = "aud.wav"
        
        # 2. 渲染（包含ulimit设置）
        print("\n===== 步骤2: 渲染视频 =====")
        render_cmd = (
            f"source /root/miniconda3/etc/profile.d/conda.sh && conda activate gt && ulimit -n 65535 && python render.py "
            f"-s {remote_data_dir} "
            f"--model_path output/{model_name} "
            f"--configs {config} "
            f"--iteration {iteration} "
            f"--batch {batch_size} "
            f"--skip_train --skip_test "
            f"--custom_aud {custom_aud} "
            f"--custom_wav {custom_wav}"
        )
        success, output = self.execute_command(render_cmd, cwd=self.remote_base)
        if not success:
            return False, f"渲染失败: {output}"
        
        # 3. 下载生成的视频
        print("\n===== 步骤3: 下载生成的视频 =====")
        remote_video = f"{self.remote_base}/output/{model_name}/custom/ours_{iteration}/renders/output_custom_{iteration}iter_renders.mov"
        local_video = f"./static/videos/cloud_{model_name}_{iteration}.mov"
        
        if not self.download_file(remote_video, local_video):
            # 尝试备用路径
            remote_video_alt = f"{self.remote_base}/output/{model_name}/renders/output.mp4"
            local_video = f"./static/videos/cloud_{model_name}_{iteration}.mp4"
            if not self.download_file(remote_video_alt, local_video):
                return False, "视频下载失败"
        
        # 4. 下载transforms_val.json（用于评估）
        print("\n===== 步骤4: 下载评估文件 =====")
        remote_transforms = f"{remote_data_dir}/transforms_val.json"
        local_transforms = f"./GaussianTalker/data/{model_name}/transforms_val.json"
        self.download_file(remote_transforms, local_transforms)  # 非必须，失败不影响
        
        print(f"[CloudTrainer] 云端渲染完成")
        return True, local_video


def cloud_train_model(data):
    """
    云端训练接口
    
    Args:
        data: 包含训练参数的字典
            - model_name: 模型名称
            - video_path: 视频路径
            - au_csv: AU文件路径
            - ssh_port: SSH端口
            - ssh_password: SSH密码
            - iterations: 迭代次数
            - config: 配置文件
    """
    trainer = CloudTrainer(
        ssh_host="connect.bjb1.seetacloud.com",
        ssh_port=data.get('ssh_port', 40258),
        ssh_password=data.get('ssh_password', '83WncIL5CoYB')
    )
    
    try:
        if not trainer.connect():
            return False, "SSH连接失败"
        
        # 从视频路径推断模型名称
        video_path = data.get('ref_video')
        model_name = os.path.splitext(os.path.basename(video_path))[0]
        
        success, message = trainer.train_model(
            model_name=model_name,
            video_path=video_path,
            au_csv_path=data.get('au_csv'),
            iterations=int(data.get('iterations', 10000)),
            config=data.get('config', 'arguments/64_dim_1_transformer.py')
        )
        
        return success, message
    
    except Exception as e:
        return False, f"云端训练异常: {str(e)}"
    finally:
        trainer.disconnect()


def cloud_render_video(data):
    """
    云端渲染接口
    
    Args:
        data: 包含渲染参数的字典
            - model_param: 模型名称
            - ref_audio: 音频路径（可选）
            - ssh_port: SSH端口
            - ssh_password: SSH密码
            - batch_size: 批大小
            - iteration: 迭代次数
    """
    trainer = CloudTrainer(
        ssh_host="connect.bjb1.seetacloud.com",
        ssh_port=data.get('ssh_port', 40258),
        ssh_password=data.get('ssh_password', '83WncIL5CoYB')
    )
    
    try:
        if not trainer.connect():
            return False, "SSH连接失败", None
        
        success, result = trainer.render_video(
            model_name=data.get('model_param'),
            audio_path=data.get('ref_audio'),
            batch_size=int(data.get('batch_size', 128)),
            iteration=int(data.get('iteration', 10000))
        )
        
        if success:
            return True, "渲染成功", result  # result是本地视频路径
        else:
            return False, result, None
    
    except Exception as e:
        return False, f"云端渲染异常: {str(e)}", None
    finally:
        trainer.disconnect()

