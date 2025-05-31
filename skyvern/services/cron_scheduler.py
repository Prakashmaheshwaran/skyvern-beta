import asyncio
from zoneinfo import ZoneInfo

import structlog
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from skyvern.config import settings
from skyvern.forge import app
from skyvern.forge.sdk.schemas.organizations import Organization
from skyvern.forge.sdk.workflow.models.workflow import Workflow, WorkflowRequestBody
from skyvern.services import workflow_service

LOG = structlog.get_logger(__name__)

scheduler = AsyncIOScheduler()


async def schedule_workflow(workflow: Workflow, organization: Organization) -> None:
    """Add a workflow to the scheduler if it has a cron schedule."""

    cron_schedule = getattr(workflow, "cron_schedule", None)
    if not cron_schedule:
        return

    timezone_str = getattr(workflow, "cron_timezone", "UTC")
    try:
        tzinfo = ZoneInfo(timezone_str)
    except Exception as exc:  # pragma: no cover - defensive
        LOG.error(
            "Invalid timezone for cron schedule",
            timezone=timezone_str,
            workflow_permanent_id=workflow.workflow_permanent_id,
            organization_id=organization.organization_id,
            exc_info=exc,
        )
        return

    try:
        trigger = CronTrigger.from_crontab(cron_schedule, timezone=tzinfo)
    except Exception as exc:  # pragma: no cover - defensive
        LOG.error(
            "Invalid cron schedule",
            cron_schedule=cron_schedule,
            timezone=timezone_str,
            workflow_permanent_id=workflow.workflow_permanent_id,
            organization_id=organization.organization_id,
            exc_info=exc,
        )
        return

    scheduler.add_job(
        workflow_service.run_workflow,
        trigger=trigger,
        args=[workflow.workflow_permanent_id, organization, WorkflowRequestBody()],
        id=f"{organization.organization_id}_{workflow.workflow_permanent_id}",
        replace_existing=True,
    )

async def load_workflows() -> None:
    """Load all workflows from the database and schedule them."""

    organizations = await app.DATABASE.get_all_organizations()
    for organization in organizations:
        workflows = await app.WORKFLOW_SERVICE.get_workflows_by_organization_id(
            organization_id=organization.organization_id,
            page_size=1000,
        )
        for workflow in workflows:
            await schedule_workflow(workflow, organization)

async def _poll_workflows(interval_seconds: int) -> None:
    """Periodically reload workflows so schedule changes take effect."""

    while True:
        await asyncio.sleep(interval_seconds)
        try:
            await load_workflows()
        except Exception:  # noqa: BLE001
            LOG.exception("Failed to reload workflows")


async def start_scheduler() -> None:
    """Start the cron scheduler and refresh workflows periodically."""

    await load_workflows()
    scheduler.start()
    asyncio.create_task(_poll_workflows(settings.CRON_WORKFLOW_REFRESH_INTERVAL_SECONDS))
    LOG.info("Cron trigger started successfully")
    await asyncio.Event().wait()
