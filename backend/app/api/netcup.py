"""
Netcup Monitor API endpoints

Provides endpoints for managing Netcup SCP accounts, servers, and monitoring throttle status.
"""

from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from app.api.auth import get_current_user
from app.services.netcup_monitor import netcup_monitor_service

router = APIRouter(prefix="/netcup", tags=["Netcup Monitor"])


# ============ Pydantic Models ============

class NetcupConfigUpdate(BaseModel):
    enabled: Optional[bool] = None
    check_interval: Optional[int] = None
    retry_interval: Optional[int] = None
    auto_control_enabled: Optional[bool] = None
    telegram_enabled: Optional[bool] = None


class NetcupAccountCreate(BaseModel):
    name: str
    loginname: str
    password: str
    enabled: bool = True


class NetcupAccountUpdate(BaseModel):
    name: Optional[str] = None
    loginname: Optional[str] = None
    password: Optional[str] = None
    enabled: Optional[bool] = None


class NetcupServerCreate(BaseModel):
    name: str
    account_id: int
    server_id_scp: Optional[int] = None
    ip_address: str
    ssh_port: int = 22
    ssh_username: str = "root"
    ssh_password: str = ""
    ssh_key_path: str = ""
    qb_control_type: str = "systemd"
    qb_docker_container: str = ""
    qb_systemd_service: str = "qbittorrent-nox"
    downloader_id: Optional[int] = None
    whitelist: bool = False
    enabled: bool = True


class NetcupServerUpdate(BaseModel):
    name: Optional[str] = None
    account_id: Optional[int] = None
    server_id_scp: Optional[int] = None
    ip_address: Optional[str] = None
    ssh_port: Optional[int] = None
    ssh_username: Optional[str] = None
    ssh_password: Optional[str] = None
    ssh_key_path: Optional[str] = None
    qb_control_type: Optional[str] = None
    qb_docker_container: Optional[str] = None
    qb_systemd_service: Optional[str] = None
    downloader_id: Optional[int] = None
    whitelist: Optional[bool] = None
    enabled: Optional[bool] = None


# ============ Config Endpoints ============

@router.get("/config")
async def get_config(user=Depends(get_current_user)):
    """Get Netcup monitor configuration"""
    config = await netcup_monitor_service.get_config()
    return {
        "enabled": config.enabled,
        "check_interval": config.check_interval,
        "retry_interval": config.retry_interval,
        "auto_control_enabled": config.auto_control_enabled,
        "telegram_enabled": config.telegram_enabled
    }


@router.put("/config")
async def update_config(data: NetcupConfigUpdate, user=Depends(get_current_user)):
    """Update Netcup monitor configuration"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    config = await netcup_monitor_service.update_config(**update_data)
    return {
        "enabled": config.enabled,
        "check_interval": config.check_interval,
        "retry_interval": config.retry_interval,
        "auto_control_enabled": config.auto_control_enabled,
        "telegram_enabled": config.telegram_enabled
    }


# ============ Account Endpoints ============

@router.get("/accounts")
async def get_accounts(user=Depends(get_current_user)):
    """Get all Netcup SCP accounts"""
    accounts = await netcup_monitor_service.get_accounts()
    return [
        {
            "id": a.id,
            "name": a.name,
            "loginname": a.loginname,
            "enabled": a.enabled,
            "created_at": a.created_at.isoformat() if a.created_at else None,
            "updated_at": a.updated_at.isoformat() if a.updated_at else None
        }
        for a in accounts
    ]


@router.get("/accounts/{account_id}")
async def get_account(account_id: int, user=Depends(get_current_user)):
    """Get a specific account"""
    account = await netcup_monitor_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "id": account.id,
        "name": account.name,
        "loginname": account.loginname,
        "password": account.password,
        "enabled": account.enabled,
        "created_at": account.created_at.isoformat() if account.created_at else None,
        "updated_at": account.updated_at.isoformat() if account.updated_at else None
    }


@router.post("/accounts")
async def create_account(data: NetcupAccountCreate, user=Depends(get_current_user)):
    """Create a new Netcup SCP account"""
    account = await netcup_monitor_service.create_account(**data.model_dump())
    return {"id": account.id, "message": "Account created successfully"}


@router.put("/accounts/{account_id}")
async def update_account(account_id: int, data: NetcupAccountUpdate, user=Depends(get_current_user)):
    """Update a Netcup SCP account"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    account = await netcup_monitor_service.update_account(account_id, **update_data)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account updated successfully"}


@router.delete("/accounts/{account_id}")
async def delete_account(account_id: int, user=Depends(get_current_user)):
    """Delete a Netcup SCP account and its servers"""
    success = await netcup_monitor_service.delete_account(account_id)
    if not success:
        raise HTTPException(status_code=404, detail="Account not found")
    return {"message": "Account deleted successfully"}


@router.post("/accounts/{account_id}/test")
async def test_account(account_id: int, user=Depends(get_current_user)):
    """Test SCP API connection for an account"""
    result = await netcup_monitor_service.test_account(account_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


@router.get("/accounts/{account_id}/servers")
async def get_account_servers(account_id: int, user=Depends(get_current_user)):
    """Get servers available from Netcup SCP API for an account"""
    from app.services.netcup_monitor import NetcupSCPClient
    from app.utils import get_logger
    logger = get_logger('pt_manager.netcup')

    account = await netcup_monitor_service.get_account(account_id)
    if not account:
        raise HTTPException(status_code=404, detail="Account not found")

    client = NetcupSCPClient(account.loginname, account.password)
    servers = await client.get_servers()

    if servers is None:
        raise HTTPException(status_code=400, detail="Failed to get servers from SCP API")

    # Get details for each server
    result = []
    for srv in servers if isinstance(servers, list) else []:
        server_id = srv.get('id')
        if server_id:
            details = await client.get_server_details(server_id)
            if details:
                server_live_info = details.get('serverLiveInfo', {}) or {}

                # Get interfaces from serverLiveInfo (that's where traffic data is)
                interfaces = server_live_info.get('interfaces', [])
                main_interface = interfaces[0] if interfaces else {}

                # Get first IPv4 address - check multiple locations
                ip_address = ""
                # First try top-level ipv4Addresses
                top_level_ips = details.get('ipv4Addresses', [])
                if top_level_ips:
                    ip_address = top_level_ips[0] if isinstance(top_level_ips[0], str) else top_level_ips[0].get('ip', '')
                # Then try interfaces in serverLiveInfo
                if not ip_address and interfaces:
                    for iface in interfaces:
                        addrs = iface.get('ipv4Addresses', [])
                        if addrs:
                            addr = addrs[0]
                            ip_address = addr if isinstance(addr, str) else addr.get('ip', '')
                            break

                # Get server status
                # Note: API returns 'serverLiveInfo' with 'state' field (e.g., 'running', 'stopped')
                state = (server_live_info.get('state') or '').upper()
                server_status = (
                    details.get('serverStatus') or
                    state or
                    ('STOPPED' if details.get('disabled') else None) or
                    srv.get('status') or
                    srv.get('serverStatus') or
                    'UNKNOWN'
                )

                logger.info(f"Server {server_id}: status={server_status}, ip={ip_address}")

                result.append({
                    "id": server_id,
                    "name": details.get('name', srv.get('name', '')),
                    "status": server_status,
                    "ip_address": ip_address,
                    "traffic_throttled": main_interface.get('trafficThrottled', False),
                    "monthly_rx_gib": main_interface.get('rxMonthlyInMiB', 0) / 1024,
                    "monthly_tx_gib": main_interface.get('txMonthlyInMiB', 0) / 1024,
                    "speed_mbits": main_interface.get('speedInMBits', 0)
                })

    return result


# ============ Server Endpoints ============

@router.get("/servers")
async def get_servers(user=Depends(get_current_user)):
    """Get all Netcup servers"""
    servers = await netcup_monitor_service.get_servers()
    return [
        {
            "id": s.id,
            "name": s.name,
            "enabled": s.enabled,
            "account_id": s.account_id,
            "server_id_scp": s.server_id_scp,
            "ip_address": s.ip_address,
            "ssh_port": s.ssh_port,
            "ssh_username": s.ssh_username,
            "qb_control_type": s.qb_control_type,
            "qb_docker_container": s.qb_docker_container,
            "qb_systemd_service": s.qb_systemd_service,
            "downloader_id": s.downloader_id,
            "whitelist": s.whitelist,
            "current_status": s.current_status.value if s.current_status else "unknown",
            "status_since": s.status_since.isoformat() if s.status_since else None,
            "last_check": s.last_check.isoformat() if s.last_check else None,
            "server_status": s.server_status,
            "monthly_rx_gib": s.monthly_rx_gib,
            "monthly_tx_gib": s.monthly_tx_gib,
            "interface_speed_mbits": s.interface_speed_mbits,
            "today_normal_seconds": s.today_normal_seconds,
            "today_throttled_seconds": s.today_throttled_seconds,
            "today_upload": s.today_upload,
            "today_download": s.today_download
        }
        for s in servers
    ]


@router.get("/servers/{server_id}")
async def get_server(server_id: int, user=Depends(get_current_user)):
    """Get a specific server"""
    server = await netcup_monitor_service.get_server(server_id)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")

    return {
        "id": server.id,
        "name": server.name,
        "enabled": server.enabled,
        "account_id": server.account_id,
        "server_id_scp": server.server_id_scp,
        "ip_address": server.ip_address,
        "ssh_port": server.ssh_port,
        "ssh_username": server.ssh_username,
        "ssh_password": server.ssh_password,
        "ssh_key_path": server.ssh_key_path,
        "qb_control_type": server.qb_control_type,
        "qb_docker_container": server.qb_docker_container,
        "qb_systemd_service": server.qb_systemd_service,
        "downloader_id": server.downloader_id,
        "whitelist": server.whitelist,
        "current_status": server.current_status.value if server.current_status else "unknown",
        "status_since": server.status_since.isoformat() if server.status_since else None,
        "last_check": server.last_check.isoformat() if server.last_check else None,
        "server_status": server.server_status,
        "monthly_rx_gib": server.monthly_rx_gib,
        "monthly_tx_gib": server.monthly_tx_gib,
        "interface_speed_mbits": server.interface_speed_mbits,
        "today_normal_seconds": server.today_normal_seconds,
        "today_throttled_seconds": server.today_throttled_seconds
    }


@router.post("/servers")
async def create_server(data: NetcupServerCreate, user=Depends(get_current_user)):
    """Create a new Netcup server"""
    server = await netcup_monitor_service.create_server(**data.model_dump())
    return {"id": server.id, "message": "Server created successfully"}


@router.put("/servers/{server_id}")
async def update_server(server_id: int, data: NetcupServerUpdate, user=Depends(get_current_user)):
    """Update a Netcup server"""
    update_data = {k: v for k, v in data.model_dump().items() if v is not None}
    server = await netcup_monitor_service.update_server(server_id, **update_data)
    if not server:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"message": "Server updated successfully"}


@router.delete("/servers/{server_id}")
async def delete_server(server_id: int, user=Depends(get_current_user)):
    """Delete a Netcup server"""
    success = await netcup_monitor_service.delete_server(server_id)
    if not success:
        raise HTTPException(status_code=404, detail="Server not found")
    return {"message": "Server deleted successfully"}


@router.post("/servers/{server_id}/test")
async def test_server(server_id: int, user=Depends(get_current_user)):
    """Test SSH connection to a server"""
    result = await netcup_monitor_service.test_server_connection(server_id)
    if not result["success"]:
        raise HTTPException(status_code=400, detail=result["error"])
    return result


# ============ Status Endpoints ============

@router.get("/status")
async def get_all_status(user=Depends(get_current_user)):
    """Get status of all servers"""
    return await netcup_monitor_service.get_all_status()


@router.get("/status/{server_id}")
async def get_server_status(server_id: int, user=Depends(get_current_user)):
    """Get status of a specific server"""
    status = await netcup_monitor_service.get_server_status(server_id)
    if not status:
        raise HTTPException(status_code=404, detail="Server not found")
    return status


@router.post("/check")
async def run_check(user=Depends(get_current_user)):
    """Manually trigger a throttle check for all servers"""
    results = await netcup_monitor_service.run_check()
    return {"message": "Check completed", "results": results}


# ============ Records Endpoints ============

@router.get("/records")
async def get_records(
    server_id: Optional[int] = None,
    limit: int = 100,
    hours: int = 24,
    user=Depends(get_current_user)
):
    """Get throttle records"""
    return await netcup_monitor_service.get_records(
        server_id=server_id,
        limit=limit,
        hours=hours
    )


@router.get("/statistics")
async def get_statistics(
    server_id: Optional[int] = None,
    user=Depends(get_current_user)
):
    """Get throttle statistics"""
    return await netcup_monitor_service.get_statistics(server_id)
