from flask import Flask, render_template, request, jsonify, Response
import os
import uuid
import threading
import json
import queue
from backend.video_generator import generate_video
from backend.model_trainer import train_model
from backend.chat_engine import chat_response, chat_pipeline, chat_pipeline_with_progress

app = Flask(__name__)

# 简单的内存任务存储（生产环境请替换为持久化/队列）
TASKS = {}

def _process_chat_task(task_id, data):
    try:
        TASKS[task_id]["stage"] = "processing"
        # 确保目录
        os.makedirs('./static/audios', exist_ok=True)
        os.makedirs('./static/videos', exist_ok=True)

        # 执行主流程（内部会读取 ./static/audios/input.wav 等）
        video_path = chat_response(data)
        video_url = "/" + video_path.replace("\\", "/")
        TASKS[task_id]["stage"] = "completed"
        TASKS[task_id]["video_url"] = video_url
        TASKS[task_id]["status"] = "success"
    except Exception as e:
        TASKS[task_id]["stage"] = "error"
        TASKS[task_id]["status"] = "error"
        TASKS[task_id]["error"] = str(e)

# 首页
@app.route('/')
def index():
    return render_template('index.html')

# 视频生成界面
@app.route('/video_generation', methods=['GET', 'POST'])
def video_generation():
    if request.method == 'POST':
        data = {
            "model_name": request.form.get('model_name'),
            "model_param": request.form.get('model_param'),
            "ref_audio": request.form.get('ref_audio'),
            "gpu_choice": request.form.get('gpu_choice', 'GPU0'),
            # TTS语音克隆参数
            "use_tts": request.form.get('use_tts') == 'on',
            "tts_text": request.form.get('tts_text'),
            "tts_ref_audio": request.form.get('tts_ref_audio'),
            # GaussianTalker专用参数
            "batch_size": request.form.get('batch_size', '128'),
            "iteration": request.form.get('iteration', '10000'),
            # 云端SSH参数
            "ssh_host": request.form.get('ssh_host', 'connect.bjb1.seetacloud.com'),
            "ssh_port": request.form.get('ssh_port', 40258),
            "ssh_password": request.form.get('ssh_password', '83WncIL5CoYB'),
        }

        try:
            result = generate_video(data)
            # 处理字典或字符串返回值
            if isinstance(result, dict):
                return jsonify(result)
            else:
                return jsonify({'status': 'success', 'video_path': result})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return render_template('video_generation.html')


# 模型训练界面
@app.route('/model_training', methods=['GET', 'POST'])
def model_training():
    if request.method == 'POST':
        data = {
            "model_choice": request.form.get('model_choice'),
            "ref_video": request.form.get('ref_video'),
            "gpu_choice": request.form.get('gpu_choice', 'GPU0'),
            "epoch": request.form.get('epoch', '10'),
            "custom_params": request.form.get('custom_params'),
            # GaussianTalker专用参数
            "iterations": request.form.get('iterations', '10000'),
            "config": request.form.get('config', 'arguments/64_dim_1_transformer.py'),
        }

        # 处理AU文件上传（GaussianTalker）
        au_csv_path = None
        if 'au_csv' in request.files and request.files['au_csv']:
            au_csv_file = request.files['au_csv']
            if au_csv_file.filename != '':
                # 保存到临时目录
                os.makedirs('./temp', exist_ok=True)
                au_csv_path = f'./temp/{au_csv_file.filename}'
                au_csv_file.save(au_csv_path)
                data['au_csv'] = au_csv_path

        try:
            video_path = train_model(data)
            video_path = "/" + video_path.replace("\\", "/")
            return jsonify({'status': 'success', 'video_path': video_path})
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return render_template('model_training.html')


# 实时对话系统界面
@app.route('/chat_system', methods=['GET', 'POST'])
def chat_system():
    if request.method == 'POST':
        data = {
            "model_name": request.form.get('model_name'),
            "model_param": request.form.get('model_param'),
            "voice_clone": request.form.get('voice_clone'),
            "api_choice": request.form.get('api_choice'),
            "gpu_choice": request.form.get('gpu_choice', 'GPU0'),
            "batch_size": request.form.get('batch_size', '128'),
            "iteration": request.form.get('iteration', '10000'),
            "ref_audio": request.form.get('ref_audio', ''),  # 参考音频路径（用于语音克隆）
            "ssh_host": request.form.get('ssh_host', 'connect.bjb1.seetacloud.com'),
            "ssh_port": request.form.get('ssh_port', 40258),
            "ssh_password": request.form.get('ssh_password', '83WncIL5CoYB'),
        }

        try:
            result = chat_pipeline(data)
            tts_url = "/" + result["tts_audio_path"].replace("\\", "/") if result.get("tts_audio_path") else None
            video_url = "/" + result["video_path"].replace("\\", "/") if result.get("video_path") else None
            return jsonify({
                'status': 'success',
                'recognized_text': result.get('recognized_text'),
                'ai_text': result.get('ai_text'),
                'tts_audio_url': tts_url,
                'video_path': video_url
            })
        except Exception as e:
            return jsonify({'status': 'error', 'message': str(e)}), 500

    return render_template('chat_system.html')


# SSE 实时进度推送的对话接口
@app.route('/chat_system_stream', methods=['POST'])
def chat_system_stream():
    """使用 Server-Sent Events 实时推送对话进度"""
    data = {
        "model_name": request.form.get('model_name'),
        "model_param": request.form.get('model_param'),
        "voice_clone": request.form.get('voice_clone'),
        "api_choice": request.form.get('api_choice'),
        "gpu_choice": request.form.get('gpu_choice', 'GPU0'),
        "batch_size": request.form.get('batch_size', '128'),
        "iteration": request.form.get('iteration', '10000'),
        "ref_audio": request.form.get('ref_audio', ''),
        "ssh_host": request.form.get('ssh_host', 'connect.bjb1.seetacloud.com'),
        "ssh_port": request.form.get('ssh_port', 40258),
        "ssh_password": request.form.get('ssh_password', '83WncIL5CoYB'),
    }
    
    # 创建消息队列用于线程间通信
    progress_queue = queue.Queue()
    
    def progress_callback(step, message, extra_data=None):
        """进度回调函数，将进度放入队列"""
        progress_queue.put({
            'step': step,
            'message': message,
            'data': extra_data or {}
        })
    
    def run_pipeline():
        """在后台线程运行处理流程"""
        try:
            result = chat_pipeline_with_progress(data, progress_callback)
            # 处理完成，发送最终结果
            tts_url = "/" + result["tts_audio_path"].replace("\\", "/") if result.get("tts_audio_path") else None
            video_url = "/" + result["video_path"].replace("\\", "/") if result.get("video_path") else None
            progress_queue.put({
                'step': 'complete',
                'message': '处理完成',
                'data': {
                    'status': 'success',
                    'recognized_text': result.get('recognized_text'),
                    'ai_text': result.get('ai_text'),
                    'tts_audio_url': tts_url,
                    'video_path': video_url
                }
            })
        except Exception as e:
            progress_queue.put({
                'step': 'error',
                'message': str(e),
                'data': {'status': 'error'}
            })
    
    def generate():
        """生成 SSE 事件流"""
        # 启动后台处理线程
        thread = threading.Thread(target=run_pipeline, daemon=True)
        thread.start()
        
        # 持续从队列读取进度并推送
        while True:
            try:
                progress = progress_queue.get(timeout=120)  # 2分钟超时
                yield f"data: {json.dumps(progress, ensure_ascii=False)}\n\n"
                
                # 如果是完成或错误，结束流
                if progress['step'] in ('complete', 'error'):
                    break
            except queue.Empty:
                # 超时，发送心跳
                yield f"data: {json.dumps({'step': 'heartbeat', 'message': '处理中...'})}\n\n"
    
    return Response(
        generate(),
        mimetype='text/event-stream',
        headers={
            'Cache-Control': 'no-cache',
            'Connection': 'keep-alive',
            'X-Accel-Buffering': 'no'
        }
    )

@app.route('/chat/once', methods=['POST'])
def chat_once():
    # 接收音频（可选）与参数
    model_name = request.form.get('model_name', 'GaussianTalker')
    model_param = request.form.get('model_param', '')
    voice_clone = request.form.get('voice_clone')
    api_choice = request.form.get('api_choice')
    gpu_choice = request.form.get('gpu_choice', '0')
    iteration = request.form.get('iteration', '10000')

    # 处理音频文件（如果上传）
    if 'audio' in request.files and request.files['audio'] and request.files['audio'].filename:
        audio_file = request.files['audio']
        os.makedirs('./static/audios', exist_ok=True)
        # 为兼容现有 chat_engine，先固定写入 input.wav
        save_path = './static/audios/input.wav'
        audio_file.save(save_path)

    task_id = str(uuid.uuid4())
    TASKS[task_id] = {
        "task_id": task_id,
        "status": "queued",
        "stage": "queued",
        "video_url": None,
        "error": None
    }

    data = {
        "model_name": model_name,
        "model_param": model_param,
        "voice_clone": voice_clone,
        "api_choice": api_choice,
        "gpu_choice": gpu_choice,
        "iteration": iteration
    }

    t = threading.Thread(target=_process_chat_task, args=(task_id, data), daemon=True)
    t.start()

    return jsonify({"task_id": task_id, "status": "queued"})

@app.route('/chat/status', methods=['GET'])
def chat_status():
    task_id = request.args.get('id')
    if not task_id or task_id not in TASKS:
        return jsonify({"status": "error", "message": "invalid task id"}), 400
    return jsonify(TASKS[task_id])

@app.route('/save_audio', methods=['POST'])
def save_audio():
    if 'audio' not in request.files:
        return jsonify({'status': 'error', 'message': '没有音频文件'})
    
    audio_file = request.files['audio']
    if audio_file.filename == '':
        return jsonify({'status': 'error', 'message': '没有选择文件'})
    
    # 确保目录存在
    os.makedirs('./static/audios', exist_ok=True)
    
    # 保存文件
    audio_file.save('./static/audios/input.wav')
    
    return jsonify({'status': 'success', 'message': '音频保存成功'})


@app.route('/upload_file', methods=['POST'])
def upload_file():
    """通用文件上传接口"""
    if 'file' not in request.files:
        return jsonify({'status': 'error', 'message': '没有文件'})
    
    file = request.files['file']
    if file.filename == '':
        return jsonify({'status': 'error', 'message': '没有选择文件'})
    
    file_type = request.form.get('type', 'unknown')
    
    # 直接使用现有的static目录
    if file_type == 'video':
        save_dir = './static/videos'
    elif file_type == 'audio':
        save_dir = './static/audios'
    else:
        save_dir = './static'
    
    # 生成唯一文件名（保留原始扩展名）
    from werkzeug.utils import secure_filename
    
    original_filename = secure_filename(file.filename)
    filename_parts = original_filename.rsplit('.', 1)
    if len(filename_parts) == 2:
        unique_filename = f"{filename_parts[0]}_{uuid.uuid4().hex[:8]}.{filename_parts[1]}"
    else:
        unique_filename = f"{original_filename}_{uuid.uuid4().hex[:8]}"
    
    file_path = os.path.join(save_dir, unique_filename)
    
    try:
        file.save(file_path)
        return jsonify({
            'status': 'success',
            'message': '文件上传成功',
            'file_path': file_path,
            'filename': unique_filename
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'文件保存失败: {str(e)}'
        }), 500


@app.route('/copy_uploaded_audio', methods=['POST'])
def copy_uploaded_audio():
    """复制上传的音频文件到input.wav（用于实时对话）"""
    import shutil
    
    data = request.get_json()
    uploaded_path = data.get('uploaded_path')
    
    if not uploaded_path or not os.path.exists(uploaded_path):
        return jsonify({'status': 'error', 'message': '上传文件不存在'})
    
    try:
        target_path = './static/audios/input.wav'
        os.makedirs(os.path.dirname(target_path), exist_ok=True)
        shutil.copy(uploaded_path, target_path)
        
        return jsonify({
            'status': 'success',
            'message': '音频文件已准备完毕'
        })
    except Exception as e:
        return jsonify({
            'status': 'error',
            'message': f'文件处理失败: {str(e)}'
        }), 500


if __name__ == '__main__':
    # 关闭 reloader 以规避 watchdog 与 werkzeug 的不兼容导致的导入错误
    app.run(debug=True, port=5001, use_reloader=False)
