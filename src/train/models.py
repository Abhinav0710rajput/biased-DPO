"""Tokenizer / model loading and the fixed evaluation scorer shared by reference.py and train.py."""

import hashlib
from pathlib import Path

import numpy as np
import torch

from data import Encoded, collate
from scoring import to_device, token_logps


def source(cfg: dict) -> str:
    return cfg["model"].get("path") or cfg["model"]["hf_id"]


def load_tokenizer(cfg: dict):
    from transformers import AutoTokenizer
    tok = AutoTokenizer.from_pretrained(source(cfg))
    if tok.pad_token_id is None:
        tok.pad_token = tok.eos_token
    return tok


def device() -> torch.device:
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def load_model(cfg: dict, tok=None):
    from transformers import AutoConfig, AutoModelForCausalLM
    dtype = torch.bfloat16 if cfg["train"]["bf16"] else torch.float32
    if cfg["model"].get("tiny_random"):
        mc = AutoConfig.from_pretrained(source(cfg))
        mc.update(dict(hidden_size=64, intermediate_size=128, num_hidden_layers=2, num_attention_heads=4,
                       num_key_value_heads=2, head_dim=16, tie_word_embeddings=True))
        torch.manual_seed(1234)
        model = AutoModelForCausalLM.from_config(mc, dtype=dtype)
    else:
        model = AutoModelForCausalLM.from_pretrained(source(cfg), dtype=dtype, attn_implementation="sdpa")
    for name, m in model.named_modules():          # plan §7.3: no dropout anywhere
        if isinstance(m, torch.nn.Dropout) and m.p > 0:
            raise RuntimeError(f"dropout p={m.p} in {name}")
    for attr in ("attention_dropout", "hidden_dropout", "dropout"):
        if getattr(model.config, attr, 0) not in (0, 0.0, None):
            raise RuntimeError(f"model.config.{attr} = {getattr(model.config, attr)}")
    return model.to(device())


@torch.no_grad()
def score_encoded(model, enc: Encoded, batch_quartets: int, pad_id: int) -> tuple[np.ndarray, np.ndarray]:
    """Per-token response log-probs for every sequence of `enc`, flattened in sequence order.
    Batching is fixed (quartets in file order, batch_quartets at a time), so the reference cache and every
    evaluation of every run see identical batches (exact r = 0 at step 0, T6).
    Returns (logp float32 [T], span mask bool [T])."""
    was_training = model.training
    model.eval()
    dev = next(model.parameters()).device
    logp, span = [], []
    n = len(enc.qids)
    for start in range(0, n, batch_quartets):
        idx = list(range(start, min(n, start + batch_quartets)))
        b = to_device(collate(enc, idx, pad_id), dev)
        lp = token_logps(model, b).cpu()
        for i in range(lp.shape[0]):
            m = b["resp_mask"][i].cpu()
            logp.append(lp[i][m].numpy())
            span.append(b["span_mask"][i].cpu()[m].numpy())
    model.train(was_training)
    return np.concatenate(logp).astype(np.float32), np.concatenate(span)


def tokenization_hash(enc: Encoded) -> str:
    h = hashlib.sha256()
    for p in enc.prompt_ids:
        h.update(np.asarray(p, dtype=np.int64).tobytes())
    for r in enc.resp_ids:
        h.update(np.asarray(r, dtype=np.int64).tobytes())
    return h.hexdigest()[:16]


def build_peft_model(cfg: dict, tok=None):
    """Base model + LoRA adapters. The LoRA init depends only on the seed (never on ρ); B = 0 at init,
    so the policy equals the reference exactly at step 0."""
    from peft import LoraConfig, get_peft_model
    model = load_model(cfg, tok)
    if cfg["train"]["gradient_checkpointing"]:
        model.gradient_checkpointing_enable(gradient_checkpointing_kwargs={"use_reentrant": False})
        model.enable_input_require_grads()
    lc = cfg["lora"]
    torch.manual_seed(cfg["train"]["seed"])
    model = get_peft_model(model, LoraConfig(r=lc["r"], lora_alpha=lc["alpha"], lora_dropout=lc["dropout"],
                                             target_modules=lc["target_modules"], task_type="CAUSAL_LM"))
    model.train()
    return model
