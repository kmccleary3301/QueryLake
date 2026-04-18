# QueryLake Documentation

[![Docs Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/docs_checks.yml)
[![SDK Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/sdk_checks.yml)
[![Retrieval Eval](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/retrieval_eval.yml)
[![Unification Checks](https://github.com/kmccleary3301/QueryLake/actions/workflows/unification_checks.yml/badge.svg)](https://github.com/kmccleary3301/QueryLake/actions/workflows/unification_checks.yml)

This directory is the durable documentation surface for QueryLake.

If the root [`README.md`](../README.md) is the front page, this file is the navigator for setup, SDK usage, CI/release policy, architecture, migration, and specialized runtime docs.

## Table of contents

- [Start here](#start-here)
- [Choose your path](#choose-your-path)
- [Documentation map](#documentation-map)
- [Setup and developer experience](#setup-and-developer-experience)
- [SDK and application integration](#sdk-and-application-integration)
- [Database compatibility and backend profiles](#database-compatibility-and-backend-profiles)
- [Architecture, topology, and migration](#architecture-topology-and-migration)
- [Specialized runtime docs](#specialized-runtime-docs)
- [How to use this docs tree](#how-to-use-this-docs-tree)

## Start here

| If you need to... | Read this first | Why |
|---|---|---|
| bring up a local backend | [`setup/DEVELOPER_SETUP.md`](setup/DEVELOPER_SETUP.md) | canonical local environment instructions |
| understand the current developer experience direction | [`setup/DEVELOPER_EXPERIENCE_PLAN.md`](setup/DEVELOPER_EXPERIENCE_PLAN.md) | roadmap and rationale for DX work |
| integrate from Python | [`sdk/SDK_QUICKSTART.md`](sdk/SDK_QUICKSTART.md) | shortest path to useful SDK usage |
| do retrieval/RAG work with the SDK | [`sdk/RAG_RESEARCH_PLAYBOOK.md`](sdk/RAG_RESEARCH_PLAYBOOK.md) | practical ingestion/search research workflows |
| understand repo/API/path migration | [`unification/`](unification/) | canonical naming, routing, and topology |
| understand Chandra runtime notes | [`chandra/CHANDRA_OCR_VLLM_SERVER.md`](chandra/CHANDRA_OCR_VLLM_SERVER.md) | specialized OCR/runtime setup |
| understand the current OCR option set | [`chandra/CHANDRA_OCR_OPTION_SET.md`](chandra/CHANDRA_OCR_OPTION_SET.md) | default vs experimental OCR paths and output contracts |
| integrate against PDF output contracts | [`chandra/CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md`](chandra/CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md) | how to branch on OCR vs text-layer contracts safely |
| understand the OCR closeout decision | [`chandra/CHANDRA_OCR_DECISION_CLOSEOUT.md`](chandra/CHANDRA_OCR_DECISION_CLOSEOUT.md) | final production/default vs experimental OCR decisions |

## Choose your path

| Audience | Best entry docs |
|---|---|
| Backend contributor | [`setup/DEVELOPER_SETUP.md`](setup/DEVELOPER_SETUP.md), [`unification/program_control.md`](unification/program_control.md) |
| SDK consumer | [`sdk/SDK_QUICKSTART.md`](sdk/SDK_QUICKSTART.md), [`sdk/API_REFERENCE.md`](sdk/API_REFERENCE.md) |
| RAG researcher | [`sdk/RAG_RESEARCH_PLAYBOOK.md`](sdk/RAG_RESEARCH_PLAYBOOK.md), [`sdk/BULK_INGEST_REFERENCE.md`](sdk/BULK_INGEST_REFERENCE.md) |
| Release / package maintainer | [`sdk/PYPI_RELEASE.md`](sdk/PYPI_RELEASE.md), [`sdk/TESTPYPI_DRYRUN.md`](sdk/TESTPYPI_DRYRUN.md) |
| CI / staging operator | [`sdk/CI_PROFILES.md`](sdk/CI_PROFILES.md), [`sdk/LIVE_STAGING_INTEGRATION.md`](sdk/LIVE_STAGING_INTEGRATION.md) |
| Repo topology / migration reviewer | [`unification/repo_migration.md`](unification/repo_migration.md), [`unification/symlink_retirement_runbook.md`](unification/symlink_retirement_runbook.md) |

## Documentation map

```text
docs/
├── README.md                           This index / landing page
├── setup/
│   ├── DEVELOPER_SETUP.md             Local backend + environment bring-up
│   └── DEVELOPER_EXPERIENCE_PLAN.md   DX planning and standardization work
├── sdk/
│   ├── SDK_QUICKSTART.md              First SDK usage
│   ├── RAG_RESEARCH_PLAYBOOK.md       Retrieval/RAG workflows through the SDK
│   ├── BULK_INGEST_REFERENCE.md       Upload-dir, dry-run, checkpoints, dedupe
│   ├── API_REFERENCE.md               SDK method and contract reference
│   ├── LOCAL_PROFILE_WORKFLOW.md      SDK workflow for the supported embedded local slice
│   ├── PYPI_RELEASE.md                Publish/release runbook
│   ├── CI_PROFILES.md                 CI matrix and release policy
│   ├── TESTPYPI_DRYRUN.md             Dry-run release workflow
│   ├── CI_PERFORMANCE_POLICY.md       Runtime profiling and CI cost controls
│   └── LIVE_STAGING_INTEGRATION.md    Live environment integration contract
├── database/
│   ├── DB_COMPAT_PROFILES.md          DB stack profiles, capabilities, and unsupported-feature contract
│   ├── CHOOSING_A_PROFILE.md          Operator guide for selecting a DB/search profile
│   ├── LOCAL_PROFILE_V1.md            First embedded/local profile target and current scaffolding
│   ├── LOCAL_DENSE_SIDECAR_CONTRACT.md Authoritative embedded dense-sidecar runtime/storage contract
│   ├── LOCAL_PROFILE_PROMOTION_BAR.md Promotion criteria for the first supported embedded profile
│   ├── LOCAL_PROFILE_WORKFLOW.md      Practical bring-up workflow for the first supported embedded profile
│   ├── LOCAL_OPERATOR_WORKFLOW.md     Operator-facing workflow for the supported embedded profile
│   ├── QUERY_IR_V2.md                 Minimal active Query IR V2 subset now driving the supported V2 route slices
│   ├── PROJECTION_IR_V2.md            Minimal active Projection IR V2 subset now driving supported bootstrap/build reporting
│   ├── V2_RUNTIME_BOUNDARY.md         Active V2 runtime boundary and explicit program edge
│   ├── V2_PROGRAM_COMPLETION_GATE.md  Final closeout gate for the V2 primitives/local-profile program
│   ├── V2_IMPLEMENTATION_REPORT.md    Final implementation report for the completed V2 program
│   ├── V2_FUTURE_SCOPE.md             Explicit future-scope boundary beyond the completed V2 program
│   ├── ADDING_A_BACKEND_PROFILE.md    Engineering policy for adding profiles honestly
│   ├── FIRST_SPLIT_STACK_DEPLOYMENT.md Bring-up guide for the first executable split-stack profile
│   ├── BACKEND_PROFILE_RELEASE_GATE.md Merge/release gate for backend profile changes
│   ├── AUTHORITY_PROJECTION_MODEL.md  Authority vs projection storage boundary
│   ├── DOCUMENT_DECOMPOSITION_TRANCHE1.md Tranche-1 authority-layer migration and operator tooling
│   ├── DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md Immediate post-tranche-1 runtime/query boundary
│   ├── PROFILE_DIAGNOSTICS.md         Operator-facing profile readiness and config diagnostics
│   ├── SUPPORTED_PROFILES.md          Authoritative supported-profile and route/capability manifest
│   ├── DB_COMPAT_COMPLETION_GATE.md   Final completion gate for the current DB compatibility program
│   ├── DB_COMPAT_IMPLEMENTATION_REPORT.md Final implementation report for the completed DB compatibility program
│   ├── DB_COMPAT_PROGRAM_STATUS.md    Current program status and completion boundary
│   ├── DB_COMPAT_FUTURE_SCOPE.md      Explicit out-of-scope work for the next program
│   ├── SDK_PROFILE_AWARE_CLIENTS.md   Capability-aware client branching and route executability checks
│   └── RETRIEVAL_EXECUTION_BOUNDARY.md Route orchestration vs backend execution boundary
├── DEBT/
│   └── DB_COMPAT_EXTENSION_NEXT_PROGRAM.md Next-program backlog after DB compatibility closeout
├── unification/
│   ├── api_strategy.md                API direction and route strategy
│   ├── auth_provider_interface.md     Auth abstraction contracts
│   ├── compat_matrix.md               Compatibility/program control notes
│   ├── observability_v1.md            Observability direction
│   ├── program_control.md             Rollout/control guidance
│   ├── repo_migration.md              Canonical repo/path migration state
│   ├── route_prefixes.md              Route layout guidance
│   ├── repo_pinning_playbook.md       Downstream pinning policy
│   ├── symlink_retirement_runbook.md  Legacy path retirement schedule
│   └── unification_done_bar.md        Status tracker
├── chandra/
│   ├── CHANDRA_OCR_VLLM_SERVER.md     Chandra OCR/vLLM runtime notes
│   ├── CHANDRA_OCR_OPTION_SET.md      Current OCR option set and output-contract boundary
│   ├── CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md Downstream branching guidance for OCR/text-layer contracts
│   └── CHANDRA_OCR_DECISION_CLOSEOUT.md Final OCR decision closeout for the current program
└── deps_upgrade/
    ├── UPGRADE_GATES.md               Dependency upgrade gates
    └── UPGRADE_MATRIX_CHOOSER.md      Upgrade path/matrix guidance
```

## Setup and developer experience

| Doc | What it covers |
|---|---|
| [`setup/DEVELOPER_SETUP.md`](setup/DEVELOPER_SETUP.md) | local bring-up, Docker services, backend run modes, SDK smoke path |
| [`setup/DEVELOPER_EXPERIENCE_PLAN.md`](setup/DEVELOPER_EXPERIENCE_PLAN.md) | standardizing setup, SDK-first usage, and docs/packaging polish |

Practical recommendation:

- if you are new to the repo, start with `DEVELOPER_SETUP.md`,
- if you are changing how people install or use QueryLake, also read `DEVELOPER_EXPERIENCE_PLAN.md`.

## SDK and application integration

This is the most active and most externally relevant documentation area.

| Doc | Use it when... |
|---|---|
| [`sdk/SDK_QUICKSTART.md`](sdk/SDK_QUICKSTART.md) | you want the shortest path to a working client |
| [`sdk/RAG_RESEARCH_PLAYBOOK.md`](sdk/RAG_RESEARCH_PLAYBOOK.md) | you want retrieval and ingestion workflows, not just auth and health |
| [`sdk/BULK_INGEST_REFERENCE.md`](sdk/BULK_INGEST_REFERENCE.md) | you need dry-run planning, checkpointing, resume, dedupe, and large ingest ergonomics |
| [`sdk/API_REFERENCE.md`](sdk/API_REFERENCE.md) | you need method-level reference material |
| [`sdk/LIVE_STAGING_INTEGRATION.md`](sdk/LIVE_STAGING_INTEGRATION.md) | you are validating against a staging deployment |

### Suggested reading order for new SDK users

1. [`sdk/SDK_QUICKSTART.md`](sdk/SDK_QUICKSTART.md)
2. [`sdk/API_REFERENCE.md`](sdk/API_REFERENCE.md)
3. [`sdk/RAG_RESEARCH_PLAYBOOK.md`](sdk/RAG_RESEARCH_PLAYBOOK.md)
4. [`sdk/BULK_INGEST_REFERENCE.md`](sdk/BULK_INGEST_REFERENCE.md)

## Database compatibility and backend profiles

This area documents the ongoing DB/search compatibility extension work.

| Doc | Use it when... |
|---|---|
| [`database/DB_COMPAT_PROFILES.md`](database/DB_COMPAT_PROFILES.md) | you need the current profile matrix, capability discovery contract, or unsupported-feature error semantics |
| [`database/CHOOSING_A_PROFILE.md`](database/CHOOSING_A_PROFILE.md) | you need to decide which QueryLake DB/search profile to deploy for a workload |
| [`database/LOCAL_PROFILE_V1.md`](database/LOCAL_PROFILE_V1.md) | you need the current design and runtime status of the first embedded/local QueryLake profile |
| [`database/LOCAL_DENSE_SIDECAR_CONTRACT.md`](database/LOCAL_DENSE_SIDECAR_CONTRACT.md) | you need the exact embedded dense-sidecar runtime/storage contract and versioned guarantees |
| [`database/LOCAL_PROFILE_PROMOTION_BAR.md`](database/LOCAL_PROFILE_PROMOTION_BAR.md) | you need the exact criteria for promoting the first local profile into the supported-profile set |
| [`database/LOCAL_PROFILE_WORKFLOW.md`](database/LOCAL_PROFILE_WORKFLOW.md) | you need the shortest end-to-end workflow for inspecting, bootstrapping, and validating the current local profile |
| [`database/LOCAL_OPERATOR_WORKFLOW.md`](database/LOCAL_OPERATOR_WORKFLOW.md) | you need the operator-facing workflow for inspecting readiness, bootstrapping the local slice, and validating widening blockers |
| [`database/QUERY_IR_V2.md`](database/QUERY_IR_V2.md) | you need the minimal active Query IR V2 subset that is already driving the supported V2 route slices |
| [`database/PROJECTION_IR_V2.md`](database/PROJECTION_IR_V2.md) | you need the minimal active Projection IR V2 subset that is already driving supported bootstrap and promotion reporting |
| [`database/V2_RUNTIME_BOUNDARY.md`](database/V2_RUNTIME_BOUNDARY.md) | you need the current live V2 runtime boundary, not just the draft contracts |
| [`database/V2_PROGRAM_COMPLETION_GATE.md`](database/V2_PROGRAM_COMPLETION_GATE.md) | you need the exact final closeout gate for the V2 primitives/local-profile program |
| [`database/V2_IMPLEMENTATION_REPORT.md`](database/V2_IMPLEMENTATION_REPORT.md) | you need the final engineering report for what the V2 program delivered |
| [`database/V2_FUTURE_SCOPE.md`](database/V2_FUTURE_SCOPE.md) | you need the explicit out-of-scope boundary beyond the completed V2 program |
| [`database/ADDING_A_BACKEND_PROFILE.md`](database/ADDING_A_BACKEND_PROFILE.md) | you are introducing or extending a backend profile and need the engineering honesty bar |
| [`database/FIRST_SPLIT_STACK_DEPLOYMENT.md`](database/FIRST_SPLIT_STACK_DEPLOYMENT.md) | you are staging or validating the first Aurora/OpenSearch split-stack deployment |
| [`database/BACKEND_PROFILE_RELEASE_GATE.md`](database/BACKEND_PROFILE_RELEASE_GATE.md) | you need the explicit merge/release gate for backend profile changes |
| [`database/AUTHORITY_PROJECTION_MODEL.md`](database/AUTHORITY_PROJECTION_MODEL.md) | you need the current authority/projection boundary and why `DocumentChunk` is transitional |
| [`database/DOCUMENT_DECOMPOSITION_TRANCHE1.md`](database/DOCUMENT_DECOMPOSITION_TRANCHE1.md) | you need the tranche-1 decomposition substrate, migration states, and repair tooling |
| [`database/DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md`](database/DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md) | you need the immediate post-tranche-1 scope, the 80% boundary, and what is explicitly deferred |
| [`database/PROFILE_DIAGNOSTICS.md`](database/PROFILE_DIAGNOSTICS.md) | you need profile readiness, config requirements, or route-executor visibility for operators and clients |
| [`database/SUPPORTED_PROFILES.md`](database/SUPPORTED_PROFILES.md) | you need the authoritative supported-profile manifest and the tested route/capability scope for each profile |
| [`database/DB_COMPAT_COMPLETION_GATE.md`](database/DB_COMPAT_COMPLETION_GATE.md) | you need the exact final closeout gate for the current DB compatibility program |
| [`database/DB_COMPAT_IMPLEMENTATION_REPORT.md`](database/DB_COMPAT_IMPLEMENTATION_REPORT.md) | you need the final engineering report for what the current DB compatibility program delivered |
| [`database/DB_COMPAT_PROGRAM_STATUS.md`](database/DB_COMPAT_PROGRAM_STATUS.md) | you need the current implementation status, closeout state, and what remains before full program completion |
| [`database/DB_COMPAT_FUTURE_SCOPE.md`](database/DB_COMPAT_FUTURE_SCOPE.md) | you need the explicit out-of-scope items that are intentionally not required for current program completion |
| [`database/SDK_PROFILE_AWARE_CLIENTS.md`](database/SDK_PROFILE_AWARE_CLIENTS.md) | you are building clients that need to branch on supported vs degraded vs unsupported retrieval behavior |
| [`database/RETRIEVAL_EXECUTION_BOUNDARY.md`](database/RETRIEVAL_EXECUTION_BOUNDARY.md) | you are changing retrieval route execution and need to know what belongs in `search.py` vs route/lane executors |

Suggested reading order for backend-compatibility work:

1. [`database/DB_COMPAT_PROFILES.md`](database/DB_COMPAT_PROFILES.md)
2. [`database/CHOOSING_A_PROFILE.md`](database/CHOOSING_A_PROFILE.md)
3. [`database/LOCAL_PROFILE_V1.md`](database/LOCAL_PROFILE_V1.md)
4. [`database/LOCAL_DENSE_SIDECAR_CONTRACT.md`](database/LOCAL_DENSE_SIDECAR_CONTRACT.md)
5. [`database/LOCAL_PROFILE_PROMOTION_BAR.md`](database/LOCAL_PROFILE_PROMOTION_BAR.md)
6. [`database/LOCAL_PROFILE_WORKFLOW.md`](database/LOCAL_PROFILE_WORKFLOW.md)
7. [`database/LOCAL_OPERATOR_WORKFLOW.md`](database/LOCAL_OPERATOR_WORKFLOW.md)
8. [`database/QUERY_IR_V2.md`](database/QUERY_IR_V2.md)
9. [`database/PROJECTION_IR_V2.md`](database/PROJECTION_IR_V2.md)
10. [`database/V2_RUNTIME_BOUNDARY.md`](database/V2_RUNTIME_BOUNDARY.md)
11. [`database/V2_PROGRAM_COMPLETION_GATE.md`](database/V2_PROGRAM_COMPLETION_GATE.md)
12. [`database/V2_IMPLEMENTATION_REPORT.md`](database/V2_IMPLEMENTATION_REPORT.md)
13. [`database/V2_FUTURE_SCOPE.md`](database/V2_FUTURE_SCOPE.md)
14. [`database/PROFILE_DIAGNOSTICS.md`](database/PROFILE_DIAGNOSTICS.md)
15. [`database/SUPPORTED_PROFILES.md`](database/SUPPORTED_PROFILES.md)
16. [`database/FIRST_SPLIT_STACK_DEPLOYMENT.md`](database/FIRST_SPLIT_STACK_DEPLOYMENT.md)
17. [`database/SDK_PROFILE_AWARE_CLIENTS.md`](database/SDK_PROFILE_AWARE_CLIENTS.md)
18. [`database/RETRIEVAL_EXECUTION_BOUNDARY.md`](database/RETRIEVAL_EXECUTION_BOUNDARY.md)
19. [`database/AUTHORITY_PROJECTION_MODEL.md`](database/AUTHORITY_PROJECTION_MODEL.md)
20. [`database/DOCUMENT_DECOMPOSITION_TRANCHE1.md`](database/DOCUMENT_DECOMPOSITION_TRANCHE1.md)
21. [`database/DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md`](database/DOCUMENT_DECOMPOSITION_TRANCHE2_BOOTSTRAP.md)
22. [`database/DB_COMPAT_COMPLETION_GATE.md`](database/DB_COMPAT_COMPLETION_GATE.md)
23. [`database/DB_COMPAT_IMPLEMENTATION_REPORT.md`](database/DB_COMPAT_IMPLEMENTATION_REPORT.md)
24. [`database/DB_COMPAT_PROGRAM_STATUS.md`](database/DB_COMPAT_PROGRAM_STATUS.md)
25. [`database/DB_COMPAT_FUTURE_SCOPE.md`](database/DB_COMPAT_FUTURE_SCOPE.md)

Practical recommendation:

- if you are building clients or deployment tooling, read this before assuming lexical/sparse/graph support,
- and treat the ParadeDB/PostgreSQL gold profile as canonical even though a narrow AWS Aurora + OpenSearch executable slice now exists.

## Architecture, topology, and migration

These docs matter if you are modifying backend structure, route layout, auth abstractions, or repository naming/layout assumptions.

| Doc | Focus |
|---|---|
| [`unification/api_strategy.md`](unification/api_strategy.md) | API shape and platform direction |
| [`unification/auth_provider_interface.md`](unification/auth_provider_interface.md) | auth provider abstraction boundaries |
| [`unification/route_prefixes.md`](unification/route_prefixes.md) | route organization and naming |
| [`unification/observability_v1.md`](unification/observability_v1.md) | observability guidance |
| [`unification/program_control.md`](unification/program_control.md) | compatibility and rollout control |
| [`unification/compat_matrix.md`](unification/compat_matrix.md) | supported combinations / compatibility notes |
| [`unification/repo_migration.md`](unification/repo_migration.md) | repo/path migration history and policy |
| [`unification/repo_pinning_playbook.md`](unification/repo_pinning_playbook.md) | downstream compatibility pinning |
| [`unification/symlink_retirement_runbook.md`](unification/symlink_retirement_runbook.md) | staged retirement of legacy local alias |
| [`unification/unification_done_bar.md`](unification/unification_done_bar.md) | status tracking |

### Read these if you are touching naming or compatibility

- do not change canonical pathing or repo naming assumptions blindly,
- read the migration/runbook docs first,
- and treat compatibility as a product contract, not an afterthought.

## Specialized runtime docs

| Area | Doc | Notes |
|---|---|---|
| Chandra OCR/runtime | [`chandra/CHANDRA_OCR_VLLM_SERVER.md`](chandra/CHANDRA_OCR_VLLM_SERVER.md) | specialized OCR and model-serving notes |
| Chandra OCR option set | [`chandra/CHANDRA_OCR_OPTION_SET.md`](chandra/CHANDRA_OCR_OPTION_SET.md) | default vs experimental OCR paths and explicit output contracts |
| Chandra output contract integration | [`chandra/CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md`](chandra/CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md) | how downstream consumers should branch on OCR vs text-layer output |
| Chandra OCR decision closeout | [`chandra/CHANDRA_OCR_DECISION_CLOSEOUT.md`](chandra/CHANDRA_OCR_DECISION_CLOSEOUT.md) | final closeout summary for the current OCR option program |
| Dependency upgrades | [`deps_upgrade/UPGRADE_GATES.md`](deps_upgrade/UPGRADE_GATES.md) | what has to be true before dependency upgrades land |
| Upgrade matrix | [`deps_upgrade/UPGRADE_MATRIX_CHOOSER.md`](deps_upgrade/UPGRADE_MATRIX_CHOOSER.md) | selecting safe upgrade paths |

## How to use this docs tree

A few practical rules make this easier:

- use the root [`README.md`](../README.md) as the project front page,
- use this file as the stable navigation layer,
- use `docs_tmp/` for working notes, experiments, reports, and temporary artifacts,
- and promote material into `docs/` only when it is durable enough to be part of the maintained surface.

> `docs/` is for maintained documentation. `docs_tmp/` is for active work, scans, reports, design notes, and transient planning artifacts.

### Repo-adjacent surfaces worth knowing about

| Surface | Location | Why it matters |
|---|---|---|
| Root repo front page | [`../README.md`](../README.md) | high-level overview, quickstart, repo map |
| SDK package page | [`../sdk/python/README.md`](../sdk/python/README.md) | package-specific install/usage docs |
| Runnable SDK examples | [`../examples/sdk/`](../examples/sdk/) | practical examples and offline demos |
| Contributor guide | [`../CONTRIBUTING.md`](../CONTRIBUTING.md) | repo expectations and contribution workflow |

If you are not sure where to start, use this sequence:

1. [`../README.md`](../README.md)
2. [`setup/DEVELOPER_SETUP.md`](setup/DEVELOPER_SETUP.md)
3. [`sdk/SDK_QUICKSTART.md`](sdk/SDK_QUICKSTART.md)
