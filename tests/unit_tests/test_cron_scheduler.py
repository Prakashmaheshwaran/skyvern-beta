import pytest
from apscheduler.schedulers.asyncio import AsyncIOScheduler

from skyvern.services import cron_scheduler


class DummyWorkflow:
    def __init__(self, cron_schedule=None, cron_timezone="UTC", workflow_permanent_id="wf"): 
        self.cron_schedule = cron_schedule
        self.cron_timezone = cron_timezone
        self.workflow_permanent_id = workflow_permanent_id


class DummyOrganization:
    def __init__(self, organization_id="org"):
        self.organization_id = organization_id


@pytest.mark.asyncio
async def test_schedule_workflow_invalid_cron(monkeypatch, caplog):
    scheduler = AsyncIOScheduler()
    monkeypatch.setattr(cron_scheduler, "scheduler", scheduler)

    workflow = DummyWorkflow(cron_schedule="invalid")
    org = DummyOrganization()

    with caplog.at_level("ERROR"):
        await cron_scheduler.schedule_workflow(workflow, org)

    assert scheduler.get_jobs() == []
    assert any("Invalid cron schedule" in rec.message for rec in caplog.records)


@pytest.mark.asyncio
async def test_schedule_workflow_invalid_timezone(monkeypatch, caplog):
    scheduler = AsyncIOScheduler()
    monkeypatch.setattr(cron_scheduler, "scheduler", scheduler)

    workflow = DummyWorkflow(cron_schedule="* * * * *", cron_timezone="Invalid/Zone")
    org = DummyOrganization()

    with caplog.at_level("ERROR"):
        await cron_scheduler.schedule_workflow(workflow, org)

    assert scheduler.get_jobs() == []
    assert any("Invalid timezone" in rec.message for rec in caplog.records)
