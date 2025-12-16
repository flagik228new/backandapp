from sqlalchemy import select, update
from models import async_session, User, ServersVPN, VPNKey, VPNSubscription
from outline_api import OutlineAPI
from typing import List
from datetime import datetime, timedelta


# --- Пользователи ---
async def add_user(tg_id: int, user_role: str):
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if user:
            return user

        new_user = User(tg_id=tg_id, userRole=user_role)
        session.add(new_user)
        await session.commit()
        await session.refresh(new_user)
        return new_user


# --- Серверы VPN ---
async def get_servers() -> List[dict]:
    async with async_session() as session:
        servers = await session.scalars(select(ServersVPN).where(ServersVPN.is_active == True))
        return [
            {
                "idServerVPN": s.idServerVPN,
                "nameVPN": s.nameVPN,
                "price": s.price,
                "max_conn": s.max_conn,
                "now_conn": s.now_conn,
                "server_ip": s.server_ip,
                "api_url": s.api_url
            } for s in servers
        ]


# --- Покупка VPN ---
async def buy_vpn(tg_id: int, server_id: int, outline_api_url: str) -> dict:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            raise Exception("Пользователь не найден")

        server = await session.scalar(select(ServersVPN).where(ServersVPN.idServerVPN == server_id))
        if not server or not server.is_active:
            raise Exception("Сервер не найден или неактивен")

        # Создаём ключ через Outline API
        outline_api = OutlineAPI(api_url=outline_api_url)
        key_data = outline_api.create_key(name=f"User {tg_id}")

        expires_at = datetime.utcnow() + timedelta(days=30)

        # VPNKey
        vpn_key = VPNKey(
            idUser=user.idUser,
            idServerVPN=server.idServerVPN,
            provider="outline",
            provider_key_id=key_data["accessKey"]["id"],
            access_data=key_data["accessUrl"],
            expires_at=expires_at,
            is_active=True
        )
        session.add(vpn_key)
        await session.commit()
        await session.refresh(vpn_key)

        # VPNSubscription
        subscription = VPNSubscription(
            idUser=user.idUser,
            vpn_key_id=vpn_key.id,
            started_at=datetime.utcnow(),
            expires_at=expires_at,
            status="active"
        )
        session.add(subscription)
        await session.commit()
        await session.refresh(subscription)

        return {"vpn_key": vpn_key.access_data, "expires_at": vpn_key.expires_at.isoformat()}


# --- Список VPN пользователя ---
async def get_my_vpns(tg_id: int) -> List[dict]:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            return []

        subscriptions = await session.scalars(
            select(VPNSubscription, VPNKey)
            .join(VPNKey, VPNSubscription.vpn_key_id == VPNKey.id)
            .where(VPNSubscription.idUser == user.idUser)
        )

        result = []
        for sub, key in subscriptions:
            result.append({
                "server_id": key.idServerVPN,
                "access_data": key.access_data,
                "expires_at": key.expires_at.isoformat(),
                "is_active": key.is_active
            })
        return result


# --- Продление VPN ---
async def renew_vpn(tg_id: int, vpn_key_id: int, months: int = 1) -> dict:
    async with async_session() as session:
        user = await session.scalar(select(User).where(User.tg_id == tg_id))
        if not user:
            raise Exception("Пользователь не найден")

        vpn_key = await session.scalar(select(VPNKey).where(VPNKey.id == vpn_key_id, VPNKey.idUser == user.idUser))
        if not vpn_key:
            raise Exception("VPN ключ не найден")

        # Новая дата окончания = старая дата или сейчас, + месяцы
        new_expiry = max(vpn_key.expires_at, datetime.utcnow()) + timedelta(days=30 * months)

        # Обновляем VPNKey
        await session.execute(update(VPNKey).where(VPNKey.id == vpn_key.id).values(expires_at=new_expiry))

        # Обновляем последнюю подписку
        await session.execute(update(VPNSubscription)
                              .where(VPNSubscription.vpn_key_id == vpn_key.id)
                              .values(expires_at=new_expiry, status="active"))

        await session.commit()
        return {"vpn_key": vpn_key.access_data, "new_expires_at": new_expiry.isoformat()}
