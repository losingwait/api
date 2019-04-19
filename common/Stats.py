from datetime import timedelta
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
    maxCount = 0
    for archive in archives:
        time = archive['arrived']
        left = archive['left']
        prevHour = time.hour
        while time < left:
            if time.weekday() not in time_stats:
                time_stats[time.weekday()] = {}
            if time.hour not in time_stats[time.weekday()]:
                time_stats[time.weekday()][time.hour] = 1
            else:
                time_stats[time.weekday()][time.hour] += 1
            if time_stats[time.weekday()][time.hour] > maxCount:
                maxCount = time_stats[time.weekday()][time.hour]
            prevHour = time.hour
            time += timedelta(hours=1)
        # checks if the left times hour was left out
        if prevHour is not left.hour:
            if left.hour not in time_stats[left.weekday()]:
                time_stats[left.weekday()][left.hour] = 1
            else:
                time_stats[left.weekday()][left.hour] += 1
            if time_stats[left.weekday()][left.hour] > maxCount:
                maxCount = time_stats[left.weekday()][left.hour]
        
    # assigns the time slots to the correct business buckets, effectively normalization
    for day, hours in time_stats.items():
        for hour, count in hours.items():
            ratio = count / maxCount
            # 4 different busy buckets
            if ratio >= 0.75:
                time_stats[day][hour] = 3
            elif ratio >= 0.50:
                time_stats[day][hour] = 2
            elif ratio >= 0.25:
                time_stats[day][hour] = 1
            else:
                time_stats[day][hour] = 0
            
    return time_stats
