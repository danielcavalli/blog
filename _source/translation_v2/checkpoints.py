"""Reusable successful stages, addressed by all effective inputs and contracts."""

from dataclasses import asdict
from pathlib import Path

from .accepted import digest
from .opencode_runner import ParsedStageOutput, _stage_result_from_payload
from .storage import atomic_json, read_json


class StageCheckpoints:
    def __init__(self, root):
        self.root = Path(root)
        self.contract = digest(
            [
                Path(__file__).with_name(name).read_text()
                for name in ("contracts.py", "opencode_runner.py")
            ]
        )

    def key(self, *, stage, prompt, model, reasoning):
        return digest(
            {
                "stage": stage,
                "prompt": prompt,
                "model": model,
                "reasoning": reasoning,
                "contract": self.contract,
            }
        )

    def load(self, key, *, request, stage, model):
        raw = read_json(self.root / f"{key}.json")
        if raw is None:
            return None
        if raw.get("digest") != digest(raw.get("payload")):
            raise RuntimeError(f"Damaged translation stage checkpoint: {key}")
        return _stage_result_from_payload(
            request=request,
            stage=stage,
            model=model,
            parsed_output=ParsedStageOutput(stage=stage, payload=raw["payload"], raw_json=raw),
        )

    def save(self, key, result):
        payload = asdict(result.payload)
        # A rejected final review must be rerunnable after a transient/model issue.
        if result.stage == "final_review" and not (payload["accept"] and payload["publish_ready"]):
            return
        atomic_json(self.root / f"{key}.json", {"payload": payload, "digest": digest(payload)})
