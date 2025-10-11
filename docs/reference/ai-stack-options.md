# AI Stack Options for Little Wan

Notes distilled from Manus’s research on balancing cloud APIs and local models for the S350 embodiment.

## Core Scenarios

| Mode                             | Components                                                                                                                                                 | Monthly Cost (est.)               | Notes                                                                               |
| -------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------- | --------------------------------- | ----------------------------------------------------------------------------------- |
| **Minimum Viable (cloud-light)** | Whisper API for STT, Gemini 2.5 Flash for conversation, ElevenLabs Starter for TTS, OpenCV motion detection, `eufy-security-client` for control            | ~€12–25 depending on usage        | Prioritizes presence + personality without heavy ML overhead.                       |
| **Hybrid Optimized**             | Gemini 2.5 Flash (LLM), local Faster-Whisper Medium (STT), local Coqui XTTS (TTS), local DeepFace/MediaPipe for emotion & gesture, Qwen2.5-VL 7B for scene | ~€60 (Gemini usage + electricity) | Keeps GPU load ~8GB VRAM, reduces latency ~54%, preserves privacy for vision/audio. |
| **Full Cloud Premium**           | GPT-4o + gpt-realtime + OpenAI TTS HD + ElevenLabs                                                                                                         | €380–1,700                        | Best quality but overkill; only for luxury demo days.                               |
| **All-Local (4090 rig)**         | Llama 3.1 70B (Q4) via Ollama, LLaVA 13B, Faster-Whisper Large, Coqui XTTS, DeepFace                                                                       | Electricity only (~€30)           | Needs ~40GB VRAM → not feasible on MacBook; fits dedicated RTX 4090 PC.             |

## Cost Reference (2025)

- **Gemini 2.5 Flash** vision analysis once per minute (24/7): ~€34.5/month. Flash-Lite variant ~€7.8/month.
- **OpenAI Whisper API**: €0.006/min; 1 hr/day ≈ €10.8/month.
- **OpenAI Realtime (mini)**: €15–45 per hour of conversation; pricey for sustained use.
- **ElevenLabs Creator plan**: €22/month (100k credits → ~100 minutes HQ audio or 200 minutes low-latency).
- **All-local electric cost** estimate: ~€30/month for 24/7 RTX 4090 operation.

## Recommended Path for MacBook Phase

1. Start with **Minimum Viable** stack: Whisper API + Gemini Flash + ElevenLabs; focus on wiring S350 control and persona.
2. Once stable, shift to **Hybrid Optimized** by:
   - Replacing Whisper API with local Faster-Whisper Medium.
   - Swapping ElevenLabs with local Coqui XTTS (if latency acceptable).
   - Adding background emotion/scene threads powered by Qwen2.5-VL + DeepFace + MediaPipe.
3. Reserve **All-Local** for future dedicated PC build.

## Design Principles from Research

- **Presence over complexity:** Motion/presence detection + short-term memory deliver most of the vibes; skip heavy emotion pipelines until needed.
- **Parallel background loops:** Run scene/emotion classifiers at fixed intervals; main conversation loop only reads cached context.
- **Persona prompt > model weight:** A well-crafted prompt in Gemini provides the sass and warmth without extra compute.
- **Smart cost controls:** Use vision triggers (motion detection) and context caching to limit API calls; batch when possible for discounts.

## Suggested Prompts / Config Hooks

- Persona system prompt snippet (from Manus):
  ```
  You are Little Wan, a warm, cheeky dojo companion. Notice patterns (working, procrastinating, late-night sessions). Respond in ≤2 sentences with gentle humor.
  ```
- Context fields to maintain:
  - `presence_state` (alone/present/active)
  - `work_session_minutes`
  - `time_of_day`
  - `recent_topics`
  - `camera_posture` (upright/slumped)

## Migration Notes

- When moving from cloud STT/TTS to local models, ensure the MacBook has headroom (consider eGPU or external rig if needed).
- Keep Node bridge independent so swapping control tower hosts (MacBook → future mini PC) is trivial.
- Log usage metrics to predict monthly spend before committing to higher tiers.
