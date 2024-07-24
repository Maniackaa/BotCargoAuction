import asyncio
import datetime
import json
import pickle
import re
from typing import Optional, Sequence

from sqlalchemy import select, insert, update, delete
from sqlalchemy.ext.asyncio import async_sessionmaker, AsyncSession
from sqlalchemy.sql.functions import count



from database.db import User, Session, Order, Message, engine, BotSettings


from config.bot_settings import logger, settings
from services.api_func import get_active_orders, get_async_cookies, get_order_info

err_log = logger


async def read_bot_settings(name: str) -> str:
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings).where(BotSettings.name == name).limit(1)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().one_or_none()
    return readed_setting.value


async def read_all_bot_settings():
    async_session: async_sessionmaker[AsyncSession] = async_sessionmaker(
        engine, expire_on_commit=False)
    async with async_session() as session:
        q = select(BotSettings)
        result = await session.execute(q)
        readed_setting: BotSettings = result.scalars().all()
    # print(readed_setting)
    return readed_setting


async def set_botsettings_value(name, value):
    try:
        async_session = async_sessionmaker(engine)
        async with async_session() as session:
            query = select(BotSettings).where(BotSettings.name == name).limit(1)
            result = await session.execute(query)
            setting: BotSettings = result.scalar()
            if setting:
                setting.value = value
            await session.commit()
    except Exception as err:
        err_log.error(f'Ошибка set_botsettings_value. name: {name}, value: {value}')
        raise err


async def refresh_db(login, password):
    logger.debug('Обновляем базу')
    response_orders = await get_active_orders(login, password)
    logger.debug(f'response_orders: {response_orders}')
    # response_orders.pop()
    response_orders_ids = [order['order_id'] for order in response_orders]
    session = Session(expire_on_commit=False)
    with session:
        # Найдем в базе заказы, которых нет в обновлении и поставим статус Устарел:
        closed_orders_q = update(Order).where(Order.order_id.notin_(response_orders_ids), Order.status != 'Устарел').values(status='Устарел')
        closed_orders = session.execute(closed_orders_q).rowcount
        logger.debug(f'Обновлено статусов: {closed_orders}')
        session.commit()


        # Проверим есть ли заказы с обновления в базе. Если нет - добавим в базу.
        # Если есть обновим статус с обновления и обновим order_info.
        for order in response_orders:
            print(order)
            order_id = order['order_id']
            order_from_db_q = select(Order).where(Order.order_id == order_id).limit(1)
            order_from_db: Order = session.execute(order_from_db_q).scalar()
            if not order_from_db:
                new_order = Order(**order)
                session.add(new_order)
            else:
                order_from_db.status = order['status']
                # order_from_db.order_info = order['order_info']
                session.add(order_from_db)
        session.commit()
    return True


def get_order_from_id(pk) -> Order:
    session = Session(expire_on_commit=True)
    with session:
        orders_q = select(Order).where(Order.id == pk)
        order = session.execute(orders_q).scalar()
        return order



async def fill_order_info(login, password):
    """Заполняет Активные и На ожидании order info если он пуст"""
    session = Session(expire_on_commit=False)
    with session:
        q = select(Order).where(Order.status.in_(['Активна', 'На ожидании'])).where(Order.order_info.is_(None))
        orders: Sequence[Order] = session.execute(q).scalars().all()
        logger.debug(f'Заказы с пустым order.info: {orders}')
        cookies = await get_async_cookies(login, password)
        cookies_dict = cookies['cookies_dict']
        for order in orders:
            print(order)
            order_info = await get_order_info(order.order_id, cookies=cookies_dict)
            if order_info:
                order.order_info = order_info
                # Достаем дату
                start_date = order_info['StartDate']
                date = int(re.findall(r'[\d]+', start_date)[0]) / 1000
                target_date = datetime.datetime.fromtimestamp(date)
                order.target_date = target_date
                session.add(order)
        session.commit()


async def main():
    await refresh_db(settings.LOGIN, settings.PASSWORD)
    # get_not_sendet_orders_from_db()
    # get_users_to_send()
    # get_messages_to_delete()
    await fill_order_info(settings.LOGIN, settings.PASSWORD)

    pass

if __name__ == '__main__':
    asyncio.run(main())
