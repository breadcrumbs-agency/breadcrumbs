# The move: from one repository to seven parts

This file is the ledger. A line is added when a thing moves. Nothing here is a plan that is not also a fact,
except the section "Not moved yet".

## From

| Repository | State | Role now |
|---|---|---|
| `hermes-breadcrumb-plugin` | public; `master` = `0d0385b`; tag `v0.4.1` = `b897564` | The live plugin. The Hermes catalog entry pins the tag. It stays as it is until the hackathon results. |
| `hermes-breadcrumb-plugin-old` | private | The history before the baseline. To delete. |

## To

The source of each part is one folder of the branch `refactor/layers` at `c4af2f3` (four commits on `0d0385b`).
Each repository holds one commit with no parent. Its tree is equal to the folder (checked by tree id).

| Part | Baseline commit | Python lines (no tests) | Tests, run alone |
|---|---|---:|---|
| breadcrumbs-common | `777fb9fc` | 5,369 | 158, OK (162 after step 5 below) |
| breadcrumbs-spacegraph | `614ea6d9` | 5,515 | 7, OK |
| breadcrumbs-hermes | `8023b55c` | 6,594 | 928, OK (19 skipped) |
| breadcrumbs-claude | `bdfa02c0` | 11 | 5, OK |
| breadcrumbs-codex | `4941a950` | 10 | 5, OK |
| breadcrumbs-opencode | `c8c46259` | 12 | 5, OK |
| breadcrumbs-grok | `5d0e00e7` | 14 | 5, OK |

"Run alone" means: only the part and the parts below it are on `PYTHONPATH`. The runs are of 2026-11-11.

## How the code was cut

1. `4fe0a07`: 24 imports went from a lower layer to a higher one. They were cut. A port registry
   (`breadcrumbs/ports.py`) carries what was imported.
2. `d51e070`: issue #1, first part: one writer for the hide file, with a lock.
3. `a3ca8dd`: common got its own reader and its own `find`. Each layer gives its ports from one adapter.
4. `c4af2f3`: the files moved into seven folders, one package each.
5. `4da1fb4`: one harness contract in common. One `config` reader; `ports.mcp_add` for the setup line of three
   adapters; one shared test case for an adapter (`breadcrumbs/harness_case.py`); one session ingest
   (`ingest.ingest_sessions`) that a harness feeds with a source; the command `ingest HARNESS [PATH]`.
   The measure of repeated code (functions with an equal body, blocks of 8 equal lines) went from 1 to 0.
6. `cb58a4d`, `6ae5aae`, `6299733`, `a7ebcf2`: the ports. Claude Code, Codex and OpenCode each give a session source
   (`sessions.py`) to the one ingest of common. What two sources share is in common (`breadcrumbs/transcript.py`).
   The measure of repeated code stays 0.
7. `80eb9ae`, `7e8aece`: metrics. One metric type and one fold in common (`breadcrumbs/metrics.py`); a ratio folds
   as a ratio of sums. The LLM cache metrics are defined once (`breadcrumbs/usage.py`): hit share, write share, reuse,
   breaks, break tokens, saved USD (prices from Hermes through a port). Claude Code, Codex and OpenCode give the usage
   of each request into the same usage.log that the viewer reads.
8. `d7c3267`, `ffa7719`, `40160cb`: cache writes beside the ACE acts. Each act (pass, keep, fold, ratchet) has
   acts_, cw_after_, breaks_after_ (sums), cw_per_, break_rate_ (ratios), and fold_cw_share. A request counts once, for
   its act of highest rank (fold > ratchet > keep > pass). An ace.log line joins the request whose START is at or
   after it (97.4% of joined lines match the provider's count of the request before; the first join matched 49.4%).
9. `8fed1f7`: the viewer's request axis takes its pairs from that one join (it had a second pairing by the end
   stamp: 35.4% of its slots right, now 97.4%). The totals of the ace measures did not change; only their slots moved.

The help text of 41 command forms is byte-equal before and after. A run on a seeded store gave equal results.

## Not moved yet

| Thing | Where it is | Why it waits |
|---|---|---|
| The catalog pin (hermes-agent PR 153020) | `hermes-breadcrumb-plugin` at `v0.4.1` | Hermes does not install a plugin's Python dependencies and reads no submodule. `breadcrumbs-hermes` needs `breadcrumbs-common` and `breadcrumbs-spacegraph` from PyPI first, and the seven repositories are private. |
| Issues #1 and #2 | `hermes-breadcrumb-plugin` | They are public there. A transfer keeps the numbers. They go to `breadcrumbs-hermes` with the pin. |
| The site (GitHub Pages, `docs/`) | `hermes-breadcrumb-plugin` | The README pictures and the films load from it. It goes with the pin. |
| The live plugin of the local Hermes | a symlink to the `master` checkout of the old layout | It moves to `breadcrumbs-hermes/` at a gateway restart. |
| PyPI packages | none | Needs an account token. |
| The delete of the two old repositories | not done | After the pin moves. |

## Work in progress on the parts

| Work | Part | State |
|---|---|---|
| DRY: one harness contract, one shared adapter test, one session ingest | common, then each adapter | done (`4da1fb4`) |
| Ports: read the sessions of Claude Code, Codex, OpenCode | claude, codex, opencode | done (`a7ebcf2`). Claude Code and Codex: one real session file each was read into a scratch store. OpenCode: built from its source at v1.18.30; a real database (5 sessions, 8 messages, made by OpenCode 1.18.30 on NVIDIA Nemotron) was read into a scratch store on 2026-11-11, and a second run added no session |
| Port: read the sessions of Grok CLI | grok | open. The xAI documents name the folder `~/.grok/sessions/` and no file format. The part only names the harness and prints the setup line |
| Issue #1: agent tools for hide, unhide, remove, rehome; retract | common | first commit is in (`d51e070`) |
| Issue #1: the right-click menu | spacegraph | open |
| Links (issue, PR, commit, card) as cost centers, with open and close marks | common, spacegraph | design only |
| Issue #2: the interchange minimums | common | analysis posted on the issue 2026-11-11 |

## Log

- 2026-11-11 12:52 CST: the old repository became `hermes-breadcrumb-plugin-old` (private). A new `hermes-breadcrumb-plugin` took one baseline commit.
- 2026-11-11 13:20 CST: `master` = `0d0385b` (pictures in `docs/media/`). Tag `v0.4.1` = `b897564`. The catalog entry pins the tag.
- 2026-11-11 14:39 CST: the split is done on `refactor/layers` (`c4af2f3`).
- 2026-11-11 14:53 CST: the seven repositories were created, private, one commit each.
- 2026-11-11 15:10 CST: this repository links them.
- 2026-11-11 15:25 CST: step 5 (`4da1fb4`) went to common, hermes, claude, codex, opencode and grok. The seven suites passed alone on that commit.
- 2026-11-11 15:35 CST: step 6 (`a7ebcf2`) went to common, claude, codex and opencode. The seven suites passed alone on that commit: 162, 7, 928 (19 skipped), 9, 9, 9, 5.
- 2026-11-11 16:40 CST: OpenCode on this Mac now uses NVIDIA Nemotron (`nemotron-3-ultra-550b-a55b`; small model `nemotron-3.5-lightning-30b-a3b`). Its first sessions gave the OpenCode port its real proof.
- 2026-11-11 18:25 CST: step 7 (`7e8aece`) went to common, spacegraph, hermes, claude, codex and opencode. The seven suites passed alone on that commit: 174, 7, 932 (19 skipped), 11, 11, 11, 5.
- 2026-11-11 19:05 CST: step 8 (`40160cb`) went to common, spacegraph and hermes. The seven suites passed alone on that commit: 179, 7, 940 (19 skipped), 11, 11, 11, 5.
- 2026-11-11 19:12 CST: step 9 (`8fed1f7`) went to common, spacegraph and hermes. The seven suites passed alone on that commit: 179, 7, 941 (19 skipped), 11, 11, 11, 5.
- 2026-11-11 19:30 CST: `breadcrumbs-common` runs its suite on GitHub Actions on each push (`.github/workflows/suite.yml`); the first run passed. The other six parts have no workflow yet: the org disallows deploy keys, so a run there cannot fetch the private parts below it.
