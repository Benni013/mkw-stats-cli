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
            roomID = getRoomIDByFC(args.friendcode[0])
            parseRoom(roomID, args.friendcode[0], args.refresh)
        else:
            print('Format "XXXX-XXXX-XXXX" required', file=sys.stderr)
            exit(1)
    elif args.name:
        fc = getFcByName(args.name[0])
        roomID = getRoomIDByFC(fc)
        parseRoom(roomID, fc, args.refresh)
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


def parseRoom(roomID, fc, refresh):
    url = rf'https://wiimmfi.de/stats/mkw/room/{roomID}'
    tables = pandas.read_html(url, header=1, encoding='utf-8')  # Returns list of all tables on page
    table = tables[0]  # Select table of interest

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
    loginregion = '—'
    for i in range(0, len(table['role'])):
        if 'HOST' in table['role'][i]:
            loginregion = table['loginregion'][i]
            break
    for lr in table['loginregion']:
        if lr != loginregion:
            loginregion = '—'

    # calculate max loss and max gain rating
    playerIndex = table[table['friend code'] == fc].index.item()
    playerVR = table.iloc[playerIndex]['versuspoints']
    playerBR = table.iloc[playerIndex]['battlepoints']
    minVR, maxVR, minBR, maxBR = 0, 0, 0, 0
    for i in range(0, len(table)):
        if i != playerIndex:
            minVR -= calcVR(table.iloc[i]['versuspoints'], playerVR)
            maxVR += calcVR(playerVR, table.iloc[i]['versuspoints'])
            minBR -= calcVR(table.iloc[i]['battlepoints'], playerBR)
            maxBR += calcVR(playerBR, table.iloc[i]['battlepoints'])

    # output data
    table = table.append({'friend code': 'Max loss', 'role': table['role'].iloc[playerIndex], 'loginregion': table['loginregion'].iloc[playerIndex], 'room,match': table['room,match'].iloc[playerIndex], 'world': table['world'].iloc[playerIndex], 'connfail': table['connfail'].iloc[playerIndex], 'versuspoints': minVR, 'battlepoints': minBR, 'Mii name': table['Mii name'].iloc[playerIndex]}, ignore_index=True)
    table = table.append({'friend code': 'Max gain', 'role': table['role'].iloc[playerIndex], 'loginregion': table['loginregion'].iloc[playerIndex], 'room,match': table['room,match'].iloc[playerIndex], 'world': table['world'].iloc[playerIndex], 'connfail': table['connfail'].iloc[playerIndex], 'versuspoints': maxVR, 'battlepoints': maxBR, 'Mii name': table['Mii name'].iloc[playerIndex]}, ignore_index=True)
    table = table.append({'friend code': 'Average', 'role': '—', 'loginregion': loginregion, 'room,match': table['room,match'].iloc[playerIndex], 'world': '—', 'connfail': '—', 'versuspoints': vr_avg, 'battlepoints': br_avg, 'Mii name': '—'}, ignore_index=True)
    print(table)

    if refresh:
        try:
            time.sleep(10)
            sys.stdout.write('\x1B[1A\x1B[2K' * (len(table.index) + 1))
            sys.stdout.flush()
            parseRoom(roomID, fc, refresh)
        except KeyboardInterrupt:
            print(' Exiting...')
            return table
    return table


# vr function from http://wiki.tockdom.com/wiki/Player_Rating
def calcVR(Pw, Pl):
    D = Pl - Pw
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
