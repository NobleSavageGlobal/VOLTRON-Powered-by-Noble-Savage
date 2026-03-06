from fastapi import APIRouter

from app.api.v1 import auth, documents, tasks, audit, organizations

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(tasks.router)
router.include_router(audit.router)
router.include_router(organizations.router)
