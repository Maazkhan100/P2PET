
interval_in_mins = 10
num_of_participants = 1000
sessions_per_hour = 60 / interval_in_mins
tph = sessions_per_hour * num_of_participants
tps = tph / 3600

print(tps)