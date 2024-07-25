import asyncio
import datetime

import pytz

from config.bot_settings import logger, settings
from database.db import Order
from services.api_func import get_auction_data, get_active_orders
from services.db_func import get_order_from_id, find_orders_to_job


async def task_order_check(order: Order):
    logger.debug(f'начата задача по {order} {order.activation_time}')
    logger.debug(f'Ищем данные по торгам')
    auctions_data = await get_auction_data()
    for order_auction in auctions_data:
        activation_time = order_auction.get('SoonActivationTime')
        if activation_time:
            print(order_auction)
            activation_time = datetime.datetime.strptime(activation_time, "%Y-%m-%dT%H:%M:%S.%f")
            print(repr(order.activation_time), repr(activation_time))
            print(order.time_to_activation())

async def main():
    orders = await find_orders_to_job()
    # print(orders)
    # for order in orders:
    #     print(order)
    if orders:
        order = orders[-1]
        print(order)
        print(order.time_to_activation())
        await task_order_check(order)
        pass

if __name__ == '__main__':
    asyncio.run(main())