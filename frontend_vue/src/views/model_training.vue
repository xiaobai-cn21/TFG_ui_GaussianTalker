<template>
  <div class="training-container">
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

    <div class="content-wrapper">
      <header class="page-header">
        <CpuIcon class="header-icon" />
        <div class="title-group">
          <h2>模型训练中心</h2>
          <p>Model Training Laboratory</p>
        </div>
      </header>

      <div class="grid-layout">
        <section class="monitor-section">
          <div class="video-frame">
            <div class="video-overlay">
              <div class="scanline"></div>
              <div class="rec-dot"></div>
              <span class="corner-text top-left">REC [00:42:15]</span>
              <span class="corner-text bottom-right">GPU_RENDER_ACTIVE</span>
            </div>

            <video
              id="trainVideo"
              ref="videoRef"
              class="main-video"
              controls
              :src="currentVideoSrc"
            >
              您的浏览器不支持视频播放
            </video>
          </div>

          <div class="status-indicator">
            <div class="status-item">
              <span class="label">渲染引擎</span>
              <span class="value">{{ modelStatus }}</span>
            </div>
            <div class="status-item">
              <span class="label">帧率</span>
              <span class="value">60 FPS</span>
            </div>
          </div>
        </section>

        <section class="control-section">
          <form @submit.prevent="handleTraining" class="cyber-form">
            <div class="input-grid">
              <!-- 模型选择 -->
              <div class="form-group">
                <label><BoxIcon class="inline w-4 h-4 mr-1" /> 模型架构</label>
                <select v-model="form.model_choice" @change="toggleGaussianTalkerOptions">
                  <option value="SyncTalk">SyncTalk</option>
                  <option value="GaussianTalker">GaussianTalker</option>
                </select>
              </div>

              <!-- GPU选择 -->
              <div class="form-group">
                <label><ZapIcon class="inline w-4 h-4 mr-1" /> GPU 算力分配</label>
                <div class="gpu-selector">
                  <div
                    v-for="gpu in ['GPU0', 'GPU1', 'cloud']"
                    :key="gpu"
                    :class="['gpu-card', form.gpu_choice === gpu ? 'active' : '']"
                    @click="form.gpu_choice = gpu; toggleCloudConfig()"
                  >
                    {{ gpu === 'cloud' ? 'Cloud (AutoDL)' : gpu }}
                  </div>
                </div>
              </div>

              <!-- 参考视频/图像上传 -->
              <div class="form-group">
                <label><LinkIcon class="inline w-4 h-4 mr-1" /> 参考资源</label>
                <div class="file-input-group">
                  <input
                    type="file"
                    ref="refFileInput"
                    accept="video/*,image/*"
                    @change="handleRefFileChange"
                    class="file-input"
                  />
                  <div class="file-display">
                    <input
                      type="text"
                      v-model="form.ref_video"
                      placeholder="或输入文件路径"
                      readonly
                    />
                    <button
                      type="button"
                      @click="triggerFileUpload"
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
              <div v-if="showCloudConfig" class="form-group cloud-config">
                <div class="sub-group">
                  <label>SSH端口号</label>
                  <input
                    type="number"
                    v-model="form.ssh_port"
                    placeholder="40258"
                  />
                </div>
                <div class="sub-group">
                  <label>SSH密码</label>
                  <input
                    type="password"
                    v-model="form.ssh_password"
                    placeholder="83WncIL5CoYB"
                  />
                </div>
                <div v-if="showCloudConfig && form.model_choice === 'GaussianTalker'" class="cloud-warning">
                  ⚠️ 云端训练强制需要上传au.csv文件
                </div>
              </div>

              <!-- Epoch -->
              <div class="form-group">
                <label><RefreshCwIcon class="inline w-4 h-4 mr-1" /> Epoch (训练轮数)</label>
                <div class="range-wrapper">
                  <input type="range" v-model="form.epoch" min="1" max="100">
                  <span class="range-val">{{ form.epoch }}</span>
                </div>
              </div>

              <!-- GaussianTalker专用参数 -->
              <div v-if="showGaussianTalkerOptions" class="form-group gt-options">
                <div class="sub-group">
                  <label>Iterations (训练迭代次数)</label>
                  <input
                    type="number"
                    v-model="form.iterations"
                    min="1000"
                    step="1000"
                    placeholder="10000"
                  />
                </div>
                <div class="sub-group">
                  <label>配置文件</label>
                  <input
                    type="text"
                    v-model="form.config"
                    placeholder="arguments/64_dim_1_transformer.py"
                  />
                </div>

                <!-- 跳过预处理选项 -->
                <div class="skip-preprocess-group">
                  <div class="skip-checkbox">
                    <input
                      type="checkbox"
                      id="skip_preprocess"
                      v-model="form.skip_preprocess"
                      @change="toggleSkipPreprocess"
                    />
                    <label for="skip_preprocess">跳过数据预处理（使用云端已有数据）</label>
                  </div>
                  <div v-if="form.skip_preprocess" class="model-name-input">
                    <label>模型名称（云端已存在的数据目录名）</label>
                    <input
                      type="text"
                      v-model="form.model_name"
                      placeholder="如：May、obama、Jae-in"
                      required
                    />
                    <div class="skip-hint">
                      ⚠️ 请确保云端已存在该模型的预处理数据
                    </div>
                  </div>
                </div>

                <!-- AU文件上传 -->
                <div v-if="!form.skip_preprocess" class="au-upload-group">
                  <div class="au-checkbox">
                    <input
                      type="checkbox"
                      id="use_manual_au"
                      v-model="form.use_manual_au"
                      @change="toggleAuUpload"
                    />
                    <label for="use_manual_au">手动上传AU文件 (如果OpenFace封装失败)</label>
                  </div>
                  <div v-if="showAuUpload" class="au-file-input">
                    <input
                      type="file"
                      ref="auFileInput"
                      accept=".csv"
                      @change="handleAuFileChange"
                      class="file-input"
                    />
                    <button
                      type="button"
                      @click="triggerAuUpload"
                      class="browse-btn small"
                    >
                      选择CSV文件
                    </button>
                  </div>
                </div>
              </div>

              <!-- 自定义参数 -->
              <div class="form-group full-width">
                <label><TerminalIcon class="inline w-4 h-4 mr-1" /> 自定义训练脚本参数</label>
                <textarea
                  v-model="form.custom_params"
                  placeholder="--lr 0.001 --batch_size 16..."
                ></textarea>
              </div>
            </div>

            <button type="submit" :class="['train-btn', isTraining ? 'loading' : '']" :disabled="isTraining">
              <span v-if="!isTraining">START TRAINING!</span>
              <span v-else class="flex items-center">
                <Loader2Icon class="animate-spin mr-2" /> 训练任务下发中...
              </span>
            </button>
          </form>
        </section>
      </div>
    </div>

    <!-- 进度条弹窗 -->
    <ProgressSteps
      :visible="progressState.visible"
      title="模型训练中"
      subtitle="MODEL TRAINING IN PROGRESS"
      :steps="progressState.steps"
      :current-step="progressState.currentStep"
      :status-message="progressState.statusMessage"
      :estimated-time="progressState.estimatedTime"
      :cancellable="false"
    />
  </div>
</template>

<script setup>
/** 外观控件：主题 + 字体（与 chat_system 对齐） */
import ThemeToggle from '../components/ThemeToggle.vue'
import FontSelector from '../components/FontSelector.vue'
import ProgressSteps from '../components/ProgressSteps.vue'

import { ref, reactive, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import {
  ArrowLeft as ArrowLeftIcon,
  Cpu as CpuIcon,
  Box as BoxIcon,
  Zap as ZapIcon,
  Link as LinkIcon,
  RefreshCw as RefreshCwIcon,
  Terminal as TerminalIcon,
  Loader2 as Loader2Icon
} from 'lucide-vue-next';

const router = useRouter();
const videoRef = ref(null);
const refFileInput = ref(null);
const auFileInput = ref(null);

const isTraining = ref(false);
const showCloudConfig = ref(false);
const showGaussianTalkerOptions = ref(false);
const showAuUpload = ref(false);
const currentVideoSrc = ref('/static/videos/sample.mp4');
const auFile = ref(null);

const sessionId = ref(Math.random().toString(36).substr(2, 9).toUpperCase());

const form = reactive({
  model_choice: 'SyncTalk',
  gpu_choice: 'GPU0',
  ref_video: '',
  ssh_port: 40258,
  ssh_password: '83WncIL5CoYB',
  epoch: 10,
  iterations: 10000,
  config: 'arguments/64_dim_1_transformer.py',
  use_manual_au: false,
  custom_params: '',
  skip_preprocess: false,  // 跳过数据预处理
  model_name: ''           // 跳过预处理时使用的模型名称
});

// 进度条相关状态
const progressState = reactive({
  visible: false,
  currentStep: 0,
  statusMessage: '',
  estimatedTime: '',
  steps: [
    { label: '环境准备', detail: '初始化训练环境' },
    { label: '数据预处理', detail: '处理输入视频/图像' },
    { label: '特征提取', detail: '提取面部特征点' },
    { label: 'AU提取', detail: '提取Action Units' },
    { label: '模型初始化', detail: '加载预训练权重' },
    { label: '训练进行中', detail: '迭代优化模型' },
    { label: '模型保存', detail: '保存训练结果' },
    { label: '完成', detail: '训练完成' }
  ]
});

const updateProgress = (step, message, time = '') => {
  progressState.currentStep = step;
  progressState.statusMessage = message;
  progressState.estimatedTime = time;
};

const modelStatus = computed(() => {
  const models = {
    'modelA': 'Model A Engine',
    'modelB': 'Model B Engine',
    'SyncTalk': 'SyncTalk V4',
    'GaussianTalker': 'GaussianTalker Pro'
  };
  return models[form.model_choice] || 'Neural-Link V4';
});

const goBack = () => {
  if (router) router.push('/');
  else window.location.href = '/';
};

const toggleGaussianTalkerOptions = () => {
  showGaussianTalkerOptions.value = form.model_choice === 'GaussianTalker';
  if (showGaussianTalkerOptions.value && form.gpu_choice === 'cloud') {
    form.use_manual_au = true;
    showAuUpload.value = true;
  }
};

const toggleCloudConfig = () => {
  showCloudConfig.value = form.gpu_choice === 'cloud';
  if (showCloudConfig.value && form.model_choice === 'GaussianTalker') {
    form.use_manual_au = true;
    showAuUpload.value = true;
  }
};

const toggleAuUpload = () => {
  showAuUpload.value = form.use_manual_au;
};

const toggleSkipPreprocess = () => {
  // 如果跳过预处理，清空视频路径（不需要上传）
  if (form.skip_preprocess) {
    form.use_manual_au = false;
    showAuUpload.value = false;
  }
};

const triggerFileUpload = () => {
  refFileInput.value?.click();
};

const triggerAuUpload = () => {
  auFileInput.value?.click();
};

const handleRefFileChange = async (event) => {
  const file = event.target.files[0];
  if (!file) return;

  if (file.type.startsWith('video/') || file.type.startsWith('image/')) {
    const objectUrl = URL.createObjectURL(file);
    currentVideoSrc.value = objectUrl;
    if (videoRef.value) {
      videoRef.value.src = objectUrl;
      videoRef.value.load();
      videoRef.value.play().catch(e => console.log('自动播放可能被阻止:', e));
    }
  }

  try {
    const uploadFormData = new FormData();
    uploadFormData.append('file', file);
    uploadFormData.append('type', file.type.startsWith('video/') ? 'video' : 'image');

    const uploadRes = await fetch('/upload_file', {
      method: 'POST',
      body: uploadFormData
    });

    const uploadData = await uploadRes.json();
    if (uploadData.status === 'success') {
      form.ref_video = uploadData.file_path;
      console.log('文件上传成功:', uploadData.file_path);
    } else {
      alert('文件上传失败: ' + uploadData.message);
    }
  } catch (err) {
    console.error('上传错误:', err);
    alert('上传失败: ' + err.message);
  }
};

const handleAuFileChange = (event) => {
  const file = event.target.files[0];
  if (file && file.name.endsWith('.csv')) {
    auFile.value = file;
  }
};

const handleTraining = async () => {
  if (isTraining.value) return;

  // 验证：如果跳过预处理，必须提供模型名称
  if (form.skip_preprocess && !form.model_name.trim()) {
    alert('跳过预处理时必须提供模型名称');
    return;
  }

  // 验证：如果不跳过预处理，必须提供视频
  if (!form.skip_preprocess && !form.ref_video) {
    alert('请先上传参考视频');
    return;
  }

  isTraining.value = true;
  progressState.visible = true;
  updateProgress(0, '正在连接服务器...', '');

  try {
    const formData = new FormData();
    Object.keys(form).forEach(key => {
      if (key === 'use_manual_au') {
        formData.append(key, form[key] ? '1' : '0');
      } else if (key === 'skip_preprocess') {
        formData.append(key, form[key] ? '1' : '0');
      } else if (form[key] !== undefined && form[key] !== null) {
        formData.append(key, form[key]);
      }
    });

    if (form.use_manual_au && auFile.value) {
      formData.append('au_csv', auFile.value);
    }

    // 使用 SSE 流式接口获取实时进度
    const res = await fetch('/model_training_stream', {
      method: 'POST',
      body: formData
    });

    if (!res.ok) {
      throw new Error(`HTTP error! status: ${res.status}`);
    }

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

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
              updateProgress(7, '训练完成！');
              await new Promise(resolve => setTimeout(resolve, 500));
              progressState.visible = false;
              alert('训练完成！模型已保存到云端。');
            } else if (data.step === 'error') {
              progressState.visible = false;
              alert('训练失败: ' + data.message);
            } else if (typeof data.step === 'number') {
              updateProgress(data.step, data.message);
            }
          } catch (parseErr) {
            console.warn('SSE 数据解析失败:', parseErr, line);
          }
        }
      }
    }
  } catch (err) {
    console.error('训练提交失败:', err);
    progressState.visible = false;
    alert('训练提交失败: ' + err.message);
  } finally {
    isTraining.value = false;
  }
};

onMounted(() => {
  toggleGaussianTalkerOptions();
  toggleCloudConfig();

  const dropZone = document.querySelector('.file-input-group');
  if (dropZone) {
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
        const dataTransfer = new DataTransfer();
        dataTransfer.items.add(file);
        refFileInput.value.files = dataTransfer.files;

        const event = new Event('change', { bubbles: true });
        refFileInput.value.dispatchEvent(event);
      }
    });
  }
});
</script>

<style scoped>
/* ===============================
   关键修复 1：根容器不要写死暗色背景
   改用 var(--bg)，这样日/夜切换才可见
   =============================== */
.training-container {
  min-height: 100vh;
  background: var(--bg);
  color: var(--fg);
  padding: 100px 40px 40px;
  font-family: var(--font-sans);
  position: relative;
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

.back-btn {
  display: flex;
  align-items: center;
  gap: 10px;
  background: none;
  border: none;
  color: var(--text-muted);
  cursor: pointer;
  font-size: 13px;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.back-btn:hover {
  color: var(--accent);
}

.system-id {
  font-size: 12px;
  color: var(--text-muted);
  font-family: var(--font-mono);
}

.content-wrapper {
  max-width: 1100px;
  margin: 0 auto;
  position: relative;
  z-index: 10;
}

.page-header {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  margin-bottom: 3rem;
}

.header-icon {
  width: 3rem;
  height: 3rem;
  color: var(--accent);
}

.title-group h2 {
  font-size: 1.8rem;
  font-weight: 800;
  letter-spacing: 2px;
  color: var(--fg);
}

.title-group p {
  font-size: 0.8rem;
  color: var(--text-muted);
  text-transform: uppercase;
  letter-spacing: 4px;
}

.grid-layout {
  display: grid;
  grid-template-columns: 1.2fr 1fr;
  gap: 2.5rem;
}

/* 面板底色/边框改为变量，日间模式不发灰 */
.monitor-section {
  background: var(--panel-bg);
  border: 1px solid var(--panel-border);
  padding: 1rem;
  border-radius: 1rem;
}

.video-frame {
  position: relative;
  aspect-ratio: 16/9;
  background: #000;
  border-radius: 0.5rem;
  overflow: hidden;
  box-shadow: 0 0 30px rgba(0, 0, 0, 0.35);
}

.main-video {
  width: 100%;
  height: 100%;
  object-fit: contain;
}

.video-overlay {
  position: absolute;
  inset: 0;
  pointer-events: none;
  border: 1px solid rgba(34, 211, 238, 0.2);
  z-index: 2;
}

.scanline {
  position: absolute;
  top: 0;
  height: 100%;
  width: 100%;
  background: linear-gradient(to bottom, transparent, rgba(34, 211, 238, 0.05) 50%, transparent);
  animation: scan 4s linear infinite;
}

.rec-dot {
  position: absolute;
  top: 1rem;
  right: 1rem;
  width: 8px;
  height: 8px;
  background: #ef4444;
  border-radius: 50%;
  animation: blink 1s infinite;
}

.corner-text {
  position: absolute;
  font-size: 0.6rem;
  color: var(--accent);
  font-family: var(--font-mono);
  padding: 0.5rem;
}

.top-left { top: 0; left: 0; }
.bottom-right { bottom: 0; right: 0; }

.status-indicator {
  display: flex;
  gap: 2rem;
  margin-top: 1rem;
  padding: 0.5rem;
}

.status-item {
  display: flex;
  flex-direction: column;
}

.status-item .label {
  font-size: 0.7rem;
  color: var(--text-muted);
  text-transform: uppercase;
}

.status-item .value {
  font-size: 0.9rem;
  color: var(--accent);
  font-weight: bold;
}

/* 右侧表单面板同样变量化 */
.control-section {
  background: var(--panel-bg);
  padding: 2rem;
  border-radius: 1rem;
  border: 1px solid var(--panel-border);
}

.input-grid {
  display: flex;
  flex-direction: column;
  gap: 1.5rem;
}

.form-group label {
  display: block;
  font-size: 0.85rem;
  color: var(--text-muted);
  margin-bottom: 0.5rem;
}

/* ===============================
   关键修复 3：输入框不要写死白字黑底
   改用主题变量，日间模式变深色字体
   =============================== */
.cyber-form input[type="text"],
.cyber-form input[type="number"],
.cyber-form input[type="password"],
.cyber-form select,
.cyber-form textarea {
  width: 100%;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  padding: 0.75rem;
  color: var(--fg);
  outline: none;
  transition: 0.3s;
}

.cyber-form input:focus,
.cyber-form select:focus,
.cyber-form textarea:focus {
  border-color: var(--accent);
  box-shadow: 0 0 10px rgba(34, 211, 238, 0.18);
}

.cyber-form textarea {
  min-height: 100px;
  resize: vertical;
  font-family: var(--font-mono);
  font-size: 0.9rem;
}

.gpu-selector {
  display: flex;
  gap: 0.75rem;
}

/* GPU 卡片：默认用 muted，active 用 accent */
.gpu-card {
  flex: 1;
  padding: 0.75rem 0.5rem;
  text-align: center;
  background: color-mix(in srgb, var(--panel-bg) 70%, transparent);
  border: 1px solid transparent;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: 0.3s;
  color: var(--text-muted);
  font-size: 0.85rem;
}

.gpu-card:hover {
  border-color: var(--panel-border);
}

.gpu-card.active {
  background: rgba(34, 211, 238, 0.1);
  border-color: var(--accent);
  color: var(--accent);
}

.file-input-group { position: relative; }
.file-input { display: none; }

.file-display {
  display: flex;
  gap: 0.5rem;
  margin-bottom: 0.25rem;
}

.browse-btn {
  padding: 0.75rem 1.5rem;
  background: rgba(34, 211, 238, 0.1);
  border: 1px solid rgba(34, 211, 238, 0.3);
  color: var(--accent);
  border-radius: 0.5rem;
  cursor: pointer;
  transition: 0.3s;
  font-size: 0.85rem;
  font-weight: 600;
}

.browse-btn:hover {
  background: rgba(34, 211, 238, 0.2);
}

.browse-btn.small {
  padding: 0.5rem 1rem;
  font-size: 0.8rem;
}

.file-hint {
  font-size: 0.7rem;
  color: var(--text-muted);
  margin-top: 0.25rem;
}

.cloud-config,
.gt-options {
  background: color-mix(in srgb, var(--panel-bg) 70%, transparent);
  padding: 1rem;
  border-radius: 0.5rem;
  border: 1px solid var(--panel-border);
}

.sub-group { margin-bottom: 1rem; }
.sub-group:last-child { margin-bottom: 0; }

.cloud-warning {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(239, 68, 68, 0.1);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 0.25rem;
  color: #ef4444;
  font-size: 0.7rem;
  text-align: center;
}

.skip-preprocess-group {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--panel-border);
}

.skip-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.skip-checkbox label {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.model-name-input {
  margin-top: 0.75rem;
}

.model-name-input label {
  font-size: 0.75rem;
  color: var(--text-muted);
  margin-bottom: 0.25rem;
}

.model-name-input input {
  width: 100%;
  padding: 0.5rem;
  background: var(--card);
  border: 1px solid var(--border);
  border-radius: 0.5rem;
  color: var(--fg);
}

.skip-hint {
  margin-top: 0.5rem;
  padding: 0.5rem;
  background: rgba(251, 191, 36, 0.1);
  border: 1px solid rgba(251, 191, 36, 0.3);
  border-radius: 0.25rem;
  color: #f59e0b;
  font-size: 0.7rem;
  text-align: center;
}

.au-upload-group {
  margin-top: 1rem;
  padding-top: 1rem;
  border-top: 1px solid var(--panel-border);
}

.au-checkbox {
  display: flex;
  align-items: center;
  gap: 0.5rem;
  margin-bottom: 0.75rem;
}

.au-checkbox label {
  margin: 0;
  color: var(--text-muted);
  font-size: 0.8rem;
}

.au-file-input {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.range-wrapper {
  display: flex;
  align-items: center;
  gap: 1rem;
}

.range-val {
  color: var(--accent);
  font-weight: bold;
  min-width: 2rem;
}

input[type="range"] {
  flex: 1;
  height: 4px;
  background: rgba(255, 255, 255, 0.15);
  border-radius: 2px;
  outline: none;
  -webkit-appearance: none;
  appearance: none;
}

input[type="range"]::-webkit-slider-thumb {
  -webkit-appearance: none;
  appearance: none;
  width: 16px;
  height: 16px;
  background: var(--accent);
  border-radius: 50%;
  cursor: pointer;
}

.full-width { grid-column: 1 / -1; }

.train-btn {
  width: 100%;
  padding: 1rem;
  background: var(--accent);
  color: #000;
  font-weight: 800;
  border: none;
  border-radius: 0.5rem;
  cursor: pointer;
  transition: 0.3s;
  letter-spacing: 2px;
  margin-top: 1rem;
  font-size: 1rem;
}

.train-btn:hover:not(:disabled) {
  filter: brightness(1.05);
  box-shadow: 0 0 20px rgba(34, 211, 238, 0.35);
  transform: translateY(-1px);
}

.train-btn:disabled,
.train-btn.loading {
  opacity: 0.7;
  cursor: not-allowed;
}

/* 顶部导航右侧容器：保持不破坏原有布局 */
.nav-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* 主题+字体并排 */
.appearance-inline {
  display: inline-flex;
  align-items: center;
  gap: 10px;
}

/* 小屏幕压缩间距，避免顶栏拥挤 */
@media (max-width: 768px) {
  .nav-right { gap: 10px; }
  .appearance-inline { gap: 8px; }
}

@keyframes scan {
  from { top: 0; }
  to { top: 100%; }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.3; }
}

@media (max-width: 900px) {
  .grid-layout {
    grid-template-columns: 1fr;
  }

  .gpu-selector {
    flex-direction: column;
  }

  .file-display {
    flex-direction: column;
  }

  .browse-btn {
    width: 100%;
  }

  .training-container {
    padding: 80px 20px 20px;
  }

  .top-nav {
    padding: 0 20px;
  }
}
</style>
