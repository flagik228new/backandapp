from sqlalchemy import ForeignKey, String, BigInteger, Integer, Boolean, DateTime
from sqlalchemy.orm import Mapped, DeclarativeBase, mapped_column
from sqlalchemy.ext.asyncio import AsyncAttrs, async_sessionmaker, create_async_engine
from datetime import datetime


engine = create_async_engine(url='sqlite+aiosqlite:///db.sqlite3', echo = True)

async_session = async_sessionmaker(bind=engine, expire_on_commit=False)

class Base(AsyncAttrs, DeclarativeBase):
    pass


# юзеры
class User(Base):
    __tablename__ = "users"
    idUser: Mapped[int] = mapped_column(primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    userRole: Mapped[str] = mapped_column(String(200), default="user")
    trial_until: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    # реферальная система
    referrer_id: Mapped[int | None] = mapped_column(ForeignKey("users.idUser"),nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)

# VPN DICTIONARIES
class TypesVPN(Base):
    """
    outline / hiddify / vless / shadowsocks
    """
    __tablename__ = "types_vpn"
    idTypeVPN: Mapped[int] = mapped_column(primary_key=True)
    nameType: Mapped[str] = mapped_column(String(200), nullable=False)
    descriptionType: Mapped[str] = mapped_column(String(200), nullable=False)


class CountriesVPN(Base):
    __tablename__ = "countries_vpn"
    idCountry: Mapped[int] = mapped_column(primary_key=True)
    nameCountry: Mapped[str] = mapped_column(String(200), nullable=False)

# VPN SERVERS
class ServersVPN(Base):
    __tablename__ = "servers_vpn"
    idServerVPN: Mapped[int] = mapped_column(primary_key=True)
    nameVPN: Mapped[str] = mapped_column(String(200), nullable=False)
    price: Mapped[int] = mapped_column(Integer,nullable=False)  # цена за месяц (в копейках / центах)
    max_conn: Mapped[int] = mapped_column(Integer, nullable=False)
    now_conn: Mapped[int] = mapped_column(Integer, default=0)
    server_ip: Mapped[str] = mapped_column(String(300), nullable=False)
    # данные для управления сервером
    api_url: Mapped[str] = mapped_column(String(300), nullable=False)
    api_token: Mapped[str] = mapped_column(String(300), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    idTypeVPN: Mapped[int] = mapped_column(ForeignKey("types_vpn.idTypeVPN", ondelete="CASCADE"))
    idCountry: Mapped[int] = mapped_column(ForeignKey("countries_vpn.idCountry", ondelete="CASCADE"))


# VPN KEYS (САМОЕ ВАЖНОЕ)
class VPNKey(Base):
    """
    Один ключ = один доступ к VPN
    """
    __tablename__ = "vpn_keys"
    id: Mapped[int] = mapped_column(primary_key=True)
    idUser: Mapped[int] = mapped_column(ForeignKey("users.idUser", ondelete="CASCADE"))
    idServerVPN: Mapped[int] = mapped_column(ForeignKey("servers_vpn.idServerVPN", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(200))
    # outline / hiddify
    provider_key_id: Mapped[str] = mapped_column(String(200))
    # ID ключа в Outline или UUID
    access_data: Mapped[str] = mapped_column(String(500))
    # outline://... / ss://... / vless://...
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)

# VPN SUBSCRIPTIONS
class VPNSubscription(Base):
    """
    Бизнес-логика подписки
    """
    __tablename__ = "vpn_subscriptions"
    id: Mapped[int] = mapped_column(primary_key=True)
    idUser: Mapped[int] = mapped_column(ForeignKey("users.idUser", ondelete="CASCADE"))
    vpn_key_id: Mapped[int] = mapped_column(ForeignKey("vpn_keys.id", ondelete="CASCADE"))
    started_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    expires_at: Mapped[datetime] = mapped_column(DateTime)
    status: Mapped[str] = mapped_column(String(50),default="active")  # active / expired / revoked

# REFERRAL EARNINGS
class ReferralEarning(Base):
    __tablename__ = "referral_earnings"
    id: Mapped[int] = mapped_column(primary_key=True)
    referrer_id: Mapped[int] = mapped_column(ForeignKey("users.idUser", ondelete="CASCADE"))
    referred_id: Mapped[int] = mapped_column(ForeignKey("users.idUser", ondelete="CASCADE"))
    amount: Mapped[int] = mapped_column(Integer)  # копейки / центы
    created_at: Mapped[datetime] = mapped_column(DateTime,default=datetime.utcnow)
    
async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)