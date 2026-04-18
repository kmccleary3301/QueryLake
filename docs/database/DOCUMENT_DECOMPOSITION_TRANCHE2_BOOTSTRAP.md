# Document Decomposition Tranche 2 Bootstrap

This document defines the immediate post-tranche-1 scope for the document decomposition program.

It exists to keep the next phase narrow, operationally safe, and aligned with the 80% completion target for the overall program.

## Purpose

Tranche 2 does **not** begin with frontier retrieval features.

It begins with controlled runtime/query integration on top of the tranche-1 authority layer so that QueryLake can consume canonical segment/view/member state directly without destabilizing current public retrieval behavior.

## 80% boundary

The overall program is considered at least 80% complete when all of the following are true:

1. new ingest is canonical on the decomposition substrate,
2. tranche-1 migration/repair/audit tooling is stable,
3. the foreground historical normalization stop-point has been reached and frozen,
4. current public retrieval behavior remains stable,
5. at least one real internal runtime/query path consumes canonical decomposition state directly.

## Required before 80%

These items are required before the program should be described as 80% complete:

- freeze the next post-190k audited checkpoint and cross the 200,000 historical normalization stop-point,
- record the 200,000 foreground milestone in durable status docs,
- keep campaign/doc status surfaces consistent,
- keep repair and compatibility invariants green,
- retain stable public retrieval behavior,
- keep the internal provenance/authority helper as the first decomposition-aware runtime surface.

## Desirable after 80%

These items are useful, but are **not** required for the 80% threshold:

- additional historical rollout beyond the foreground stop-point,
- public decomposition-aware retrieval APIs,
- representation generalization beyond the current compatibility projection,
- multi-view routing exposed publicly,
- late chunking, multivector retrieval, page-visual retrieval, or table-native retrieval.

## Immediate tranche-2 scope

Tranche 2 should cover only the smallest runtime/query work needed to make the new authority model operationally real beyond migration tooling.

That scope is:

1. keep the internal canonical provenance helper stable,
2. add small internal read helpers that consume `document_segment`, `document_segment_view`, and `document_segment_member` directly,
3. make compatibility/read paths explicitly understand that `DocumentChunk` is a compatibility projection backed by canonical authority state,
4. add regression tests proving those internal read paths stay aligned with canonical segment state,
5. preserve current external API shapes while this internal shift happens.

## Explicitly out of scope for immediate tranche 2

The following are deferred on purpose:

- representation-generalized storage replacing current compatibility projections,
- late chunking,
- multivector retrieval,
- visual/page-native retrieval,
- table-native retrieval,
- public multi-view retrieval selection,
- broad route-planning redesign.

## Why this boundary exists

If tranche 2 starts by chasing frontier retrieval features, the program will overbuild before the authority-layer migration is fully absorbed into runtime behavior.

That would increase scope, risk, and regression potential without improving the core migration story.

The correct next move is to make the canonical decomposition substrate a real internal dependency of runtime/query code first.

## Foreground versus background work

Once the documented historical foreground stop-point is crossed, additional historical normalization should continue as background maintenance unless a specific tranche-2 change depends on widening the normalized front.

This keeps the program moving forward without pretending the entire historical tail must be normalized before any further runtime work can proceed.
