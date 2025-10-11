# Local vs Hybrid Architecture Notes

Quick comparison of the two main blueprints from Manus’s research for running Little Wan on the S350.

## All-Local (RTX 4090 Rig)

- **Stack:** Llama 3.1 70B (Q4) for conversation, LLaVA 13B or Qwen2.5-VL 7B for vision, Faster-Whisper Large-v3, Coqui XTTS v2, DeepFace, MediaPipe.
- **VRAM needs:** ~40 GB (exceeds single 24 GB GPU without offloading). Requires quantization + layer offloading.
- **Latency:** ~6–8 s per interaction (sequential pipeline).
- **Pros:** Zero API spend, full privacy, offline capable.
- **Cons:** Hardware heavy, large power draw (~€30/month electricity), complex to maintain. Not feasible on MacBook.

## Hybrid Optimized (Recommended)

- **Stack:** Gemini 2.5 Flash API for LLM, Qwen2.5-VL 7B local for scene, Faster-Whisper Medium (int8), Coqui XTTS v2, DeepFace (CPU), MediaPipe.
- **VRAM needs:** ~8 GB → fits comfortably on future GPU rig and keeps MacBook tasks light.
- **Latency:** ~3.5 s per interaction via parallel background threads.
- **Cost:** ~€60/month (Gemini usage + electricity). Still 80% cheaper than full cloud.
- **Pros:** Fast, low VRAM, keeps most data local. Easy to scale persona updates.
- **Cons:** Requires cloud dependency for the LLM; need caching/usage watchdog.

## MacBook Phase Plan

- Start with Minimum Viable cloud-first stack (Gemini + Whisper + ElevenLabs) to get loops working.
- When MacBook proves underpowered for local models, plan migration target:
  - Step 1: Move to hybrid optimized on a dedicated PC (when available).
  - Step 2: Optionally add offline fallback (Ollama Llama 3.1 8B + local TTS) for resilience.

## Control Tower Considerations

- Keep Control Tower stateless; allow environment variables to choose `mode=cloud`, `mode=hybrid`, `mode=local`.
- Wrap STT/TTS/LLM providers behind adapters so switching between APIs vs local backends is painless.
- Monitor usage metrics to avoid surprise Gemini bills (log token > convert to €).
