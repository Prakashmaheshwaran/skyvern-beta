import asyncio
import os
import shutil
import subprocess
from pathlib import Path
from typing import List

import psutil
import typer
import uvicorn
from dotenv import load_dotenv, set_key
from mcp.server.fastmcp import FastMCP
from rich.panel import Panel
from rich.prompt import Confirm

from skyvern.cli.utils import start_services
from skyvern.config import settings
from skyvern.library.skyvern import Skyvern
from skyvern.services.cron_scheduler import start_scheduler
from skyvern.utils import detect_os

from .console import console

run_app = typer.Typer(help="Commands to run Skyvern services such as the API server or UI.")

mcp = FastMCP("Skyvern")


@mcp.tool()
async def skyvern_run_task(prompt: str, url: str) -> dict[str, str]:
    """Use Skyvern to execute anything in the browser. Useful for accomplishing tasks that require browser automation.

    This tool uses Skyvern's browser automation to navigate websites and perform actions to achieve
    the user's intended outcome. It can handle tasks like form filling, clicking buttons, data extraction,
    and multi-step workflows.

    It can even help you find updated data on the internet if your model information is outdated.

    Args:
        prompt: A natural language description of what needs to be accomplished (e.g. "Book a flight from
               NYC to LA", "Sign up for the newsletter", "Find the price of item X", "Apply to a job")
        url: The starting URL of the website where the task should be performed
    """
    skyvern_agent = Skyvern(
        base_url=settings.SKYVERN_BASE_URL,
        api_key=settings.SKYVERN_API_KEY,
    )
    res = await skyvern_agent.run_task(prompt=prompt, url=url, user_agent="skyvern-mcp", wait_for_completion=True)

    # TODO: It would be nice if we could return the task URL here
    output = res.model_dump()["output"]
    base_url = settings.SKYVERN_BASE_URL
    run_history_url = (
        "https://app.skyvern.com/history" if "skyvern.com" in base_url else "http://localhost:8080/history"
    )
    return {"output": output, "run_history_url": run_history_url}


def get_pids_on_port(port: int) -> List[int]:
    """Return a list of PIDs listening on the given port."""
    pids = []
    try:
        for conn in psutil.net_connections(kind="inet"):
            if conn.laddr and conn.laddr.port == port and conn.pid:
                pids.append(conn.pid)
    except Exception:
        pass
    return list(set(pids))


def kill_pids(pids: List[int]) -> None:
    """Kill the given list of PIDs in a cross-platform way."""
    host_system = detect_os()
    for pid in pids:
        try:
            if host_system in {"windows", "wsl"}:
                subprocess.run(f"taskkill /PID {pid} /F", shell=True, check=False)
            else:
                os.kill(pid, 9)
        except Exception:
            console.print(f"[red]Failed to kill process {pid}[/red]")


@run_app.command(name="server")
def run_server() -> None:
    """Run the Skyvern API server."""
    load_dotenv()
    load_dotenv(".env")
    from skyvern.config import settings

    port = settings.PORT
    console.print(Panel(f"[bold green]Starting Skyvern API Server on port {port}...", border_style="green"))
    uvicorn.run(
        "skyvern.forge.api_app:app",
        host="0.0.0.0",
        port=port,
        log_level="info",
    )


@run_app.command(name="ui")
def run_ui() -> None:
    """Run the Skyvern UI server."""
    console.print(Panel("[bold blue]Starting Skyvern UI Server...[/bold blue]", border_style="blue"))
    try:
        with console.status("[bold green]Checking for existing process on port 8080...") as status:
            pids = get_pids_on_port(8080)
            if pids:
                status.stop()
                response = Confirm.ask("Process already running on port 8080. [yellow]Kill it?[/yellow]")
                if response:
                    kill_pids(pids)
                    console.print("✅ [green]Process killed.[/green]")
                else:
                    console.print("[yellow]UI server not started. Process already running on port 8080.[/yellow]")
                    return
            status.stop()
    except Exception as e:  # pragma: no cover - CLI safeguards
        console.print(f"[red]Error checking for process: {e}[/red]")

    current_dir = Path(__file__).parent.parent.parent
    frontend_dir = current_dir / "skyvern-frontend"
    if not frontend_dir.exists():
        console.print(
            f"[bold red]ERROR: Skyvern Frontend directory not found at [path]{frontend_dir}[/path]. Are you in the right repo?[/bold red]"
        )
        return

    if not (frontend_dir / ".env").exists():
        console.print("[bold blue]Setting up frontend .env file...[/bold blue]")
        shutil.copy(frontend_dir / ".env.example", frontend_dir / ".env")
        main_env_path = current_dir / ".env"
        if main_env_path.exists():
            load_dotenv(main_env_path)
            skyvern_api_key = os.getenv("SKYVERN_API_KEY")
            if skyvern_api_key:
                frontend_env_path = frontend_dir / ".env"
                set_key(str(frontend_env_path), "VITE_SKYVERN_API_KEY", skyvern_api_key)
            else:
                console.print("[red]ERROR: SKYVERN_API_KEY not found in .env file[/red]")
        else:
            console.print("[red]ERROR: .env file not found[/red]")

        console.print("✅ [green]Successfully set up frontend .env file[/green]")

    os.chdir(frontend_dir)

    try:
        console.print("📦 [bold blue]Running npm install...[/bold blue]")
        subprocess.run("npm install --silent", shell=True, check=True)
        console.print("✅ [green]npm install complete.[/green]")
        console.print("🚀 [bold blue]Starting npm UI server...[/bold blue]")
        subprocess.run("npm run start", shell=True, check=True)
    except subprocess.CalledProcessError as e:
        console.print(f"[bold red]Error running UI server: {e}[/bold red]")
        return


@run_app.command(name="all")
def run_all() -> None:
    """Run the Skyvern API server and UI server in parallel."""
    asyncio.run(start_services())


@run_app.command(name="scheduler")
def run_scheduler() -> None:
    """Run the cron scheduler."""
    console.print(
        Panel(
            "[bold green]Starting Skyvern Cron Scheduler...[/bold green]",
            border_style="green",
        )
    )
    load_dotenv()
    load_dotenv(".env")
    asyncio.run(start_scheduler())


@run_app.command(name="mcp")
def run_mcp() -> None:
    """Run the MCP server."""
    console.print(Panel("[bold green]Starting MCP Server...[/bold green]", border_style="green"))
    mcp.run(transport="stdio")
