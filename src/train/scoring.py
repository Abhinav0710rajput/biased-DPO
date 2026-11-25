"""Per-token response log-probs, the quartet loss, and quartet metrics.

Index order inside a quartet is data.ORDER = (CW, CN, IW, IN).
  r = log π − log π_ref (summed over response tokens)
  u = ½(CW+CN) − ½(IW+IN)    fact preference
  v = ½(CW+IW) − ½(CN+IN)    tone preference
  w = ½(CW−IW) − ½(CN−IN)    tone × fact interaction
Pair gaps: CW≻IW = u+w, CN≻IN = u−w, CW≻IN = u+v, CN≻IW = u−v.
"""

import numpy as np
import torch
import torch.nn.functional as F


# ---------------------------------------------------------------- log-probs

LOGPROB_CHUNK = 8   # sequences per fp32 log-softmax chunk (memory only; results are identical)

def token_logps(model, batch: dict) -> torch.Tensor:
    """[S, K] log-prob of each target token (0 outside the response). Only the last K+1 positions'
    logits are computed (responses are at the end of the left-padded sequences)."""
    K = batch["K"]
    out = model(input_ids=batch["input_ids"], attention_mask=batch["attention_mask"],
                position_ids=batch["position_ids"], logits_to_keep=K + 1, use_cache=False)
    logits = out.logits[:, :-1]                               # predicts positions L-K .. L-1 (model dtype)
    tgt = batch["targets"]
    # fp32 log-softmax pieces in chunks of sequences: a full fp32 copy of [S, K, vocab] is ~6 GB at S = 128
    parts = []
    for i in range(0, logits.shape[0], LOGPROB_CHUNK):
        lg = logits[i:i + LOGPROB_CHUNK].float()
        parts.append(lg.gather(-1, tgt[i:i + LOGPROB_CHUNK].unsqueeze(-1)).squeeze(-1) - torch.logsumexp(lg, -1))
    return torch.cat(parts) * batch["resp_mask"]


def to_device(batch: dict, device) -> dict:
    return {k: (v.to(device) if torch.is_tensor(v) else v) for k, v in batch.items()}


# ---------------------------------------------------------------- loss

def contrasts(r: torch.Tensor):
    CW, CN, IW, IN = r.unbind(-1)
    u = 0.5 * (CW + CN) - 0.5 * (IW + IN)
    v = 0.5 * (CW + IW) - 0.5 * (CN + IN)
    w = 0.5 * (CW - IW) - 0.5 * (CN - IN)
    return u, v, w


def ell(z):  # −log σ(z)
    return F.softplus(-z)


def pair_weights(obj: dict) -> dict:
    """Weight of each preference pair for this objective (plan §2.4, §7.2)."""
    if obj["name"] == "posctrl":
        return {"CW_IW": 0.0, "CN_IN": 0.0, "CW_IN": obj["posctrl_weights"]["CW_IN"],
                "CN_IW": obj["posctrl_weights"]["CN_IW"]}
    rho = 0.0 if obj["name"] == "ties" else obj["rho"]
    return {"CW_IW": (1 - rho) / 2, "CN_IN": (1 - rho) / 2, "CW_IN": rho / 2, "CN_IW": rho / 2}


def quartet_loss(r: torch.Tensor, obj: dict) -> torch.Tensor:
    """Per-quartet loss [B] from r [B, 4]. Mean over quartets is taken by the caller."""
    beta, pw = obj["beta"], pair_weights(obj)
    u, v, w = contrasts(r)
    loss = (pw["CW_IW"] * ell(beta * (u + w)) + pw["CN_IN"] * ell(beta * (u - w))
            + pw["CW_IN"] * ell(beta * (u + v)) + pw["CN_IW"] * ell(beta * (u - v)))
    if obj["name"] == "ties":   # tie pairs CW~CN (gap v+w) and IW~IN (gap v−w): soft label ½, minimised at gap 0
        for m in (v + w, v - w):
            loss = loss + obj["tie_weight"] * 0.5 * (ell(beta * m) + ell(-beta * m))
    return loss


def quartet_loss_pairwise(r: torch.Tensor, obj: dict) -> torch.Tensor:
    """Same loss written pair by pair from the raw r values (T1 compares the two)."""
    beta, pw = obj["beta"], pair_weights(obj)
    CW, CN, IW, IN = r.unbind(-1)
    loss = (pw["CW_IW"] * ell(beta * (CW - IW)) + pw["CN_IN"] * ell(beta * (CN - IN))
            + pw["CW_IN"] * ell(beta * (CW - IN)) + pw["CN_IW"] * ell(beta * (CN - IW)))
    if obj["name"] == "ties":
        for a, b in ((CW, CN), (IW, IN)):
            loss = loss + obj["tie_weight"] * 0.5 * (ell(beta * (a - b)) + ell(beta * (b - a)))
    return loss


# ---------------------------------------------------------------- metrics

def quartet_metrics(s: np.ndarray, prefix: str = "") -> dict:
    """Summary of scores s [N, 4] (r, or log π_ref for the untrained-model check)."""
    s = np.asarray(s, dtype=np.float64)
    CW, CN, IW, IN = s.T
    u = 0.5 * (CW + CN) - 0.5 * (IW + IN)
    v = 0.5 * (CW + IW) - 0.5 * (CN + IN)
    w = 0.5 * (CW - IW) - 0.5 * (CN - IN)
    gaps = {"CW>IW": u + w, "CN>IN": u - w, "CW>IN": u + v, "CN>IW": u - v}
    out = {"n": len(s), "u": u.mean(), "v": v.mean(), "w": w.mean(), "abs_v": np.abs(v).mean(),
           "abs_w": np.abs(w).mean(), "worst_case_acc": float(np.mean(np.all(np.stack(list(gaps.values())) > 0, 0)))}
    for k, g in gaps.items():
        out[f"acc_{k}"] = float(np.mean(g > 0))
    out["pairwise_acc"] = float(np.mean([out[f"acc_{k}"] for k in gaps]))
    return {prefix + k: (round(float(v), 6) if isinstance(v, (float, np.floating)) else v) for k, v in out.items()}


def sums_from_tokens(tok: np.ndarray, offsets: np.ndarray, mask: np.ndarray | None = None) -> np.ndarray:
    """Flat per-token values -> per-sequence sums reshaped [N, 4] (optionally restricted by a flat mask)."""
    vals = tok if mask is None else tok * mask
    seq = np.add.reduceat(vals, offsets[:-1]) if len(vals) else np.zeros(len(offsets) - 1)
    seq[offsets[1:] == offsets[:-1]] = 0.0
    return seq.reshape(-1, 4)
