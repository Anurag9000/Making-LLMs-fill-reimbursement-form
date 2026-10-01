"""Central local-inference device policy for retained reimbursement workflows.

This module governs only model/OCR libraries executing inside this Python
process. OpenAI and Ollama services are external processes/services and are
reported separately; this module does not pretend to control their accelerators.
"""
from __future__ import annotations

import os
from typing import Any, Mapping

_TRUE = {"1", "true", "yes", "on", "y"}
_CPU_FLAGS = (
    "CPU_ONLY",
    "TRAINING_CONTROL_CPU_ONLY",
    "OPF_ADP_DISABLE_GPU_ACCELERATORS",
)


def cpu_admission_requested(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return (
        str(env.get("TRAINING_CONTROL_BACKEND", "")).strip().lower() == "cpu"
        or any(str(env.get(name, "")).strip().lower() in _TRUE for name in _CPU_FLAGS)
        or (
            "CUDA_VISIBLE_DEVICES" in env
            and str(env.get("CUDA_VISIBLE_DEVICES", "")).strip() in {"", "-1"}
        )
    )


def gpu_admission_requested(environ: Mapping[str, str] | None = None) -> bool:
    env = os.environ if environ is None else environ
    return str(env.get("TRAINING_CONTROL_BACKEND", "")).strip().lower() == "gpu"


def _check_admission(environ: Mapping[str, str] | None = None) -> bool:
    cpu = cpu_admission_requested(environ)
    if cpu and gpu_admission_requested(environ):
        raise RuntimeError("conflicting CPU and GPU scheduler admission")
    return cpu


def _cuda_probe(torch_module: Any, index: int) -> bool:
    try:
        probe = torch_module.empty((1,), device=f"cuda:{index}")
        probe.fill_(1)
        torch_module.cuda.synchronize(index)
        del probe
        return True
    except (RuntimeError, OSError, AttributeError, TypeError, ValueError):
        return False


def best_cuda_index(
    torch_module: Any,
    environ: Mapping[str, str] | None = None,
) -> int:
    """Return the best usable *local masked* CUDA index, or -1.

    Physical CUDA_VISIBLE_DEVICES identifiers are never reinterpreted as local
    Torch indices. Each candidate must complete an actual tensor operation.
    """
    if _check_admission(environ):
        return -1
    try:
        if not torch_module.cuda.is_available():
            return -1
        count = int(torch_module.cuda.device_count())
    except (RuntimeError, OSError, AttributeError, TypeError, ValueError):
        return -1

    usable: list[tuple[int, int]] = []
    for index in range(max(0, count)):
        if not _cuda_probe(torch_module, index):
            continue
        try:
            props = torch_module.cuda.get_device_properties(index)
            total = int(getattr(props, "total_memory", 0))
            reserved = int(torch_module.cuda.memory_reserved(index))
            free = max(0, total - reserved)
        except (RuntimeError, OSError, AttributeError, TypeError, ValueError):
            free = 0
        usable.append((free, index))
    if not usable:
        return -1
    return max(usable)[1]


def resolve_torch_device(
    torch_module: Any,
    environ: Mapping[str, str] | None = None,
):
    cpu = _check_admission(environ)
    if cpu:
        return torch_module.device("cpu")
    index = best_cuda_index(torch_module, environ)
    if index >= 0:
        return torch_module.device(f"cuda:{index}")
    if gpu_admission_requested(environ):
        raise RuntimeError(
            "GPU-admitted reimbursement inference worker has no usable Torch CUDA device"
        )
    return torch_module.device("cpu")


def transformers_device_map(device: Any) -> dict[str, str]:
    """Pin a retained local Transformer model to the already-resolved device."""
    return {"": str(device)}


def easyocr_gpu_argument(
    torch_module: Any,
    environ: Mapping[str, str] | None = None,
) -> bool | str:
    """Return EasyOCR's explicit gpu= argument without independent probing."""
    device = resolve_torch_device(torch_module, environ)
    return False if getattr(device, "type", str(device).split(":", 1)[0]) == "cpu" else str(device)


def external_llm_device_boundary(
    provider: str,
    environ: Mapping[str, str] | None = None,
) -> dict[str, object]:
    """Describe the accelerator-control boundary for OpenAI/Ollama clients.

    The Python client cannot prove which accelerator an external daemon/service
    uses. This must never be reported as local CUDA certification.
    """
    env = os.environ if environ is None else environ
    provider_name = str(provider).strip().lower()
    return {
        "provider": provider_name,
        "local_process_device_controlled": False,
        "scheduler_backend": str(env.get("TRAINING_CONTROL_BACKEND", "")).strip().lower() or None,
        "cuda_visible_devices": env.get("CUDA_VISIBLE_DEVICES"),
        "reason": "external service owns model placement",
    }
