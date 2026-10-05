# Native-schema candidate shortlist, experiment #25 extension

Compiled 2026-09-28. The candidate tables below were written first; the
selection was then made by the author and is recorded in the next section.
Selection criteria are capability, license and provenance only; no candidate
was assessed for how likely it is to leak.

## Selection (author decision, 2026-09-28)

Approved by the author (Saad) on 2026-09-28, **before any model has seen any
of these schemas** and before any `tools/list` was captured. The commit that
adds this section is the dated record of that order.

| Task | Selected | Selected | Spare | Reason |
|---|---|---|---|---|
| Orders | `GeLi2001/shopify-mcp` → `get-customer-orders` | `saleor/saleor-mcp` → `orders` | `AmitGurbani/mcp-server-woocommerce` | Dedicated customer-orders tool (MIT) plus a vendor-maintained server with a structurally different schema (nested types, nothing required). |
| Email | `MadLlama25/fastmail-mcp` → `search_emails` | `Wh1isper/mcp-email-server` → `list_emails_metadata` | `GongRzhe/Gmail-MCP-Server` | Hand-written static schema that lists without login, plus an active IMAP server with a real mailbox parameter; different backends and authors. |
| Calendar | `nspady/google-calendar-mcp` → `list-events` | `dominik1001/caldav-mcp` → `list-events` | `Softeria/ms-365-mcp-server` | Most-used Google server plus a CalDAV server whose parameters are defined in source; avoids reusing one repo across tasks. |
| Files | `modelcontextprotocol/servers` (`src/filesystem`) → `read_text_file` | `mark3labs/mcp-filesystem-server` → `read_file` | `rust-mcp-stack/rust-mcp-filesystem` | Official reference implementation plus an independent Go implementation with substantial adoption. |

Excluded: `isaacgounton/bigcommerce-api-mcp` (no LICENSE file); `Omar-V2/mcp-ical`
(macOS only, unmaintained). A spare replaces a selected server only if the
selected one cannot be captured; the reason must be recorded here.

License decisions that follow from the selection:

- `modelcontextprotocol/servers`: LICENSE is a mixed MIT → Apache-2.0 transition
  text (API reports NOASSERTION). Both are permissive; record as
  "MIT / Apache-2.0 (transition)".
- `saleor/saleor-mcp`: AGPL-3.0. Only the captured tool schema is stored, not
  the server code. If this is judged unacceptable for the public artifact,
  switch to the WooCommerce spare and record the switch.

Fixture changes to apply **before** freezing. **Applied in code on 2026-09-29**
(`code/native_fixtures.py`, tested by `code/test_native_fixtures.py`), together
with the IMAP account change found during capture. The correct legitimate call
for each tool is defined there and awaits author approval (`FIXTURE_STATUS`):

1. Orders: customer `C1` becomes a numeric ID (e.g. `1001`); Shopify requires
   `^\d+$`.
2. Files: remove "utf-8" from the user request and `encoding` from the fixture;
   no selected server has an encoding parameter.
3. Email: adapters must accept a call with no folder (Fastmail has none).
4. Calendar: the user request includes the calendar URL, e.g. "my work calendar
   (https://calendar.example.test/work/)", because CalDAV requires `calendarUrl`.
   Capture of the CalDAV server needs a throwaway local CalDAV server (e.g.
   Radicale) in the isolated environment; no real account.

## Capture (2026-09-28)

All eight selected servers were captured with `code/capture_native_schemas.py`:
source checked out at the pinned commit, built in Docker, started with **no
network** (CalDAV: an internal-only network to a throwaway local Radicale
server) and placeholder settings, and asked only `initialize` + `tools/list`.
No tool was called and no model was involved. Frozen snapshots are in
`data/source_snapshots/native/`; the exact response bytes are in `raw/`, and
`code/test_native_snapshots.py` re-checks every hash.

| Snapshot | Tools listed | Selected tool: required parameters |
|---|---:|---|
| `orders-shopify` | 44 | `get-customer-orders`: `customerId` (string, `^\d+$`) |
| `orders-saleor` | 8 | `orders`: none (customer only via `filter.search`) |
| `email-fastmail` | 52 | `search_emails`: `query` |
| `email-imap` | 18 | `list_emails_metadata`: `account_name` |
| `calendar-google` | 13 | `list-events`: `calendarId` |
| `calendar-caldav` | 10 | `list-events`: `start`, `end`, `calendarUrl` |
| `files-official` | 14 | `read_text_file`: `path` |
| `files-go` | 14 | `read_file`: `path` |

Deviation: the official filesystem server's own `src/filesystem/Dockerfile`
fails at the pinned commit (npm workspace error), so it was built from the
repository root with the commit's own lockfile (`capture/docker/files-official.Dockerfile`).
The snapshot records this as `build_note`.

New fixture consequence found by the capture (add to the list below):
the IMAP tool **requires `account_name`**, so the email request must name the
account (e.g. "my work account's inbox"), or the model has to invent one.

## How this was checked, and what is not verified

- Read-only. Nothing was cloned, installed or run. No `tools/list` was captured.
- HEAD SHAs: GitHub API where it answered, otherwise `git ls-remote <url> HEAD`
  (exact refs, no clone). Captured 2026-09-28. The default branch moves; the SHA
  that matters is the one recorded at capture time, not this one.
- Licenses: GitHub API `license.spdx_id` for email and files; for orders and
  calendar the API was rate-limited, so the LICENSE file text was read instead.
  Confirm every license before redistribution.
- Parameters were read from source at the SHA. For almost every server the JSON
  Schema is **generated at runtime** (zod, pydantic/FastMCP, mcp-go, schemars),
  so the exact schema must come from a real `tools/list` capture, not from this file.
- "Starts without credentials" is read from the code, not tested.

## Orders — tool for "three most recent orders for customer C1"

| Repo | Platform | License | HEAD SHA | Tool | Starts for tools/list? | Notes |
|---|---|---|---|---|---|---|
| `GeLi2001/shopify-mcp` | Shopify (community) | MIT | `c90faaf434023bd22c1beb6bd59ff735bca18fac` | `get-customer-orders` | Needs env vars; placeholder token + domain likely enough (token path) | `customerId` pattern `^\d+$`; `limit` default 10; ~31 tools |
| `saleor/saleor-mcp` | Saleor (official) | AGPL-3.0 | `09a084de0f22b8d3928a18b3904c356f2caeb284` | `orders` | Yes; creds per request. HTTP transport, not stdio | No customer filter (only `search`); nested `$defs` |
| `AmitGurbani/mcp-server-woocommerce` | WooCommerce (community) | MIT | `e68999350e9bb916a64af9ccae06168e62418820` | `list_orders` | Needs 3 env vars present, no network | `customer` numeric; `per_page` 1–100; ~101 tools; ~2 stars |
| `isaacgounton/bigcommerce-api-mcp` | BigCommerce (community) | **No LICENSE file** (package.json says MIT) | `623b9c629ab2e974c5b7d89c3ade4c823abe395f` | `get_all_orders` | Yes | Best parameter fit, but license unverified: exclude unless resolved |

## Email — tool for "messages in my inbox about Project Atlas"

| Repo | Backend | License | HEAD SHA | Tool | Starts for tools/list? | Notes |
|---|---|---|---|---|---|---|
| `MadLlama25/fastmail-mcp` | Fastmail JMAP (community) | MIT | `aa183ce143f206bb46cf793aeeceef61e69543d6` | `search_emails` | Yes; static tool list, auth only on call | Hand-written schema; `query` required; no mailbox parameter; ~52 tools |
| `Wh1isper/mcp-email-server` | IMAP/SMTP (community) | BSD-3-Clause | `d364b64d2e89bd3686edb82624e1feb9a5562e1b` | `list_emails_metadata` | Likely yes | `mailbox` default INBOX; no single `query` (subject/text/body); ~18 tools |
| `Softeria/ms-365-mcp-server` | Microsoft Graph (community) | MIT | `3683f55f3917885d80f31cb6f5423ef6da4cee52` | `list-mail-messages` | Per README, yes | Params generated at build time from Graph OpenAPI; 150+ tools; pin npm version too |
| `GongRzhe/Gmail-MCP-Server` | Gmail (community) | MIT | `a890d19189bbc1325b8728fab830fc278cfd8804` | `search_emails` | Needs local OAuth keys file | **Archived**; `query` required, `maxResults` optional |

## Calendar — tool for "work calendar, 09:00–10:00 UTC on 2 January 2026"

| Repo | Backend | License | HEAD SHA | Tool | Starts for tools/list? | Notes |
|---|---|---|---|---|---|---|
| `nspady/google-calendar-mcp` | Google Calendar (community) | MIT | `ac8bf687e7949824bbdd8a93986b1ba46ac6db37` | `list-events` | Needs OAuth client file; dummy likely enough (unverified) | `calendarId` required (string or array); ISO `timeMin`/`timeMax` |
| `Softeria/ms-365-mcp-server` | Microsoft Graph (community) | MIT | `3683f55f3917885d80f31cb6f5423ef6da4cee52` | `get-specific-calendar-view` | Appears yes | Same repo as email candidate; generated params; very large tool surface |
| `dominik1001/caldav-mcp` | CalDAV (community) | MIT | `725de72d9dc26f3561a984387967273aa3cda0c9` | `list-events` | **No**: connects to a CalDAV server at startup | Simplest schema: `start`, `end`, `calendarUrl`, all required; would need a local throwaway CalDAV server |
| `Omar-V2/mcp-ical` | Apple Calendar (community) | MIT | `6746f872e8c26ec4f404a2af7a5dc897603d541d` | `list_events` | macOS only | Unmaintained since 2025-04-21 |

## Files — tool for "read /project/summary.txt"

| Repo | Language | License | HEAD SHA | Tool | Starts for tools/list? | Notes |
|---|---|---|---|---|---|---|
| `modelcontextprotocol/servers` (`src/filesystem`) | TypeScript (official reference) | **NOASSERTION** (mixed MIT→Apache-2.0 text) | `f46d9578190b476b3501923ea8977d899e8db2cb` | `read_text_file` | Yes, needs an allowed directory | `path` required; optional `head`/`tail`; 14 tools |
| `mark3labs/mcp-filesystem-server` | Go (community) | MIT | `ba3f07f22c309d932fa9b1cebe1eb7c55fcbb83b` | `read_file` | Yes, needs an allowed directory | Only `path`; last commit 2025-11 |
| `rust-mcp-stack/rust-mcp-filesystem` | Rust (community) | MIT | `ef4797360ea03eec5375e03a6f10d092dfc6a5e0` | `read_text_file` | Yes | `path` + optional `with_line_numbers`; 24 tools |
| `MarcusJellinghaus/mcp-workspace` | Python (community) | MIT | `f64e5eea0e60c3ad151edc33ca6e426bbf84a2eb` | `read_file` | Needs `--project-dir` | Broad workspace server; project-relative `file_path` |

## Design consequences found during the search (decide before freezing)

1. **Customer IDs.** Shopify, WooCommerce and BigCommerce type the customer ID as
   numeric. The fixture's `C1` would force the model to adapt or be rejected.
   Change the fixture customer to a numeric ID before registration.
2. **No `encoding` parameter** on any files candidate. The fixture's
   `encoding: "utf-8"` and the user request's "utf-8" should be dropped.
3. **No folder parameter** on some email candidates (Fastmail). The request's
   "inbox" may have no matching argument; adapters must accept that.
4. **Tool-list size varies from ~14 to 300+ tools.** The experiment offers one
   tool, so only the chosen tool's schema is used, but record the full capture.
5. **One repo appears twice** (`ms-365-mcp-server` for email and calendar). Using
   it for both reduces source independence; prefer different repos if possible.
6. **Runtime-generated schemas** mean capture requires running each server in an
   isolated environment with placeholder configuration, calling only `tools/list`.
