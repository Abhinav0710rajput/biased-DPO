"""Quartets -> token sequences.

Each quartet becomes 4 sequences in the fixed order CW, CN, IW, IN (ORDER). A sequence is
  prompt tokens (chat template, user turn + generation prompt)  +  response tokens
where the response tokens are the response text followed by the end-of-turn token (include_eot).
Only response tokens are scored. The answer span (`ans_span`, character offsets into the response
text) is mapped to the response tokens that overlap it.

Prompt and response are tokenized separately and concatenated, so the response tokenization is
identical in every context (training, evaluation, every ρ).
"""

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

import numpy as np
import torch

ORDER = ("CW", "CN", "IW", "IN")      # index 0..3 everywhere (loss, metrics, saved arrays)
WARM = (0, 2)                          # CW, IW
NEUTRAL = (1, 3)                       # CN, IN


def load_quartets(path: Path) -> list[dict]:
    return [json.loads(l) for l in open(path)]


@dataclass
class Encoded:
    """Token data for N quartets (4N sequences, quartet-major: seq 4*i + k is response ORDER[k])."""
    qids: list[str]
    prompt_ids: list[list[int]]        # per quartet
    resp_ids: list[list[int]]          # per sequence (4N)
    span_mask: list[list[bool]]        # per sequence, same length as resp_ids

    def n_resp_tokens(self) -> np.ndarray:
        return np.array([len(r) for r in self.resp_ids])

    def offsets(self) -> np.ndarray:
        return np.concatenate([[0], np.cumsum(self.n_resp_tokens())])


class Encoder:
    def __init__(self, tokenizer, cfg: dict):
        self.tok = tokenizer
        self.template = cfg["prompt"]["template"]
        self.template_kwargs = cfg["model"].get("chat_template_kwargs") or {}
        eot = cfg["model"].get("eot_token") or tokenizer.eos_token
        self.eot_ids = tokenizer.encode(eot, add_special_tokens=False) if cfg["prompt"]["include_eot"] else []
        if cfg["prompt"]["include_eot"] and len(self.eot_ids) != 1:
            raise ValueError(f"end-of-turn {eot!r} is not a single token: {self.eot_ids}")

    def prompt_text(self, q: dict) -> str:
        user = self.template.format(passage=q["passage"], question=q["question"])
        return self.tok.apply_chat_template([{"role": "user", "content": user}], tokenize=False,
                                            add_generation_prompt=True, **self.template_kwargs)

    def prompt_ids(self, q: dict) -> list[int]:
        return self.tok.encode(self.prompt_text(q), add_special_tokens=False)

    def response(self, text: str, span: list[int] | None) -> tuple[list[int], list[bool]]:
        enc = self.tok(text, add_special_tokens=False, return_offsets_mapping=True)
        ids = list(enc["input_ids"])
        if span is None:
            mask = [False] * len(ids)
        else:
            s, e = span
            mask = [a < e and b > s for a, b in enc["offset_mapping"]]
        return ids + self.eot_ids, mask + [False] * len(self.eot_ids)

    def encode(self, quartets: list[dict]) -> Encoded:
        qids, p_ids, r_ids, s_mask = [], [], [], []
        for q in quartets:
            qids.append(q["qid"])
            p_ids.append(self.prompt_ids(q))
            for k in ORDER:
                resp = q["responses"][k]
                ids, mask = self.response(resp["text"], resp.get("ans_span"))
                r_ids.append(ids)
                s_mask.append(mask)
        return Encoded(qids, p_ids, r_ids, s_mask)


def collate(enc: Encoded, quartet_idx: list[int], pad_id: int) -> dict:
    """Left-padded batch of 4·len(quartet_idx) sequences, so every response ends at the last position.

    Returns input_ids, attention_mask, position_ids [S, L] and, for the last K = max response length
    positions, the response mask, span mask and targets [S, K]. Position ids count real tokens only, so
    a sequence's log-probs do not depend on how much padding its batch needs.
    """
    seqs, resp_len, span = [], [], []
    for qi in quartet_idx:
        for k in range(4):
            j = 4 * qi + k
            seqs.append(enc.prompt_ids[qi] + enc.resp_ids[j])
            resp_len.append(len(enc.resp_ids[j]))
            span.append(enc.span_mask[j])
    S, L, K = len(seqs), max(map(len, seqs)), max(resp_len)
    input_ids = torch.full((S, L), pad_id, dtype=torch.long)
    attn = torch.zeros((S, L), dtype=torch.long)
    resp_mask = torch.zeros((S, K), dtype=torch.bool)
    span_mask = torch.zeros((S, K), dtype=torch.bool)
    for i, s in enumerate(seqs):
        input_ids[i, L - len(s):] = torch.tensor(s)
        attn[i, L - len(s):] = 1
        resp_mask[i, K - resp_len[i]:] = True
        if resp_len[i]:
            span_mask[i, K - resp_len[i]:] = torch.tensor(span[i] + [False] * (resp_len[i] - len(span[i])))
    position_ids = (attn.cumsum(-1) - 1).clamp(min=0)
    return {"input_ids": input_ids, "attention_mask": attn, "position_ids": position_ids,
            "targets": input_ids[:, L - K:], "resp_mask": resp_mask, "span_mask": span_mask, "K": K}


def epoch_order(n: int, seed: int, epoch: int) -> np.ndarray:
    """Quartet order for one epoch. Depends only on (seed, epoch): identical for every ρ (plan §7.3)."""
    return np.random.default_rng([seed, epoch]).permutation(n)


def batches(n: int, seed: int, epochs: int, batch_quartets: int):
    """Yield (step, epoch, quartet indices) for the whole run. The incomplete last batch of each epoch is
    dropped so every optimizer step sees exactly batch_quartets whole quartets."""
    step = 0
    per_epoch = n // batch_quartets
    for epoch in range(epochs):
        order = epoch_order(n, seed, epoch)
        for b in range(per_epoch):
            yield step, epoch, order[b * batch_quartets:(b + 1) * batch_quartets].tolist()
            step += 1


def total_steps(n: int, epochs: int, batch_quartets: int) -> int:
    return (n // batch_quartets) * epochs


def batch_hash(qids: list[str]) -> str:
    return hashlib.sha256(",".join(qids).encode()).hexdigest()[:16]
