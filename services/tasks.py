import asyncio
import datetime
import time

import pytz

from config.bot_settings import logger, settings
from database.db import Order
from services.func import cancel_order, create_order, read_auction_data
from services.func import *
from services.func import get_order_info_from_db


async def get_auction_data_from_order(order: Order) -> dict:
    # auctions_data = await get_auction_data()
    auctions_data = await read_auction_data()
    for order_auction in auctions_data:
        activation_time = order_auction.get('SoonActivationTime')
        if activation_time:
            print(activation_time)
            activation_time = datetime.datetime.strptime(activation_time, "%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)
            # activation_time = datetime.datetime.strptime(activation_time, "%Y-%m-%dT%H:%M:%S")
            if activation_time == order.activation_time:
                return order_auction


async def last_second_task(order: Order, start_auction):
    logger.info(f'начата задача на последних секундах {order}. До активации: {order.time_to_activation()}')
    await asyncio.sleep(order.time_to_activation() - 15)
    logger.info(f'До активации: {order.time_to_activation()}')
    start = time.perf_counter()
    # cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    # cookies = cookies['cookies_dict']
    # token = await get_token(cookies)
    cookies = await read_cookies_dict()
    token = await read_token()
    order_info = await get_order_info_from_db(order.order_id, cookies=cookies)
    await asyncio.sleep(order.time_to_activation() - settings.ENDTIME)
    logger.info(f'АКТИВРИУЕМСЯ. Проверяем акуцион. Осталось {order.time_to_activation()}')
    order_auction = await get_auction_data_from_order(order)
    new_bid_count = order_auction.get('SaleBidCount')
    logger.info(f'До активации {order.time_to_activation()}. Новые ставки: {new_bid_count}. order_auctionЖ {order_auction}')
    if order_auction != start_auction:
        logger.info(f'{order.time_to_activation()} Отменяем заявку')
        await cancel_order(order.order_id, token, cookies=cookies)
        logger.info(f'Пересоздаем заявку')
        await create_order(order_info, cookies=cookies)
    else:
        logger.info(f'{order.time_to_activation()} Ставок нет, расходимся')


async def task_order_check(order: Order):
    logger.info(f'начата задача по {order} {order.activation_time}')
    order.set('is_sended', 1)
    logger.debug(f'Ищем данные по торгам')
    # print(*auctions_data, sep='\n')
    order_auction = await get_auction_data_from_order(order)
    if order_auction:
        bid_count = order_auction.get('SaleBidCount')
        logger.info(f'--start_bid_count: {bid_count} До активации {order.time_to_activation()}. order_auction: {order_auction}')
        asyncio.create_task(last_second_task(order, order_auction))
    else:
        logger.warning('Нет аукциона')



async def main():

    order = get_last_order()

    auction_data = await get_auction_data_from_order(order)

    await task_order_check(order)
    await asyncio.sleep(100)
    # orders = await find_orders_to_job()
    # print(orders)
    # for order in orders:
    #
    #     print(order)
    #     print(order.time_to_activation())
    #     asyncio.create_task(task_order_check(order))
    #     pass
    # await asyncio.sleep(500)

if __name__ == '__main__':
    asyncio.run(main())