from cProfile import label
from calendar import week
from enum import Enum
import pendulum
from collections import defaultdict
import pydash as py_
class CoatLength(Enum) :
    DAILY = "day",
    WEEKLY = "week",
    MONTHLY = "month"
    

test_data = [
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-10-25 16:50:04",
    "active_users":2,
    "all_pets":2,
    "all_users":3
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-10-26 16:50:04",
    "active_users":2,
    "all_pets":2,
    "all_users":3
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-11-27 16:50:04",
    "active_users":2,
    "all_pets":2,
    "all_users":5
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-11-28 16:50:04",
    "active_users":4,
    "all_pets":3,
    "all_users":5
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-11-29 16:50:04",
    "active_users":5,
    "all_pets":6,
    "all_users":10
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-11-30 16:50:04",
    "active_users":8,
    "all_pets":6,
    "all_users":10
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442145",
    "date":"2022-12-01 16:50:04",
    "active_users":8,
    "all_pets":9,
    "all_users":13
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442324",
    "date":"2022-12-02 16:50:04",
    "active_users":8,
    "all_pets":9,
    "all_users":13
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442643",
    "date":"2022-12-03 16:50:04",
    "active_users":9,
    "all_pets":10,
    "all_users":15
  },
  {
    "id":"450047d9-4dfe-4205-beab-a8a4d6442155",
    "date":"2022-12-04 16:50:04",
    "active_users":7,
    "all_pets":12,
    "all_users":15
  },
  {
    "id":"61a8ace5-28fa-404d-b418-436fdce74244",
    "date":"2022-12-05 15:57:40",
    "active_users":6,
    "all_pets":12,
    "all_users":21
  },
  {
    "id":"61a8ace5-28fa-404d-b418-436fdce74244",
    "date":"2022-12-06 15:57:40",
    "active_users":6,
    "all_pets":17,
    "all_users":21
  },
  {
    "id":"61a8ace5-28fa-404d-b418-436fdce74244",
    "date":"2022-12-07 15:57:40",
    "active_users":6,
    "all_pets":19,
    "all_users":28
  },
]
# Date range to group by week
# dates = [pendulum.parse('2022-12-06'), pendulum.parse('2022-11-02'), pendulum.parse('2022-10-15'), pendulum.parse('2022-10-01')]

# Create a defaultdict to store the dates by week
date_groups = {}

# Parse each date and add it to the appropriate week group
for object in test_data:
    group = pendulum.parse(object.get("date")).start_of("week").format("YYYY-MM-DD")
    if date_groups.get(group) == None :
        date_groups[group]= []
    date_groups[group].append(object)

statistics = {
    "labels" : [],
    "active_users_mean" : [],
    "active_users_min" : [],
    "active_users_max" : [],
    "all_users": [],
    "all_pets": [],
}

for key in date_groups.keys():
    print(key)
    print(len(date_groups[key]))
    statistics["labels"].append(key)
    statistics["active_users_mean"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "active_users")))
    statistics["all_pets"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "all_pets")))
    statistics["all_users"].append( "{0:.2f}".format(py_.mean_by(date_groups[key], "all_users")))
    statistics["active_users_max"].append( "{0:.2f}".format(py_.max_by(date_groups[key], "active_users")["active_users"]))
    statistics["active_users_min"].append( "{0:.2f}".format(py_.min_by(date_groups[key], "active_users")["active_users"]))
print(statistics)
# Print the groups of dates
# print(date_groups.keys())