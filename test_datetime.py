from datetime import datetime, timedelta
date_time=datetime.now()
print (date_time)
# Format date_time to ISO 8601 format
iso_date = date_time.strftime('%Y-%m-%dT%H:%M:%S.%fZ')
print (iso_date)
