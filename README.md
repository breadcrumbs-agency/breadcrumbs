# breadcrumbs

Memory for coding agents with exact provenance: each recalled line has a content address.

This repository links the parts. Each part is one repository and one Python package. A higher part imports a
lower part by name. No part holds a copy of the code of another part.

| Part | Package | What it holds | Needs |
|---|---|---|---|
| [breadcrumbs-common](https://github.com/breadcrumbs-agency/breadcrumbs-common) | `breadcrumbs` | the store, the index, the reader, the verbs (MCP, socket, A2A), the ports | google-crc32c |
| [breadcrumbs-spacegraph](https://github.com/breadcrumbs-agency/breadcrumbs-spacegraph) | `breadcrumbs_spacegraph` | the viewers: explorer page, terminal views | common |
| [breadcrumbs-hermes](https://github.com/breadcrumbs-agency/breadcrumbs-hermes) | `breadcrumbs_hermes` | the Hermes plugin: memory provider, ACE, islands, the usage log | common, spacegraph |
| [breadcrumbs-claude](https://github.com/breadcrumbs-agency/breadcrumbs-claude) | `breadcrumbs_claude` | the adapter for Claude Code | common |
| [breadcrumbs-codex](https://github.com/breadcrumbs-agency/breadcrumbs-codex) | `breadcrumbs_codex` | the adapter for Codex | common |
| [breadcrumbs-opencode](https://github.com/breadcrumbs-agency/breadcrumbs-opencode) | `breadcrumbs_opencode` | the adapter for OpenCode | common |
| [breadcrumbs-grok](https://github.com/breadcrumbs-agency/breadcrumbs-grok) | `breadcrumbs_grok` | the adapter for Grok CLI | common |
| [breadcrumbs-pi](https://github.com/breadcrumbs-agency/breadcrumbs-pi) (private for now) | `breadcrumbs_pi` | the adapter for Pi | common |

## Get all parts

```
git clone --recurse-submodules git@github.com:breadcrumbs-agency/breadcrumbs.git
```

Each folder is a submodule at the commit that was tested together with the others.

## Run the tests of one part

Put the part and the parts that it needs on `PYTHONPATH`, then run its suite. For the Hermes part:

```
cd breadcrumbs-hermes
PYTHONPATH=../breadcrumbs-common:../breadcrumbs-spacegraph:. python -m unittest discover -s tests
```

## The move

[MOVE.md](MOVE.md) is the ledger of the move from `hermes-breadcrumb-plugin` to these parts: what moved, what did
not move yet, and why.
