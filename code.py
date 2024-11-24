import os, time, ssl, wifi, socketpool, adafruit_requests, json
import board, digitalio
import neopixel, time
import adafruit_ntp
import rtc
from adafruit_debouncer import Button

button_A_input = digitalio.DigitalInOut(board.GP17)
button_A_input.switch_to_input(digitalio.Pull.UP)
button_A = Button(button_A_input, value_when_pressed=True)

button_B_input = digitalio.DigitalInOut(board.GP18)
button_B_input.switch_to_input(digitalio.Pull.UP)
button_B = Button(button_B_input, value_when_pressed=True)

strip = neopixel.NeoPixel(board.GP28, 64, brightness=0.01)
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
three_sixty_five_days_ago = time.localtime(time.time() - 365 * 24 * 60 * 60)
from_date = f"{three_sixty_five_days_ago.tm_year:04d}-{three_sixty_five_days_ago.tm_mon:02d}-{three_sixty_five_days_ago.tm_mday:02d}T00:00:00Z"
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
# Process the data to create a list of 1s and 0s for the last 64 days
contribution_list = []
weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']
all_contributions = []
for week in weeks:
    for day in week['contributionDays']:
        all_contributions.append(1 if day['contributionCount'] > 0 else 0)

# Take only the last 64 days
contribution_list = all_contributions[-64:]
print(contribution_list)
days_behind = 0

while True:
    button_A.update()
    button_B.update()
    if button_A.pressed:
        if (days_behind/7) >= 20:
            pass
        strip.fill((0,0,0))
        days_behind += 7
        contribution_list = all_contributions[-(64+days_behind):-(days_behind)]
        print(contribution_list)
        print(f"Looking {days_behind} days behind")
    if button_B.pressed:
        if days_behind == 0:
            pass
        strip.fill((0,0,0))
        days_behind -= 7
        if days_behind <= 0:
            contribution_list = all_contributions[-64:]
            days_behind = 0
        else:
            contribution_list = all_contributions[-(64+days_behind):-(days_behind)]
        print(contribution_list)
        print(f"Looking {days_behind} days behind")

    for col in range(8):  # 8 columns
        for row in range(7):  # 7 rows
            # Calculate index in contribution list - each column is a week
            # Start from the rightmost column (most recent week)
            week_offset = col  # 0 is leftmost column, 7 is rightmost
            day_offset = row
            index = week_offset * 7 + day_offset  # Most recent week on the right
            
            if index < len(contribution_list) and contribution_list[index] == 1:
                # Calculate LED index - each column has 8 LEDs but we only use 7
                strip_index = row * 8 + col
                strip[strip_index] = (0, 255, 0)
