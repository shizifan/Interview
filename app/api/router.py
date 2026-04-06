from fastapi import APIRouter

from app.api.candidate import router as candidate_router
from app.api.hr import router as hr_router
from app.api.interview import router as interview_router
from app.api.files import router as files_router

api_router = APIRouter()

api_router.include_router(candidate_router, prefix="/candidate")
api_router.include_router(hr_router, prefix="/hr")
api_router.include_router(interview_router, prefix="/interview")
api_router.include_router(files_router, prefix="/files")
