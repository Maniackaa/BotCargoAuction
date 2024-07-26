import asyncio
import datetime
import time

import pytz

from config.bot_settings import logger, settings
from database.db import Order
from services.api_func import get_auction_data, get_active_orders, cancel_order, get_async_cookies, get_token, \
    create_order, get_order_info
from services.db_func import get_order_from_id, find_orders_to_job


async def get_auction_data_from_order(order: Order) -> dict:
    auctions_data = await get_auction_data()
    print(auctions_data)
    for order_auction in auctions_data:
        activation_time = order_auction.get('SoonActivationTime')
        if activation_time:
            activation_time = datetime.datetime.strptime(activation_time, "%Y-%m-%dT%H:%M:%S.%f").replace(microsecond=0)
            print(activation_time, order.activation_time)
            if activation_time == order.activation_time:
                return order_auction


async def last_second_task(order: Order, start_auction):
    logger.debug(f'начата задача на последних секундах {order}. До активации: {order.time_to_activation()}')
    await asyncio.sleep(order.time_to_activation() - 20)
    logger.debug(f'До активации: {order.time_to_activation()}')
    start = time.perf_counter()
    cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    cookies = cookies['cookies_dict']
    token = await get_token(cookies)
    order_info = await get_order_info(order.order_id, cookies=cookies)
    await asyncio.sleep(order.time_to_activation() - 10)
    logger.debug(f'АКТИВРИУЕМСЯ. Проверяем акуцион. Осталось {order.time_to_activation()}')
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



async def main():
    orders = await find_orders_to_job()
    print(orders)
    for order in orders:

        print(order)
        print(order.time_to_activation())
        asyncio.create_task(task_order_check(order))
        pass
    await asyncio.sleep(500)

if __name__ == '__main__':
    asyncio.run(main())