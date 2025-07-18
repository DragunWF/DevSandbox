water_lilies = 1
days = 48
water_lilies_by_day = [water_lilies]

for i in range(days - 1):
    water_lilies *= 2
    water_lilies_by_day.append(water_lilies)

# 140737488355328 Water Lilies
print(f"Water lilies at day 48 (full): {water_lilies}")
# 47 Days
print(f"Number of days for water lilies to take half of the lake: {water_lilies_by_day.index(water_lilies // 2) + 1}")
