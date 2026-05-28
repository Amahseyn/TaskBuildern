from typing import Dict, Type
from extractor.strategies.base import BaseStrategy
from extractor.strategies.native_multimodal import NativeMultimodalStrategy
from extractor.strategies.pure_text import PureTextStrategy
from extractor.strategies.hybrid_chunking import HybridChunkingStrategy
from extractor.strategies.ocr_pipeline import OCRPipelineStrategy
from extractor.strategies.vision_vlm import VisionVLMStrategy
from extractor.strategies.two_stage import TwoStageHybridStrategy
from extractor.strategies.self_verification import SelfVerificationStrategy

STRATEGIES: Dict[str, Type[BaseStrategy]] = {
    "native_multimodal": NativeMultimodalStrategy,
    "pure_text": PureTextStrategy,
    "hybrid_chunking": HybridChunkingStrategy,
    "ocr_pipeline": OCRPipelineStrategy,
    "vision_vlm": VisionVLMStrategy,
    "two_stage": TwoStageHybridStrategy,
    "self_verification": SelfVerificationStrategy,
}

__all__ = ["STRATEGIES", "BaseStrategy"]
