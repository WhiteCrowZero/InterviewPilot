from __future__ import annotations

from fastapi import APIRouter

from interview_pilot.api.deps import CacheDep, CurrentActiveUserDep, DbSessionDep
from interview_pilot.modules.dashboard import service
from interview_pilot.modules.dashboard.schemas import DashboardSummary

router = APIRouter()


@router.get("/summary", response_model=DashboardSummary)
async def get_dashboard_summary(
    current_user: CurrentActiveUserDep,
    session: DbSessionDep,
    cache: CacheDep,
) -> DashboardSummary:
    return await service.get_dashboard_summary(current_user, session, cache)
