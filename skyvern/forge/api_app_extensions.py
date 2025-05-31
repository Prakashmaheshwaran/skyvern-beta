"""
Extensions to the FastAPI application for cron scheduling support.
"""
import structlog
from fastapi import FastAPI

from skyvern.services.cron_trigger_service import CronTriggerService

LOG = structlog.get_logger(__name__)

# Initialize cron trigger service
cron_service = CronTriggerService()


def register_cron_service(app: FastAPI) -> None:
    """Register the cron trigger service with the FastAPI application."""
    
    @app.on_event("startup")
    async def start_cron_service():
        """Start the cron trigger service on application startup."""
        try:
            LOG.info("Starting cron trigger service during application startup")
            await cron_service.start()
        except Exception as e:
            LOG.error("Failed to start cron trigger service", error=str(e))

    @app.on_event("shutdown")
    async def stop_cron_service():
        """Stop the cron trigger service on application shutdown."""
        try:
            LOG.info("Stopping cron trigger service during application shutdown")
            await cron_service.stop()
        except Exception as e:
            LOG.error("Failed to stop cron trigger service", error=str(e))
