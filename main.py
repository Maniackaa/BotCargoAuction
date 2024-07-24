import asyncio
import time

import aioschedule

from config.bot_settings import logger, settings
from services.db_func import refresh_db, fill_order_info

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


async def timer(start):

    print(round(time.perf_counter(), 2), round(time.perf_counter() - start, 2))


async def shedulers():
    start = time.perf_counter()
    aioschedule.every(3).seconds.do(refresh_orders_list)
    aioschedule.every(3).seconds.do(fill_order_info_job)
    # aioschedule.every(1).seconds.do(timer, start)
    while True:
        await aioschedule.run_pending()
        await asyncio.sleep(1)


async def main():
    logger.info('Starting bot')
    await asyncio.create_task(shedulers())


try:
    asyncio.run(main())
except (KeyboardInterrupt, SystemExit):
    logger.info('Bot stopped!')
