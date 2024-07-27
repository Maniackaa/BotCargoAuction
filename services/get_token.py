import asyncio

import requests

from config.bot_settings import settings
from services.api_func import post_aiohttp_response




async def main():
    # x = await get_token()
    # print(x)
    # orders = await get_active_orders(settings.LOGIN, settings.PASSWORD)
    # print(orders)
    # auction_data = await get_auction_data()
    # print(auction_data)
    pass
    cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    cookies = cookies['cookies_dict']
    response = requests.get('https://dev2.bgruz.com/signalr/negotiate', cookies=cookies)
    token = response.json().get('ConnectionToken')
    print(token)

    params = {
        'transport': 'serverSentEvents',
        'connectionToken': token,
        'connectionData': '[{"name":"matchingpushhub"}]',
    }
    data = {
        'data': '{"H":"matchingpushhub","M":"GetQuotationByUser","A":[],"I":2}',
    }
    url = 'https://dev2.bgruz.com/signalr/send'
    response = await post_aiohttp_response(url, response_type='json', params=params,  data=data, cookies=cookies, content_type='application/json')
    print(response)





if __name__ == '__main__':
    asyncio.run(main())
    import requests



