# Chandra OCR via External vLLM Server (Recommended)

This doc describes the **recommended** way to run QueryLake's Chandra OCR: keep the OCR model in an
**external vLLM OpenAI-compatible server**, and configure QueryLake to proxy OCR requests to it.

Why this is the best fit for QueryLake patterns:
- You get **vLLM continuous batching + high throughput** for OCR pages.
- You can run **1 GPU (default)** or **2 GPU striped** topologies without needing Ray-managed DP=2.
- QueryLake stays responsible for **routing, batching, caching, files pipeline**, and toolchain integration.
- Ray PACK/SPREAD/autoscaling remains clean because QueryLake's Chandra deployment becomes **CPU-only** in this mode.

For the current OCR option set and output-contract split, also read:
- [`CHANDRA_OCR_OPTION_SET.md`](CHANDRA_OCR_OPTION_SET.md)
- [`CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md`](CHANDRA_OUTPUT_CONTRACT_INTEGRATION.md)

---

## Topologies

### 1) Single (default)

One vLLM server on one GPU:
- best for day-to-day QueryLake usage (keeps a GPU free for local LLMs/embeddings/rerankers)
- good enough throughput for most OCR workloads

### 2) Striped (max throughput)

Two vLLM servers, each pinned to a different GPU, both serving the same model.
QueryLake is configured with both endpoints and stripes page requests across them.

This effectively dedicates **two GPUs** to OCR throughput.

---

## Profile defaults

`ChandraDeployment` now treats the `speed` profile as the throughput-oriented preset:
- `speed`: `589_824` max image pixels
- `balanced`: `1_048_576` max image pixels
- `quality`: `2_097_152` max image pixels

Use `speed` when throughput is the priority and the corpus is not especially structure-fragile.
Use `balanced` when you want a safer middle ground. Use `quality` when fidelity matters more than
throughput.

## Current OCR option set

Current durable recommendation:
- `Chandra-1` is the default production OCR lane.
- `Chandra-2` remains opt-in / experimental.
- PDF text-layer routing remains opt-in / experimental under a separate output contract.

This matters because QueryLake no longer treats text-layer fast paths as silently equivalent to OCR
markdown. When a PDF is served from the text layer, metadata makes that explicit through:
- `output_contract`
- `page_source_by_page`
- `page_source_counts`

Expected contract values are:
- `ocr_markdown`
- `text_layer_fastpath_markdown`
- `mixed_text_layer_fastpath_markdown`

If you are integrating downstream consumers, branch on the contract instead of assuming all PDF
transcription output is OCR-equivalent markdown.

## Runtime compatibility snapshot

The Chandra benchmark harness now records a runtime compatibility snapshot alongside benchmark
results. It captures:
- configured and effective runtime backend
- local model config metadata when `models/chandra` is used
- package versions for `torch`, `transformers`, `vllm`, `ray`, `Pillow`, and `pypdfium2`
- vLLM server topology / retry / media-path settings

Use the snapshot when comparing Chandra-1 and Chandra-2 so runtime and dependency drift are explicit
in the benchmark artifact, not just in the surrounding notes.

For staged lane validation, use `scripts/chandra_runtime_compatibility_report.py` with separate
`--current-model-path` and `--target-model-path` values. Keep the current reference lane on
`models/chandra`, and validate a staged `models/chandra2` lane independently before benchmark or
promotion work.

If you pass `--probe-pdf`, the compatibility report will also run `scripts/chandra_vllm_probe.py`
for each lane and include real load/generate probe results in the same artifact.

---

## vLLM Server: start/stop

Use:
- `scripts/chandra_vllm_server.sh`

For striped:

```bash
# GPU0
CHANDRA_VLLM_RUNTIME_DIR=/tmp/querylake_chandra_vllm_server_gpu0 \
CHANDRA_VLLM_PORT=8022 \
CHANDRA_VLLM_CUDA_VISIBLE_DEVICES=0 \
./scripts/chandra_vllm_server.sh start

# GPU1
CHANDRA_VLLM_RUNTIME_DIR=/tmp/querylake_chandra_vllm_server_gpu1 \
CHANDRA_VLLM_PORT=8023 \
CHANDRA_VLLM_CUDA_VISIBLE_DEVICES=1 \
./scripts/chandra_vllm_server.sh start
```

---

## QueryLake Configuration (JSON patch)

QueryLake configs (`config.json`) are git-ignored in this repo. Treat the snippets below as patches.

### Enable Chandra (external vLLM server mode)

```json
{
  "enabled_model_classes": {
    "chandra": true
  },
  "other_local_models": {
    "chandra_models": [
      {
        "name": "Chandra OCR",
        "id": "chandra",
        "source": "models/chandra",
        "deployment_config": {
          "runtime_args": {
            "runtime_backend": "vllm_server"
          }
        }
      }
    ]
  }
}
```

### Point QueryLake at your vLLM server(s)

Single:

```json
{
  "chandra_vllm_server_base_urls": ["http://127.0.0.1:8022/v1"],
  "chandra_vllm_server_model": "chandra",
  "chandra_vllm_server_topology": "single"
}
```

Striped:

```json
{
  "chandra_vllm_server_base_urls": [
    "http://127.0.0.1:8022/v1",
    "http://127.0.0.1:8023/v1"
  ],
  "chandra_vllm_server_model": "chandra",
  "chandra_vllm_server_topology": "striped"
}
```

### Optional: let QueryLake autostart the vLLM servers (local dev convenience)

Autostart is intentionally **local-only** (it is not a multi-node supervisor).

```json
{
  "chandra_vllm_server_autostart": true,
  "chandra_vllm_server_autostart_topology": "single",
  "chandra_vllm_server_autostart_port_base": 8022,
  "chandra_vllm_server_autostart_gpu_memory_utilization": 0.90
}
```

Notes:
- Default autostart topology is **single**.
- If autostart is enabled, QueryLake will **reserve** the GPU(s) used by the external server by
  **not starting Ray worker nodes** on those GPU indices.
- When the external server is on the same host, QueryLake can send multimodal pages as **local file
  paths** instead of re-encoding them as data URLs. vLLM's OpenAI server must be launched with an
  allowed local media path, and QueryLake should be configured with the same path.
- QueryLake also attaches a stable per-image **media UUID** so vLLM can reuse cached media results
  across requests when the server supports it.

For the current `speed` lane, QueryLake also renders PDF pages against the profile pixel budget up front rather than always rasterizing at the full fixed render DPI and shrinking later inside Chandra. This keeps the external `vllm_server` path from paying avoidable render/encode cost before model inference.

---

## Ray Scheduling Integration (important)

In `runtime_backend="vllm_server"` mode:
- QueryLake's Chandra Serve deployment is **CPU-only**
- GPU scheduling is done by how you provision the external vLLM servers

If you supervise vLLM externally (systemd/docker/k8s), explicitly reserve those GPU indices from Ray:
- Config: `ray_cluster.worker_gpu_exclude_indices=[0]` (or `[0,1]` for striped)
- Env: `QUERYLAKE_RAY_WORKER_GPU_EXCLUDE=0` (or `0,1`)

---

## Environment Variables (alternative to config)

```bash
export QUERYLAKE_CHANDRA_RUNTIME_BACKEND=vllm_server
export QUERYLAKE_CHANDRA_VLLM_SERVER_BASE_URLS=http://127.0.0.1:8022/v1,http://127.0.0.1:8023/v1
export QUERYLAKE_CHANDRA_VLLM_SERVER_MODEL=chandra
export QUERYLAKE_CHANDRA_VLLM_SERVER_API_KEY=chandra-local-key
export QUERYLAKE_CHANDRA_VLLM_SERVER_ALLOWED_LOCAL_MEDIA_PATH=/shared_folders/querylake_server/QueryLake/object_store

# Reserve GPUs from Ray workers when the vLLM servers are external.
export QUERYLAKE_RAY_WORKER_GPU_EXCLUDE=0,1
```

---

## Failure Mode: HF fallback in vLLM-server mode

By default, QueryLake does **not** fall back to HF inside the vLLM-server proxy actor.
This is intentional: HF fallback can silently use GPUs outside Ray scheduling, which is unsafe.

If you want fallback anyway (not recommended), set:
- `QUERYLAKE_CHANDRA_VLLM_SERVER_FALLBACK_TO_HF=1`
