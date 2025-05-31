from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Path, Query
from pydantic import BaseModel, Field

from skyvern.forge.sdk.services.org_auth_service import get_current_org as get_current_organization
# User authentication will be handled through the organization authentication
from skyvern.forge import app
from skyvern.forge.sdk.schemas.organizations import Organization
from skyvern.utils.cron_validator import validate_cron_expression, get_next_run_description

router = APIRouter(prefix="/api/workflows", tags=["workflow-schedules"])


class CronScheduleRequest(BaseModel):
    """Schema for cron schedule request."""
    
    cron_schedule: Optional[str] = Field(
        None, 
        description="Cron expression for scheduling workflow (e.g. '0 0 * * *' for daily at midnight)",
        example="0 9 * * MON-FRI"
    )
    cron_enabled: bool = Field(
        False, 
        description="Whether the cron schedule is enabled"
    )
    timezone: str = Field(
        "UTC", 
        description="Timezone for the cron schedule",
        example="America/New_York"
    )


class CronScheduleResponse(BaseModel):
    """Schema for cron schedule response."""
    
    workflow_id: str = Field(..., description="Unique identifier for the workflow")
    cron_schedule: Optional[str] = Field(None, description="Cron expression for scheduling workflow")
    cron_enabled: bool = Field(..., description="Whether the cron schedule is enabled")
    timezone: str = Field(..., description="Timezone for the cron schedule")
    next_run_description: Optional[str] = Field(None, description="Human-readable description of the next run time")


@router.post(
    "/{workflow_id}/cron-schedule",
    response_model=CronScheduleResponse,
    summary="Set cron schedule for a workflow",
    description="Configure a cron schedule for automated workflow execution",
)
async def set_cron_schedule(
    workflow_id: str = Path(..., title="Workflow ID"),
    cron_request: CronScheduleRequest = None,
    organization: Organization = Depends(get_current_organization),
):
    """Set cron schedule for a workflow."""
    # Check if workflow exists
    workflow = await app.DATABASE.get_workflow(workflow_id, organization_id=organization.organization_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Validate cron expression if provided and enabled
    if cron_request.cron_enabled and cron_request.cron_schedule:
        is_valid, error_message = validate_cron_expression(cron_request.cron_schedule)
        if not is_valid:
            raise HTTPException(status_code=400, detail=f"Invalid cron expression: {error_message}")
    
    # Update workflow cron settings
    updated_workflow = await app.DATABASE.update_workflow_cron_settings(
        workflow_id=workflow_id,
        cron_schedule=cron_request.cron_schedule,
        cron_enabled=cron_request.cron_enabled,
        timezone=cron_request.timezone,
        organization_id=organization.organization_id,
    )
    
    if not updated_workflow:
        raise HTTPException(status_code=500, detail="Failed to update workflow cron schedule")
    
    # Get human-readable description of the next run
    next_run_description = None
    if updated_workflow.cron_enabled and updated_workflow.cron_schedule:
        next_run_description = get_next_run_description(updated_workflow.cron_schedule)
    
    # Return the updated cron schedule
    return CronScheduleResponse(
        workflow_id=workflow_id,
        cron_schedule=updated_workflow.cron_schedule,
        cron_enabled=updated_workflow.cron_enabled,
        timezone=updated_workflow.timezone,
        next_run_description=next_run_description,
    )


@router.get(
    "/{workflow_id}/cron-schedule",
    response_model=CronScheduleResponse,
    summary="Get cron schedule for a workflow",
    description="Retrieve the current cron schedule configuration for a workflow",
)
async def get_cron_schedule(
    workflow_id: str = Path(..., title="Workflow ID"),
    organization: Organization = Depends(get_current_organization),
):
    """Get cron schedule for a workflow."""
    # Check if workflow exists
    workflow = await app.DATABASE.get_workflow(workflow_id, organization_id=organization.organization_id)
    if workflow is None:
        raise HTTPException(status_code=404, detail="Workflow not found")
    
    # Get human-readable description of the next run
    next_run_description = None
    if workflow.cron_enabled and workflow.cron_schedule:
        next_run_description = get_next_run_description(workflow.cron_schedule)
    
    # Return the workflow's cron schedule
    return CronScheduleResponse(
        workflow_id=workflow_id,
        cron_schedule=workflow.cron_schedule,
        cron_enabled=workflow.cron_enabled,
        timezone=workflow.timezone or "UTC",
        next_run_description=next_run_description,
    )
