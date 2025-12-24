<template>
  <div class="video-gen-container">
    <nav class="top-nav">
      <!-- 左侧：返回系统首页按钮 -->
      <button @click="goBack" class="back-btn group">
        <ArrowLeftIcon class="w-5 h-5 transition-transform group-hover:-translate-x-1" />
        <span>返回系统首页</span>
      </button>

      <!-- 右侧区域：系统信息 + 外观控制条 -->
      <div class="nav-right">
        <div class="system-id">
          <span class="text-cyan-500/50">PROTOCOL:</span>
          <span class="ml-2">{{ sessionId }}</span>
        </div>

        <!-- 主题 + 字体（横向并排） -->
        <div class="appearance-inline">
          <ThemeToggle />
          <FontSelector />
        </div>
      </div>
    </nav>

    <main class="content-layout">
      <!-- 左侧：视频显示区域 -->
      <section class="video-preview-section">
        <div class="panel-header">
          <PlayIcon class="w-5 h-5 text-cyan-400" />
          <h3>实时预览输出</h3>
        </div>

        <div class="video-frame">
          <div class="scanline"></div>
          <video id="outputVideo" ref="videoRef" controls class="main-video">
            <source src="/static/videos/sample.mp4" type="video/mp4">
            您的浏览器不支持视频播放。
          </video>
          <!-- 装饰角标 -->
          <div class="corner-tl"></div>
          <div class="corner-br"></div>
        </div>

        <div class="video-meta">
          <span class="label">RESOLUTION: 1080P</span>
          <span class="label">CODEC: H.264</span>
          <span class="label">FPS: 30</span>
        </div>
      </section>

      <!-- 右侧：控制表单区域 -->
      <section class="controls-section">
        <div class="panel-header">
          <CpuIcon class="w-5 h-5 text-cyan-400" />
          <h3>渲染参数配置</h3>
        </div>

        <form @submit.prevent="handleGenerate" class="cyber-form">
          <div class="form-grid">
            <!-- 模型选择 -->
            <div class="form-group">
              <label>算法模型</label>
              <div class="select-wrapper">
                <select v-model="formData.model_name" name="model_name" @change="toggleGaussianTalkerOptions">
                  <option value="SyncTalk">SyncTalk</option>
                  <option value="GaussianTalker">GaussianTalker</option>
                </select>
              </div>
            </div>

            <!-- GPU 选择 -->
            <div class="form-group">
              <label>运算核心 (GPU)</label>
              <div class="select-wrapper">
                <select v-model="formData.gpu_choice" name="gpu_choice" @change="toggleCloudConfig">
                  <option value="GPU0">GPU 0</option>
                  <option value="GPU1">GPU 1</option>
                  <option value="cloud">Cloud (AutoDL)</option>
                </select>
              </div>
            </div>

            <!-- 模型目录地址 -->
            <div class="form-group full-width">
              <label>模型目录地址</label>
              <div class="input-wrapper">
                <input
                  type="text"
                  v-model="formData.model_param"
                  placeholder="请输入模型目录路径（如：obama）"
                  name="model_param"
                />
              </div>
            </div>

            <!-- 使用语音克隆复选框 -->
            <div class="form-group full-width">
              <div class="checkbox-wrapper">
                <input
                  type="checkbox"
                  v-model="formData.use_tts"
                  id="use_tts_checkbox"
                  name="use_tts"
                  @change="toggleTTSOptions"
                />
                <label for="use_tts_checkbox" class="checkbox-label">
                  使用语音克隆（将文字转为语音）
                </label>
              </div>
            </div>

            <!-- TTS文字输入框（使用语音克隆时显示） -->
            <div v-if="formData.use_tts" class="form-group full-width">
              <label>要说的文字 *</label>
              <div class="textarea-wrapper">
                <textarea
                  v-model="formData.tts_text"
                  name="tts_text"
                  id="tts_text_input"
                  placeholder="输入要转换为语音的文字内容"
                  rows="3"
                  required
                ></textarea>
              </div>
            </div>

            <!-- TTS参考音频（使用语音克隆时显示） -->
            <div v-if="formData.use_tts" class="form-group full-width">
              <label>语音克隆参考音频 *</label>
              <div class="file-input-group">
                <input
                  type="file"
                  ref="ttsRefAudioInput"
                  accept="audio/*"
                  @change="handleTTSRefAudioChange"
                  class="file-input"
                  name="tts_ref_audio_file"
                />
                <div class="file-display">
                  <input
                    type="text"
                    v-model="formData.tts_ref_audio"
                    name="tts_ref_audio"
                    placeholder="或输入音频路径"
                    readonly
                  />
                  <button
                    type="button"
                    @click="triggerTTSRefAudioUpload"
                    class="browse-btn"
                  >
                    浏览
                  </button>
                </div>
                <div class="file-hint">
                  用于克隆音色的参考音频（支持拖拽）
                </div>
              </div>
            </div>

            <!-- 直接上传音频（不使用语音克隆时显示） -->
            <div v-if="!formData.use_tts" class="form-group full-width">
              <label>参考音频上传</label>
              <div class="file-input-group">
                <input
                  type="file"
                  ref="refAudioInput"
                  accept="audio/*"
                  @change="handleRefAudioChange"
                  class="file-input"
                  name="ref_audio_file"
                />
                <div class="file-display">
                  <input
                    type="text"
                    v-model="formData.ref_audio"
                    name="ref_audio"
                    placeholder="或输入音频路径"
                    readonly
                  />
                  <button
                    type="button"
                    @click="triggerRefAudioUpload"
                    class="browse-btn"
                  >
                    浏览
                  </button>
                </div>
                <div class="file-hint">
                  支持拖拽文件到上传框
                </div>
              </div>
            </div>

            <!-- 云端SSH配置 -->
            <div v-if="showCloudConfig" class="form-group full-width cloud-config-group">
              <div class="sub-group">
                <label>SSH端口号</label>
                <input
                  type="number"
                  v-model="formData.ssh_port"
                  name="ssh_port"
                  placeholder="40258"
                />
              </div>
              <div class="sub-group">
                <label>SSH密码</label>
                <input
                  type="password"
                  v-model="formData.ssh_password"
                  name="ssh_password"
                  placeholder="83WncIL5CoYB"
                />
              </div>
            </div>

            <!-- GaussianTalker专用参数 -->
            <div v-if="showGaussianTalkerOptions" class="form-group full-width gt-options">
              <div class="sub-group">
                <label>Batch Size (GaussianTalker)</label>
                <input
                  type="number"
                  v-model="formData.batch_size"
                  name="batch_size"
                  value="128"
                  min="1"
                  max="512"
                />
              </div>
              <div class="sub-group">
                <label>Iteration (GaussianTalker检查点)</label>
                <input
                  type="number"
                  v-model="formData.iteration"
                  name="iteration"
                  value="10000"
                  min="1000"
                  step="1000"
                />
              </div>
            </div>

            <!-- 驱动文本内容（保留Vue原有字段，但非必填） -->
            <div class="form-group full-width">
              <label>驱动文本内容 (可选)</label>
              <div class="textarea-wrapper">
                <textarea
                  v-model="formData.target_text"
                  placeholder="留空则直接使用参考音频的波形特征进行驱动..."
                  name="target_text"
                ></textarea>
              </div>
            </div>
          </div>

          <!-- 提交按钮 -->
          <button type="submit" :disabled="isGenerating" class="submit-btn">
            <div class="btn-content">
              <Loader2Icon v-if="isGenerating" class="w-5 h-5 animate-spin" />
              <ZapIcon v-else class="w-5 h-5" />
              <span>{{ isGenerating ? '正在构建数字孪生...' : '开始生成视频' }}</span>
            </div>
            <div class="btn-glitch"></div>
          </button>
        </form>
      </section>
    </main>

    <!-- 消息提示 -->
    <Transition name="toast">
      <div v-if="toast.show" :class="['toast-msg', toast.type]">
        {{ toast.text }}
      </div>
    </Transition>

    <!-- 进度条弹窗 -->
    <ProgressSteps
      :visible="progressState.visible"
      title="视频生成中"
      subtitle="VIDEO GENERATION IN PROGRESS"
      :steps="progressState.steps"
      :current-step="progressState.currentStep"
      :status-message="progressState.statusMessage"
      :cancellable="false"
    />
  </div>
</template>

<script setup>
import ThemeToggle from '../components/ThemeToggle.vue'
import FontSelector from '../components/FontSelector.vue'
import ProgressSteps from '../components/ProgressSteps.vue'

import { ref, reactive, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowLeft as ArrowLeftIcon,
  Play as PlayIcon,
  Cpu as CpuIcon,
  Zap as ZapIcon,
  Loader2 as Loader2Icon
} from 'lucide-vue-next';

const router = useRouter();
const videoRef = ref(null);
const refAudioInput = ref(null);
const ttsRefAudioInput = ref(null);

const isGenerating = ref(false);
const showCloudConfig = ref(false);
const showGaussianTalkerOptions = ref(false);

// 与其他页面保持一致（你顶部显示需要它）
const sessionId = ref(Math.random().toString(36).substr(2, 9).toUpperCase());

const formData = reactive({
  model_name: 'SyncTalk',
  model_param: '',
  use_tts: false,
  tts_text: '',
  tts_ref_audio: '',
  ref_audio: '',
  gpu_choice: 'GPU0',
  ssh_port: 40258,
  ssh_password: '83WncIL5CoYB',
  batch_size: 128,
  iteration: 10000,
  target_text: ''
});

const toast = reactive({
  show: false,
  text: '',
  type: 'success'
});

// 进度条相关状态
const progressState = reactive({
  visible: false,
  currentStep: 0,
  statusMessage: '',
  steps: [
    { label: '参数验证', detail: '检查输入参数' },
    { label: '音频处理', detail: '处理语音文件' },
    { label: '特征提取', detail: '提取音频特征' },
    { label: '模型推理', detail: '生成面部动画' },
    { label: '视频合成', detail: '渲染最终视频' },
    { label: '完成', detail: '准备播放' }
  ]
});

const updateProgress = (step, message) => {
  progressState.currentStep = step;
  progressState.statusMessage = message;
};

const showToast = (text, type = 'success') => {
  toast.text = text;
  toast.type = type;
  toast.show = true;
  setTimeout(() => toast.show = false, 3000);
};

const goBack = () => {
  router.push('/');
};

const toggleGaussianTalkerOptions = () => {
  showGaussianTalkerOptions.value = formData.model_name === 'GaussianTalker';
};

const toggleCloudConfig = () => {
  showCloudConfig.value = formData.gpu_choice === 'cloud';
};

const toggleTTSOptions = () => {
  if (formData.use_tts) {
    formData.ref_audio = '';
  } else {
    formData.tts_text = '';
    formData.tts_ref_audio = '';
  }
};

const triggerRefAudioUpload = () => {
  refAudioInput.value?.click();
};

const triggerTTSRefAudioUpload = () => {
  ttsRefAudioInput.value?.click();
};

const handleRefAudioChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  showToast('正在上传音频文件，请稍候...', 'info');

  try {
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);
    uploadFormData.append('type', 'audio');

    const uploadRes = await fetch('/upload_file', {
      method: 'POST',
      body: uploadFormData
    });

    const uploadData = await uploadRes.json();
    if (uploadData.status === 'success') {
      formData.ref_audio = uploadData.file_url;
      showToast('音频上传成功', 'success');
    } else {
      showToast('音频上传失败: ' + uploadData.message, 'error');
    }
  } catch (err) {
    console.error('上传错误:', err);
    showToast('上传失败: ' + err.message, 'error');
  }
};

const handleTTSRefAudioChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  showToast('正在上传语音克隆参考音频，请稍候...', 'info');

  try {
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);
    uploadFormData.append('type', 'audio');

    const uploadRes = await fetch('/upload_file', {
      method: 'POST',
      body: uploadFormData
    });

    const uploadData = await uploadRes.json();
    if (uploadData.status === 'success') {
      formData.tts_ref_audio = uploadData.file_path;
      showToast('参考音频上传成功', 'success');
    } else {
      showToast('参考音频上传失败: ' + uploadData.message, 'error');
    }
  } catch (err) {
    console.error('上传错误:', err);
    showToast('上传失败: ' + err.message, 'error');
  }
};

const handleGenerate = async () => {
  if (isGenerating.value) return;

  if (formData.use_tts) {
    if (!formData.tts_text || !formData.tts_text.trim()) {
      showToast('请输入要转换为语音的文字内容', 'error');
      return;
    }

    if (!formData.tts_ref_audio && !formData.ref_audio) {
      showToast('请上传语音克隆参考音频', 'error');
      return;
    }
  }

  isGenerating.value = true;
  progressState.visible = true;
  updateProgress(0, '正在连接服务器...');

  const payload = new FormData();
  Object.keys(formData).forEach(key => {
    if (key === 'use_tts') {
      payload.append(key, formData[key] ? 'on' : '');
    } else if (formData[key] !== undefined && formData[key] !== null) {
      payload.append(key, formData[key]);
    }
  });

  try {
    // 使用 SSE 流式接口获取实时进度
    const res = await fetch('/video_generation_stream', {
      method: 'POST',
      body: payload
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let lastVideoPath = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;

      buffer += decoder.decode(value, { stream: true });
      
      const lines = buffer.split('\n\n');
      buffer = lines.pop() || '';

      for (const line of lines) {
        if (line.startsWith('data: ')) {
          try {
            const data = JSON.parse(line.slice(6));
            
            if (data.step === 'heartbeat') {
              continue;
            } else if (data.step === 'complete') {
              updateProgress(6, '视频生成完成！');
              await new Promise(resolve => setTimeout(resolve, 500));
              progressState.visible = false;
              showToast('视频生成成功', 'success');
              
              lastVideoPath = data.data?.video_path || '';
              if (videoRef.value && lastVideoPath) {
                const newSrc = lastVideoPath + '?t=' + new Date().getTime();
                videoRef.value.src = newSrc;
                videoRef.value.load();
                videoRef.value.play().catch(err => console.warn('自动播放受限:', err));
              }
            } else if (data.step === 'error') {
              progressState.visible = false;
              showToast('生成失败: ' + data.message, 'error');
            } else if (typeof data.step === 'number') {
              updateProgress(data.step, data.message);
            }
          } catch (parseErr) {
            console.warn('SSE 数据解析失败:', parseErr, line);
          }
        }
      }
    }
  } catch (error) {
    console.error('Fetch Error:', error);
    progressState.visible = false;
    showToast('网络连接失败，请检查后端服务', 'error');
  } finally {
    isGenerating.value = false;
  }
};

onMounted(() => {
  toggleGaussianTalkerOptions();
  toggleCloudConfig();
  setupFileDropzone('.file-input-group');
});

const setupFileDropzone = (selector) => {
  const dropZones = document.querySelectorAll(selector);

  dropZones.forEach(dropZone => {
    if (!dropZone) return;

    dropZone.addEventListener('dragover', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.border = '2px dashed #4CAF50';
    });

    dropZone.addEventListener('dragleave', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.border = '';
    });

    dropZone.addEventListener('drop', (e) => {
      e.preventDefault();
      e.stopPropagation();
      dropZone.style.border = '';

      if (e.dataTransfer.files.length > 0) {
        const file = e.dataTransfer.files[0];
        const fileInput = dropZone.querySelector('input[type="file"]');
        if (fileInput) {
          const dataTransfer = new DataTransfer();
          dataTransfer.items.add(file);
          fileInput.files = dataTransfer.files;

          const event = new Event('change', { bubbles: true });
          fileInput.dispatchEvent(event);
        }
      }
    });
  });
};
</script>

<style scoped>
/* 关键修复：不要写死暗色背景，否则日间模式无效 */
.video-gen-container {
  position: relative;
  min-height: 100vh;
  background: var(--bg);
  color: var(--fg);
  padding: 80px 40px 40px;
  font-family: var(--font-sans);
}

/* 顶部导航：背景跟随主题 */
.top-nav {
  position: fixed;
  top: 0;
  left: 0;
  width: 100%;
  height: 64px;
  background: color-mix(in srgb, var(--bg) 75%, transparent);
  backdrop-filter: blur(12px);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 40px;
  z-index: 100;
  border-bottom: 1px solid var(--panel-border);
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 8px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  transition: color 0.3s;
}

.back-btn:hover {
  color: var(--accent);
}

.system-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* 布局 */
.content-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 40px;
  max-width: 1400px;
  margin: 0 auto;
  position: relative;
  z-index: 10;
}

/* 面板通用头部 */
.panel-header {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 20px;
}

.panel-header h3 {
  font-size: 16px;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: var(--text-muted);
}

/* 视频预览区 */
.video-frame {
  position: relative;
  background: #000;
  border-radius: 4px;
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, 0.2);
  aspect-ratio: 16 / 9;
  display: flex;
  align-items: center;
  justify-content: center;
}

.main-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 2px;
  background: rgba(34, 211, 238, 0.1);
  z-index: 2;
  pointer-events: none;
  animation: scan 4s linear infinite;
}

.video-meta {
  margin-top: 15px;
  display: flex;
  gap: 20px;
}

/* label：不要写死深色底 + 淡字，改为主题变量 */
.label {
  font-size: 10px;
  color: var(--text-muted);
  background: color-mix(in srgb, var(--card) 70%, transparent);
  border: 1px solid var(--border);
  padding: 4px 8px;
  border-radius: 2px;
}

/* 表单区域：面板变量化，日间模式不发灰 */
.cyber-form {
  background: var(--panel-bg);
  backdrop-filter: blur(20px);
  border: 1px solid var(--panel-border);
  padding: 30px;
  border-radius: 12px;
}

.form-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.full-width {
  grid-column: span 2;
}

.form-group label {
  display: block;
  font-size: 13px;
  color: var(--text-muted);
  margin-bottom: 8px;
  font-weight: 500;
}

/* 输入框：关键修复，移除写死白字黑底 */
.input-wrapper input,
.select-wrapper select,
.textarea-wrapper textarea,
.file-display input,
.sub-group input {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  padding: 12px 16px;
  color: var(--fg);
  border-radius: 6px;
  transition: all 0.3s;
}

.input-wrapper input:focus,
.select-wrapper select:focus,
.textarea-wrapper textarea:focus,
.file-display input:focus,
.sub-group input:focus {
  outline: none;
  border-color: var(--accent);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.12);
}

.textarea-wrapper textarea {
  height: 100px;
  resize: none;
  font-family: var(--font-mono);
}

/* 复选框样式 */
.checkbox-wrapper {
  display: flex;
  align-items: center;
  gap: 10px;
}

.checkbox-wrapper input[type="checkbox"] {
  width: 18px;
  height: 18px;
  cursor: pointer;
}

.checkbox-label {
  margin: 0;
  cursor: pointer;
  color: var(--text-muted);
  font-size: 13px;
}

/* 文件上传区域 */
.file-input-group {
  position: relative;
  padding: 10px;
  border: 1px dashed var(--border);
  border-radius: 6px;
  transition: all 0.3s;
}

.file-input-group:hover {
  border-color: var(--accent);
}

.file-input {
  display: none;
}

.file-display {
  display: flex;
  gap: 10px;
  margin-bottom: 8px;
}

.browse-btn {
  padding: 10px 20px;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  color: var(--accent);
  border-radius: 6px;
  cursor: pointer;
  transition: all 0.3s;
  font-size: 13px;
  font-weight: 600;
  white-space: nowrap;
}

.browse-btn:hover {
  background: rgba(34, 211, 238, 0.2);
}

.file-hint {
  font-size: 11px;
  color: var(--text-muted);
  margin-top: 5px;
}

/* 云端配置和GaussianTalker选项：变量化 */
.cloud-config-group,
.gt-options {
  background: color-mix(in srgb, var(--panel-bg) 70%, transparent);
  padding: 15px;
  border-radius: 8px;
  border: 1px solid var(--panel-border);
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
}

.sub-group {
  display: flex;
  flex-direction: column;
}

.sub-group label {
  font-size: 12px;
  margin-bottom: 5px;
}

/* 按钮样式：主色使用 var(--accent) */
.submit-btn {
  margin-top: 30px;
  width: 100%;
  position: relative;
  padding: 16px;
  background: var(--accent);
  border: none;
  color: #000;
  font-weight: 800;
  text-transform: uppercase;
  letter-spacing: 2px;
  cursor: pointer;
  overflow: hidden;
  border-radius: 4px;
  transition: all 0.3s;
}

.btn-content {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  position: relative;
  z-index: 2;
}

.submit-btn:disabled {
  background: color-mix(in srgb, var(--card) 70%, transparent);
  color: var(--text-muted);
  cursor: not-allowed;
  border: 1px solid var(--border);
}

.submit-btn:not(:disabled):hover {
  filter: brightness(1.05);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.35);
  transform: translateY(-1px);
}

/* Toast 提示 */
.toast-msg {
  position: fixed;
  bottom: 40px;
  right: 40px;
  padding: 12px 24px;
  border-radius: 6px;
  font-size: 14px;
  z-index: 1000;
  backdrop-filter: blur(10px);
}

.toast-msg.success {
  background: rgba(16, 185, 129, 0.2);
  color: #10b981;
  border: 1px solid #10b981;
}

.toast-msg.error {
  background: rgba(239, 68, 68, 0.2);
  color: #ef4444;
  border: 1px solid #ef4444;
}

.toast-msg.info {
  background: rgba(34, 211, 238, 0.2);
  color: #22d3ee;
  border: 1px solid #22d3ee;
}

/* 顶部导航右侧容器：保持不破坏原有布局 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.appearance-inline {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

@media (max-width: 768px) {
  .nav-right { gap: 10px; }
  .appearance-inline { gap: 8px; }
}

@keyframes scan {
  from { top: 0; }
  to { top: 100%; }
}

/* 响应式 */
@media (max-width: 1024px) {
  .content-layout {
    grid-template-columns: 1fr;
  }
  .video-gen-container {
    padding: 80px 20px 20px;
  }
  .cloud-config-group,
  .gt-options {
    grid-template-columns: 1fr;
  }
  .file-display {
    flex-direction: column;
  }
  .browse-btn {
    width: 100%;
  }
  .top-nav {
    padding: 0 20px;
  }
}
</style>
