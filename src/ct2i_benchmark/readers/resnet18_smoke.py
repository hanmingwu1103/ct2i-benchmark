"""ResNet-18 CPU smoke test (contract §14): one forward pass, one loss, one
backward pass, one optimizer step at 224x224 on CPU. NOT a performance
experiment; never used in pilot comparison."""
from __future__ import annotations

import time

import numpy as np


def resnet18_cpu_smoke(images_gray: np.ndarray, labels: np.ndarray, seed: int = 3):
    import torch
    import torchvision

    assert not torch.cuda.is_available() or True  # branch stays CPU regardless
    torch.manual_seed(seed)
    device = torch.device("cpu")
    n = min(len(images_gray), 8)
    x = torch.tensor(images_gray[:n], dtype=torch.float32)
    if x.ndim == 3:
        x = x.unsqueeze(1)
    x = torch.nn.functional.interpolate(x, size=(224, 224), mode="bilinear",
                                        align_corners=False)
    x = x.repeat(1, 3, 1, 1).to(device)
    y = torch.tensor(labels[:n], dtype=torch.long).to(device)

    model = torchvision.models.resnet18(weights=None, num_classes=2).to(device)
    model.train()
    opt = torch.optim.Adam(model.parameters(), lr=1e-4)
    t0 = time.perf_counter()
    logits = model(x)
    loss = torch.nn.functional.cross_entropy(logits, y)
    opt.zero_grad(); loss.backward(); opt.step()
    elapsed = time.perf_counter() - t0
    return {"n": n, "loss": float(loss.item()), "elapsed_s": elapsed,
            "device": str(device), "cuda_available": torch.cuda.is_available()}
