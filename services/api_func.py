import asyncio
import datetime
import json
import time
from math import floor, ceil
from pprint import pprint

import aiohttp
import requests

from database.db import User, Order

from config.bot_settings import logger, settings

err_log = logger


async def get_async_cookies(login='TUTU', password='123', lcid='1049') -> dict:
    """Возвращает словарь из cookies в формате CookieJar и dict
    {"cookies_jar": cookies_jar, "cookies": cookies_dict}"""
    data = {'login': login,
            'password': password,
            'lcid': lcid,}
    async with aiohttp.ClientSession() as session:
        async with session.post('https://dev2.bgruz.com/Account/LogIn',
                               headers=None,
                               params=data) as response:
            cookies_jar = session.cookie_jar
            cookies = cookies_jar.filter_cookies('https://dev2.bgruz.com')
            cookies_dict = {}
            for key, cookie in cookies.items():
                cookies_dict[key] = cookie.value
    return {"cookies_jar": cookies_jar, "cookies_dict": cookies_dict}


async def get_aiohttp_response(url, response_type='text', headers=None, data=None, params=None, cookies=None,
                               cookie_jar=aiohttp.CookieJar(unsafe=True), content_type='text/html'):
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with session.get(url,
                               headers=headers,
                               params=params,
                               data=data,
                               cookies=cookies) as response:
            logger.debug(response.status)
            if response.status == 200:
                if response_type == 'json':
                    result = await response.json(content_type=content_type, encoding='UTF-8')
                elif response_type == 'text':
                    result = await response.text(encoding='UTF-8')
                return result
            else:
                raise ConnectionError(f'Неверный ответ от сервера: {response.status}')


async def post_aiohttp_response(url, response_type='text', headers=None, params=None, data=None, cookies=None,
                                cookie_jar=aiohttp.CookieJar(unsafe=True), content_type='text/html'):
    async with aiohttp.ClientSession(cookie_jar=cookie_jar) as session:
        async with session.post(url,
                                headers=headers,
                                params=params,
                                data=data,
                                cookies=cookies) as response:
            logger.debug(response.status)
            if response.status == 200:
                if response_type == 'json':
                    result = await response.json(content_type=content_type, encoding='UTF-8')
                elif response_type == 'text':
                    result = await response.text(encoding='UTF-8')
                return result
            else:
                raise ConnectionError('Неверный ответ от сервера')


async def get_order_info(order_id: str, cookies) -> dict:
    """Достает подробное инфо по order_id
    :param order_id:
    :param cookies:
    :return: dict
    """
    logger.debug(f'Получаем полное инфо по ID {order_id}')
    url = f'https://dev2.bgruz.com/Bid/GetBidFormData?bidId={order_id}&bidType=B&formMode=1'
    response_json = await get_aiohttp_response(url, response_type='json', cookies=cookies, )
    data = response_json
    logger.debug(data)
    return data


async def get_active_orders(login='tutu', password='123') -> list[dict]:
    """

    """
    logger.debug('Получаем активные заказы')
    try:
        url = 'https://dev2.bgruz.com/BuyBid/GetGridData'
        params = {
            'rows': '100',
            'page': '1',
            'sord': 'desc',
            'filters': '{"groupOp":"AND","rules":[{"field":"Status","op":"eq","data":"10001"}]}',
            # Активная + На ожидании
            'customFilters': '{"groupOp":"AND","rules":[{"field":"Bids_OnlyMy","op":"cn","data":false}]}',
            # 'filters': '{"groupOp":"AND","rules":[]}',  # Все
        }

        cookies = await get_async_cookies(login=login, password=password)
        cookies_dict = cookies['cookies_dict']
        response_json = await get_aiohttp_response(url, response_type='json', params=params, cookies=cookies_dict)
        orders = []
        orders_data = response_json
        logger.debug(f'orders_data: {orders_data}')
        rows = orders_data.get('rows')
        # {'order_id': '450503', 'status': 'На ожидании', 'link_num': '317624', 'from_city': 'Самара', 'to_city': 'Пермь', 'profile': 'Контейнеровоз 20"', 'price': 400.0, 'order_info': {'StartDate': '/Date(1703462400000)/', 'DueDate': None, 'SlideDate': None, 'Direction': {'DirectionId': 12742, 'Description': '2 суток', 'LowPrice': 1000.0, 'HighPrice': 3000000.0, 'FromCityId': 317, 'ToCityId': 4, 'IsDeleted': None, 'AuthorId': 1, 'CreateDate': '/Date(1601650988846)/', 'UpdatedUserId': 1, 'Updated': '/Date(1601650988846)/', 'DeliveryPeriod': 2, 'FromCity': {'CityId': 317, 'CityName': 'Самара', 'IsDeleted': None, 'Description': None}, 'ToCity': {'CityId': 4, 'CityName': 'Пермь', 'IsDeleted': None, 'Description': None}}, 'Vehicle': {'VehicleProfileId': 47, 'VehicleProfileName': 'Контейнеровоз 20"', 'Description': 'Платформа', 'VehicleTypeId': 6, 'TonnageId': 1, 'UntentingPrice': 0.0, 'DownloadTypeId': 1, 'IsDeleted': None, 'SortOrder': 5000, 'VehicleType': {'VehicleTypeId': 6, 'VehicleTypeName': 'Контейнеровоз 20"', 'IsDeleted': None, 'SortOrder': 1500}, 'Tonnage': {'TonnageName': '20т', 'TonnageId': 1, 'IsDeleted': None, 'SortOrder': 120, 'VehicleProfilesViews': []}, 'DownloadType': {'DownloadTypeId': 1, 'DownloadTypeName': 'Задняя', 'IsDeleted': None, 'SortOrder': 10}, 'Vehicles': []}, 'VehiclePrice': 400.0, 'VehicleCount': 1, 'ExtraServices': [], 'ExtraServicesPrice': 0.0, 'BidsType': 'B', 'TreedingFeeSumm': 0.0, 'BidPrice': 400.0, 'NormalGOSumm': 0.0, 'Description': 'Коммент', 'BidsCount': 1, 'NewStartDate': '/Date(1703462400000)/', 'NewDueDate': None, 'NewSlideDate': None, 'BidStatus': 1, 'FromAddress': 'Адрес погрузки:', 'ToAddress': 'Адрес выгрузки:', 'Cargo': 'Наименование груз', 'FilingTime': '09:30', 'PriceNDS': 0.0, 'BidСonditions': ''}, 'target_date': datetime.datetime(2023, 12, 25, 7, 0)}
        for row in rows:
            order = {}
            order_id = row['id']
            cell = row.get('cell')
            # order['all'] = row
            order['order_id'] = order_id
            order['order_num'] = cell[0]
            order['status'] = cell[15]
            order['link_num'] = cell[1]
            start_date = datetime.datetime.strptime(cell[3], '%d.%m.%Y').date()
            order['start_date'] = start_date
            order['from_city'] = cell[4]
            order['to_city'] = cell[5]
            order['profile'] = cell[6]
            order['price'] = float(cell[8])
            if cell[19]:
                print(cell[19])
                act_time = datetime.datetime.strptime(cell[19], '%H:%M:%S').time()
                order['activation_time'] = datetime.datetime.combine(start_date, act_time)


            orders.append(order)
        logger.debug(f'orders: {orders}')
        return orders
    except Exception as err:
        logger.error(err, exc_info=True)
        raise err


async def create_bids(user: User, order: Order):
    logger.debug('Отправка заявки на сайт')
    order_info = order.order_info
    my_price = order_info['VehiclePrice']
    rounded_price = floor(my_price / 200) * 200
    data = {
        'bids[0].BidDate': f'{order.target_date}',
        'bids[0].DirectionId': order_info['Direction']['DirectionId'],
        'bids[0].Price': rounded_price,
        'bids[0].VehicleProfileId': order_info['Vehicle']['VehicleProfileId'],
        'vehicleTotal': '1',
        'slideDayTotal': '0',
        'description': order_info['Description'],
        'mainVehicleProfileId': order_info['Vehicle']['VehicleProfileId'],
    }
    logger.debug(f'data: {data}')
    cookies = await get_async_cookies(user.login, user.password)
    cookies = cookies['cookies_dict']
    url = 'https://p1.bgruz.com/Bid/CreateBids'
    response = await post_aiohttp_response(url, response_type='text', params=data, cookies=cookies)
    return response


async def get_token(cookies):
    response = await get_aiohttp_response(url='https://dev2.bgruz.com/signalr/negotiate', cookies=cookies, response_type='json', content_type='application/json')
    return response.get('ConnectionToken')


async def get_auction_data() -> str:
    cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    cookies = cookies['cookies_dict']
    token = await get_token(cookies)
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
    return json.loads(response.get("R"))


async def cancel_order(order_id, token, cookies):
    # cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    # cookies = cookies['cookies_dict']
    # token = await get_token(cookies)
    params = {
        'transport': 'serverSentEvents',
        'connectionToken': f'{token}',
        'connectionData': '[{"name":"matchingpushhub"}]',
    }

    data_json = {
        "H": "matchingpushhub",
        "M": "ChangeBidPrice",
        "A": [f"{order_id}", 0, "B"],
        "I": 3
    }
    data = {
        'data': json.dumps(data_json).replace(' ', '')
    }

    response = requests.post('https://dev2.bgruz.com/signalr/send', params=params, cookies=cookies, data=data)
    print(response)


async def create_order(order_info, cookies=None):
    """
    data = {
        'bids[0].BidDate': '2024-07-25T00:00:00.000Z',
        'bids[0].DirectionId': '12962',
        'bids[0].Price': '800',
        'bids[0].VehicleProfileId': '144',
        'vehicleTotal': '2',
        'slideDayTotal': '0',
        'extraServices[0].Count': '3',
        'extraServices[0].ExtraServicesPacksDetailId': '8822',
        'extraServices[0].VehicleProfileId': '144',
        'extraServices[0].ExtraServiceId': '4',
        'extraServices[0].ExtraServicesPacksId': '1211',
        'extraServices[1].Count': '4',
        'extraServices[1].ExtraServicesPacksDetailId': '8821',
        'extraServices[1].VehicleProfileId': '144',
        'extraServices[1].ExtraServiceId': '28',
        'extraServices[1].ExtraServicesPacksId': '1211',
        'extraServices[2].Count': '1',
        'extraServices[2].ExtraServicesPacksDetailId': '8820',
        'extraServices[2].VehicleProfileId': '144',
        'extraServices[2].ExtraServiceId': '47',
        'extraServices[2].ExtraServicesPacksId': '1211',
        'description': 'Комментарий',
        'mainVehicleProfileId': '144',
        'fromAddress': '',
        'toAddress': '',
        'cargo': 'Наименование',
        'filingTime': '06:45',
        'PriceNDS': '2400',
    }
    """
    BidDate = order_info['StartDate']
    BidDate = int(''.join([x for x in BidDate if x.isdigit()])[:-3])
    BidDate = datetime.datetime.utcfromtimestamp(BidDate).isoformat()
    Direction = order_info['Direction']
    Vehicle = order_info.get('Vehicle')
    ExtraServices = order_info.get('ExtraServices')

    data = {
        'bids[0].BidDate': BidDate,
        'bids[0].DirectionId': Direction.get('DirectionId'),
        'bids[0].Price': order_info.get('BidPrice'),
        'bids[0].VehicleProfileId': Vehicle.get('VehicleProfileId'),
        'vehicleTotal': order_info.get(f'VehicleCount'),
        'slideDayTotal': '0',
        'description': order_info.get('Description'),
        'mainVehicleProfileId': Vehicle.get('VehicleProfileId'),
        'fromAddress': order_info.get('FromAddress'),
        'toAddress':  order_info.get('ToAddress'),
        'cargo': order_info.get('Cargo'),
        'filingTime': order_info.get('FilingTime'),
        'PriceNDS': order_info.get('PriceNDS'),
    }
    if len(ExtraServices) >= 1:
        data.update({
            'extraServices[0].Count': ExtraServices[0].get('ExtraServiceCount'),
            'extraServices[0].ExtraServicesPacksDetailId': f'882{len(ExtraServices)-1}',
            'extraServices[0].VehicleProfileId': Vehicle.get('VehicleProfileId'),
            'extraServices[0].ExtraServiceId': ExtraServices[0].get('ExtraServiceId'),
            'extraServices[0].ExtraServicesPacksId': ExtraServices[0].get('ExtraServicePackId'),}
        )
    if len(ExtraServices) >= 2:
        data.update({
            'extraServices[1].Count': ExtraServices[1].get('ExtraServiceCount'),
            'extraServices[1].ExtraServicesPacksDetailId': f'882{len(ExtraServices)-2}',
            'extraServices[1].VehicleProfileId': Vehicle.get('VehicleProfileId'),
            'extraServices[1].ExtraServiceId': ExtraServices[1].get('ExtraServiceId'),
            'extraServices[1].ExtraServicesPacksId': ExtraServices[1].get('ExtraServicePackId'),}
        )
    if len(ExtraServices) >= 3:
        data.update({
            'extraServices[2].Count': ExtraServices[2].get('ExtraServiceCount'),
            'extraServices[2].ExtraServicesPacksDetailId': f'882{len(ExtraServices)-3}',
            'extraServices[2].VehicleProfileId': Vehicle.get('VehicleProfileId'),
            'extraServices[2].ExtraServiceId': ExtraServices[2].get('ExtraServiceId'),
            'extraServices[2].ExtraServicesPacksId': ExtraServices[2].get('ExtraServicePackId'),}
        )

    for k, v in data.items():
        data[k] = str(v)
    pprint(data)

    response = requests.post('https://dev2.bgruz.com/Bid/CreateBids', cookies=cookies, data=data)
    print(response)
    print(response.text)

async def main():

    # print(x)
    cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    cookies = cookies['cookies_dict']
    token = await get_token(cookies)
    # print(cookies)
    #
    # response = requests.get('https://dev2.bgruz.com/signalr/send/', cookies=cookies)
    # print(response)
    orders = await get_active_orders(settings.LOGIN, settings.PASSWORD)
    # print(orders)
    # for order in orders:
    #     print(order)
    order = orders[-1]
    print(order)
    # auction_data = await get_auction_data()
    # print(auction_data)
    # for data in auction_data:
    #     print(data)
    # cookies = await get_async_cookies(settings.LOGIN, settings.PASSWORD)
    # cookies_dict = cookies['cookies_dict']
    order_info = await get_order_info(order['order_id'], cookies=cookies)
    pprint(order_info)
    await cancel_order(order['order_id'], token=token, cookies=cookies)
    await create_order(order_info, cookies=cookies)
    pass


if __name__ == '__main__':
    asyncio.run(main())
