#!/usr/bin/python
import argparse
import re
import sys
import time
import urllib.request

import pandas


def main():
    parser = argparse.ArgumentParser(description='CLI MKWii Wiimmfi Statistics\n')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-fc', '--friendcode', help='use friend code', nargs=1)
    group.add_argument('-n', '--name', help='use name', nargs=1)
    parser.add_argument('-r', '--refresh', default=False, help='set automatic refresh (every 10s)', action='store_true')
    parser.add_argument('-v', '--version', action='version', version='0.0.2')
    args = parser.parse_args()
    print(args)
    if args.friendcode:
        if re.match(r'\d{4}-\d{4}-\d{4}', args.friendcode[0]) is not None:
            room_id = getRoomIDByFC(args.friendcode[0])
            parseRoom(room_id, args.friendcode[0], args.refresh)
        else:
            print('Format "XXXX-XXXX-XXXX" required', file=sys.stderr)
            exit(1)
    elif args.name:
        fc = getFcByName(args.name[0])
        room_id = getRoomIDByFC(fc)
        parseRoom(room_id, fc, args.refresh)
    else:
        parser.print_usage()


def getRoomIDByFC(fc):
    with urllib.request.urlopen('https://wiimmfi.de/stats/mkw') as response:
        html = response.read().decode('utf-8')
        ifc = html.find(fc)
        if ifc != -1:
            isid = html.rfind('<tr id="', 0, ifc) + 8
            ieid = html.find('"', isid)
            if isid != -1 and ieid != -1:
                return html[isid:ieid]
            else:
                print('An error occurred', file=sys.stderr)
                exit(1)
        else:
            print('Friend code not found', file=sys.stderr)
            exit(1)


def getFcByName(name):
    with urllib.request.urlopen('https://wiimmfi.de/stats/mkw') as response:
        html = response.read().decode('utf-8')
        iname = []
        for match in re.finditer(name, html):
            s = match.start()
            e = match.end()
            iname.append((s, e))
        inamefc = []
        try:
            if iname and len(iname) > 1:
                print('Input the correct corresponding number to the desired player')
                for i in range(0, len(iname)):
                    isname, _ = iname[i]
                    isidre = html.rfind('<tr class="tr', 0, isname)
                    inamefc.append(re.findall(r'\d{4}-\d{4}-\d{4}', html[isidre:isname])[0])
                    print(f'{i} for player "{name}" with friend code {inamefc[i]}')
                return inputNumber(inamefc)
            elif iname:
                isname, _ = iname[0]
                isidre = html.rfind('<tr class="tr', 0, isname)
                inamefc.append(re.findall(r'\d{4}-\d{4}-\d{4}', html[isidre:isname])[0])
                return inamefc[0]
            else:
                print('Name not found', file=sys.stderr)
                exit(1)
        except IndexError:
            print('Error: Given name conflicts with website data', file=sys.stderr)
            exit(1)


def inputNumber(inamefc):
    number = input('Number: ')
    if number.isdigit():
        if int(number) < len(inamefc):
            return inamefc[int(number)]
    else:
        print('invalid input, try again')
        inputNumber(inamefc)


def parseRoom(room_id, fc, refresh):
    url = rf'https://wiimmfi.de/stats/mkw/room/{room_id}'
    tables = pandas.read_html(url, header=1, encoding='utf-8')  # Returns list of all tables on page
    table = tables[0]  # Select table of interest
    extra_line_count = 0

    # calculate Average line
    vr_avg, br_avg = '—', '—'
    if str(table['versuspoints'][0]).isdigit() and str(table['battlepoints'][0]).isdigit():
        vr_avg, br_avg, guest_count = 0, 0, 0
        for vr, br, name in zip(table['versuspoints'], table['battlepoints'], table['Mii name']):
            try:
                vr_avg += vr
                br_avg += br
                if '1. ' in name and '2. ' in name:
                    guest_count += 1
                    vr_avg += 5000
                    br_avg += 5000
            except TypeError:
                vr_avg += 5000
                br_avg += 5000
        vr_avg = round(vr_avg / (len(table['versuspoints']) + guest_count))
        br_avg = round(br_avg / (len(table['battlepoints']) + guest_count))
    loginregion, host_index = '—', 0
    for i in range(0, len(table['role'])):
        if 'HOST' in table['role'][i]:
            loginregion = table['loginregion'][i]
            host_index = i
            break
    for lr in table['loginregion']:
        if lr != loginregion:
            loginregion = '—'

    # calculate max loss and max gain rating
    try:
        player_index = table[table['friend code'] == fc].index.item()
        player_vr = table.iloc[player_index]['versuspoints']
        player_br = table.iloc[player_index]['battlepoints']
        min_vr, max_vr, min_br, max_br = 0, 0, 0, 0
        for i in range(0, len(table)):
            try:
                if i != player_index and 'viewer' not in table[i]['role']:
                    min_vr -= calcVR(table.iloc[i]['versuspoints'], player_vr)
                    max_vr += calcVR(player_vr, table.iloc[i]['versuspoints'])
                    min_br -= calcVR(table.iloc[i]['battlepoints'], player_br)
                    max_br += calcVR(player_br, table.iloc[i]['battlepoints'])
            except TypeError:
                min_vr -= 0
                max_vr += 0
                min_br -= 0
                max_br += 0
        table = table.append({'friend code': 'Max loss', 'role': table['role'].iloc[player_index], 'loginregion': table['loginregion'].iloc[player_index], 'room,match': table['room,match'].iloc[player_index], 'world': table['world'].iloc[player_index], 'connfail': table['connfail'].iloc[player_index], 'versuspoints': min_vr, 'battlepoints': min_br, 'Mii name': table['Mii name'].iloc[player_index]}, ignore_index=True)
        table = table.append({'friend code': 'Max gain', 'role': table['role'].iloc[player_index], 'loginregion': table['loginregion'].iloc[player_index], 'room,match': table['room,match'].iloc[player_index], 'world': table['world'].iloc[player_index], 'connfail': table['connfail'].iloc[player_index], 'versuspoints': max_vr, 'battlepoints': max_br, 'Mii name': table['Mii name'].iloc[player_index]}, ignore_index=True)
        extra_line_count += 2
    except ValueError:
        print('The sought-after player is no longer in this room')

    # output data
    table = table.append({'friend code': 'Average', 'role': '—', 'loginregion': loginregion, 'room,match': table['room,match'].iloc[host_index], 'world': '—', 'connfail': '—', 'versuspoints': vr_avg, 'battlepoints': br_avg, 'Mii name': '—'}, ignore_index=True)
    extra_line_count += 1
    print(table)

    if refresh:
        try:
            time.sleep(10)
            sys.stdout.write('\x1B[1A\x1B[2K' * (len(table.index) + extra_line_count))
            sys.stdout.flush()
            parseRoom(room_id, fc, refresh)
        except KeyboardInterrupt:
            print(' Exiting...')
            return table
    return table


# vr function from http://wiki.tockdom.com/wiki/Player_Rating
def calcVR(P_Winner, P_Loser):
    D = P_Loser - P_Winner
    E = k(D)
    return round(E)


def f(x):
    if 0 <= x < 1:
        return 1 / 6 * (3 * x ** 3 - 6 * x ** 2 + 4)
    elif 1 <= x < 2:
        return 1 / 6 * (2 - x) ** 3
    else:
        return 0


def k(x):
    S = [0, 0, 0, 1, 8, 50, 125, 125, 125, 125]
    vr = 0
    for j in range(0, 9):
        vr += f(abs((x - 2) / 5000 - (j - 4))) * S[j]
    return vr


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' Exiting...')
        exit(130)
