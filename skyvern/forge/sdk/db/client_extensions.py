"""
Extensions to the database client for cron scheduling support.
These methods will be imported and used in the main client.py file.
"""
from typing import Dict, List, Optional

from sqlalchemy import select, update
from sqlalchemy.exc import SQLAlchemyError

from skyvern.forge.sdk.db.models import WorkflowModel
from skyvern.forge.sdk.workflow.models.workflow import Workflow
from skyvern.forge.sdk.db.utils import convert_to_workflow

import structlog

LOG = structlog.get_logger(__name__)


async def update_workflow_cron_settings(
    self,
    workflow_id: str,
    cron_schedule: str | None,
    cron_enabled: bool,
    timezone: str,
    organization_id: str | None = None,
) -> Optional[Workflow]:
    """Update a workflow's cron scheduling settings."""
    try:
        async with self.Session() as session:
            filters = [WorkflowModel.workflow_id == workflow_id]

            if organization_id:
                filters.append(WorkflowModel.organization_id == organization_id)

            stmt = (
                update(WorkflowModel)
                .where(*filters)
                .values(
                    cron_schedule=cron_schedule,
                    cron_enabled=cron_enabled,
                    timezone=timezone,
                )
                .returning(WorkflowModel)
            )
            result = await session.execute(stmt)
            await session.commit()
            
            workflow_model = result.scalar_one_or_none()
            if workflow_model:
                return convert_to_workflow(workflow_model, self.debug_enabled)
            return None
    except SQLAlchemyError:
        LOG.error("SQLAlchemyError updating workflow cron settings", exc_info=True)
        raise


async def get_workflows_by_filters(
    self,
    organization_id: str,
    filters: Dict,
    active_only: bool = True,
) -> List[Workflow]:
    """Get workflows by applying multiple filters."""
    try:
        async with self.Session() as session:
            query = select(WorkflowModel).where(WorkflowModel.organization_id == organization_id)
            
            for key, value in filters.items():
                if hasattr(WorkflowModel, key):
                    query = query.where(getattr(WorkflowModel, key) == value)
            
            if active_only:
                query = query.where(WorkflowModel.deleted_at.is_(None))
            
            result = await session.execute(query)
            workflow_models = result.scalars().all()
            
            return [convert_to_workflow(wf, self.debug_enabled) for wf in workflow_models]
    except SQLAlchemyError:
        LOG.error("SQLAlchemyError getting workflows by filters", exc_info=True)
        raise
