# AI Agent Product

`ai-agent-product` is a Codex skill for MyVocal AI Agent product and engineering work around secure ElevenLabs passthrough/proxy implementations.

It covers:

- MyVocal customer/admin API key and usage management
- ElevenLabs REST passthrough design and review
- signed URL, WebRTC token, and WebSocket relay boundaries
- resource ownership checks, quotas, rate limits, and redacted logging
- isolated UAT execution prompts and evidence requirements

Install/use path in this repository:

```text
codex-skills/ai-agent-product
```

## Current Packaging Rule

Execution prompts, handoff prompts, and agent prompts can use the current 14,500-character ceiling. Older 10,000-character prompt packaging guidance is obsolete.

Generated validators, compression scripts, backend submit scripts, and local preflight checks must also use `PROMPT_CHAR_LIMIT = 14500`. Do not keep legacy `len(prompt) < 10000`, `MAX_PROMPT_CHARS = 10000`, or "under 10,000" checks.
