# Voice-Based Interview Input — What Hermes Actually Supports

Origin: Kene's concern that a gap-driven interview (see
`gap-analysis-engine.md`) could still mean answering dozens of
questions across multiple sessions, and that typing all of it on a
Windows/i3 laptop or via Telegram gets tiring. Question was: how far can
Hermes's own voice features go for this, is a live call feasible, is it
free, and is it accurate enough for Nigerian-accented English plus
French/Igbo/Hausa/Spanish/Portuguese/Japanese.

## What Hermes actually has, in plain terms

Three distinct voice patterns, already built into Hermes — none of
this needs to be built from scratch:

1. **Async voice notes (Telegram/Discord/WhatsApp/Slack/Signal)** — send
   a voice message like normal; the gateway transcribes it automatically
   (`stt.enabled: true`, on by default) and hands the transcript to the
   agent as if typed. This works **regardless of the `/voice` reply-mode
   setting** — that setting only controls whether Hermes's *reply* comes
   back as audio, not whether your incoming voice note gets transcribed.
   This is the closest match to "the user sees questions and answers
   with voice notes."
2. **CLI push-to-talk** — `/voice on`, Ctrl+B to record, auto-stops on
   silence, transcribes via Whisper, optionally speaks the reply back.
   Full duplex, but tied to sitting at the terminal — less useful for
   an interview meant to happen over a phone, e.g. during commute time.
3. **Discord voice channels** — the bot joins an actual voice channel,
   listens per-user, transcribes on ~1.5s silence, runs the full agent
   pipeline (memory, tools, skills — not a toy Q&A), and speaks the
   reply back into the channel, with echo prevention so it doesn't hear
   its own TTS. **This is the closest thing to "a live call" Hermes has
   built in** — it is not a PSTN phone call (no dialing an actual phone
   number; it rides Discord's own voice infrastructure), but
   functionally it's a real-time, turn-taking spoken conversation.

## Can a live call interview run on free model endpoints?

The two audio legs, yes, genuinely free:

- **STT**: `faster-whisper` running locally needs no API key at all
  (~150MB model download on first use) — this is the default and
  recommended path. Groq's Whisper endpoint is also free-tier and very
  fast (~0.5–1s) if Kene prefers offloading it from the Oracle Cloud
  box's CPU.
- **TTS**: Edge TTS (Microsoft, no key, 322 voices across 74 languages)
  or NeuTTS (fully local, free) both cost nothing.

**Worth being precise about what's actually free here**: it's the audio
legs, not the interview itself. The reasoning underneath — the LLM
actually running the interview, applying the Quantification gate,
deciding what to ask next — still costs whatever Kene's configured
model costs via Nous Portal/OpenRouter, same as every other turn in
this skill. Voice being free doesn't make the underlying agent turns
free; it just means the STT/TTS layer wrapped around those turns adds
nothing on top.

The one real cost on the audio side is CPU: local Whisper + local TTS
on a modest Oracle Cloud instance will be slower than the paid cloud
options, which matters more for a real-time Discord-voice-channel
conversation (where latency breaks the "call" feel) than for async
voice notes (where a few extra seconds of transcription delay before
Hermes replies is a non-issue).

## Accuracy — the honest, language-by-language answer

All of Hermes's STT providers (local, Groq, OpenAI) are Whisper or
Whisper-compatible under the hood, so accuracy tracks Whisper's actual
per-language training data, not a Hermes-specific limitation:

- **English, including Nigerian-accented and Pidgin-adjacent English**:
  serviceable, especially on `small`/`medium`/`large-v3` (the free local
  option) — English is Whisper's best-represented language by a wide
  margin, and it's been trained on a genuinely global spread of English
  accents. Accented English still measurably trails "standard"
  American/British English in word-error-rate research, so expect more
  correction/re-asking than a native English interviewer would need,
  but it's usable today. Hermes's built-in hallucination filter also
  helps specifically with the phantom-text-from-silence problem that
  shows up more with pauses/filler patterns.
- **French, Spanish, Portuguese, Japanese**: all comfortably
  high-resource in Whisper's training data — expect quality close to
  English, especially at `large-v3`. A transcript in any of these
  languages can go straight to the LLM turn without a separate
  translation step; a capable LLM reads French/Spanish/Portuguese/
  Japanese natively and can respond in English or the same language as
  asked.
- **Igbo**: not a matter of accuracy at all — checked this directly
  against Whisper's own tokenizer source (`openai/whisper`,
  `whisper/tokenizer.py`'s `LANGUAGES` dict, the actual list of all 99
  language tokens the model can be told to use). Yoruba (`yo`) and
  Hausa (`ha`) are both in that list; Igbo has **no entry at all** —
  there's no `<|ig|>` token, so the model has no way to even be told
  "this is Igbo." It's not that Igbo transcribes badly; there's
  structurally no slot for it to attempt. This lines up with the zero
  Igbo-language training hours documented in research on Whisper's
  training mix — the tokenizer omission and the training-data absence
  are the same underlying fact, just visible from two different angles.
  Any Igbo audio sent to Hermes's default STT chain will get
  auto-detected as some other language (or English) and produce
  nonsense, not a rough transcription.
- **Hausa and Yoruba**: unlike Igbo, these do have tokenizer slots, but
  they're a rounding error of Whisper's actual training data (well
  under 1% of hours each) — usable for isolated words maybe, not for a
  real interview answer. There are purpose-built, fine-tuned models for
  this specifically (Nigerian research groups have published Whisper
  checkpoints fine-tuned on Igbo/Hausa/Yoruba speech — e.g. the
  NaijaVoices and N-ATLAS efforts — showing large accuracy gains over
  base Whisper), but none of that is one of Hermes's built-in
  `stt.provider` options out of the box; it would mean pointing
  Hermes's "local" STT config at a custom fine-tuned Whisper checkpoint
  instead of the stock model, which `faster-whisper` can technically
  load but isn't a documented Hermes path today — a real but
  nontrivial side project, not a config toggle.

**Bottom line for this interview specifically**: since the context
interview is fundamentally in English (it's populating an English-
language application/career profile), the practical answer is — voice
notes work well for the actual use case today. Treat Igbo/Hausa/Yoruba
voice input as a "not yet, without extra engineering" rather than
something to promise Kene now.

## Should it be the default, or a secondary option?

**My take: make it always-available, not the default delivery mode —
and it barely costs anything to support this, since it's not really an
either/or.** Because incoming voice-note transcription happens
automatically whenever `stt.enabled: true` (which it is by default),
regardless of whatever mode the conversation is in, Kene doesn't need
the skill to pick "text interview" vs. "voice interview" as a hard,
upfront choice. In practice:

- The interview loop's questions can default to arriving as text (in
  Telegram or wherever the interview is happening) — this keeps the
  question itself skimmable/re-readable, which matters more for an
  interview than for a casual chat, since some bank questions are dense
  and benefit from rereading before answering.
- Kene answers however's convenient in the moment: type, or just send a
  voice note instead — no mode switch, no command needed, Hermes
  transcribes it the same either way.
- If he wants the questions themselves spoken too (fully hands-free
  both directions, e.g. doing an interview session while driving/
  walking), `/voice tts` turns that on for the session — this is the
  closest to "live call" without needing the heavier Discord-voice-
  channel setup, and doesn't require picking a different skill or mode.

Reasons not to force voice as the default: (1) accuracy still means
some fraction of answers need a re-ask or correction, which is more
disruptive if voice is the only path; (2) several bank questions
benefit from Kene seeing the exact bank phrasing in front of him while
answering (matching a specific employer's wording, per
`answer-variants.md`); (3) some answers (numbers, dates, company names)
are just more reliably captured typed than transcribed. None of these
are reasons to hide voice or bury it as some separate, hard-to-reach
setting — just reasons not to make it the assumed default.

**The one non-negotiable safeguard, regardless of default-vs-optional**:
this interview exists to feed exact figures into the Quantification
gate (`07-context-architect/SKILL.md` Phase 2/3) — a transcription
error on a number is a different kind of mistake than a typo, since
nothing about it looks wrong on the page. A mis-heard "25%" as "225%"
would sail straight through unless something catches it. So: any
voice-derived answer containing a number, date, or percentage gets
echoed back as transcribed text for an explicit yes/no confirmation
before Phase 4 writes it anywhere — not a general "did I get this
right" pleasantry, a specific "confirm the exact figure" check. This
costs one extra exchange only on the answers where it actually matters;
qualitative voice answers don't need it.

## Setup checklist (Telegram voice notes — the recommended path here)

```bash
pip install "hermes-agent[voice]" "hermes-agent[messaging]"
pip install faster-whisper   # free local STT, zero API keys
```

```yaml
# ~/.hermes/config.yaml
stt:
  provider: "local"
  local:
    model: "small"   # base is fine for testing; small/medium noticeably
                      # more accurate for accented English at modest
                      # extra CPU cost — worth it for something this
                      # answer-quality-sensitive
tts:
  provider: "edge"    # free, no key, decent quality — fine for hearing
                       # questions read back; upgrade to elevenlabs later
                       # only if voice quality itself becomes a complaint
```

No further skill-level change needed beyond what's already true: once
this is configured, any voice note sent during a `07-context-architect`
interview session is transcribed and handled exactly like a typed
answer, automatically.
