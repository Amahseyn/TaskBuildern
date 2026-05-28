from typing import List, Literal, Optional
from pydantic import BaseModel, Field

class ExtractedString(BaseModel):
    value: Optional[Literal["residential", "renovation", "extension", "unknown"]] = None
    confidence: Literal["high", "medium", "low"]
    reasoning: str

class ExtractedInt(BaseModel):
    value: Optional[int] = None
    confidence: Literal["high", "medium", "low"]
    reasoning: str

class ExtractedFloat(BaseModel):
    value: Optional[float] = None
    confidence: Literal["high", "medium", "low"]
    reasoning: str

class ExtractedBool(BaseModel):
    value: Optional[bool] = None
    confidence: Literal["high", "medium", "low"]
    reasoning: str

class ProjectSummary(BaseModel):
    type: ExtractedString = Field(description="residential, renovation, extension, or unknown")
    floors: ExtractedInt = Field(description="Number of distinct above-ground levels")
    approxFloorArea: ExtractedFloat = Field(description="Gross Floor Area in m²")

class KeySignals(BaseModel):
    roomCountApprox: ExtractedInt
    windowCountApprox: ExtractedInt
    hasExtension: ExtractedBool
    hasStructuralChanges: ExtractedBool

class ExtractionResult(BaseModel):
    projectSummary: ProjectSummary
    detectedScopes: List[Literal[
        "foundation", "framing", "roofing", "insulation",
        "windows_doors", "demolition", "retaining_walls"
    ]]
    keySignals: KeySignals
    materialsOrSpecs: List[str]
    openQuestions: List[str]
