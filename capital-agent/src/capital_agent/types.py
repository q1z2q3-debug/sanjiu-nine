import time
from dataclasses import dataclass, field
from enum import Enum

class AssetType(str, Enum):
    STATE = "state"
    TRANSITION = "transition"
    POLICY = "policy"

@dataclass
class Asset:
    type: AssetType
    payload: dict
    source: str
    trit: str
    ts: float = field(default_factory=time.time)

    def to_dict(self):
        return {"type": self.type.value, "payload": self.payload,
                "source": self.source, "trit": self.trit, "ts": self.ts}

@dataclass
class Weights:
    address: float = 0.3
    positive: float = 0.3
    coherence: float = 0.2
    potential: float = 0.2

    def normalized(self):
        s = self.address + self.positive + self.coherence + self.potential
        if s == 0:
            return Weights(0.25, 0.25, 0.25, 0.25)
        return Weights(self.address/s, self.positive/s, self.coherence/s, self.potential/s)
