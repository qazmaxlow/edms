import datetime

class Company:
    def __init__(self):
        self.date=[]
        self.user=[]
        self.User_list=[]
        self.csv=[]
    def total_action(self,user,day,timeslot):
        if user in self.user:
            user_index=self.user.index(user)
            return self.User_list[user_index].total_action(day,timeslot)
        else:
            return 0
    def user_daily_total_action(self,user,time_range,day):
        if user in self.user:
            user_index=self.user.index(user)
            return self.User_list[user_index].daily_total_action(day,time_range)
        else:
            return 0
    def user_period_total_action(self,user,time_range,start_date,end_date):
        if user in self.user:
            user_index=self.user.index(user)
            return self.User_list[user_index].period_total_action(time_range,start_date,end_date)
        else:
            return 0
    def add_user(self,user):
        if user in self.user:#check duplicate
            return
        else:
            self.user.append(user)
            self.User_list.append(User(user))
    def csv_append(self,record):
        user=record[1].strip()
        if not user:
            user=record[0]
        action=record[2]
        timeslot=record[3]
        date=record[4]
        self.csv.append(record)
        self.add_day(date)
        self.add_user(user)
        user_index=self.user.index(user)
        self.User_list[user_index].add_action(action,timeslot,date)
    def add_day(self,date):
        if date not in self.date:
            self.date.append(date)
    def sort_user_by_day(self,day,time_range):
        sort_action_by_day=[]
        sorted_User_list=[]
        for user in self.User_list:
            sort_action_by_day.append(user.daily_total_action(day,time_range))
        sort_action_by_day.sort(reverse=True)
        for action in sort_action_by_day:
            for user in self.User_list:
                if (user.daily_total_action(day,time_range)==action):
                    if user not in sorted_User_list:
                        sorted_User_list.append(user)
        return sorted_User_list
    def sort_user_by_period(self,time_range,start,end):
        sort_action_by_period=[]
        sorted_User_list=[]
        for user in self.User_list:
            sort_action_by_period.append(user.period_total_action(time_range,start,end))
        sort_action_by_period.sort(reverse=True)
        for action in sort_action_by_period:
            for user in self.User_list:
                if (user.period_total_action(time_range,start,end)==action):
                    if user not in sorted_User_list:
                        sorted_User_list.append(user)
        return sorted_User_list



class User:
    def __init__(self,username):
        self.sorted=0
        self.name=username
        self.trail_day=[]
        self.Trail_day=[]
    def add_day(self,day):
        if day in self.trail_day:
            return
        else:
            self.trail_day.append(day)
            self.Trail_day.append(Day(day))
    def add_action(self,action,timeslot,date):
        self.add_day(date)
        day_index=self.trail_day.index(date)
        self.Trail_day[day_index].add_action(action,timeslot,date)
    def total_action(self,day,timeslot):
        if day not in self.trail_day:
            return 0
        day_index=self.trail_day.index(day)
        return self.Trail_day[day_index].total_action(timeslot)
    def daily_total_action(self,day,time_range):
        action=0
        for time in time_range:
            action += self.total_action(day,time)
        return action
    def period_total_action(self,time_range,start,end):
        current=start
        action=0
        while current<=end:
            action+=self.daily_total_action(current,time_range)
            current+=datetime.timedelta(days=1)
        return action



class Day:
    def __init__(self,day):
        self.day=day
        self.timeslot=[0,1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,16,17,18,19,20,21,22,23]
        self.Timeslot_list=[]
        for time in self.timeslot:
            self.Timeslot_list.append(Timeslot(time))
    def add_action(self,action,timeslot,date):
        time_index=self.timeslot.index(timeslot)
        if action in self.Timeslot_list[time_index].action:
            return
        else:
            self.Timeslot_list[time_index].action.append(action)
    def total_action(self,timeslot):
        time_index=self.timeslot.index(timeslot)
        return self.Timeslot_list[time_index].total_action()


class Timeslot:
    def __init__(self,timeslot):
        self.timeslot=timeslot
        self.action=[]
    def total_action(self):
        return len(self.action)


class csv_vals_Append_Format:
    def __init__(self,csv_vals):
        self.trail_date = csv_vals[3].date()
        self.trail_hour = csv_vals[3].time().hour
        self.action = csv_vals[2]
        self.full_name = csv_vals[1]
        if (csv_vals[1] is None):
            self.full_name = csv_vals[0]
        self.acc_name=csv_vals[0]
