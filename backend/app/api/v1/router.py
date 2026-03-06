from fastapi import APIRouter

from app.api.v1 import (
    audit,
    auth,
    automations,
    clients,
    credit,
    documents,
    financial,
    knowledge,
    organizations,
    plans,
    tasks,
)

router = APIRouter(prefix="/api/v1")

router.include_router(auth.router)
router.include_router(documents.router)
router.include_router(tasks.router)
router.include_router(audit.router)
router.include_router(organizations.router)
router.include_router(clients.router)
router.include_router(financial.router)
router.include_router(credit.router)
router.include_router(plans.router)
router.include_router(automations.router)
router.include_router(knowledge.router)
