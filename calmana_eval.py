from __future__ import print_function
import datetime
from dateutil import relativedelta
from datetime import date
import pickle
import os.path
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from argparse import ArgumentParser
import subprocess
import sys
import numpy as np
import matplotlib as mpl
# mpl.use('Agg')
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
font_path = "/usr/share/fonts/truetype/migmix/migmix-1p-regular.ttf"
font_prop = FontProperties(fname=font_path)
mpl.rcParams["font.family"] = font_prop.get_name()

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar']

def main():
    args = get_option()
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds = flow.run_local_server()
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    if args.year:
        tstr = str(args.year) + "-04-01 00:00:00"
        time_min = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S').isoformat() + 'Z'
        tstr = str(args.year + 1) + "-04-01 00:00:00"
        time_max = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S').isoformat() + 'Z'
    else:
        time_min = datetime.datetime.utcnow().isoformat() + 'Z' # 'Z' indicates UTC time
        time_max = time_min + datetime.timedelta(days=1)
    calendar_id = args.calendar
    recurrence = args.recurrence
    date_list = []
    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max,
                                        singleEvents=True, sharedExtendedProperty="recurrence_name="+str(recurrence),
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    if not events:
        print('No upcoming events found.')
    for event in events:
        start = get_tdatetime(event)
        date_list.append(start)
        print(start, event["summary"])

    ## Heron 
    arg_dates = ""
    tstr = datetime.datetime.strptime(time_min, "%Y-%m-%dT%H:%M:%SZ") - relativedelta.relativedelta(years=2)
    time_min = tstr.isoformat() + 'Z'
    tstr = datetime.datetime.strptime(time_min, "%Y-%m-%dT%H:%M:%SZ") + relativedelta.relativedelta(years=2)
    time_max = tstr.isoformat() + 'Z'

    events_result = service.events().list(calendarId=calendar_id, timeMin=time_min, timeMax=time_max,
                                        singleEvents=True, sharedExtendedProperty="recurrence_name="+str(recurrence),
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        start = get_tdatetime(event)
        date_time = datetime.datetime.strptime(start, '%Y-%m-%dT%H:%M:%S%z')
        date = date_time.strftime('%Y-%m-%d')
        arg_dates += date
        arg_dates += "\n"
    arg_dates += "EOF\n"

    list_cp = date_list.copy()
    heron1 = heron(arg_dates, list_cp, True, args)
    list_cp = date_list.copy()
    heron2 = heron(arg_dates, list_cp, False, args)

    # eval
    x=list(range(len(date_list)))
    list_cp = date_list.copy()
    y1 = real_eval(list_cp, args)
    list_cp = date_list.copy()
    y2 = eval(heron1, list_cp, True)
    list_cp = date_list.copy()
    y3 = eval(heron2, list_cp, False)

    # plot
    plt.plot(x, np.cumsum(y2), color = "red", label = "修正内容を考慮した場合")
    plt.plot(x, np.cumsum(y3), color = "green", label = "修正内容を考慮しない場合")
    plt.legend()
    plt.show()
    # plt.savefig('{}_{}_diff.png'.format(recurrence, args.year))

def get_tdatetime(event):
    start = event['start'].get('dateTime', event['start'].get('date'))
    if 'dateTime' in event['start']:
        return start
    else:
        return start + 'T00:00:00+09:00'

def real_eval(date_list, args):
    y = [0] * 366
    while True:
        if len(date_list) < 10:
            break
        result = date_list.pop(0)[:10]
        r_diff = (datetime.datetime.strptime(result, '%Y-%m-%d') - datetime.datetime.strptime(str(args.year) + '-04-01', '%Y-%m-%d')).days
        y[r_diff] = 1.5
    return y

def heron(arg_dates, date_list, real, args):
    heron = []
    while True:
        os.chdir('')
        command = "./target/release/heron forecast"
        # print(arg_dates)
        res = subprocess.run(command, shell=True, input=arg_dates, stdout=subprocess.PIPE, stderr=sys.stdout, text=True).stdout

        print(res[:-2])
        
        tstr = str(args.year) + "-04-01 00:00:00"
        limit_min = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.strptime(res, '%Y-%m-%dZ\n') < limit_min:
            continue
  
        tstr = str(args.year + 1) + "-04-01 00:00:00"
        limit_max = datetime.datetime.strptime(tstr, '%Y-%m-%d %H:%M:%S')
        if datetime.datetime.strptime(res, '%Y-%m-%dZ\n') > limit_max:
            break

        heron.append(res[:-2])

        str_list = list(arg_dates)
        if real:
            str_list.insert(-4, date_list.pop(0)[:10] + '\n')
            if not date_list:
                break
        else:
            str_list.insert(-4, res[:-2] + '\n')
        arg_dates = ''.join(str_list)    
        
    return heron

def idx_of_the_nearest(data, value):
    nearest = None
    ref = datetime.datetime.strptime(value, '%Y-%m-%dT%H:%M:%S+09:00')
    print(data)
    for i, d in enumerate(data):
        src = datetime.datetime.strptime(d, '%Y-%m-%d')
        diff = abs((src - ref).days)
        if nearest is None:
            idx = i
            nearest = diff
        else:
            if nearest > diff:
                idx = i
                nearest = diff
    return idx

def eval(forcasts, date_list, real):
    y = [0] * len(date_list)
    print("data    : ", len(date_list))
    print("forecast: ", len(forcasts))
    for i, e in enumerate(date_list):
        if real:
            if not forcasts:
                break
            y[i] = abs(datetime.datetime.strptime(forcasts.pop(0), '%Y-%m-%d') - datetime.datetime.strptime(e[:-6], '%Y-%m-%dT%H:%M:%S')).days
        else:
            if not forcasts:
                break
            idx = idx_of_the_nearest(forcasts, e)
            y[i] = abs(datetime.datetime.strptime(forcasts.pop(idx), '%Y-%m-%d') - datetime.datetime.strptime(e[:-6], '%Y-%m-%dT%H:%M:%S')).days
    return y

def get_option():
    argparser = ArgumentParser()
    argparser.add_argument('-c', '--calendar', type=str,
                           default="primary",
                           help='Google Calendar ID')
    argparser.add_argument('-y', '--year', type=int,
                           default=None,
                           help='get event year')
    argparser.add_argument('-r', '--recurrence', type=str,
                           default=None,
                           help='recurrence name')
    return argparser.parse_args()

if __name__ == '__main__':
    main()