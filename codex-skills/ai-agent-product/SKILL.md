---
name: ai-agent-product
description: Build and review secure MyVocal-style pass-through/proxy implementations for ElevenLabs ElevenAgents. Use when the user asks to wrap ElevenLabs AI Agent, pass through core REST APIs, build MyVocal customer/admin API key and usage management, hide the ElevenLabs API key, manage MyVocal enterprise API keys/capabilities/usage, generate signed URLs server-side, relay ElevenLabs WebSocket traffic, map fields, add resource ownership checks, rate limiting, redacted logging, error mapping, or SDK/frontend integration.
---

# AI Agent Product

## Core Rule

Treat the service as a secure proxy layer, not an Agent rewrite. Preserve ElevenLabs protocol events whenever possible, and add only the controls needed for app auth, agent allowlists, secret protection, rate limits, validation, redacted observability, and stable forwarding.

## MyVocal Fast-Track Operating Rule

For MyVocal AI Agent delivery, optimize for fast product progress once the user has accepted the hard boundary: do not affect current `myvocal.ai` normal business.

Do not turn every small step into a separate gate. Combine adjacent review, adjudication, merge, UAT activation, fixture, and smoke steps into one prompt when they share the same approved scope and the same hard boundaries. Stop only when a real blocker appears, a boundary would be crossed, or the user explicitly asks for a separate approval.

Default fast-track posture for P0-A / isolated UAT after the user has approved it:

1. The primary hard stop is anything that could affect current `myvocal.ai` normal business or touch production traffic, production DB/Redis/ECS/ALB/Route53, production customers, or production access keys.
2. Using the ElevenLabs test provider credential via the approved `llmapi` locator is allowed when the current prompt authorizes real-upstream isolated UAT work. Never print, store, commit, or log the value.
3. Isolated UAT, dedicated AI Agent UAT roles, stable UAT Secrets Manager injection, Agent Admin service-token auth, synthetic MyVocal customers/API keys, and Agent config create/get/list/delete smoke should be treated as one delivery lane, not as unrelated mini-projects.
4. Small PRs that already passed focused review should use a compressed flow: commit/PR, review/merge-readiness, and merge adjudication can be drafted as adjacent or conditional steps. Do not require another chat round merely to restate the same approval unless merge, deploy, secret mutation, real-upstream calls, DDL/DML, or route changes are newly introduced.
5. Keep Obsidian durable, but do not create excessive intermediate approval artifacts for every mechanical substep. Record key product decisions, execution prompts, reports, blockers, merges, UAT activations, cleanup, and final evidence.
6. Prefer a single execution prompt that says "if preflight passes, continue to the next scoped action; if it fails, stop and report" instead of making the user manually re-authorize each obvious next action.
7. Preserve exact non-negotiable exclusions: no production touch, no `uat-api.myvocal.ai` route change unless explicitly authorized, no scope expansion to KB/Tools/Simulation/WSS/WebRTC/signed URL/SDK unless explicitly opened, and no secret values in Markdown, logs, Git, screenshots, or chat.

## Prompt Packaging Limit

When packaging execution prompts, handoff prompts, or agent prompts for MyVocal AI Agent work, the current prompt ceiling is 14,500 characters (`14500`). Treat older 10,000-character guidance as obsolete. Keep prompts concise, but do not split a scoped prompt merely because it exceeds 10,000 characters. Split only when the prompt would exceed 14,500 characters (`14500`), mix unrelated scopes, cross an approval boundary, or harm readability or safety.

This limit also applies to generated validators, compression scripts, backend submit scripts, and local preflight checks for MyVocal AI Agent prompt fields. Do not generate or preserve script logic such as `len(prompt) < 10000`, `len(prompt) <= 10000`, `MAX_PROMPT_CHARS = 10000`, or "must be under 10,000". Use `PROMPT_CHAR_LIMIT = 14500` instead. If the target API or page requires a strict less-than check, validate against `< 14500` and target a small buffer such as `14480`; do not silently fall back to 10,000.

中文规则：MyVocal AI Agent 提示词字段、本地压缩脚本、写入脚本、回读校验脚本的长度上限统一按 `14500` 字符处理。旧的 `10000` / `1万字` 口径已经废弃。遇到历史项目记录、旧脚本或旧截图写着小于 10000 时，必须以本节为准；如果后台在低于 14500 时仍拒绝，记录真实响应并按接口漂移排查，不要自行降级成 10000。

## Start Here

1. Inspect the existing project before choosing files or framework patterns.
2. If the workspace is MyVocal or the user mentions MyVocal, load `references/myvocal-rest-passthrough-guide.md` before implementation or review.
3. Load `references/elevenlabs-proxy-guide.md` for signed URL, WebRTC token, WebSocket relay, and runtime event behavior.
4. Decide which phase is in scope: MyVocal REST passthrough, Signed URL mode, Full WebSocket Relay mode, SDK, or admin tooling.
5. If exact upstream ElevenLabs behavior is uncertain or likely to have changed, verify the current official ElevenLabs docs or OpenAPI before changing production behavior.
6. Keep changes close to the existing backend and frontend conventions.

## MyVocal Phase Order

For this project, do not default to signed URL first. The current MyVocal plan is:

1. Phase 1: build the MyVocal customer/admin control plane plus core ElevenLabs REST passthrough, with enterprise `accessKey`, capabilities, quota, ownership checks, field mapping, usage APIs, and redacted logs.
2. Phase 2: wrap signed URL, WebRTC token, and WSS/WebSocket relay.
3. Phase 3: package the MyVocal REST plus WSS surface into SDKs.

When old notes conflict, prefer the latest Obsidian records under `D:\ObsidianVault\AI Agent`, especially the API mapping review and REST-passthrough notes.

## Required Modes

Use MyVocal REST Passthrough mode when the user asks to expose ElevenLabs core APIs through MyVocal first. This mode covers the MyVocal customer/admin control plane, API key creation/rotation/revocation, usage queries, Knowledge Base, Tools, Agents, simulation, SIP outbound calls, WhatsApp account/call surfaces, and MyVocal internal enterprise API key/usage management.

Use Signed URL mode when the client can connect directly to ElevenLabs WebSocket and the app only needs server-side auth plus secret protection.

Use Full WebSocket Relay mode when all realtime traffic must pass through the business backend for auth, audit, rate limiting, client compatibility, tool mediation, or domain control.

## Non-Negotiables

- Keep `ELEVENLABS_API_KEY` server-side only.
- Do not treat Phase 1 as a route-only proxy. Include MyVocal customer, API key, capability, quota, usage, audit, and resource-binding behavior.
- For MyVocal, keep the enterprise `accessKey` contract and do not expose raw ElevenLabs identifiers unless they are bound to the current customer.
- Admin APIs must not authenticate with customer `accessKey`. Use the existing MyVocal admin JWT or a deliberately scoped internal service-token mechanism.
- Map client aliases or MyVocal resource IDs to server-owned upstream `agent_id`, `documentation_id`, `tool_id`, `phone_number_id`, or `voice_id`; do not accept arbitrary upstream IDs by default.
- For MyVocal customer data-plane APIs, customer path IDs and response IDs must be MyVocal resource IDs by default. Convert MyVocal IDs to upstream IDs server-side through resource bindings.
- Enforce capability, status, expiry, quota, and owner binding before every mutating REST passthrough call.
- Treat signed URLs, conversation signatures, tokens, audio base64, and API keys as sensitive.
- Do not log `xi-api-key`, signed URLs, `conversation_signature`, `token`, `audio_base_64`, or `user_audio_chunk`.
- Do not log `access_token`, `auth_token`, API keys, full transcripts, phone numbers, SIP messages, source file URLs, or workspace secrets.
- Do not drop unknown ElevenLabs event types; pass them through subject to size and structure limits.
- Do not execute unknown client tools on the server. Pass client tool calls through unless server-side tool execution is explicitly requested and whitelisted.
- Check REST CORS and WebSocket `Origin`; never use wildcard origins outside local development.

## Implementation Checklist

Implement or verify:

1. Central config for upstream API base URL, API key, MyVocal path base, default environment, allowed origins, message limits, timeouts, feature flags, and fixed test voice IDs.
2. MyVocal customer/admin control-plane APIs for customers, API key create/list/update/rotate/revoke, capabilities, status, expiry, quota, and usage queries.
3. Admin authentication for the control plane: prove an existing admin JWT path or a scoped internal service-token path before any UAT admin key distribution smoke.
4. Resource binding for upstream document/tool/agent/phone/voice IDs to a MyVocal customer or user.
5. Phase 1 REST endpoint matrix before coding: MyVocal endpoint, upstream endpoint, capability, request mapping, response mapping, sensitive fields, quota unit, and persistence need.
6. JSON schema validation for all external inputs while preserving passthrough behavior for unmapped safe upstream fields.
7. Field mapping: mapped fields use MyVocal names; unmapped fields may pass through after validation and redaction.
8. Safe fixed upstream `voice_id` handling for the current test phase; no voice creation unless explicitly scoped.
9. Signed URL, WebRTC token, and WebSocket relay only when the scoped phase requires them.
10. Dynamic variable and override filtering for runtime conversation setup.
11. REST message size limits, user/IP/key rate limits, concurrent limits, idle timeout, and max duration for WSS.
12. Redacted logs with request or connection IDs and lightweight event metrics only.
13. Error mapping that hides upstream secrets and stack traces.
14. Tests with mocked ElevenLabs REST and WebSocket upstreams; never call real ElevenLabs from unit tests.
15. For any Agent Admin service-token path, prove the full Spring Security runtime path, not only the token parser: correct service token with no JWT must reach the Admin controller and method security; no-token, wrong-token, customer `accessKey`, and production mode must fail closed.
16. Obsidian closeout update in `D:\ObsidianVault\AI Agent` for this project family.

## MyVocal P0 Review Gates

Before calling a MyVocal AI Agent implementation ready for PR, UAT, or owner review, explicitly check these gates:

1. Admin paths match the approved schema. Prefer resource paths such as `/sound_clone/admin/api/v1/agent-customers`, `/agent-api-keys`, `/agent-usage`, `/agent-request-logs`, and `/agent-audit-logs`. Do not silently drift to nested paths such as `/agent/customers` unless product re-approves the schema.
2. Customer data-plane paths use MyVocal resource IDs, not upstream IDs. For example, `/sound_clone/api/v1/agents/configs/{id}` should treat `{id}` as a MyVocal agent ID and map it server-side to the upstream `agent_id`.
3. Customer list/create/get responses do not expose raw upstream IDs by default. Return or wrap MyVocal IDs as the customer-facing identifiers; keep upstream IDs internal/admin-only.
4. Resource owner checks use `environment + customer_id + resource_type + myvocal_resource_id + status` before translating to upstream IDs. Tests must prove an upstream ID supplied by a customer fails.
5. DDL follows DBA decisions: `utf8mb4_bin`, `environment` fields and env-prefixed indexes, fixed-length key hashes, `request_id` separated from `client_request_id`, no foreign keys unless explicitly approved, and no executed DDL during implementation review.
6. Request logs are metadata-only by default. Do not store request/response bodies or "redacted snapshots" unless product and security explicitly approve that retention.
7. Feature flags are split by surface: admin, REST/data plane, conversation retrieval, outbound, and WSS. A single global `enabled` flag is not enough for P0 review.
8. Server request IDs are generated by the service. Client `X-Request-Id` is stored separately as `client_request_id` and must not control uniqueness.
9. Redis keys use the approved namespace pattern such as `mv:agent:{env}:...` and never include plaintext access keys, full hashes, phone numbers, signed URLs, transcript, or audio.
10. Production beta remains No-Go if infrastructure P0 blockers such as public data security group / 3306 exposure are open, even when code tests pass.
11. Before UAT admin key distribution or Agent config passthrough inspection, prove Admin API auth separately: an approved admin credential locator can obtain a valid MyVocal admin JWT, or a UAT-only/internal-only Agent Admin service token is implemented, deployed, and provisioned.
12. A UAT-only Agent Admin service token is not proven by filter unit tests alone. Reviewers must see a controller/method-security integration proof where `X-Agent-Admin-Service-Token` works without a JWT on `/sound_clone/admin/api/v1/agent-customers` and `/sound_clone/admin/api/v1/agent-api-keys`; `JWTAuthenticationTokenFilter` or equivalent legacy JWT filters must not clear a valid service-token `SecurityContext`.

## MyVocal UAT / Segment B Execution Guardrails

Use this section when the user explicitly authorizes UAT activation, real-upstream smoke, or a live inspection window. In normal conservative mode, keep review-only, approval-only, mock-only, and real-upstream execution as separate gates. In MyVocal fast-track mode, compress them into a single scoped execution prompt when the user has already accepted the risk and the only hard condition is no impact to current `myvocal.ai` normal business.

Fast-track packaging:

1. For PR work, combine "review ready -> merge adjudication -> merge if gates still pass" into one prompt when the PR is narrow, already reviewed, and no new deploy/secret/UAT mutation is introduced.
2. For isolated UAT Agent config work, combine stable secret/ECS preflight, service-token provisioning, Admin customers/keys preflight, synthetic fixture creation, Agent config create/get/list/delete real-upstream smoke, cleanup, rollback/no-impact checks, and report into one execution prompt when all are inside the same approved scope.
3. Do not make the user approve again merely because an obvious next action follows from a passed preflight. Continue until the scoped goal is complete, or stop at the first true blocker.
4. If a blocker is found, report the exact missing owner/mechanism/evidence and propose the smallest next action. Do not loop on the same approval collection if the user has already requested fast delivery.

Preflight:

1. Read the latest `D:\ObsidianVault\AI Agent\AI Agent 项目首页.md`, `当前权威决策.md`, the exact execution prompt, and the latest readiness/execution report before touching infrastructure.
2. Prove the target is isolated UAT and not serving current `myvocal.ai` traffic. Record cluster, service, task revision, image tag, task id, base URL, and whether any route changed.
3. Check `https://myvocal.ai` health before activation and after activation/rollback. Stop if the no-impact guard is not proven.
4. Keep `uat-api.myvocal.ai` route changes, production DB/Redis/ECS/ALB/Route53, production customers, and production access keys out of scope unless the prompt explicitly reopens them.
5. For isolated-direct UAT prompts that explicitly do not use or modify `uat-api.myvocal.ai`, treat public `uat-api.myvocal.ai` health as informational when it is already down and the public UAT service is intentionally `0/0`. Do not block isolated-direct execution on that alone; instead require `myvocal.ai` and `api.myvocal.ai` no-impact health, unchanged public route, and a healthy isolated direct base URL after deployment. Do not restore or scale the public UAT service unless the prompt explicitly authorizes it.
6. If public UAT service desired/running or `uat-api.myvocal.ai` health drifts during an isolated-direct run, do not automatically restore it or block the isolated lane after Product accepts the new public UAT state. Preserve the public UAT state as-is, record service/route/CloudTrail metadata, and continue only on the isolated service. Stop only if the isolated run itself would mutate public UAT, current `myvocal.ai` / `api.myvocal.ai` health is impacted, or the prompt explicitly requests public UAT route/service changes.
7. For a dedicated AI Agent UAT domain behind an existing ALB, explicitly prove the host-header rule wins over any generic `/sound_clone/*` path rule. Record HTTPS/HTTP listener priorities, target group, target health, and whether the existing `uat-api.myvocal.ai` rule target changed. If a generic path rule priority must be moved so the dedicated host rule wins, record the old and new priorities and prove the generic rule still points to its original target.
8. Confirm high-risk flags remain off unless specifically in scope: outbound, SIP, WhatsApp, WSS, conversation retrieval, signed URL, WebRTC, and SDK.

Secrets and credentials:

1. If the prompt authorizes `llmapi`, read it from Obsidian with the vault pinned: `obsidian "vault=AI Agent" ...`. Do not rely on the default Obsidian vault.
2. Use the provider key only at runtime. Prefer a temporary Secrets Manager secret or isolated task secret reference. Do not write the value to Markdown, Git, state JSON, shell output, logs, screenshots, or issue comments.
3. For Product/QA live inspection access keys, store only in Obsidian secretStorage. Secret ids must be lowercase letters, digits, and hyphens, and at most 64 characters. Reports should contain the locator only, never the value.
4. Temporary IAM policies must be least-privilege and scoped to the exact temporary secret ARN. Remove them during cleanup, including failed attempts before ECS deployment.
5. Before every retry, verify old temporary provider secrets and temporary IAM inline policies are absent or delete them first.
6. If isolated MyVocal proxy reaches ElevenLabs but maps upstream auth failure such as `462401`, treat it as a provider credential / ECS secret injection / upstream auth header gate. In fast-track mode, use one bounded prompt to validate the current stable UAT provider secret in memory, refresh the same stable secret from the approved `llmapi` locator only if the current value fails direct validation, and rerun the Agent config smoke. If the stable secret validates directly but MyVocal still returns `462401`, stop and route to backend config/injection/header mapping instead of looping on owner approvals.

Admin key distribution and service-token gates:

1. Do not start a MyVocal API key distribution or Agent config passthrough matrix until Admin customers and Admin keys probes pass with authenticated Admin API auth. A no-auth `401` app code is a stop line, not a reason to keep rerunning the matrix.
2. Resolve Admin API auth before upstream work. Acceptable paths are an approved UAT admin credential locator that yields a standard MyVocal admin JWT, or a deliberately implemented Agent Admin service-token path.
3. If no approved admin credential locator exists and no service-token mechanism exists, stop and write a focused backend delta prompt. Do not guess admin credentials, ask the user to paste passwords, use customer `accessKey` as admin auth, bypass Spring Security, or direct-write DB permissions.
4. A UAT Agent Admin service-token must be narrow: `/sound_clone/admin/api/v1/agent-*` only, feature-flagged, environment-guarded, production hard-disabled, injected through ECS secrets or an equivalent secret manager, hash or constant-time compared, and audited metadata-only.
5. The service-token authority set should be limited to Agent Admin needs such as `agent_customer_manage`, `agent_key_manage`, `agent_usage_read`, and `agent_audit_read`. It must not grant broader admin, billing, user, order, or production operation permissions.
6. The service-token path must be tested through the full Spring filter chain and `@PreAuthorize` path with no JWT header. A correct service token must pass Admin customers / keys; no token, wrong token, customer `accessKey`, missing authority, and production mode must fail closed.
7. When the project uses a legacy JWT filter, explicitly verify that the no-JWT branch does not clear an already-established valid Agent Admin service-token authentication. If the JWT filter clears `SecurityContextHolder` after the service-token filter runs, adjust filter order or make the JWT filter skip valid Agent Admin service-token requests.
8. If correct service-token preflight returns an app/internal error such as `462500` or a Spring `AuthenticationCredentialsNotFoundException`, stop immediately and route to a backend auth-integration fix. Do not rerun isolated UAT, create customer/key fixtures, or spend real upstream calls until correct-token Admin preflight passes.
9. After provisioning Admin auth, run only Admin customers / keys preflight first. Create synthetic customer/key fixtures and call ElevenLabs only after that preflight passes and the exact execution prompt authorizes it.
10. Owner routing for this gate: Backend and Security own the auth mechanism, DevOps owns isolated target and secret injection evidence, QA owns the post-auth matrix evidence. Product should not be asked to accept a passthrough result when Admin auth never passed.

Execution and live windows:

1. For real-upstream smoke, keep a hard call budget and count only real upstream families. A local usage read is not an ElevenLabs upstream call.
2. For live inspection windows, create both an opener and a closer/rollback path. Record the state path, close summary path, manual close command, owner, start/end time, and background close process evidence.
3. Synthetic fixtures must be UAT-only and capability-scoped. Use low quotas, concurrency 1, and a resource name prefix that makes cleanup unambiguous, but do not set rate limits so low that the approved smoke or Product/QA inspection matrix fails locally with `461021` before the intended upstream checks complete. Real upstream spend should be controlled by the explicit call budget, not by an artificially tiny local rate limit.
4. Opening readiness should avoid unnecessary upstream side effects. Prefer health plus local usage/accessKey readiness, then leave Product/QA to spend the allowed upstream budget.
5. When Product/QA manual inspection passes before the scheduled close time, close the window immediately instead of leaving the isolated service open until auto-close. Preserve evidence first, then run the manual close command, verify cleanup gap `0`, and only then move to stable UAT readiness.
6. At close, delete active upstream-created resources through the MyVocal proxy first, then tombstone/revoke local bindings/keys, then roll back the isolated service to a no-provider-secret task revision.
7. After a full-pass closeout, do not keep using transient Fargate public IPs as the product access surface. Move to stable UAT readiness: compare a dedicated AI Agent UAT route/service against reusing existing `uat-api.myvocal.ai`, prefer the dedicated route when it avoids disturbing other UAT traffic, and keep route/service mutation in a separate execution prompt.
8. After stable UAT manual validation passes on the dedicated domain, stop re-proving whether Agent config passthrough works. Treat P0-A Agent config UAT as available and move to API handoff, customer/key distribution readiness, or the next explicit scope decision. Keep production beta blocked until the production blockers are closed.

Evidence and cleanup:

1. Evidence stays metadata-only: status class/product code, path family, duration bucket, counts, masked MyVocal ids, and cleanup gap. Do not persist full request/response bodies or raw upstream error bodies.
2. When querying metadata across joined tables, qualify columns such as `l.status`, `u.status`, and `b.status`; ambiguous SQL in evidence scripts should not be confused with product path failure. If a harness query fails after the smoke, run a corrected metadata readback and say so.
3. Report created/deleted/tombstoned counts, active binding rows, active key rows, provider secret deletion, temporary IAM policy removal, and post-rollback health.
4. Run high-confidence sensitive scans on final reports, helper scripts, state/open/close summaries, and relevant logs. Output category counts only.
5. Keep Production beta as No-Go until production infrastructure blockers, historical sensitive-shape debt, timestamp/migration divergence, and stable UAT secret-injection policy are closed and re-reviewed.

Windows/PowerShell hygiene:

1. Use `$true` and `$false` in PowerShell, not JavaScript-style `true`/`false`.
2. Test Obsidian secretStorage set/get/delete with a dummy value before writing a live locator. Quote `obsidian eval` carefully; JSON-style JavaScript snippets can break under PowerShell quoting.
3. Use `-LiteralPath` for Chinese paths and paths with spaces.
4. Treat Fargate public IPs as transient. Durable evidence is the ECS service, task revision, task id, image tag, and state/report paths.

## MyVocal Implementation Anchors

When working in MyVocal, look for existing Java/Spring patterns before inventing new ones:

- `myvocal-java` public API controllers, base controller, interceptors, and API logs.
- Existing enterprise TTS domain `https://api.voicelibrary.co/enterprise`.
- Existing ASR domain `https://openapi.myvocal.ai/asr/v1/transcriptions`.
- Existing `accessKey` behavior and any quota or usage tables.
- Existing logging aspects that may need redaction before Agent payloads are routed through them.

## Closeout

Report:

- Files added or changed.
- Required environment variables.
- How to start the service.
- Phase delivered: REST passthrough, signed URL/WebRTC token, WSS relay, SDK, or admin tooling.
- MyVocal endpoints and upstream endpoints touched.
- API key, capability, quota, and resource-ownership behavior.
- Customer/admin API behavior for key creation, rotation, revocation, and usage lookup.
- Admin auth readiness: admin JWT locator or service-token status, authenticated Admin customers/keys preflight result, and whether any service-token delta remains unmerged or undeployed.
- How to request a signed URL or connect to the WebSocket relay, when applicable.
- Security restrictions and feature flags.
- Tests run and results.
- Obsidian note updated.
- For UAT/live windows: exact isolated target, active window time, accessKey locator only, upstream call budget used/remaining, cleanup gap, rollback state, and sensitive scan counts.
- Open decisions, stale mappings, or credentials still needed.
