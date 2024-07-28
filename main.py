import asyncio
import time

import aioschedule

from config.bot_settings import logger, settings
from services.func import refresh_async_cookies, refresh_token, get_auction_data
from services.func import refresh_db, fill_order_info, find_orders_to_job, read_cookies_dict, read_token
from services.tasks import task_order_check

err_log = logger


async def refresh_orders_list():
    logger.debug('Обновление списка заказов')
    try:
        await refresh_db(login=settings.LOGIN, password=settings.PASSWORD)

    except Exception as err:
        logger.error(err, exc_info=False)
        err_log.error(err, exc_info=True)


async def fill_order_info_job():
    logger.debug('Обновление подробного инфо')
    try:
        await fill_order_info(login=settings.LOGIN, password=settings.PASSWORD)
    except Exception as err:
        logger.error(err, exc_info=False)
        err_log.error(err, exc_info=True)


async def find_order_job():
    logger.debug('Задача поиска заказов для работы')
    orders = await find_orders_to_job(settings.STARTTIME)
    for order in orders:
        logger.info(f'Запускаем заказ {order}')
        asyncio.create_task(task_order_check(order))


async def refresh_auction():
    logger.debug('refresh_auction')
    cookies = await read_cookies_dict()
    token = await read_token()
    start = time.perf_counter()
    auction = await get_auction_data(cookies, token)
    # for a in auction:
    #     if a.get('SoonActivationTime'):
    #         print(a)
    # print()
    if not auction:
        logger.error(f'{time.perf_counter() - start}, auction: {auction}')

async def shedulers():
    start = time.perf_counter()
    aioschedule.every(15).seconds.do(refresh_orders_list)
    aioschedule.every(5).seconds.do(fill_order_info_job)
    aioschedule.every(3).seconds.do(find_order_job)
    # aioschedule.every(1).seconds.do(timer, start)
    aioschedule.every(1).seconds.do(refresh_auction)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    logger.info('Starting bot')
    await refresh_async_cookies(settings.LOGIN, settings.PASSWORD)
    cookies = await read_cookies_dict()
    print(cookies)
    token = await refresh_token(cookies)
    print(token)
    await asyncio.create_task(shedulers())


try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    logger.info('Bot stopped!')
