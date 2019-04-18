import math

def getMachineStats(machines):
    # get the machine stats
    machine_stats = {}
    for machine in machines:
        if machine['machine_group_id'] not in machine_stats:
            machine_stats[machine['machine_group_id']] = {}
            machine_stats[machine['machine_group_id']]['total'] = 1
        else:
            machine_stats[machine['machine_group_id']]['total'] += 1
        if machine['in_use'] not in machine_stats[machine['machine_group_id']]:
            machine_stats[machine['machine_group_id']][machine['in_use']] = 1
        else:
            machine_stats[machine['machine_group_id']][machine['in_use']] += 1
    return machine_stats

def getUserStats(gym_users):
    # get the user stats
    user_stats = {}
    user_stats['total'] = 0
    user_stats['machine'] = 0
    user_stats['queued'] = 0
    for user in gym_users:
        user_stats['total'] += 1
        if 'machine_id' in user:
            user_stats['machine'] += 1
        if 'current_queue' in user:
            user_stats['queued'] +=1
    return user_stats

def getTimeStats(archives):
    # get the time stats
    time_stats = {}
    for archive in archives:
        print(archive)
        dayOfWeek = archive['arrived'].weekday()
        if dayOfWeek not in time_stats:
            time_stats[dayOfWeek] = {}

        timeDiff = archive['left'] - archive['arrived']
        hoursAtGym = math.ceil(timeDiff.total_seconds() / 3600)
        startingHour = archive['arrived'].hour
        print(startingHour)
        print(hoursAtGym)
        for hour in range(startingHour, startingHour + hoursAtGym):
            adjustedHour = ((hour - 1) % 24) + 1
            if adjustedHour not in time_stats[dayOfWeek]:
                time_stats[dayOfWeek][adjustedHour] = 1
            else:
                time_stats[dayOfWeek][adjustedHour] += 1
            # if its about to become the next day
            if adjustedHour is 24:
                dayOfWeek += 1
                if dayOfWeek not in time_stats:
                    time_stats[dayOfWeek] = {}
    print(time_stats)
    return time_stats
