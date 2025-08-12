from datetime import datetime, time

import pytz
from django.utils.dateparse import parse_datetime
from django.utils.timezone import is_aware, make_aware


def time_date_or_live(request):
    start_time = request.GET.get('start_date_time',None)
    end_time = request.GET.get('end_date_time', None)

    if start_time and end_time:
        start_time = parse_datetime(start_time)
        end_time = parse_datetime(end_time)
        if not is_aware(start_time) and not is_aware(end_time):
            start_time = make_aware(start_time)
            end_time = make_aware(end_time)

    else:
        timezone_obj = pytz.timezone('UTC')
        current_time = datetime.now(timezone_obj)
        start_time = datetime.combine(
            current_time.date(), time.min, tzinfo=timezone_obj)
        end_time = current_time



    return start_time, end_time
