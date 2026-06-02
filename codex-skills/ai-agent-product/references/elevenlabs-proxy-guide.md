# ElevenLabs ElevenAgents Proxy Guide

Use this reference when implementing or reviewing a secure backend pass-through/proxy for ElevenLabs ElevenAgents. The goal is not to reimplement an ElevenLabs Agent. The goal is to add a thin, secure, observable, low-intrusion backend layer so business clients can access ElevenLabs AI Agent capabilities without receiving secrets.

## Core Goal

Implement a secure ElevenLabs AI Agent proxy layer that normally includes:

1. Keep the ElevenLabs API key on the server. Never expose it to browsers, apps, mini programs, or third-party clients.
2. Generate ElevenLabs signed URLs through the backend.
3. Relay WebSocket traffic bidirectionally between the client and ElevenLabs.
4. Avoid changing ElevenLabs protocol structures unless required for auth, rate limits, audit, redaction, or business allowlists.
5. Preserve native ElevenLabs events: audio, text, transcripts, agent responses, ping/pong, client tool calls, contextual updates, and multimodal messages.
6. Support runtime personalization by business user, agent alias, environment, branch ID, and dynamic variables.
7. Default to clear security boundaries: auth, agent whitelist, field validation, message size limits, rate limits, log redaction, error mapping, and connection cleanup.

## When To Use

Use this skill when the task says or implies:

- Wrap, pass through, or proxy ElevenLabs AI Agent.
- Do not let frontend call ElevenLabs directly.
- Relay ElevenLabs WebSocket through a backend.
- Add business auth, user binding, logging, rate limits, or auditing to ElevenLabs Agent.
- Return ElevenLabs signed URLs from our own API.
- Connect ElevenLabs Agent to SaaS, apps, mini programs, or other business clients.

## Architecture Modes

### Mode A: Signed URL Mode

This is the lighter approach.

Flow:

1. Client calls the business backend.
2. Backend authenticates the business user.
3. Backend maps `agentAlias` to a real server-side ElevenLabs `agent_id`.
4. Backend uses `ELEVENLABS_API_KEY` to request an ElevenLabs signed URL.
5. Backend returns the signed URL to the client.
6. Client connects directly to ElevenLabs WebSocket using the signed URL.

Use when:

- Web frontend can connect to an external WebSocket directly.
- Full realtime event logging is not required.
- Audio traffic does not need to flow through our server.
- Lower backend bandwidth, cost, and latency matter.

Rules:

- Treat the signed URL as a sensitive temporary credential.
- Redact signed URLs from logs.
- Do not parse tokens or `conversation_signature` out of signed URLs; treat them as opaque strings.
- Fetch a fresh signed URL for each new session.
- Do not cache signed URLs for long periods.

### Mode B: Full WebSocket Relay Mode

This is the more complete proxy.

Flow:

1. Client connects to our WebSocket route:

   ```text
   /ws/elevenlabs/agents/:agentAlias/conversation
   ```

2. Backend authenticates the user, origin, permissions, and `agentAlias`.
3. Backend obtains a signed URL using the ElevenLabs API key, or builds the configured public-agent WebSocket URL if explicitly allowed.
4. Backend connects to ElevenLabs as a WebSocket client.
5. Backend forwards client messages to ElevenLabs.
6. Backend forwards ElevenLabs messages to the client.
7. Closing either side closes the other side.
8. Errors are mapped to business-safe messages without leaking API keys, signed URLs, or internal tokens.

Use when:

- ElevenLabs traffic must stay behind the business domain.
- Unified app auth, audit, risk controls, limits, billing, logging, or monitoring are required.
- Signed URLs should not reach the client.
- Mini programs, apps, or restricted networks need the business backend as the stable endpoint.
- Server-side client tool handling or event mediation is explicitly required.

## Public API

### Signed URL Endpoint

Recommended route:

```http
GET /api/elevenlabs/agents/:agentAlias/signed-url
```

Optional query parameters:

```text
environment=production
branch_id=agtbrch_xxxx
include_conversation_id=false
```

Backend behavior:

1. Verify the current business user is allowed to access `agentAlias`.
2. Map `agentAlias` to a configured ElevenLabs `agent_id`.
3. Request ElevenLabs:

   ```http
   GET https://api.elevenlabs.io/v1/convai/conversation/get-signed-url?agent_id=...
   Header: xi-api-key: ${ELEVENLABS_API_KEY}
   ```

4. Return:

   ```json
   {
     "signedUrl": "...",
     "expiresInSeconds": 900
   }
   ```

If ElevenLabs returns a conversation ID and product requirements allow it, return:

```json
{
  "signedUrl": "...",
  "conversationId": "conv_xxx",
  "expiresInSeconds": 900
}
```

Never return:

- `ELEVENLABS_API_KEY`
- Internal agent config
- Raw stack traces
- Unredacted upstream response headers

### WebSocket Relay Endpoint

Recommended route:

```text
/ws/elevenlabs/agents/:agentAlias/conversation
```

Supported query parameters:

```text
environment=production
branch_id=agtbrch_xxxx
mode=voice|text
```

After connection:

- Client JSON messages pass through to ElevenLabs by default.
- ElevenLabs JSON messages pass through to the client by default.
- The backend only adds security checks, protocol maintenance, connection cleanup, and redacted observability.

## Client To Server Messages

The relay should support these client-origin messages without arbitrary dropping.

Conversation initiation:

```json
{
  "type": "conversation_initiation_client_data",
  "conversation_config_override": {
    "agent": {
      "prompt": {
        "prompt": "overriding system prompt",
        "llm": "gpt-4o"
      },
      "first_message": "overriding first message",
      "language": "en"
    },
    "tts": {
      "voice_id": "voice-id-here"
    },
    "conversation": {
      "text_only": false
    }
  },
  "custom_llm_extra_body": {
    "temperature": 0.7,
    "max_tokens": 100
  },
  "dynamic_variables": {
    "user_name": "Nan",
    "plan": "pro"
  },
  "user_id": "business_user_id",
  "branch_id": "agtbrch_xxxx",
  "environment": "production"
}
```

User audio:

```json
{
  "user_audio_chunk": "base64EncodedAudioData=="
}
```

User text:

```json
{
  "type": "user_message",
  "text": "I would like to upgrade my account"
}
```

Pong:

```json
{
  "type": "pong",
  "event_id": 12345
}
```

Client tool result:

```json
{
  "type": "client_tool_result",
  "tool_call_id": "tool_call_123",
  "result": "Account is active",
  "is_error": false
}
```

Contextual update:

```json
{
  "type": "contextual_update",
  "text": "User is viewing the pricing page"
}
```

User activity:

```json
{
  "type": "user_activity"
}
```

Multimodal message:

```json
{
  "type": "multimodal_message",
  "text": {
    "type": "user_message",
    "text": "What is this file?"
  },
  "file": {
    "type": "file_input",
    "file_id": "file_12345"
  }
}
```

## Server To Client Messages

The relay should return these upstream events as close to the original form as possible.

Conversation metadata:

```json
{
  "type": "conversation_initiation_metadata",
  "conversation_initiation_metadata_event": {
    "conversation_id": "conv_123456789",
    "agent_output_audio_format": "pcm_16000",
    "user_input_audio_format": "pcm_16000"
  }
}
```

User transcript:

```json
{
  "type": "user_transcript",
  "user_transcription_event": {
    "user_transcript": "I need help with my voice cloning project."
  }
}
```

Agent response:

```json
{
  "type": "agent_response",
  "agent_response_event": {
    "agent_response": "I'd be happy to help."
  }
}
```

Agent response correction:

```json
{
  "type": "agent_response_correction",
  "agent_response_correction_event": {
    "original_agent_response": "...",
    "corrected_agent_response": "..."
  }
}
```

Audio:

```json
{
  "type": "audio",
  "audio_event": {
    "audio_base_64": "base64EncodedAudioResponse==",
    "event_id": 1,
    "alignment": {
      "chars": ["H", "e", "l", "l", "o"],
      "char_durations_ms": [50, 30, 40, 40, 60],
      "char_start_times_ms": [0, 50, 80, 120, 160]
    }
  }
}
```

Ping:

```json
{
  "type": "ping",
  "ping_event": {
    "event_id": 12345,
    "ping_ms": 50
  }
}
```

Client tool call:

```json
{
  "type": "client_tool_call",
  "client_tool_call": {
    "tool_name": "check_account_status",
    "tool_call_id": "tool_call_123",
    "parameters": {
      "user_id": "user_123"
    }
  }
}
```

VAD score:

```json
{
  "type": "vad_score",
  "vad_score_event": {
    "vad_score": 0.95
  }
}
```

Interruption:

```json
{
  "type": "interruption",
  "interruption_event": {
    "reason": "..."
  }
}
```

## Passthrough Principles

Do only four things by default:

1. Authenticate.
2. Whitelist.
3. Protect secrets.
4. Forward reliably.

Do not:

- Use a client-supplied arbitrary URL as the upstream target.
- Let the client pass an ElevenLabs API key.
- Let the client pass arbitrary `agent_id` by default.
- Rewrite native ElevenLabs events unless required for security or business policy.
- Log audio base64, signed URLs, tokens, or API keys.
- Drop unknown event types. Unknown events should pass through with size limits.
- Reimplement Agent logic in the proxy layer.

Allowed proxy behavior:

- Add `requestId` or `connectionId`.
- Inject the authenticated business `userId` into `conversation_initiation_client_data.user_id`.
- Merge allowed server-side dynamic variables.
- Filter unsafe override fields.
- Keep ping/pong alive.
- Clean up upstream/downstream connections on close, error, timeout, or max duration.
- Emit redacted lightweight event metrics.

## Security Strategy

### Environment Variables

Minimum config:

```text
ELEVENLABS_API_KEY=
ELEVENLABS_AGENT_DEFAULT_ID=
ELEVENLABS_AGENT_MAP=default:agent_xxx,sales:agent_xxx,support:agent_xxx
ELEVENLABS_DEFAULT_ENVIRONMENT=production
ELEVENLABS_PROXY_ALLOWED_ORIGINS=
ELEVENLABS_PROXY_MAX_MESSAGE_BYTES=1048576
ELEVENLABS_PROXY_CONNECTION_TIMEOUT_MS=30000
```

Optional flags:

```text
ALLOW_PROMPT_OVERRIDE=false
ALLOW_LLM_OVERRIDE=false
ALLOW_TTS_OVERRIDE=true
ELEVENLABS_PROXY_MAX_DYNAMIC_VARIABLES=20
ELEVENLABS_PROXY_MAX_DYNAMIC_VARIABLE_STRING_LENGTH=512
ELEVENLABS_PROXY_MAX_CONNECTIONS_PER_USER=3
ELEVENLABS_PROXY_MAX_MESSAGES_PER_SECOND=20
ELEVENLABS_PROXY_MAX_CONNECTION_DURATION_MS=900000
```

### Agent Whitelist

Client sends:

```text
agentAlias=default
```

Server resolves:

```text
agent_id=agent_xxx
```

Do not support this by default:

```text
agent_id=client_supplied_anything
```

Only allow direct `agent_id` if the user explicitly asks for it and the service has strong permission checks.

### Override Whitelist

`conversation_config_override` is high-risk.

Allow by default:

```text
conversation.text_only
agent.language
tts.voice_id
```

Reject or strip by default:

```text
agent.prompt.prompt
agent.prompt.llm
custom_llm_extra_body
```

Only open these fields behind explicit feature flags and authorization:

```text
ALLOW_PROMPT_OVERRIDE=false
ALLOW_LLM_OVERRIDE=false
ALLOW_TTS_OVERRIDE=true
```

### Dynamic Variables

Allow business variables after filtering:

- Key pattern: letters, digits, and underscores only.
- Reject `system__` prefix.
- Value types: string, number, or boolean only.
- Limit variable count.
- Limit string length.

### Log Redaction

Never log:

```text
xi-api-key
ELEVENLABS_API_KEY
signed_url
conversation_signature
token
audio_base_64
user_audio_chunk
```

Safe log shape:

```json
{
  "requestId": "...",
  "userId": "...",
  "agentAlias": "support",
  "conversationId": "conv_xxx",
  "eventType": "agent_response",
  "direction": "upstream_to_client",
  "messageBytes": 1234,
  "timestamp": "..."
}
```

### Rate Limits

Limit at least:

- IP
- `userId`
- `agentAlias`
- Concurrent WebSocket connections per user
- Messages per second per connection
- Maximum connection duration
- Maximum bytes per message

### CORS And Origin

- Apply CORS allowlists to the signed URL REST endpoint.
- Check WebSocket `Origin` during handshake.
- Do not configure `*` except in local development.

## WebSocket Relay Requirements

1. Do not declare the downstream connection fully connected until the upstream ElevenLabs connection succeeds.
2. If upstream connection fails, close downstream with a clear business-safe error.
3. For downstream-to-upstream messages:
   - Enforce byte limits.
   - Parse JSON.
   - Validate the basic structure.
   - Merge or override authenticated `user_id` and allowed dynamic variables when needed.
   - Forward to upstream.
4. For upstream-to-downstream messages:
   - Enforce byte limits.
   - Avoid sensitive logging.
   - Forward the original payload to downstream.
5. On either side closing:
   - Close the other side.
   - Clear timers.
   - Log redacted close metadata.
6. On either side erroring:
   - Log the redacted error.
   - Notify the other side if possible.
   - Close both sides.
7. For ping/pong:
   - Default to protocol passthrough. Forward ElevenLabs `ping` to the client and client `pong` to upstream.
   - If the frontend explicitly does not want to handle ping, the proxy may respond automatically to upstream pings, but do not break the client-facing protocol unexpectedly.

## Client Tool Calls

Default strategy: passthrough.

1. ElevenLabs sends `client_tool_call`.
2. Proxy forwards it to the client.
3. Client executes the local tool.
4. Client sends `client_tool_result`.
5. Proxy forwards the result to ElevenLabs.

Only intercept and execute tools on the server if the user explicitly requests server-side tool execution.

If server-side execution is requested:

- Check `tool_name` against an allowlist.
- Validate `parameters` with a schema.
- Execute the business service.
- Return `client_tool_result`.
- On failure, return `is_error: true`.

Never execute unknown tools by default.

## Error Mapping

REST errors:

```text
400 invalid_request
401 unauthorized
403 forbidden
404 agent_not_found
408 upstream_timeout
422 invalid_payload
429 rate_limited
502 upstream_error
504 upstream_timeout
```

WebSocket proxy error event:

```json
{
  "type": "proxy_error",
  "error": {
    "code": "upstream_error",
    "message": "Failed to connect to ElevenLabs upstream."
  }
}
```

Do not expose raw ElevenLabs errors unless they have been reviewed and redacted.

## TypeScript Implementation Notes

Use existing project framework patterns. If the project is Node.js/TypeScript and has no stronger local convention, prefer:

```text
src/
  config/
    elevenlabs.config.ts
  elevenlabs/
    elevenlabs.types.ts
    elevenlabs.schemas.ts
    elevenlabs.service.ts
    elevenlabs.controller.ts
    elevenlabs.ws-relay.ts
    elevenlabs.redaction.ts
    elevenlabs.rate-limit.ts
  auth/
    auth.middleware.ts
  logger/
    logger.ts
tests/
  elevenlabs.signed-url.test.ts
  elevenlabs.ws-relay.test.ts
```

Coding rules:

- Validate all external input with schemas.
- Avoid `any` for core message types; allow an unknown-event fallback type for passthrough.
- Keep error handling explicit.
- Centralize config.
- Use a shared redaction utility for logs.
- Mock ElevenLabs upstream in tests.
- Never hardcode API keys, agent IDs, or signed URLs.
- Read secrets only from environment variables or Secret Manager.

## Recommended Implementation Order

1. Read project structure and identify the framework.
2. Add environment variables and config validation.
3. Implement `agentAlias -> agent_id` mapping.
4. Implement the signed URL REST endpoint.
5. Implement log redaction.
6. Implement the WebSocket relay.
7. Add message size limits, origin checks, and rate limits.
8. Add dynamic variable and override filtering.
9. Add tests.
10. Add frontend integration examples.

## Test Checklist

Cover:

- Unauthenticated users cannot fetch signed URLs.
- Unauthorized users cannot access a given `agentAlias`.
- Unknown `agentAlias` returns 404.
- Backend sends `xi-api-key` to ElevenLabs.
- Client responses never contain `xi-api-key`.
- Logs do not contain signed URLs, tokens, `audio_base_64`, or `user_audio_chunk`.
- Signed URL upstream 401, 422, 429, and 5xx map correctly.
- WebSocket establishes downstream and upstream connections.
- Client `user_message` forwards upstream.
- Client `user_audio_chunk` forwards upstream.
- Upstream `audio` forwards to the client.
- Upstream `agent_response` forwards to the client.
- Upstream `ping` and client `pong` forward correctly.
- Closing either side closes the other side.
- Oversized messages are rejected.
- Disallowed `conversation_config_override` fields are filtered or rejected by policy.
- `system__` dynamic variables are rejected.
- Unknown event types pass through while still respecting size limits.

## Frontend Examples

### Signed URL Mode

```ts
const res = await fetch("/api/elevenlabs/agents/support/signed-url", {
  headers: {
    Authorization: `Bearer ${appToken}`,
  },
});

const { signedUrl } = await res.json();

const ws = new WebSocket(signedUrl);

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "conversation_initiation_client_data",
    dynamic_variables: {
      user_name: "Nan",
    },
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("ElevenLabs event:", data);
};
```

### Relay Mode

```ts
const ws = new WebSocket(
  `wss://your-domain.com/ws/elevenlabs/agents/support/conversation?token=${appToken}`
);

ws.onopen = () => {
  ws.send(JSON.stringify({
    type: "conversation_initiation_client_data",
    dynamic_variables: {
      user_name: "Nan",
    },
  }));
};

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log("Proxy event:", data);
};
```

## Final Delivery Contract

After implementation, report:

1. Files added or changed.
2. Required environment variables.
3. How to start the service.
4. How to request a signed URL.
5. How to connect to the WebSocket relay.
6. Security restrictions.
7. How to run tests.
8. Open decisions or credentials still needed.

## Reminder

This is a proxy layer, not an Agent rewrite.

Default to minimum necessary changes:

- Pass through anything that can safely pass through.
- Protect secrets on the server.
- Use allowlists for business control.
- Use redacted logs for troubleshooting.
- Do not reshape the ElevenLabs protocol just to make it look like a custom API.
