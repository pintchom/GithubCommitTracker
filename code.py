import os, time, ssl, wifi, socketpool, adafruit_requests, json
import board
import neopixel, time
import adafruit_ntp
import rtc


strip = neopixel.NeoPixel(board.GP28, 30)
strip.fill((0, 0, 0))

wifi.radio.connect(os.getenv("WIFI_SSID"), os.getenv("WIFI_PASSWORD"))
print("Connected to WiFi")

pool = socketpool.SocketPool(wifi.radio)
requests = adafruit_requests.Session(pool, ssl.create_default_context())

token = os.getenv("TOKEN")
username = os.getenv("USERNAME")

ntp = adafruit_ntp.NTP(pool, tz_offset=0)

# Get the current time from NTP and set the RTC
current_time = ntp.datetime
rtc.RTC().datetime = current_time

print("Current time:", time.localtime())
thirty_days_ago = time.localtime(time.time() - 30 * 24 * 60 * 60)
from_date = f"{thirty_days_ago.tm_year:04d}-{thirty_days_ago.tm_mon:02d}-{thirty_days_ago.tm_mday:02d}T00:00:00Z"
to_date = f"{current_time.tm_year:04d}-{current_time.tm_mon:02d}-{current_time.tm_mday:02d}T23:59:59Z"

query = f"""
    query {{
    user(login: "{username}") {{
        contributionsCollection(from: "{from_date}", to: "{to_date}") {{
        contributionCalendar {{
            weeks {{
            contributionDays {{
                date
                contributionCount
            }}
            }}
        }}
        }}
    }}
    }}
    """

headers = {"Authorization": f"Bearer {token}"}

url = 'https://api.github.com/graphql'
response = requests.post(url, json={'query': query}, headers=headers)

if response.status_code != 200:
    print(f"Query failed with status code {response.status_code}: {response.text}")
    sys.exit(1)
else:
    print("SUCCESS")

data = response.json()
print(data)
# Process the data to create a list of 1s and 0s
contribution_list = []
weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
for week in weeks:
    for day in week['contributionDays']:
        contribution_list.append(1 if day['contributionCount'] > 0 else 0)

print(contribution_list)

i = 0
for contribution in contribution_list:
    if contribution == 1:
        strip[i] = (0, 255, 0)
    i += 1

