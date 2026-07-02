from pydantic import BaseModel, Field


class BaseProduct(BaseModel):
    name: str = Field(..., min_length=1)
    brand: str = Field(..., min_length=1)


class URLGenerationResponse(BaseModel):
    amazon_ae_url: str
    noon_url: str


class EvaluateMatchRequest(BaseModel):
    product: BaseProduct
    competitor_target: str = Field(..., min_length=1)


class LLMMatchResult(BaseModel):
    exact_match_found: bool
    matched_competitor_title: str
    price: float
    confidence_score: float
    reasoning: str


class EvaluateMatchResponse(BaseModel):
    search_url: str
    scraped_results: list[str]
    llm_evaluation: LLMMatchResult
