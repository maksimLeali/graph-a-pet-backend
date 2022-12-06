import pendulum
from collections import defaultdict

# Date range to group by week
dates = [pendulum.parse('2022-12-06'), pendulum.parse('2022-11-02'), pendulum.parse('2022-10-15'), pendulum.parse('2022-10-01')]

# Create a defaultdict to store the dates by week
date_groups = {}

# Parse each date and add it to the appropriate week group
for date in dates:
    if date_groups.get(date.week_of_year) == None : 
        date_groups[date.week_of_year] = []
    date_groups[date.week_of_year].append(date.format("YYYY-MM-DD"))

# Print the groups of dates
print(date_groups)