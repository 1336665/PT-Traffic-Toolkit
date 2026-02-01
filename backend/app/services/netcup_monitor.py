"""
Netcup Server Throttle Monitor Service

Monitors Netcup servers for bandwidth throttling using the SCP REST API
and automatically controls qBittorrent services when throttling is detected.
"""

import asyncio
import json
import paramiko
from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List

import httpx
from sqlalchemy import select, delete, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import async_session_maker
from app.models.models import (
    NetcupAccount, NetcupServer, NetcupRecord, NetcupConfig, NetcupThrottleStatus
)
from app.utils import get_logger
from app.services.notification import get_notifier

logger = get_logger('pt_manager.netcup_monitor')


class NetcupSCPClient:
    """Netcup SCP REST API Client using OAuth2 authentication"""

    BASE_URL = "https://www.servercontrolpanel.de/scp-core/api/v1"
    AUTH_URL = "https://www.servercontrolpanel.de/realms/scp/protocol/openid-connect/token"

    def __init__(self, loginname: str, password: str):
        self.loginname = loginname
        self.password = password
        self.access_token: Optional[str] = None
        self.refresh_token: Optional[str] = None
        self.token_expires_at: Optional[datetime] = None

    async def _authenticate(self, client: httpx.AsyncClient) -> bool:
        """Authenticate using OAuth2 Password Grant"""
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "password",
            "client_id": "scp",
            "username": self.loginname,
            "password": self.password,
            "scope": "openid offline_access"
        }

        try:
            response = await client.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token')
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data['expires_in']
            )
            logger.debug(f"Account {self.loginname} authenticated successfully")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Account {self.loginname} authentication failed: {e}")
            return False
        except Exception as e:
            logger.error(f"Account {self.loginname} authentication error: {e}")
            return False

    async def _refresh_token_if_needed(self, client: httpx.AsyncClient) -> bool:
        """Refresh access token if expired"""
        if self.token_expires_at and datetime.now(timezone.utc) < self.token_expires_at - timedelta(minutes=1):
            return True  # Token still valid

        if not self.refresh_token:
            return await self._authenticate(client)

        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "refresh_token",
            "client_id": "scp",
            "refresh_token": self.refresh_token
        }

        try:
            response = await client.post(self.AUTH_URL, headers=headers, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data['access_token']
            self.refresh_token = token_data.get('refresh_token', self.refresh_token)
            self.token_expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=token_data['expires_in']
            )
            logger.debug(f"Account {self.loginname} token refreshed")
            return True
        except Exception as e:
            logger.warning(f"Token refresh failed: {e}, re-authenticating...")
            return await self._authenticate(client)

    async def get_servers(self) -> Optional[List[dict]]:
        """Get all servers from the account"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            if not await self._refresh_token_if_needed(client):
                return None

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/hal+json"
            }

            try:
                response = await client.get(f"{self.BASE_URL}/servers", headers=headers)
                response.raise_for_status()
                return response.json()
            except Exception as e:
                logger.error(f"Failed to get servers: {e}")
                return None

    async def get_server_details(self, server_id: int) -> Optional[dict]:
        """Get server details including live traffic info"""
        async with httpx.AsyncClient(timeout=30.0) as client:
            if not await self._refresh_token_if_needed(client):
                return None

            headers = {
                "Authorization": f"Bearer {self.access_token}",
                "Accept": "application/hal+json"
            }
            params = {"loadServerLiveInfo": "true"}

            try:
                response = await client.get(
                    f"{self.BASE_URL}/servers/{server_id}",
                    headers=headers,
                    params=params
                )
                response.raise_for_status()
                data = response.json()
                # Log full response for debugging
                logger.info(f"SCP Server {server_id} response keys: {list(data.keys())}")
                server_live_info = data.get('serverLiveInfo', {})
                if server_live_info:
                    logger.info(f"SCP Server {server_id} serverLiveInfo keys: {list(server_live_info.keys())}")
                    if 'interfaces' in server_live_info:
                        ifaces = server_live_info.get('interfaces', [])
                        if ifaces:
                            logger.info(f"SCP Server {server_id} first interface: {ifaces[0]}")
                if 'serverStatus' in data:
                    logger.info(f"SCP Server {server_id} serverStatus: {data.get('serverStatus')}")
                elif 'disabled' in data:
                    logger.info(f"SCP Server {server_id} disabled: {data.get('disabled')}")
                return data
            except Exception as e:
                logger.error(f"Failed to get server details: {e}")
                return None


class SSHController:
    """SSH Controller for qBittorrent service control"""

    def __init__(self, host: str, port: int, username: str, password: str):
        self.host = host
        self.port = port
        self.username = username
        self.password = password

    def _execute_command(self, command: str) -> dict:
        """Execute SSH command"""
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(
                self.host,
                port=self.port,
                username=self.username,
                password=self.password,
                timeout=10
            )

            stdin, stdout, stderr = ssh.exec_command(command)
            exit_code = stdout.channel.recv_exit_status()
            output = stdout.read().decode('utf-8').strip()
            error = stderr.read().decode('utf-8').strip()

            ssh.close()

            return {
                'success': exit_code == 0,
                'exit_code': exit_code,
                'output': output,
                'error': error
            }
        except Exception as e:
            logger.error(f"SSH connection failed {self.host}:{self.port} - {e}")
            return {
                'success': False,
                'exit_code': -1,
                'output': '',
                'error': str(e)
            }

    def stop_service(self, control_type: str, target: str) -> dict:
        """Stop qBittorrent service"""
        if control_type == "docker":
            command = f"docker stop {target}"
        else:  # systemd
            command = f"sudo systemctl stop {target}"
        return self._execute_command(command)

    def start_service(self, control_type: str, target: str) -> dict:
        """Start qBittorrent service"""
        if control_type == "docker":
            command = f"docker start {target}"
        else:  # systemd
            command = f"sudo systemctl start {target}"
        return self._execute_command(command)

    def get_service_status(self, control_type: str, target: str) -> dict:
        """Get service running status"""
        if control_type == "docker":
            command = f"docker ps --filter name={target} --format '{{{{.Status}}}}'"
        else:  # systemd
            command = f"systemctl is-active {target}"

        result = self._execute_command(command)

        if control_type == "systemd":
            running = result['success'] and result['output'] == 'active'
        else:
            running = result['success'] and 'Up' in result['output']

        return {'success': True, 'running': running}


class NetcupMonitorService:
    """Service for monitoring Netcup server throttling status"""

    def __init__(self):
        self._running = False
        self._clients: Dict[int, NetcupSCPClient] = {}  # account_id -> client
        self._status_cache: Dict[int, Dict[str, Any]] = {}

    async def get_config(self) -> Optional[NetcupConfig]:
        """Get global Netcup monitor configuration"""
        async with async_session_maker() as session:
            result = await session.execute(select(NetcupConfig).limit(1))
            config = result.scalar_one_or_none()
            if not config:
                config = NetcupConfig(enabled=False)
                session.add(config)
                await session.commit()
                await session.refresh(config)
            return config

    async def update_config(self, **kwargs) -> NetcupConfig:
        """Update global configuration"""
        async with async_session_maker() as session:
            result = await session.execute(select(NetcupConfig).limit(1))
            config = result.scalar_one_or_none()
            if not config:
                config = NetcupConfig(**kwargs)
                session.add(config)
            else:
                for key, value in kwargs.items():
                    if hasattr(config, key):
                        setattr(config, key, value)
            await session.commit()
            await session.refresh(config)
            return config

    # Account management
    async def get_accounts(self) -> List[NetcupAccount]:
        """Get all configured accounts"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupAccount).order_by(NetcupAccount.id)
            )
            return result.scalars().all()

    async def get_account(self, account_id: int) -> Optional[NetcupAccount]:
        """Get a specific account by ID"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupAccount).where(NetcupAccount.id == account_id)
            )
            return result.scalar_one_or_none()

    async def create_account(self, **kwargs) -> NetcupAccount:
        """Create a new account"""
        async with async_session_maker() as session:
            account = NetcupAccount(**kwargs)
            session.add(account)
            await session.commit()
            await session.refresh(account)
            logger.info(f"Created Netcup account: {account.name}")
            return account

    async def update_account(self, account_id: int, **kwargs) -> Optional[NetcupAccount]:
        """Update account configuration"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupAccount).where(NetcupAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            if account:
                for key, value in kwargs.items():
                    if hasattr(account, key):
                        setattr(account, key, value)
                await session.commit()
                await session.refresh(account)
                # Clear cached client
                self._clients.pop(account_id, None)
                logger.info(f"Updated Netcup account: {account.name}")
            return account

    async def delete_account(self, account_id: int) -> bool:
        """Delete an account and its servers"""
        async with async_session_maker() as session:
            # Delete related servers first
            servers = await session.execute(
                select(NetcupServer).where(NetcupServer.account_id == account_id)
            )
            for server in servers.scalars().all():
                await session.execute(
                    delete(NetcupRecord).where(NetcupRecord.server_id == server.id)
                )
                await session.delete(server)

            # Delete account
            result = await session.execute(
                select(NetcupAccount).where(NetcupAccount.id == account_id)
            )
            account = result.scalar_one_or_none()
            if account:
                await session.delete(account)
                await session.commit()
                self._clients.pop(account_id, None)
                logger.info(f"Deleted Netcup account: {account.name}")
                return True
            return False

    async def test_account(self, account_id: int) -> Dict[str, Any]:
        """Test account API connection"""
        account = await self.get_account(account_id)
        if not account:
            return {"success": False, "error": "Account not found"}

        client = NetcupSCPClient(account.loginname, account.password)
        servers = await client.get_servers()

        if servers is not None:
            return {
                "success": True,
                "message": f"Connected successfully, found {len(servers) if isinstance(servers, list) else 0} servers"
            }
        else:
            return {"success": False, "error": "Failed to connect to Netcup SCP API"}

    # Server management
    async def get_servers(self) -> List[NetcupServer]:
        """Get all configured servers"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupServer).order_by(NetcupServer.id)
            )
            return result.scalars().all()

    async def get_server(self, server_id: int) -> Optional[NetcupServer]:
        """Get a specific server by ID"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupServer).where(NetcupServer.id == server_id)
            )
            return result.scalar_one_or_none()

    async def create_server(self, **kwargs) -> NetcupServer:
        """Create a new server configuration"""
        async with async_session_maker() as session:
            server = NetcupServer(**kwargs)
            session.add(server)
            await session.commit()
            await session.refresh(server)
            logger.info(f"Created Netcup server: {server.name}")
            return server

    async def update_server(self, server_id: int, **kwargs) -> Optional[NetcupServer]:
        """Update server configuration"""
        async with async_session_maker() as session:
            result = await session.execute(
                select(NetcupServer).where(NetcupServer.id == server_id)
            )
            server = result.scalar_one_or_none()
            if server:
                for key, value in kwargs.items():
                    if hasattr(server, key):
                        setattr(server, key, value)
                await session.commit()
                await session.refresh(server)
                logger.info(f"Updated Netcup server: {server.name}")
            return server

    async def delete_server(self, server_id: int) -> bool:
        """Delete a server configuration"""
        async with async_session_maker() as session:
            await session.execute(
                delete(NetcupRecord).where(NetcupRecord.server_id == server_id)
            )
            result = await session.execute(
                select(NetcupServer).where(NetcupServer.id == server_id)
            )
            server = result.scalar_one_or_none()
            if server:
                await session.delete(server)
                await session.commit()
                logger.info(f"Deleted Netcup server: {server.name}")
                return True
            return False

    def _get_client(self, account: NetcupAccount) -> NetcupSCPClient:
        """Get or create SCP client for account"""
        if account.id not in self._clients:
            self._clients[account.id] = NetcupSCPClient(account.loginname, account.password)
        return self._clients[account.id]

    async def _check_server_status_from_api(
        self, server: NetcupServer, account: NetcupAccount
    ) -> Dict[str, Any]:
        """Check server throttle status from SCP API"""
        client = self._get_client(account)

        if not server.server_id_scp:
            # Need to find server by IP
            servers_data = await client.get_servers()
            if not servers_data:
                return {"error": "Failed to get servers from API"}

            # Find server by IP
            for srv in servers_data if isinstance(servers_data, list) else []:
                details = await client.get_server_details(srv.get('id'))
                if details:
                    interfaces = details.get('interfaces', [])
                    for iface in interfaces:
                        addrs = iface.get('ipv4Addresses', [])
                        for addr in addrs:
                            if isinstance(addr, dict) and addr.get('ip') == server.ip_address:
                                # Found matching server
                                return await self._parse_server_details(details)
                            elif addr == server.ip_address:
                                return await self._parse_server_details(details)

            return {"error": f"Server with IP {server.ip_address} not found"}
        else:
            details = await client.get_server_details(server.server_id_scp)
            if details:
                return await self._parse_server_details(details)
            return {"error": "Failed to get server details"}

    async def _parse_server_details(self, details: dict) -> Dict[str, Any]:
        """Parse server details from API response"""
        # Try to get server status from multiple locations
        # Note: API returns 'state' in serverLiveInfo (e.g., 'running', 'stopped')
        server_live_info = details.get('serverLiveInfo', {}) or {}
        state = server_live_info.get('state', '').upper()
        status = (
            details.get('serverStatus') or
            state or
            ('STOPPED' if details.get('disabled') else None) or
            'UNKNOWN'
        )

        result = {
            "server_id": details.get('id'),
            "name": details.get('name'),
            "status": status,
            "traffic_throttled": False,
            "monthly_rx_gib": 0,
            "monthly_tx_gib": 0,
            "interface_speed_mbits": 0
        }

        # Check interfaces from serverLiveInfo if not at top level
        interfaces = details.get('interfaces', []) or server_live_info.get('interfaces', [])
        if interfaces:
            main_interface = interfaces[0]
            result["traffic_throttled"] = main_interface.get('trafficThrottled', False)
            result["monthly_rx_gib"] = main_interface.get('rxMonthlyInMiB', 0) / 1024
            result["monthly_tx_gib"] = main_interface.get('txMonthlyInMiB', 0) / 1024
            result["interface_speed_mbits"] = main_interface.get('speedInMBits', 0)

        return result

    async def _control_qbittorrent(self, server: NetcupServer, action: str) -> bool:
        """Control qBittorrent service on the server

        If downloader_id is set, use the downloader API to pause/resume.
        Otherwise, use SSH to stop/start the service.
        """
        if server.whitelist:
            logger.info(f"Server {server.name} is whitelisted, skipping control")
            return True

        # If downloader is linked, use API control
        if server.downloader_id:
            return await self._control_via_downloader(server, action)

        # Otherwise use SSH control
        try:
            controller = SSHController(
                server.ip_address,
                server.ssh_port,
                server.ssh_username,
                server.ssh_password
            )

            target = server.qb_docker_container if server.qb_control_type == "docker" else server.qb_systemd_service

            if action == "stop":
                result = controller.stop_service(server.qb_control_type, target)
            else:
                result = controller.start_service(server.qb_control_type, target)

            if result['success']:
                logger.info(f"qBittorrent {action} on {server.name}: success")
            else:
                logger.error(f"qBittorrent {action} on {server.name} failed: {result['error']}")

            return result['success']
        except Exception as e:
            logger.error(f"Failed to {action} qBittorrent on {server.name}: {e}")
            return False

    async def _control_via_downloader(self, server: NetcupServer, action: str) -> bool:
        """Control qBittorrent via downloader API (pause/resume all torrents)

        This uses pause/resume instead of speed limits to avoid conflicts with
        the dynamic speed limiter. When torrents are paused, they won't transfer
        at all, so the dynamic speed limiter won't interfere.
        """
        from app.models import Downloader
        from app.services.downloader import create_downloader

        try:
            async with async_session_maker() as session:
                result = await session.execute(
                    select(Downloader).where(Downloader.id == server.downloader_id)
                )
                downloader = result.scalar_one_or_none()

                if not downloader:
                    logger.error(f"Downloader {server.downloader_id} not found for server {server.name}")
                    return False

                client = create_downloader(downloader)
                if not client:
                    logger.error(f"Failed to get client for downloader {downloader.name}")
                    return False

                await client.connect()

                if action == "stop":
                    # Pause all torrents to stop traffic completely
                    await client.pause_all_torrents()
                    logger.info(f"Paused all torrents on {downloader.name} for server {server.name} (throttled)")
                else:
                    # Resume all torrents
                    await client.resume_all_torrents()
                    logger.info(f"Resumed all torrents on {downloader.name} for server {server.name} (normal)")

                return True
        except Exception as e:
            logger.error(f"Failed to control downloader for {server.name}: {e}")
            return False

    async def run_check(self) -> Dict[int, Dict[str, Any]]:
        """Run throttle check for all enabled servers"""
        config = await self.get_config()
        if not config or not config.enabled:
            return {}

        accounts = await self.get_accounts()
        servers = await self.get_servers()
        results = {}

        # Group servers by account
        account_map = {acc.id: acc for acc in accounts}

        for server in servers:
            if not server.enabled or not server.account_id:
                continue

            account = account_map.get(server.account_id)
            if not account or not account.enabled:
                continue

            # Get status from API
            api_result = await self._check_server_status_from_api(server, account)

            if "error" in api_result:
                logger.error(f"Error checking {server.name}: {api_result['error']}")
                continue

            old_status = server.current_status
            new_status = (
                NetcupThrottleStatus.THROTTLED
                if api_result.get('traffic_throttled')
                else NetcupThrottleStatus.NORMAL
            )

            now = datetime.utcnow()
            today = now.strftime("%Y-%m-%d")

            async with async_session_maker() as session:
                result = await session.execute(
                    select(NetcupServer).where(NetcupServer.id == server.id)
                )
                db_server = result.scalar_one_or_none()
                if not db_server:
                    continue

                # Update server ID from SCP if not set
                if api_result.get('server_id') and not db_server.server_id_scp:
                    db_server.server_id_scp = api_result['server_id']

                # Reset daily stats if new day
                if db_server.stats_date != today:
                    db_server.stats_date = today
                    db_server.today_normal_seconds = 0
                    db_server.today_throttled_seconds = 0

                # Calculate duration since last check
                duration = 0
                if db_server.last_check:
                    duration = int((now - db_server.last_check).total_seconds())

                # Update daily stats
                if old_status == NetcupThrottleStatus.NORMAL:
                    db_server.today_normal_seconds += duration
                elif old_status == NetcupThrottleStatus.THROTTLED:
                    db_server.today_throttled_seconds += duration

                # Update traffic stats
                db_server.monthly_rx_gib = api_result.get('monthly_rx_gib', 0)
                db_server.monthly_tx_gib = api_result.get('monthly_tx_gib', 0)
                db_server.interface_speed_mbits = api_result.get('interface_speed_mbits', 0)
                db_server.server_status = api_result.get('status', 'UNKNOWN')

                # Status changed
                if new_status != old_status:
                    db_server.status_since = now

                    if new_status == NetcupThrottleStatus.THROTTLED:
                        db_server.throttle_start_time = now
                        db_server.throttle_end_time = None
                    elif new_status == NetcupThrottleStatus.NORMAL and old_status == NetcupThrottleStatus.THROTTLED:
                        db_server.throttle_end_time = now
                        if db_server.throttle_start_time:
                            db_server.throttle_duration = int(
                                (now - db_server.throttle_start_time).total_seconds()
                            )

                    # Auto control qBittorrent
                    if config.auto_control_enabled and not db_server.whitelist:
                        if new_status == NetcupThrottleStatus.THROTTLED:
                            await self._control_qbittorrent(db_server, "stop")
                        elif new_status == NetcupThrottleStatus.NORMAL:
                            await self._control_qbittorrent(db_server, "start")

                    # Send notification
                    if config.telegram_enabled:
                        await self._send_notification(db_server, old_status, new_status)

                db_server.current_status = new_status
                db_server.last_check = now

                # Create record
                record = NetcupRecord(
                    server_id=db_server.id,
                    status=new_status,
                    duration_seconds=duration
                )
                session.add(record)
                await session.commit()

                # Build result
                status_duration = 0
                if db_server.status_since:
                    status_duration = int((now - db_server.status_since).total_seconds())

                results[server.id] = {
                    "id": server.id,
                    "name": server.name,
                    "status": new_status.value,
                    "status_changed": new_status != old_status,
                    "status_duration": status_duration,
                    "traffic_throttled": api_result.get('traffic_throttled', False),
                    "monthly_rx_gib": api_result.get('monthly_rx_gib', 0),
                    "monthly_tx_gib": api_result.get('monthly_tx_gib', 0),
                    "interface_speed_mbits": api_result.get('interface_speed_mbits', 0),
                    "today_normal": db_server.today_normal_seconds,
                    "today_throttled": db_server.today_throttled_seconds,
                    "last_check": now.isoformat()
                }

        self._status_cache = results
        return results

    async def _send_notification(
        self,
        server: NetcupServer,
        old_status: NetcupThrottleStatus,
        new_status: NetcupThrottleStatus
    ):
        """Send notification about status change"""
        if new_status == NetcupThrottleStatus.THROTTLED:
            message = f"⚠️ Netcup 限速警告\n\n服务器: {server.name}\n状态: 已被限速\nIP: {server.ip_address}"
        elif new_status == NetcupThrottleStatus.NORMAL:
            duration_str = ""
            if server.throttle_duration:
                hours = server.throttle_duration // 3600
                minutes = (server.throttle_duration % 3600) // 60
                duration_str = f"\n限速时长: {hours}小时{minutes}分钟"
            message = f"✅ Netcup 限速解除\n\n服务器: {server.name}\n状态: 恢复正常\nIP: {server.ip_address}{duration_str}"
        else:
            message = f"❓ Netcup 状态未知\n\n服务器: {server.name}\nIP: {server.ip_address}"

        try:
            notifier = get_notifier()
            await notifier.send_message(message)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")

    async def get_server_status(self, server_id: int) -> Optional[Dict[str, Any]]:
        """Get current status for a server"""
        if server_id in self._status_cache:
            return self._status_cache[server_id]

        server = await self.get_server(server_id)
        if not server:
            return None

        now = datetime.utcnow()
        status_duration = 0
        if server.status_since:
            status_duration = int((now - server.status_since).total_seconds())

        return {
            "id": server.id,
            "name": server.name,
            "status": server.current_status.value if server.current_status else "unknown",
            "status_duration": status_duration,
            "monthly_rx_gib": server.monthly_rx_gib,
            "monthly_tx_gib": server.monthly_tx_gib,
            "interface_speed_mbits": server.interface_speed_mbits,
            "today_normal": server.today_normal_seconds,
            "today_throttled": server.today_throttled_seconds,
            "last_check": server.last_check.isoformat() if server.last_check else None
        }

    async def get_all_status(self) -> List[Dict[str, Any]]:
        """Get status for all servers"""
        servers = await self.get_servers()
        result = []

        for server in servers:
            status = await self.get_server_status(server.id)
            if status:
                result.append(status)

        return result

    async def get_records(
        self,
        server_id: Optional[int] = None,
        limit: int = 100,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """Get throttle records"""
        async with async_session_maker() as session:
            query = select(NetcupRecord)

            if server_id:
                query = query.where(NetcupRecord.server_id == server_id)

            since = datetime.utcnow() - timedelta(hours=hours)
            query = query.where(NetcupRecord.created_at >= since)
            query = query.order_by(NetcupRecord.created_at.desc()).limit(limit)

            result = await session.execute(query)
            records = result.scalars().all()

            return [
                {
                    "id": r.id,
                    "server_id": r.server_id,
                    "status": r.status.value if r.status else "unknown",
                    "duration_seconds": r.duration_seconds,
                    "created_at": r.created_at.isoformat()
                }
                for r in records
            ]

    async def get_statistics(self, server_id: Optional[int] = None) -> Dict[str, Any]:
        """Get statistics summary"""
        servers = await self.get_servers()
        if server_id:
            servers = [s for s in servers if s.id == server_id]

        total_normal = 0
        total_throttled = 0

        for server in servers:
            total_normal += server.today_normal_seconds
            total_throttled += server.today_throttled_seconds

        # Count today's throttle events
        async with async_session_maker() as session:
            today = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
            query = select(func.count(NetcupRecord.id)).where(
                and_(
                    NetcupRecord.created_at >= today,
                    NetcupRecord.status == NetcupThrottleStatus.THROTTLED
                )
            )
            if server_id:
                query = query.where(NetcupRecord.server_id == server_id)

            result = await session.execute(query)
            throttle_count = result.scalar() or 0

        total = total_normal + total_throttled
        throttle_ratio = total_throttled / total if total > 0 else 0

        return {
            "total_normal_seconds": total_normal,
            "total_throttled_seconds": total_throttled,
            "throttle_ratio": throttle_ratio,
            "throttle_count": throttle_count,
            "server_count": len(servers)
        }

    async def test_server_connection(self, server_id: int) -> Dict[str, Any]:
        """Test connection to a server - tests downloader if linked, otherwise skips SSH"""
        from app.models import Downloader
        from app.services.downloader import create_downloader

        server = await self.get_server(server_id)
        if not server:
            return {"success": False, "error": "Server not found"}

        # If downloader is linked, test downloader connection
        if server.downloader_id:
            try:
                async with async_session_maker() as session:
                    result = await session.execute(
                        select(Downloader).where(Downloader.id == server.downloader_id)
                    )
                    downloader = result.scalar_one_or_none()

                    if not downloader:
                        return {"success": False, "error": f"Downloader {server.downloader_id} not found"}

                    client = create_downloader(downloader)
                    await client.connect()
                    # Try to get stats to verify connection works
                    stats = await client.get_stats()
                    return {
                        "success": True,
                        "message": f"Downloader connection successful ({downloader.name})",
                        "stats": {
                            "download_speed": stats.download_speed if stats else 0,
                            "upload_speed": stats.upload_speed if stats else 0
                        }
                    }
            except Exception as e:
                return {"success": False, "error": f"Downloader connection failed: {str(e)}"}
        else:
            # No downloader linked, SSH not required for API-only monitoring
            return {
                "success": True,
                "message": "No downloader linked. Server will be monitored via SCP API only."
            }


# Global service instance
netcup_monitor_service = NetcupMonitorService()
