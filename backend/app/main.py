import logging

from fastapi import FastAPI, HTTPException
from fastapi.concurrency import run_in_threadpool
from fastapi.middleware.cors import CORSMiddleware
from pydantic import ValidationError

from .ai_client import AIClientError, AIReviewerClient
from .config import settings
from .parsing import ParseError, parse_review_json
from .schemas import MOCK_ISSUES, ReviewRequest, ReviewResponse

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="AI Code Reviewer API",
    version="0.3.1",
    description="AI-powered code review endpoint with robust parsing and validation.",
)

allow_credentials = "*" not in settings.cors_origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

ai_reviewer = AIReviewerClient()


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/review", response_model=ReviewResponse)
async def review_code(payload: ReviewRequest) -> ReviewResponse:
    line_count = payload.code.count("\n") + 1
    if line_count > settings.max_code_lines:
        raise HTTPException(
            status_code=400,
            detail=f"Code input too large. Maximum is {settings.max_code_lines} lines.",
        )

    if len(payload.code) > settings.max_code_chars:
        raise HTTPException(
            status_code=400,
            detail=f"Code input too large. Maximum is {settings.max_code_chars} characters.",
        )

    if settings.mock_mode:
        logger.info("MOCK_MODE enabled: returning mock issues")
        return ReviewResponse(issues=MOCK_ISSUES)

    try:
        raw_output = await run_in_threadpool(
            ai_reviewer.review_code, payload.code, payload.language
        )
    except AIClientError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc

    try:
        parsed = parse_review_json(raw_output)
        return ReviewResponse.model_validate(parsed)
    except ParseError as exc:
        logger.exception("Failed to parse model output")
        raise HTTPException(
            status_code=502,
            detail=f"AI returned non-JSON output: {exc}",
        ) from exc
    except ValidationError as exc:
        logger.exception("Model JSON failed schema validation")
        raise HTTPException(
            status_code=502,
            detail=f"AI returned invalid schema: {exc.errors()}",
        ) from exc