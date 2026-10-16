from .types import Asset, AssetType

class AssetExtractor:
    def __init__(self, memory):
        self.mem = memory

    def extract(self, trit, action, source, success) -> list[Asset]:
        assets = []
        self.mem.upsert_policy(trit, action, source=source, success=success,
                              confidence_delta=0.1 if success else -0.05)
        assets.append(Asset(AssetType.POLICY,
                            {"trit": trit, "action": action, "success": success},
                            source, trit))
        if success:
            self.mem.record_transition(trit, action)
            assets.append(Asset(AssetType.TRANSITION,
                                {"from": trit, "to": action}, source, trit))
        existing = self.mem.by_address(action, limit=1)
        if not existing:
            states = {str(i): int(c) - 1 for i, c in enumerate(action, 1)}
            self.mem.store(context=f"self-discovered {action}",
                           encoding={"trit": action, "decimal": int(action, 3),
                                     "hex_id": "0x0"},
                           states=states, summary=f"发现 {action}",
                           task_tag="self-discovered")
            assets.append(Asset(AssetType.STATE, {"trit": action}, source, action))
        return assets
