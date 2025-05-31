import asyncio
import datetime
from typing import Dict, List, Optional

import croniter
import pytz
import structlog
from fastapi import FastAPI

from skyvern.forge import app
from skyvern.forge.sdk.executor.factory import AsyncExecutorFactory
from skyvern.forge.sdk.schemas.organizations import Organization
from skyvern.forge.sdk.workflow.models.workflow import WorkflowRequestBody

LOG = structlog.get_logger(__name__)


class CronTriggerService:
    """Service for managing cron-based workflow triggers."""

    def __init__(self) -> None:
        self._running_tasks: Dict[str, asyncio.Task] = {}
        self._shutdown_event = asyncio.Event()
        self._task_lock = asyncio.Lock()
        self._main_task: Optional[asyncio.Task] = None

    async def start(self) -> None:
        """Start the cron trigger service."""
        LOG.info("Starting cron trigger service")
        self._shutdown_event.clear()
        self._main_task = asyncio.create_task(self._scheduler_loop())
        LOG.info("Cron trigger service started successfully")

    async def stop(self) -> None:
        """Stop the cron trigger service."""
        LOG.info("Stopping cron trigger service")
        if self._main_task:
            self._shutdown_event.set()
            await self._main_task
            self._main_task = None
        
        async with self._task_lock:
            for task_id, task in list(self._running_tasks.items()):
                if not task.done():
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
                    except Exception as e:
                        LOG.error("Error cancelling task", task_id=task_id, error=str(e))
                self._running_tasks.pop(task_id, None)
        LOG.info("Cron trigger service stopped")

    async def _scheduler_loop(self) -> None:
        """Main scheduler loop that checks for workflows to trigger based on their cron schedule."""
        while not self._shutdown_event.is_set():
            try:
                await self._check_workflows()
            except Exception as e:
                LOG.error("Error in scheduler loop", error=str(e))
            
            # Wait for 60 seconds before checking again
            # Using wait_for with timeout allows for clean shutdown
            try:
                await asyncio.wait_for(self._shutdown_event.wait(), timeout=60)
            except asyncio.TimeoutError:
                # Timeout is expected, just continue the loop
                pass

    async def _check_workflows(self) -> None:
        """Check all workflows with enabled cron schedules and trigger them if needed."""
        current_time = datetime.datetime.now(pytz.UTC)
        LOG.debug("Checking workflows for cron triggers", current_time=current_time)

        # Get all organizations
        organizations = await app.DATABASE.get_organizations()
        
        # For each organization, get all workflows with cron schedules
        for org in organizations:
            org_workflows = await self._get_cron_enabled_workflows(org.organization_id)
            
            for workflow in org_workflows:
                try:
                    # Skip workflows with no cron schedule or disabled cron
                    if not workflow.cron_schedule or not workflow.cron_enabled:
                        continue

                    # Convert the schedule to the workflow's timezone
                    tz = pytz.timezone(workflow.timezone)
                    local_time = current_time.astimezone(tz)
                    
                    # Create a croniter instance to check if the workflow should be triggered
                    cron = croniter.croniter(workflow.cron_schedule, local_time)
                    prev_execution_time = cron.get_prev(datetime.datetime)
                    
                    # Check if the workflow should run in the last minute
                    # This approach accounts for cases where the service might have been down
                    time_diff = (local_time - prev_execution_time).total_seconds()
                    
                    if 0 <= time_diff < 60:  # Within the last minute
                        task_id = f"{workflow.workflow_id}_{int(current_time.timestamp())}"
                        
                        async with self._task_lock:
                            # Check if this workflow is not already running
                            existing_tasks = [k for k in self._running_tasks.keys() if k.startswith(workflow.workflow_id)]
                            if existing_tasks:
                                LOG.info(
                                    "Skipping cron trigger for workflow as it's already running", 
                                    workflow_id=workflow.workflow_id, 
                                    workflow_title=workflow.title,
                                    task_id=task_id
                                )
                                continue
                                
                            LOG.info(
                                "Triggering workflow from cron schedule", 
                                workflow_id=workflow.workflow_id, 
                                workflow_title=workflow.title,
                                cron_schedule=workflow.cron_schedule,
                                timezone=workflow.timezone,
                                task_id=task_id
                            )
                            
                            # Create a task to run the workflow
                            task = asyncio.create_task(
                                self._run_workflow(
                                    workflow_id=workflow.workflow_permanent_id, 
                                    organization=await app.DATABASE.get_organization(workflow.organization_id),
                                    task_id=task_id
                                )
                            )
                            self._running_tasks[task_id] = task
                
                except Exception as e:
                    LOG.error(
                        "Error processing cron schedule for workflow", 
                        workflow_id=workflow.workflow_id, 
                        error=str(e)
                    )

    async def _run_workflow(self, workflow_id: str, organization: Organization, task_id: str) -> None:
        """Run a workflow based on its cron schedule."""
        try:
            LOG.info("Running workflow from cron schedule", workflow_id=workflow_id, task_id=task_id)
            
            # Create a simple workflow request body
            workflow_request = WorkflowRequestBody(
                parameters={},  # Empty parameters for cron-triggered workflows
                browser_session_id=None,  # No browser session for cron-triggered workflows
                metadata={
                    "trigger_type": "cron",
                    "task_id": task_id,
                    "scheduled_at": datetime.datetime.utcnow().isoformat()
                }
            )

            # Run the workflow
            workflow_run = await app.WORKFLOW_SERVICE.setup_workflow_run(
                request_id=task_id,
                workflow_request=workflow_request,
                workflow_permanent_id=workflow_id,
                organization=organization,
                is_template_workflow=False
            )
            
            # Create task run record
            workflow = await app.WORKFLOW_SERVICE.get_workflow_by_permanent_id(
                workflow_permanent_id=workflow_id,
                organization_id=organization.organization_id
            )
            await app.DATABASE.create_task_run(
                task_run_type="workflow_run",
                organization_id=organization.organization_id,
                run_id=workflow_run.workflow_run_id,
                title=f"{workflow.title} (Cron Scheduled)",
            )
            
            # Execute the workflow
            await AsyncExecutorFactory.get_executor().execute_workflow(
                request=None,
                background_tasks=None,
                organization=organization,
                workflow_id=workflow_run.workflow_id,
                workflow_run_id=workflow_run.workflow_run_id,
                browser_session_id=None,
                api_key=None,
            )
            
            LOG.info(
                "Successfully triggered workflow from cron schedule", 
                workflow_id=workflow_id,
                workflow_run_id=workflow_run.workflow_run_id,
                task_id=task_id
            )
        except Exception as e:
            LOG.error(
                "Error running workflow from cron schedule", 
                workflow_id=workflow_id, 
                error=str(e),
                task_id=task_id
            )
        finally:
            # Clean up the task
            async with self._task_lock:
                self._running_tasks.pop(task_id, None)

    async def _get_cron_enabled_workflows(self, organization_id: str) -> List:
        """Get all workflows for an organization that have cron scheduling enabled."""
        # Fetch workflows with cron_enabled=True
        workflows = await app.DATABASE.get_workflows_by_filters(
            organization_id=organization_id,
            filters={"cron_enabled": True},
            active_only=True
        )
        return workflows
