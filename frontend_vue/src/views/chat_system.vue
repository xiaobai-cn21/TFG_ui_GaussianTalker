<template>
  <div class="chat-system-container">
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

    <main class="chat-layout">
      <section class="interaction-panel">
        <div class="panel-header">
          <div class="header-icon-box">
            <MicIcon class="w-5 h-5 text-cyan-400" />
          </div>
          <div class="header-text">
            <h3>语音交互终端</h3>
            <p>VOICE INTERACTION TERMINAL</p>
          </div>
        </div>

        <div class="recorder-card cyber-glass">
          <div class="recorder-main">
            <div :class="['timer-display', { 'recording-active': isRecording }]">
              {{ formattedTime }}
            </div>

            <div class="visualizer-container">
              <div v-if="isRecording" :class="['wave-bars', { recording: isRecording }]">
                <div v-for="i in 18" :key="i" class="bar" :style="{ animationDelay: `${i * 0.05}s` }"></div>
              </div>
              <div v-else class="wave-idle">AWAITING VOICE INPUT...</div>
            </div>

            <button
              @click="toggleRecording"
              :class="['record-action-btn', { 'is-recording': isRecording }]"
            >
              <div class="btn-glow"></div>
              <CircleIcon v-if="!isRecording" class="fill-current w-5 h-5" />
              <SquareIcon v-else class="fill-current w-5 h-5" />
              <span>{{ isRecording ? '停止监听' : '开始监听' }}</span>
            </button>

            <!-- 分隔线 -->
            <div class="divider">
              <span>或</span>
            </div>

            <!-- 文件上传按钮 -->
            <button
              @click="triggerFileUpload"
              :class="['upload-action-btn', { 'is-uploading': isUploading }]"
            >
              <UploadIcon class="fill-current w-5 h-5 mr-2" />
              <span>{{ isUploading ? '上传中...' : '上传音频文件' }}</span>
            </button>

            <!-- 隐藏的文件输入 -->
            <input
              type="file"
              ref="audioFileInput"
              accept="audio/*"
              class="hidden"
              @change="handleAudioUpload"
            >

            <div class="format-hint">
              支持 mp3、wav、m4a 等格式
            </div>
          </div>

          <div class="status-footer">
            <div class="status-indicator">
              <div :class="['dot', statusColorClass]"></div>
              <span class="status-text">{{ statusText }}</span>
            </div>
          </div>
        </div>

        <div class="video-preview-wrapper cyber-border">
          <div class="video-overlay">
            <div class="scanline"></div>
            <div class="corner-tag">LIVE_FEED</div>
          </div>
          <video
            id="chatVideo"
            ref="videoRef"
            class="cyber-video"
            :src="videoSrc"
            autoplay
            muted
            playsinline
            controls
          >
            您的浏览器不支持视频播放。
          </video>
        </div>

        <!-- TTS音频播放器 -->
        <div class="audio-player-container cyber-glass">
          <div class="audio-header">
            <Volume2Icon class="w-4 h-4 text-cyan-400" />
            <span>TTS语音输出</span>
          </div>
          <audio
            id="ttsAudio"
            ref="ttsAudioRef"
            controls
            class="cyber-audio"
            :src="ttsSrc"
          ></audio>
        </div>

        <!-- 文本输出区域 -->
        <div class="text-outputs cyber-glass">
          <div class="text-output-item">
            <div class="text-label">
              <TypeIcon class="w-3 h-3 mr-2" />
              <span>识别文本：</span>
            </div>
            <div class="text-content" id="recognizedText">
              {{ recognizedText || '（待识别）' }}
            </div>
          </div>
          <div class="text-output-item">
            <div class="text-label">
              <BrainIcon class="w-3 h-3 mr-2" />
              <span>AI回复：</span>
            </div>
            <div class="text-content ai-text" id="aiText">
              {{ aiText || '（待生成）' }}
            </div>
          </div>
        </div>
      </section>

      <section class="config-panel">
        <div class="panel-header">
          <div class="header-icon-box">
            <SettingsIcon class="w-5 h-5 text-cyan-400" />
          </div>
          <div class="header-text">
            <h3>协议参数配置</h3>
            <p>SYSTEM PROTOCOL CONFIG</p>
          </div>
        </div>

        <div class="cyber-form cyber-glass">
          <form @submit.prevent="handleChatSubmit" class="form-stack">
            <!-- 模型名称 -->
            <div class="form-group">
              <label>核心驱动模型 / MODEL</label>
              <div class="select-wrapper">
                <select v-model="formData.model_name" @change="toggleGaussianTalkerFields">
                  <option value="">不使用数字人（仅语音）</option>
                  <option value="SyncTalk">SyncTalk</option>
                  <option value="GaussianTalker">GaussianTalker</option>
                </select>
              </div>
            </div>

            <!-- 模型目录地址 -->
            <div class="form-group">
              <label>资源指纹 / MODEL_PATH</label>
              <input
                type="text"
                v-model="formData.model_param"
                placeholder="请输入模型目录路径"
              />
            </div>

            <!-- 语音克隆参考音频 -->
            <div class="form-group">
              <label>音色克隆 / VOICE_CLONE</label>
              <div class="file-input-wrapper">
                <input
                  type="file"
                  ref="refAudioInput"
                  accept="audio/*"
                  @change="handleRefAudioChange"
                  class="file-input"
                />
                <div class="file-input-display">
                  <input
                    type="text"
                    v-model="formData.ref_audio"
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
                  上传参考音频以克隆数字人的声音
                </div>
              </div>
            </div>

            <!-- GPU选择 -->
            <div class="form-group">
              <label>处理单元 / GPU_SELECT</label>
              <div class="select-wrapper">
                <select v-model="formData.gpu_choice" @change="toggleCloudConfig">
                  <option value="GPU0">GPU 0</option>
                  <option value="GPU1">GPU 1</option>
                  <option value="CPU">CPU</option>
                  <option value="cloud">Cloud (AutoDL)</option>
                </select>
              </div>
            </div>

            <!-- 云端SSH配置 -->
            <div v-if="showCloudConfig" class="form-group cloud-config-group">
              <div class="form-subgroup">
                <label>SSH端口号</label>
                <input
                  type="number"
                  v-model="formData.ssh_port"
                  placeholder="40258"
                />
              </div>
              <div class="form-subgroup">
                <label>SSH密码</label>
                <input
                  type="password"
                  v-model="formData.ssh_password"
                  placeholder="83WncIL5CoYB"
                />
              </div>
            </div>

            <!-- GaussianTalker专用参数 -->
            <div v-if="showGaussianTalkerFields" class="form-group gaussian-fields">
              <div class="form-subgroup">
                <label>Batch Size</label>
                <input
                  type="number"
                  v-model="formData.batch_size"
                  min="1"
                  placeholder="128"
                />
              </div>
              <div class="form-subgroup">
                <label>Iteration</label>
                <input
                  type="number"
                  v-model="formData.iteration"
                  min="1"
                  placeholder="10000"
                />
              </div>
            </div>

            <!-- 对话API选择 -->
            <div class="form-group">
              <label>逻辑引擎 / LLM_ENGINE</label>
              <div class="select-wrapper">
                <select v-model="formData.api_choice">
                  <option value="openai">OpenAI API</option>
                  <option value="azure">Azure Speech API</option>
                </select>
              </div>
            </div>

            <!-- 手动触发按钮 -->
            <button
              type="submit"
              :disabled="isProcessing"
              class="chat-submit-btn group"
            >
              <div class="submit-bg"></div>
              <Loader2Icon v-if="isProcessing" class="animate-spin w-5 h-5 mr-2" />
              <MessageSquareIcon v-else class="w-5 h-5 mr-2 group-hover:scale-110 transition-transform" />
              <span>{{ isProcessing ? '处理中...' : '执行对话协议' }}</span>
            </button>

            <!-- 自动提示 -->
            <div class="auto-hint">
              <InfoIcon class="w-4 h-4" />
              <span>左侧录音或上传音频后将自动开始对话</span>
            </div>
          </form>

          <div class="form-footer-info">
            <ShieldCheckIcon class="w-3 h-3 text-cyan-500/40" />
            <span>SECURE CONNECTION ENCRYPTED</span>
          </div>
        </div>
      </section>
    </main>
  </div>
</template>

<script setup>
import ThemeToggle from '../components/ThemeToggle.vue'
import FontSelector from '../components/FontSelector.vue'

import { ref, reactive, computed, onUnmounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowLeft as ArrowLeftIcon,
  Mic as MicIcon,
  Settings as SettingsIcon,
  Circle as CircleIcon,
  Square as SquareIcon,
  MessageSquare as MessageSquareIcon,
  Loader2 as Loader2Icon,
  ShieldCheck as ShieldCheckIcon,
  Upload as UploadIcon,
  Volume2 as Volume2Icon,
  Type as TypeIcon,
  Brain as BrainIcon,
  Info as InfoIcon
} from 'lucide-vue-next';

const router = useRouter();
const videoRef = ref(null);
const ttsAudioRef = ref(null);
const audioFileInput = ref(null);
const refAudioInput = ref(null);
const sessionId = ref(Math.random().toString(36).substr(2, 9).toUpperCase());

const isRecording = ref(false);
const isProcessing = ref(false);
const isUploading = ref(false);
const showCloudConfig = ref(false);
const showGaussianTalkerFields = ref(false);
const statusText = ref('SYSTEM READY');
const recognizedText = ref('');
const aiText = ref('');
const timer = ref(0);
let timerInterval = null;

const videoSrc = ref('/static/videos/sample.mp4');
const ttsSrc = ref('');

const formData = reactive({
  model_name: '',
  model_param: '',
  ref_audio: '',
  gpu_choice: 'GPU0',
  ssh_port: 40258,
  ssh_password: '83WncIL5CoYB',
  batch_size: 128,
  iteration: 10000,
  api_choice: 'openai'
});

let mediaRecorder = null;
let audioChunks = [];

const formattedTime = computed(() => {
  const mins = Math.floor(timer.value / 60);
  const secs = timer.value % 60;
  return `${mins.toString().padStart(2, '0')}:${secs.toString().padStart(2, '0')}`;
});

const statusColorClass = computed(() => {
  if (isRecording.value) return 'bg-rose-500 shadow-[0_0_10px_#f43f5e]';
  if (isProcessing.value) return 'bg-amber-500 shadow-[0_0_10px_#f59e0b]';
  return 'bg-cyan-500 shadow-[0_0_10px_#22d3ee]';
});

const goBack = () => {
  if (router) router.push('/');
  else window.location.href = '/';
};

const toggleGaussianTalkerFields = () => {
  showGaussianTalkerFields.value = formData.model_name === 'GaussianTalker';
};

const toggleCloudConfig = () => {
  showCloudConfig.value = formData.gpu_choice === 'cloud';
};

const triggerFileUpload = () => {
  audioFileInput.value?.click();
};

const triggerRefAudioUpload = () => {
  refAudioInput.value?.click();
};

const handleRefAudioChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  isUploading.value = true;
  statusText.value = '上传参考音频...';

  try {
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);
    uploadFormData.append('type', 'audio');

    const response = await fetch('/upload_file', {
      method: 'POST',
      body: uploadFormData
    });

    const data = await response.json();
    if (data.status === 'success') {
      formData.ref_audio = (data.file_path || '').replace(/^\.\//, '/');
      statusText.value = '参考音频上传成功';
    } else {
      statusText.value = '上传失败';
      alert('参考音频上传失败: ' + data.message);
    }
  } catch (error) {
    console.error('上传错误:', error);
    statusText.value = '上传错误';
    alert('上传失败: ' + error.message);
  } finally {
    isUploading.value = false;
  }
};

const handleAudioUpload = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  isUploading.value = true;
  statusText.value = '上传音频文件...';

  try {
    const uploadFormData = new FormData();
    uploadFormData.append('audio', file, 'input.wav');

    const response = await fetch('/save_audio', {
      method: 'POST',
      body: uploadFormData
    });

    const data = await response.json();
    if (data.status === 'success') {
      statusText.value = '音频上传成功';
      setTimeout(autoStartChat, 500);
    } else {
      statusText.value = '上传失败';
      alert('音频上传失败: ' + data.message);
    }
  } catch (error) {
    console.error('上传错误:', error);
    statusText.value = '上传错误';
    alert('上传失败: ' + error.message);
  } finally {
    isUploading.value = false;
  }
};

const autoStartChat = () => {
  statusText.value = '正在处理对话...';
  processChat();
};

const toggleRecording = async () => {
  if (!isRecording.value) {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorder = new MediaRecorder(stream);
      audioChunks = [];

      mediaRecorder.ondataavailable = (e) => audioChunks.push(e.data);

      mediaRecorder.onstop = async () => {
        const audioBlob = new Blob(audioChunks, { type: 'audio/wav' });
        const postData = new FormData();
        postData.append('audio', audioBlob, 'input.wav');

        statusText.value = '上传录音...';
        try {
          const res = await fetch('/save_audio', {
            method: 'POST',
            body: postData
          });
          const data = await res.json();

          if (data.status === 'success') {
            statusText.value = '录音保存成功';
            setTimeout(autoStartChat, 500);
          } else {
            statusText.value = '保存失败';
          }
        } catch (err) {
          statusText.value = '网络错误';
          console.error('保存录音错误:', err);
        }
        stream.getTracks().forEach(t => t.stop());
      };

      mediaRecorder.start();
      isRecording.value = true;
      statusText.value = '录音中...';
      startTimer();
    } catch (err) {
      console.error('获取麦克风权限失败:', err);
      statusText.value = '麦克风权限被拒绝';
    }
  } else {
    if (mediaRecorder) mediaRecorder.stop();
    isRecording.value = false;
    stopTimer();
  }
};

const startTimer = () => {
  timer.value = 0;
  timerInterval = setInterval(() => timer.value++, 1000);
};

const stopTimer = () => {
  if (timerInterval) clearInterval(timerInterval);
};

const processChat = async () => {
  isProcessing.value = true;
  statusText.value = '处理对话中...';

  const payload = new FormData();
  Object.keys(formData).forEach(key => {
    if (formData[key] !== undefined && formData[key] !== null) {
      payload.append(key, formData[key]);
    }
  });

  try {
    const res = await fetch('/chat_system', {
      method: 'POST',
      body: payload
    });

    const data = await res.json();

    if (data.status === 'success') {
      recognizedText.value = data.recognized_text || '（无识别文本）';
      aiText.value = data.ai_text || '（无AI回复）';

      if (data.tts_audio_url) {
        ttsSrc.value = data.tts_audio_url + '?t=' + Date.now();
        if (ttsAudioRef.value) {
          ttsAudioRef.value.load();
          ttsAudioRef.value.play().catch(() => {});
        }
      }

      if (data.video_path) {
        videoSrc.value = data.video_path + '?t=' + Date.now();
        if (videoRef.value) {
          videoRef.value.load();
          videoRef.value.play().catch(() => {});
        }
      }

      statusText.value = '对话完成';
    } else {
      statusText.value = '对话失败';
      alert('对话失败: ' + (data.message || '未知错误'));
    }
  } catch (err) {
    console.error('处理错误:', err);
    statusText.value = '请求失败';
    alert('请求失败: ' + err.message);
  } finally {
    isProcessing.value = false;
  }
};

const handleChatSubmit = async () => {
  if (isProcessing.value) return;
  await processChat();
};

toggleGaussianTalkerFields();
toggleCloudConfig();

onUnmounted(() => {
  stopTimer();
  if (mediaRecorder && isRecording.value) {
    mediaRecorder.stop();
  }
});
</script>

<style scoped>
/* =========================
   Chat System - Theme Ready
   ========================= */

/* 页面根：不写死暗色，全部跟随主题变量 */
.chat-system-container {
  position: relative;
  min-height: 100vh;
  background: var(--bg);
  color: var(--fg);
  padding: 100px 40px 40px;
  font-family: var(--font-sans);
  overflow-x: hidden;
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

/* 左侧返回按钮 */
.back-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: transparent;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1px;
  transition: color 0.25s ease;
}

.back-btn:hover {
  color: var(--accent);
}

/* 右侧系统信息 */
.system-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

/* 顶部导航右侧容器 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 主题 + 字体并排 */
.appearance-inline {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

/* 主体布局 */
.chat-layout {
  max-width: 1200px;
  margin: 0 auto;
  display: grid;
  grid-template-columns: 1.2fr 400px;
  gap: 30px;
  position: relative;
  z-index: 10;
}

/* 面板头部 */
.panel-header {
  display: flex;
  align-items: center;
  gap: 16px;
  margin-bottom: 24px;
}

.header-icon-box {
  padding: 10px;
  background: rgba(34, 211, 238, 0.1);
  border-radius: 8px;
  border: 1px solid rgba(34, 211, 238, 0.2);
}

.header-text h3 {
  font-size: 1.25rem;
  font-weight: 800;
  color: var(--fg);
  margin: 0;
  letter-spacing: 1px;
}

.header-text p {
  font-size: 0.65rem;
  color: var(--text-muted);
  letter-spacing: 3px;
  margin: 2px 0 0;
}

/* ===== 卡片/面板：变量化，日间不发灰 ===== */
.cyber-glass {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  border-radius: 16px;
}

/* 录音卡片 */
.recorder-card {
  padding: 30px;
  margin-bottom: 30px;
  position: relative;
  overflow: hidden;
}

.recorder-main {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 20px;
}

.timer-display {
  font-size: 48px;
  font-weight: 100;
  color: var(--text-muted);
  font-family: var(--font-mono);
  letter-spacing: -2px;
}

.recording-active {
  color: #f43f5e;
  text-shadow: 0 0 30px rgba(244, 63, 94, 0.4);
}

/* 波形/提示 */
.visualizer-container {
  height: 50px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.wave-bars {
  display: flex;
  align-items: center;
  gap: 3px;
}

.bar {
  width: 3px;
  height: 15px;
  background: var(--accent);
  border-radius: 4px;
  animation: wave 0.8s ease-in-out infinite;
}

.is-recording .bar {
  background: #f43f5e;
}

@keyframes wave {
  0%, 100% { height: 10px; opacity: 0.5; }
  50% { height: 40px; opacity: 1; }
}

.wave-idle {
  font-size: 11px;
  color: var(--text-muted);
  letter-spacing: 4px;
  font-family: var(--font-mono);
}

/* 录音/上传按钮：不写死白字黑底，改为变量化 */
.record-action-btn,
.upload-action-btn {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 16px 30px;
  border-radius: 12px;
  border: 1px solid var(--border);
  background: var(--card);
  color: var(--fg);
  font-weight: 600;
  font-size: 14px;
  cursor: pointer;
  transition: all 0.25s ease;
  overflow: hidden;
  width: 100%;
  max-width: 280px;
}

.record-action-btn:hover:not(.is-recording) {
  border-color: var(--accent);
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.18);
  transform: translateY(-2px);
}

.record-action-btn.is-recording {
  background: #f43f5e;
  color: #fff;
  border-color: #f43f5e;
  box-shadow: 0 0 20px rgba(244, 63, 94, 0.35);
}

.upload-action-btn {
  border-style: dashed;
  color: var(--text-muted);
}

.upload-action-btn:hover {
  border-color: var(--accent);
  color: var(--accent);
  box-shadow: 0 0 18px rgba(34, 211, 238, 0.12);
}

.upload-action-btn.is-uploading {
  background: color-mix(in srgb, var(--card) 70%, transparent);
  color: #f59e0b;
  border-color: #f59e0b;
}

/* 分隔线 */
.divider {
  margin: 10px 0;
  display: flex;
  align-items: center;
  width: 100%;
  max-width: 280px;
  color: var(--text-muted);
  font-size: 12px;
}

.divider::before,
.divider::after {
  content: '';
  flex: 1;
  border-bottom: 1px solid var(--border);
}

.divider span {
  padding: 0 15px;
}

.format-hint {
  font-size: 11px;
  color: var(--text-muted);
  text-align: center;
  margin-top: 5px;
}

/* 状态栏 */
.status-footer {
  margin-top: 20px;
  padding-top: 15px;
  border-top: 1px solid var(--panel-border);
}

.status-indicator {
  display: flex;
  align-items: center;
  gap: 12px;
}

.status-text {
  font-size: 11px;
  font-family: var(--font-mono);
  color: var(--text-muted);
  letter-spacing: 1px;
}

.dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

/* 隐藏 input */
.hidden { display: none; }

/* 视频区域（保持黑色视频底） */
.video-preview-wrapper {
  position: relative;
  background: #000;
  border-radius: 16px;
  overflow: hidden;
  border: 1px solid rgba(34, 211, 238, 0.2);
  box-shadow: 0 10px 40px rgba(0, 0, 0, 0.5);
  margin-bottom: 20px;
}

.video-overlay {
  position: absolute;
  inset: 0;
  z-index: 5;
  pointer-events: none;
}

.scanline {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: linear-gradient(to bottom, transparent, rgba(34, 211, 238, 0.05) 50%, transparent);
  animation: scanY 6s linear infinite;
}

@keyframes scanY {
  from { transform: translateY(-100%); }
  to { transform: translateY(100%); }
}

.corner-tag {
  position: absolute;
  top: 15px;
  right: 15px;
  font-size: 10px;
  color: var(--accent);
  font-family: var(--font-mono);
  background: rgba(0, 0, 0, 0.6);
  padding: 4px 8px;
  border-radius: 4px;
  border: 1px solid rgba(34, 211, 238, 0.3);
}

.cyber-video {
  width: 100%;
  aspect-ratio: 16 / 9;
  display: block;
}

/* 音频播放器卡片 */
.audio-player-container {
  padding: 15px;
  margin-bottom: 20px;
}

.audio-header {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 10px;
  font-size: 12px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

.cyber-audio {
  width: 100%;
  border-radius: 8px;
}

/* 文本输出卡片 */
.text-outputs {
  padding: 20px;
}

.text-output-item {
  margin-bottom: 15px;
}

.text-output-item:last-child {
  margin-bottom: 0;
}

.text-label {
  display: flex;
  align-items: center;
  font-size: 11px;
  color: var(--text-muted);
  margin-bottom: 5px;
  letter-spacing: 1px;
}

/* 文本框：不要写死黑底白字 */
.text-content {
  font-size: 14px;
  color: var(--fg);
  line-height: 1.5;
  padding: 10px 12px;
  background: var(--card);
  border-radius: 8px;
  border: 1px solid var(--border);
  min-height: 40px;
  word-break: break-word;
}

.ai-text {
  color: var(--accent);
}

/* 右侧表单面板 */
.cyber-form {
  padding: 25px;
  border-radius: 16px;
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
}

.form-stack {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.form-group label {
  display: block;
  font-size: 11px;
  font-weight: 600;
  color: var(--text-muted);
  margin-bottom: 8px;
  letter-spacing: 1px;
}

/* 输入框：关键修复，移除写死白字黑底 */
.form-group select,
.form-group input,
.file-input-display input,
.form-subgroup input {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  padding: 12px 14px;
  color: var(--fg);
  border-radius: 10px;
  font-size: 13px;
  outline: none;
  transition: all 0.25s ease;
  box-sizing: border-box;
}

.form-group select:focus,
.form-group input:focus,
.file-input-display input:focus,
.form-subgroup input:focus {
  border-color: var(--accent);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.12);
}

.file-input-wrapper { position: relative; }
.file-input { display: none; }

.file-input-display {
  display: flex;
  gap: 10px;
  margin-bottom: 5px;
}

.browse-btn {
  padding: 0 20px;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  color: var(--accent);
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.25s ease;
  font-size: 12px;
  font-weight: 600;
  white-space: nowrap;
}

.browse-btn:hover {
  background: rgba(34, 211, 238, 0.2);
}

.file-hint {
  font-size: 10px;
  color: var(--text-muted);
  margin-top: 3px;
}

/* 云端/GT 参数区域：变量化 */
.cloud-config-group,
.gaussian-fields {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 15px;
  padding: 15px;
  background: color-mix(in srgb, var(--panel-bg) 70%, transparent);
  border-radius: 12px;
  border: 1px solid var(--panel-border);
}

.form-subgroup {
  display: flex;
  flex-direction: column;
}

.form-subgroup label {
  font-size: 10px;
  margin-bottom: 5px;
}

/* 提交按钮 */
.chat-submit-btn {
  margin-top: 10px;
  width: 100%;
  padding: 16px;
  background: var(--accent);
  color: #000;
  border: none;
  border-radius: 12px;
  font-weight: 800;
  font-size: 14px;
  letter-spacing: 1px;
  display: flex;
  align-items: center;
  justify-content: center;
  cursor: pointer;
  transition: all 0.25s ease;
  position: relative;
  overflow: hidden;
}

.chat-submit-btn:hover:not(:disabled) {
  filter: brightness(1.05);
  transform: translateY(-2px);
  box-shadow: 0 0 26px rgba(34, 211, 238, 0.35);
}

.chat-submit-btn:disabled {
  background: color-mix(in srgb, var(--card) 70%, transparent);
  color: var(--text-muted);
  cursor: not-allowed;
  border: 1px solid var(--border);
}

/* 自动提示 */
.auto-hint {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 10px;
  background: color-mix(in srgb, var(--panel-bg) 70%, transparent);
  border-radius: 10px;
  border: 1px solid var(--panel-border);
  font-size: 11px;
  color: var(--accent);
  margin-top: 10px;
}

.form-footer-info {
  margin-top: 20px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  font-size: 10px;
  color: var(--text-muted);
  letter-spacing: 1px;
}

/* 顶栏小屏适配 */
@media (max-width: 768px) {
  .nav-right { gap: 10px; }
  .appearance-inline { gap: 8px; }
}

/* 响应式：布局变单列 */
@media (max-width: 1024px) {
  .chat-layout {
    grid-template-columns: 1fr;
  }
  .chat-system-container {
    padding: 80px 20px 20px;
  }
  .cloud-config-group,
  .gaussian-fields {
    grid-template-columns: 1fr;
  }
  .top-nav {
    padding: 0 20px;
  }
}
</style>

