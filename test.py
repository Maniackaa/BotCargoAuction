import asyncio


from config.bot_settings import settings
from services.api_func import refresh_token, get_async_cookies, get_auction_data, get_token


async def main():
    for i in range(1):
        cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
        cookies = cookies['cookies_dict']
        # token = await refresh_token(cookies)
        token = await get_token()
        for i in range(100):
            await asyncio.sleep(1)
            auction = asyncio.create_task(get_auction_data(cookies, token))
        

if __name__ == '__main__':
    asyncio.run(main())