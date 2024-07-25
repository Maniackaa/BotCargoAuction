import datetime

import pytz

from config.bot_settings import settings

date_string = '2024-07-25T05:23:19.08'
t = datetime.datetime.strptime(date_string, "%Y-%m-%dT%H:%M:%S.%f")
print(t.astimezone())

act_time = datetime.datetime.strptime('8:40:50', '%H:%M:%S').time()
print(act_time)
now_date = settings.tz.localize(datetime.datetime.utcnow()).date()
activation_time = settings.tz.localize(datetime.datetime.combine(now_date, act_time)) - datetime.timedelta(hours=3)
print(repr(activation_time))
print(activation_time)