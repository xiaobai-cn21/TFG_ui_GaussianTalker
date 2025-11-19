# OpenVoice-main/run_demo.py
from main import synthesize

if __name__ == "__main__":
    # 英文示例
    synthesize(
        text="Hello, this is a test of voice cloning.",
        speaker="default",
        language="en",
        ref_audio="resources/demo_speaker0.mp3",  # 可以不提供
        output_path="outputs/english_test.wav"
    )

    # 中文示例
    synthesize(
        text="你好，这是一段语音克隆测试。",
        speaker="default",
        language="zh",
        ref_audio="resources/demo_speaker1.mp3",  # 可以不提供
        output_path="outputs/chinese_test.wav"
    )
