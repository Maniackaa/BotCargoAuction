import datetime
import json

from typing import List

from sqlalchemy import create_engine, ForeignKey, Date, String, DateTime, \
    Float, UniqueConstraint, Integer, MetaData, BigInteger, ARRAY, Table, Column, select, JSON, BLOB, delete
from sqlalchemy.dialects.mysql import TEXT
from sqlalchemy.orm import DeclarativeBase, relationship
from sqlalchemy.orm import Mapped
from sqlalchemy.orm import mapped_column
from sqlalchemy.orm import sessionmaker
from sqlalchemy_utils.functions import database_exists, create_database

from config.bot_settings import get_my_loggers, BASE_DIR, logger

metadata = MetaData()
# db_url = conf.db.db_url
# engine = create_engine(db_url, echo=False)

db_path = BASE_DIR / 'db.sqlite3'
engine = create_engine(f"sqlite:///{db_path}", echo=False)

Session = sessionmaker(bind=engine)

err_log = logger


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = 'users'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    tg_id = mapped_column(String(30), unique=True)
    username: Mapped[str] = mapped_column(String(100), nullable=True)
    first_name: Mapped[str] = mapped_column(String(100), nullable=True)
    last_name: Mapped[str] = mapped_column(String(100), nullable=True)
    full_name: Mapped[str] = mapped_column(String(200), nullable=True)
    register_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    referral: Mapped[str] = mapped_column(String(20), nullable=True)
    anket_data = mapped_column(JSON, nullable=True)
    login: Mapped[str] = mapped_column(String(50), nullable=True)
    password: Mapped[str] = mapped_column(String(50), nullable=True)
    is_active: Mapped[int] = mapped_column(Integer(), default=1)
    tax: Mapped[int] = mapped_column(Integer(), nullable=True)
    old_orders = mapped_column(JSON, default="[]", nullable=True)
    messages: Mapped[List['Message']] = relationship('Message', back_populates='user')

    def __repr__(self):
        return f'{self.id}. {self.tg_id} {self.username or "-"}'

    def set(self, key, value):
        _session = Session()
        try:
            with _session:
                order = _session.query(User).filter(User.id == self.id).one_or_none()
                setattr(order, key, value)
                _session.commit()
                logger.debug(f'Изменено значение {key} на {value}')
        except Exception as err:
            err_log.error(f'Ошибка изменения {key} на {value}')
            raise err

    def append_old_order(self, num):
        old_orders = json.loads(self.old_orders)
        old_orders.append(num)
        self.set('old_orders', json.dumps(list(set(old_orders))))


class BotSettings(Base):
    __tablename__ = 'bot_settings'
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(50))
    value: Mapped[str] = mapped_column(String(50), nullable=True, default='')
    description: Mapped[str] = mapped_column(String(255),
                                             nullable=True,
                                             default='')
    data = mapped_column(JSON, default="[]", nullable=True)

    @classmethod
    def get_item(cls, name):
        _session = Session()
        try:
            with _session:
                setting = _session.query(cls).filter(cls.name == name).one_or_none()
                if setting:
                    return setting.value
        except Exception as err:
            err_log.error(f'err')
            raise err


class Order(Base):
    __tablename__ = 'orders'
    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    order_id: Mapped[int] = mapped_column(Integer())
    order_num: Mapped[str] = mapped_column(String(50))
    start_date: Mapped[datetime.date] = mapped_column(Date(), nullable=True)
    target_date: Mapped[datetime.datetime] = mapped_column(DateTime(), nullable=True)
    link_num: Mapped[int] = mapped_column(Integer())
    status: Mapped[str] = mapped_column(String(20))
    from_city: Mapped[str] = mapped_column(String(50))
    to_city: Mapped[str] = mapped_column(String(50))
    profile: Mapped[str] = mapped_column(String(50))
    price: Mapped[int] = mapped_column(Integer())
    order_info = mapped_column(JSON, nullable=True)
    image: Mapped[str] = mapped_column(String(100), nullable=True)
    is_sended: Mapped[int] = mapped_column(Integer(), default=0)
    activation_time: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), nullable=True)
    # messages = relationship("Message", back_populates="order")
    messages: Mapped[List['Message']] = relationship('Message', back_populates='order',
                                                     cascade='save-update, merge, delete',
                                                     passive_deletes=True,)

    def __repr__(self):
        return f'{self.id}: {self.order_id} {self.status}'

    def time_to_activation(self) -> int:
        if self.activation_time:
            return (self.activation_time - datetime.datetime.utcnow()).total_seconds()

    @classmethod
    def get_items(cls):
        session = Session()
        with session:
            items_q = select(cls).where(cls.status != 'Устарел')
            items = session.execute(items_q).scalars().all()
            return items

    def get_item(self, num):
        if num == 0:
            return None
        items = self.get_items()
        # print(f'items: {items}, num: {num}')
        return items[num - 1]

    def get_nav_btn(self, num):
        nav_btn = {
            '<<': 'back',
            f'{num}/{len(self.get_items())}' if num != 0 else f'Заказов: {len(self.get_items())}': '-',
            '>>': 'fwd',
        }
        return nav_btn

    @classmethod
    def get_title_menu(cls):
        menus = []
        for num, item in enumerate(cls.get_items(), 1):
            order: Order = item
            title = f'{num}. {order.from_city}-{order.to_city} {order.profile}'
            menus.append([title, item.id])
        # print(menus)
        return menus

    def set(self, key, value):
        _session = Session()
        try:
            with _session:
                order = _session.query(Order).filter(Order.id == self.id).one_or_none()
                setattr(order, key, value)
                _session.commit()
                logger.debug(f'Изменено значение {key} на {value}')
        except Exception as err:
            err_log.error(f'Ошибка изменения {key} на {value}')
            raise err

    def __getattr__(self, item):
        # dict_keys(['StartDate', 'DueDate', 'SlideDate', 'Direction', 'Vehicle', 'VehiclePrice', 'VehicleCount',
        # 'ExtraServices', 'ExtraServicesPrice', 'BidsType', 'TreedingFeeSumm', 'BidPrice', 'NormalGOSumm',
        # 'Description', 'BidsCount', 'NewStartDate', 'NewDueDate', 'NewSlideDate', 'BidStatus', 'FromAddress',
        # 'ToAddress', 'Cargo', 'FilingTime', 'PriceNDS', 'BidСonditions'])
        if self.__dict__ and self.__dict__.get('order_info') and item in self.__dict__.get('order_info'):
            return self.__dict__.get('order_info')[item]
        return object.__getattribute__(self, item)


class Message(Base):
    __tablename__ = 'messages'

    id: Mapped[int] = mapped_column(primary_key=True,
                                    autoincrement=True,
                                    comment='Первичный ключ')
    created_date: Mapped[datetime.datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.datetime.now(tz=tz))
    order_id: Mapped[int] = mapped_column(ForeignKey('orders.id', ondelete='CASCADE'))
    order = relationship("Order", back_populates="messages")
    user_id: Mapped[int] = mapped_column(ForeignKey('users.id'))
    user = relationship("User", back_populates="messages")
    chat_id: Mapped[int] = mapped_column(Integer())
    message_id: Mapped[int] = mapped_column(Integer())

    def __repr__(self):
        return f'Message {self.id}. order: {self.order_id} user: {self.user_id}'


# if not database_exists(db_url):
#     create_database(db_url)

Base.metadata.create_all(engine)

# print(BotSettings().get_item('phone'))

session = Session()
with session:
    q = select(BotSettings)
    settings = session.execute(q).scalars().all()
    if not settings:
        session = Session()
        settings = [
            ['broker_email', 'FTL@postavkaservis.ru', 'Почта брокера для предложений'],
            ['phone', '+7 (499) 112-39-77', ''],
            ['telegram', '@tg', ''],
            ['whatsapp', 'whatsapp', ''],
            ['email', 'info@bgruz.com', ''],
        ]
        with session:
            for setting in settings:
                s = BotSettings(name=setting[0],
                                value=setting[1],
                                description=setting[2],
                                )
                session.add(s)
            session.commit()




# session = Session()
# with session:
#     q = select(Order).where(Order.id == 2)
#     order: Order = session.execute(q).scalars().first()
#     print(order)
#     if order:
#         session.delete(order)
#         session.commit()
#
#
# session = Session()
# with session:
#     q = select(Message).where(Message.id == 2)
#     message: Message = session.execute(q).scalars().first()
#     print(message)
#     if message:
#         session.delete(message)
#         session.commit()


# if order:
#     print(order)
#     print(order.order_info)
# #
# session = Session()
# with session:
#     q = select(Order)
#     order: Order = session.execute(q).scalars().first()
#     print(order)
#
# print(order.order_info)
# for key, val in order.order_info.items():
#     print(key)
#     print(val)
#     print('-----------')
# order_info = order.order_info
# print(order_info)
#
# data = {
#     'bids[0].BidDate': '2023-12-24T00:00:00.000Z',
#     'bids[0].DirectionId': '902',
#     'bids[0].Price': '19400',
#     'bids[0].VehicleProfileId': '98',
#     'vehicleTotal': '1',
#     'slideDayTotal': '0',
#     'description': '',
#     'mainVehicleProfileId': '98',
# }
#
# my_price = 10000
#
# data = {
#     'bids[0].BidDate': f'{order.target_date}',
#     'bids[0].DirectionId': order_info['Direction']['DirectionId'],
#     'bids[0].Price': f'{my_price}',
#     'bids[0].VehicleProfileId': order_info['Vehicle']['VehicleProfileId'],
#     'vehicleTotal': '1',
#     'slideDayTotal': '0',
#     'description': order_info['Description'],
#     'mainVehicleProfileId': order_info['Vehicle']['VehicleProfileId'],
# }
#
# cookies = {
#     '.ASPXAUTH': '4601DBE952DEE5B5C322B0441239D3590689A36560906F260CA97F82B5F62155F3E8AA1B68BD74D7191912E2E60FA0EA5D46762536DD8F99667B0A935FB289BE6407CE5F4A94FF0E79A23B5889F4126445E3DF60',
#     'TransportMarket_LCID': '1049',
# }


# response = requests.post('https://p1.bgruz.com/Bid/CreateBids', cookies=cookies, headers=headers, data=data)
# print(response)
# print(response.text)