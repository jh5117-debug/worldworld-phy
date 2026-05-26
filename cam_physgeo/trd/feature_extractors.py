class FeatureExtractorUnavailable(RuntimeError): pass
class FrozenVideoFeatureExtractor:
    def __init__(self, name: str='vjepa2_or_videomae_fallback', checkpoint: str|None=None): self.name=name; self.checkpoint=checkpoint
    def __call__(self, video):
        raise FeatureExtractorUnavailable('External feature extractor is not loaded. Configure V-JEPA/VideoMAE locally; no download is attempted here.')
