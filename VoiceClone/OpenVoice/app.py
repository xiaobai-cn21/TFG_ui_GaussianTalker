# app.py
import os
import uuid
import shutil
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse

from main import synthesize

app = FastAPI(
    title="VoiceClone API",
    description="voice cloning service",
    version="1.0.0",
)

# ===== 统一临时目录（Docker / ECS 都安全）=====
TMP_ROOT = "/tmp/openvoice"
os.makedirs(TMP_ROOT, exist_ok=True)


@app.post("/clone")
async def clone_voice(
    text: str = Form(..., description="Input text"),
    language: str = Form("en", description="en or zh"),
    ref_audio: UploadFile = File(..., description="Reference audio (wav/mp3)"),
):
    """
    voice cloning API
    """

    # ===== 请求级隔离 =====
    req_id = uuid.uuid4().hex
    work_dir = os.path.join(TMP_ROOT, req_id)
    os.makedirs(work_dir, exist_ok=True)

    ref_path = os.path.join(work_dir, "ref.wav")
    out_path = os.path.join(work_dir, "out.wav")

    try:
        # ===== 保存上传音频 =====
        with open(ref_path, "wb") as f:
            shutil.copyfileobj(ref_audio.file, f)

        # ===== 调用你的 synthesize =====
        synthesize(
            text=text,
            language=language,
            ref_audio=ref_path,     # 👈 绝对路径，与你 main.py 兼容
            output_path=out_path,
        )

        # ===== 直接返回音频 =====
        return FileResponse(
            out_path,
            media_type="audio/wav",
            filename="voice.wav",
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        # ⚠️ 生产环境可延迟清理
        pass
        # shutil.rmtree(work_dir, ignore_errors=True)
