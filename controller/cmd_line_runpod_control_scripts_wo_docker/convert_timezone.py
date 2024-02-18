#!/usr/bin/python3
from datetime import datetime
from pytz import timezone

# Given time in UTC
utc_time_str = "Sat Feb 10 2024 19:01:03 GMT+0000"
utc_format = "%a %b %d %Y %H:%M:%S GMT%z"

# Convert string to datetime object in UTC
utc_time = datetime.strptime(utc_time_str, utc_format)

# Define the Austin, TX timezone
austin_tz = timezone('America/Chicago')

# Convert UTC time to Austin time
austin_time = utc_time.astimezone(austin_tz)

print(f"Time in Austin, TX: {austin_time.strftime('%Y-%m-%d %H:%M:%S %Z%z')}")

