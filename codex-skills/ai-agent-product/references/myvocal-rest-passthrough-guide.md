# MyVocal REST Passthrough Guide

Use this reference for MyVocal AI Agent work when the goal is to pass through core ElevenLabs ElevenAgents REST APIs before WSS and SDK work.

## Source Of Truth Order

Use this order when sources conflict:

1. Current official ElevenLabs docs / OpenAPI.
2. Current MyVocal codebase behavior.
3. Current Obsidian notes under `D:\ObsidianVault\AI Agent`.
4. Historical mapping docs such as `api_url_mapping.md`.

Historical docs are useful, but do not treat them as current upstream truth without checking OpenAPI.

## Current MyVocal Product Shape

The phase order for this project is:

1. Phase 1: MyVocal REST passthrough for core ElevenLabs APIs.
2. Phase 2: signed URL, WebRTC token, and WebSocket relay.
3. Phase 3: SDK over MyVocal REST plus WSS.

The user explicitly corrected the earlier signed-URL-first interpretation. Do not revert to that assumption.

## Phase 1 Has Two Planes

Do not implement Phase 1 as a route-only proxy.

Phase 1 needs both:

1. Customer/Admin control plane:
   - MyVocal customer records.
   - API key create, list, update, rotate, revoke.
   - Capability, status, expiry, quota, rate limit, audit log, and usage lookup.
   - Resource binding between MyVocal customers and upstream ElevenLabs IDs.

2. ElevenLabs REST passthrough data plane:
   - Customers call MyVocal with `accessKey`.
   - MyVocal validates customer/key/capability/quota/owner binding.
   - MyVocal forwards to ElevenLabs with the server-side key.
   - MyVocal records redacted request logs and usage ledgers.

The ElevenLabs key may have full upstream permissions, but customers must only receive the MyVocal-scoped permissions granted by their API key.

## Phase 1 Interface Scope

Phase 1 should focus on these REST surfaces:

- Knowledge Base documents: create from URL/text/file, list, get, update, delete, content, chunk, source file URL.
- Knowledge Base folders: create folder, move document, bulk move.
- Knowledge Base related reads: dependent agents, size, summaries.
- Tools: create, list, get, update, delete, dependent agents.
- Agents: create, get, list, update, delete, duplicate, stream simulation, summaries.
- SIP trunk: outbound call.
- WhatsApp: list/get/update/delete accounts and outbound call. Add outbound message to backlog or Phase 1.5 if required.
- Internal MyVocal admin API keys and usage: create/get/list/update/delete keys plus usage stats.

WSS/WebSocket belongs to Phase 2 unless the current task explicitly scopes it into Phase 1.

## Minimum Admin API Surface

Use the existing MyVocal admin conventions if the codebase already has them. If not, use this shape as the starting point:

- `POST /sound_clone/admin/api/v1/agent-customers`
- `GET /sound_clone/admin/api/v1/agent-customers`
- `GET /sound_clone/admin/api/v1/agent-customers/{customerId}`
- `PATCH /sound_clone/admin/api/v1/agent-customers/{customerId}`
- `POST /sound_clone/admin/api/v1/agent-customers/{customerId}/disable`
- `POST /sound_clone/admin/api/v1/agent-api-keys`
- `GET /sound_clone/admin/api/v1/agent-api-keys`
- `GET /sound_clone/admin/api/v1/agent-api-keys/{apiKeyId}`
- `PATCH /sound_clone/admin/api/v1/agent-api-keys/{apiKeyId}`
- `POST /sound_clone/admin/api/v1/agent-api-keys/{apiKeyId}/rotate`
- `POST /sound_clone/admin/api/v1/agent-api-keys/{apiKeyId}/revoke`
- `GET /sound_clone/admin/api/v1/agent-usage`
- `GET /sound_clone/admin/api/v1/agent-usage/customers/{customerId}`
- `GET /sound_clone/admin/api/v1/agent-usage/api-keys/{apiKeyId}`

Also provide customer self-service usage:

- `GET /sound_clone/api/v1/agents/usage` with `accessKey`.

Admin APIs must not authenticate with the customer `accessKey`. Use internal auth, service tokens, VPN/IP allowlists, or the existing admin system.

API key creation returns the plaintext key only once. Store only a hash, prefix, and last four characters.

Do not let implementation drift to alternate Admin paths without an explicit product decision. In the 2026-05-26 MyVocal P0-A review, `/sound_clone/admin/api/v1/agent/customers` and `/agent/keys` were rejected in favor of the approved resource names above.

## UAT Default

Even for a new product with no users, require a lightweight internal UAT environment before production.

Minimum UAT:

- Separate base URL, path/profile, or deployment target.
- Separate DB schema or table namespace.
- Separate test `accessKey` values for active, expired, suspended, capability missing, and quota exhausted cases.
- Test-only ElevenLabs resources or an explicit allowlist.
- Outbound SIP, WhatsApp, and WSS disabled by default.
- UAT logs in a separate log group with short retention.

This is required because a full-permission ElevenLabs key can create, update, or delete real upstream resources if the proxy or binding logic is wrong.


## Known Historical Mapping Corrections

The old `api_url_mapping.md` is useful but stale in at least these places:

1. Stream simulate conversation:
   - Old upstream: `POST /v1/convai/agents/{agent_id}/simulate-conversation-stream`
   - Current upstream: `POST /v1/convai/agents/{agent_id}/simulate-conversation/stream`

2. WhatsApp account import:
   - Old upstream: `POST /v1/convai/whatsapp-accounts`
   - Current OpenAPI did not expose this POST path during the 2026-05-26 review.
   - Re-check official WhatsApp account import/connect docs before implementation.

Current OpenAPI did show:

- `GET /v1/convai/whatsapp-accounts`
- `GET /v1/convai/whatsapp-accounts/{phone_number_id}`
- `PATCH /v1/convai/whatsapp-accounts/{phone_number_id}`
- `DELETE /v1/convai/whatsapp-accounts/{phone_number_id}`
- `POST /v1/convai/whatsapp/outbound-call`
- `POST /v1/convai/whatsapp/outbound-message`

## MyVocal Field Mapping Policy

Use the historical mapping as a first draft for field names:

- Fields listed in the mapping use MyVocal names.
- Fields not listed may be forwarded with upstream names only after schema validation and redaction.
- Do not force a total rewrite of the upstream schema when passthrough is safer.
- Preserve upstream error detail only after redacting secrets and unsafe payloads.

Common mapping direction:

- `name` -> `display_name`
- `id` -> resource-specific id such as `document_id`, `tool_id`, `agent_id`
- `documentation_id` -> `document_id`
- `parent_folder_id` -> `folder_id`
- `url` -> `source_url`
- `documents` -> `items`
- `created_at_unix_secs` -> `created_at`
- `last_updated_at_unix_secs` -> `updated_at`

## MyVocal Authentication And Usage

The REST passthrough should use MyVocal enterprise API-key semantics, not raw ElevenLabs credentials.

Current desired shape:

- Client sends MyVocal `accessKey`.
- MyVocal validates status, expiry, capabilities, quota, and ownership.
- MyVocal sends `xi-api-key` to ElevenLabs server-side only.
- Usage should support TTS, ASR, and Agents under a unified enterprise API key.
- REST management calls should track request/count/error usage. WSS and outbound call features should track seconds. Do not force all Agent usage into a seconds-only model.

Minimum admin API-key fields:

- `user_id`
- `api_key_id`
- `total_quota_seconds`
- `used_seconds`
- `remaining_seconds`
- `status`
- `expires_at`
- `capabilities`

Suggested capability granularity:

- `tts`
- `asr`
- `agents`
- `agents_knowledge_base`
- `agents_tools`
- `agents_config`
- `agents_simulation`
- `agents_outbound_sip`
- `agents_whatsapp`
- `agents_wss`

Suggested usage splits:

- `tts_seconds`
- `asr_seconds`
- `agents_rest_seconds`
- `agents_wss_seconds`
- `agents_outbound_call_seconds`
- `total_seconds`

## Resource Ownership

Do not let a customer pass arbitrary upstream IDs.

Bind or verify these IDs against the current MyVocal customer/user/API key before forwarding:

- `documentation_id`
- `document_id`
- `tool_id`
- `agent_id`
- `phone_number_id`
- `conversation_id`
- `voice_id`
- `mcp_server_id`

If a resource was created through MyVocal, persist the upstream ID with a MyVocal owner binding. If the resource predates MyVocal, add an explicit import/allowlist step instead of trusting the client.

For customer-facing data-plane APIs, use MyVocal resource IDs as the public contract:

- Path IDs such as `/configs/{id}` are MyVocal IDs, not upstream `agent_id` values.
- Translate MyVocal IDs to upstream IDs only after checking `environment + customer_id + resource_type + myvocal_resource_id + status`.
- Customer list responses should return MyVocal IDs. Hide upstream IDs unless the caller is an authorized admin or diagnostic flow.
- Create responses should return the newly created MyVocal resource ID after the binding is written.
- Tests must prove that supplying a raw upstream ID from the customer side fails and does not call upstream.
- The resource-binding index should match the customer lookup path: `(environment, customer_id, resource_type, myvocal_resource_id, status)`.

## Conversation Transcript And Audio Retrieval

Default MyVocal policy:

- Do not persist full transcripts or audio in MyVocal DB/S3.
- Persist minimal metadata and ownership binding: `conversation_id`, `customer_id`, `api_key_id`, `agent_binding_id`, upstream `agent_id`, status, start time, duration, `has_audio`, `has_user_audio`, `has_response_audio`, and usage counters.
- If full transcript/audio is needed, retrieve it from ElevenLabs on demand through controlled admin APIs.

Current ElevenLabs APIs confirmed on 2026-05-26:

- `GET /v1/convai/conversations/{conversation_id}` returns conversation details including transcript and audio availability flags.
- `GET /v1/convai/conversations/{conversation_id}/audio` returns the conversation audio recording when audio was saved and retained.
- `GET /v1/convai/conversations` lists conversations and can be used to discover conversation IDs and summaries.

Retention caveats:

- ElevenLabs default conversation data retention is 2 years, but configure an explicit MyVocal policy instead of relying on the default.
- Suggested MyVocal default: UAT 30 days, production beta 90 days, GA per customer contract.
- Do not enable zero retention or disable audio saving if the product expects later audio retrieval.
- If audio saving is disabled, retention has expired, or the conversation is deleted, MyVocal cannot guarantee later transcript/audio retrieval.

Retrieval API guidance:

- Phase 1 should expose internal/admin retrieval first.
- Customer-facing retrieval should require explicit capabilities such as `agents_conversation_read` and `agents_conversation_audio_read`.
- Every retrieval must verify customer ownership, write audit logs, and avoid caching full content unless a short encrypted TTL cache is explicitly approved.

## Test Voice IDs

The current test phase supports fixed upstream voice IDs only:

- `i1WvcRxtJvqOsE1O2VOX`
- `Ku8UJnErSVc1Hcgtes9Z`

Do not add voice creation to scope unless the user explicitly asks for it.

## Logging And Redaction

Never log:

- ElevenLabs API keys or `xi-api-key`
- MyVocal enterprise API keys / `accessKey`
- `access_token` or mapped `auth_token`
- signed URLs
- WebRTC tokens
- `conversation_signature`
- `audio_base_64`
- `user_audio_chunk`
- full transcripts or full conversations
- phone numbers
- SIP messages
- source file download URLs
- workspace secrets
- raw tool credentials

Prefer log records like:

```json
{
  "requestId": "...",
  "apiKeyId": "...",
  "userId": "...",
  "capability": "agents_knowledge_base",
  "upstreamPath": "/v1/convai/knowledge-base",
  "direction": "myvocal_to_elevenlabs",
  "status": 200,
  "durationMs": 123,
  "usageSeconds": 0
}
```

Default request logs should be metadata-only. Avoid storing request bodies, response bodies, or redacted payload snapshots unless product and security explicitly approve the retention. In MyVocal P0, store fields such as request ID, client request ID, customer ID, API key ID, capability, path, status, upstream status, error code, duration, and usage.

Generate the primary `request_id` server-side. If the client sends `X-Request-Id`, preserve it only as `client_request_id` for correlation. Do not let the client choose the unique request ID.

Use Redis keys under an environment namespace, for example:

- `mv:agent:{env}:rl:{customerId}:{apiKeyId-or-fingerprint}:{capability}:{window}`
- `mv:agent:{env}:quota:daily:{customerId}:{yyyyMMdd}`
- `mv:agent:{env}:idem:{customerId}:{idempotencyKeyHash}`

Redis keys must not contain plaintext access keys, complete hashes, phone numbers, signed URLs, transcript, or audio.

Feature flags should be split by risk surface:

- `myvocal.ai-agent.admin-enabled`
- `myvocal.ai-agent.rest-enabled`
- `myvocal.ai-agent.conversation-retrieval-enabled`
- `myvocal.ai-agent.outbound-enabled`
- `myvocal.ai-agent.wss-enabled`

Keep outbound and WSS disabled by default in Phase 1.

## DB And Migration Review Gates

When creating MyVocal Agent tables, align with DBA decisions before asking for review:

- Use explicit `DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_bin` unless DBA approves otherwise.
- Include `environment` and put it in high-volume index prefixes.
- Store API-key hashes as fixed length `CHAR(64)` or `BINARY(32)`.
- Keep `request_id` and `client_request_id` separate.
- Use owner-check indexes that match service lookup paths.
- Prefer application validation plus unique indexes over foreign keys when the existing MyVocal project style avoids foreign keys.
- Do not execute DDL during implementation or review unless the release owner and DBA explicitly approve it.

## Review Status Labels

Use narrow, evidence-based status labels:

- `Implemented local branch`: code exists locally but is not committed, pushed, deployed, or migrated.
- `Implemented with gaps`: compile/tests may pass, but product/security/DBA gates still have material issues.
- `Ready for DBA/Security/QA review`: product gate is satisfied and remaining work is owner review, not known product drift.
- `UAT write-ready`: DBA, security, DevOps, and QA gates are complete; UAT data writes can begin.

Do not call a branch UAT-ready just because compile, unit tests, and sensitive scans pass.

## Phase 1 Endpoint Matrix Gate

Before coding, produce or update a matrix with:

- MyVocal endpoint.
- Upstream endpoint.
- Method.
- Capability.
- Auth requirement.
- Request field mapping.
- Response field mapping.
- Sensitive fields to redact or hide.
- Quota unit.
- Local persistence required.
- Tests.

If this matrix is missing, create it before implementation unless the user explicitly asks for a quick spike.

## MyVocal Repo Orientation

Before editing code, find the real owning repo and surface. Do not assume the current folder is the code repo.

Look for:

- `myvocal-java` Spring controllers and interceptors.
- Public API base path and `accessKey` auth.
- Enterprise TTS routes under `api.voicelibrary.co/enterprise` integration.
- ASR routes under `openapi.myvocal.ai/asr/v1/transcriptions` integration.
- API logging aspects and redaction hooks.
- Existing usage/quota tables.

## Verification

Use mocked upstream ElevenLabs responses for unit tests.

Cover at least:

- Invalid, expired, suspended, or capability-missing MyVocal API key.
- Quota exhausted.
- Customer tries to access another customer's upstream document/tool/agent.
- Request field mapping and unmapped safe passthrough.
- Sensitive log redaction.
- Upstream 400/401/403/404/422/429/5xx error mapping.
- Stale endpoint guard for simulate conversation stream.
- WhatsApp import marked unsupported until official path is reverified.

For this project family, also update `D:\ObsidianVault\AI Agent` with what changed, what was verified, what remains open, and any stale mappings found.
