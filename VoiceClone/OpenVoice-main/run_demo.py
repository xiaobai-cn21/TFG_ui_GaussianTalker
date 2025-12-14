from main import synthesize

synthesize(
    text= "This is a test.",
    language="en",
    ref_audio="resources/demo_speaker1.mp3",     # 👈 你的参考音频
    output_path="outputs/my_voice_test.wav",
)
