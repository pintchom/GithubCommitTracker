import requests
import datetime
import numpy as np
import sys
import os
import matplotlib.pyplot as plt

def main():
    username = input("Enter GitHub username: ")

    token = os.environ.get('GITHUB_TOKEN')
    if not token:
        token = input("Enter your GitHub personal access token: ")

    # Get date range from user input
    from_date = input("Enter start date (YYYY-MM-DD): ")
    to_date = input("Enter end date (YYYY-MM-DD): ")

    # Convert date strings to datetime objects
    start_date = datetime.datetime.strptime(from_date, "%Y-%m-%d").date()
    end_date = datetime.datetime.strptime(to_date, "%Y-%m-%d").date()

    # Convert date strings to ISO 8601 format with time component
    from_date = start_date.isoformat() + "T00:00:00Z"
    to_date = end_date.isoformat() + "T23:59:59Z"

    # Use these formatted dates in your GraphQL query
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

    data = response.json()

    if 'errors' in data:
        print("Errors:", data['errors'])
        sys.exit(1)

    contributions = []
    weeks = data['data']['user']['contributionsCollection']['contributionCalendar']['weeks']

    for week in weeks:
        for day in week['contributionDays']:
            date_str = day['date']
            count = day['contributionCount']
            date = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
            contributions.append({'date': date, 'count': count})

    N_weeks = ((end_date - start_date).days + 1) // 7
    grid = np.zeros((7, N_weeks))

    for c in contributions:
        date = c['date']
        count = c['count']
        day_of_week = date.weekday()  # Monday=0, Sunday=6
        day_index = (day_of_week + 1) % 7  # Sunday=0 to Saturday=6
        week_index = (date - start_date).days // 7
        if 0 <= week_index < N_weeks:
            grid[day_index, week_index] = 1 if count > 0 else 0

    # Plotting
    plt.figure(figsize=(N_weeks/2, 4))
    plt.imshow(grid, interpolation='none', cmap='binary', aspect='auto', origin='lower')

    # Month labels
    month_positions = []
    month_names = []
    prev_month = None
    for week_index in range(N_weeks):
        date = start_date + datetime.timedelta(days=week_index*7)
        month = date.month
        if month != prev_month:
            month_positions.append(week_index)
            month_names.append(date.strftime('%b'))
            prev_month = month

    plt.xticks(month_positions, month_names, fontsize=8)
    # Day labels
    days = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat']
    plt.yticks(range(7), days, fontsize=8)
    plt.title(f'GitHub Contributions for {username}')
    plt.tight_layout()
    plt.show()

if __name__ == '__main__':
    main()
