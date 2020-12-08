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
    parser.add_argument('-v', '--version', action='version', version='0.0.1')
    args = parser.parse_args()
    print(args)
    if args.friendcode:
        if re.match(r'\d{4}-\d{4}-\d{4}', args.friendcode[0]) is not None:
            roomID = getRoomIDByFC(args.friendcode[0])
            parseRoom(roomID, args.refresh)
        else:
            print('Format "XXXX-XXXX-XXXX" required', file=sys.stderr)
            exit(1)
    elif args.name:
        roomID = getRoomIDByName(args.name[0])
        parseRoom(roomID, args.refresh)
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


def getRoomIDByName(name):
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
                return getRoomIDByFC(inamefc[0])
            else:
                print('Name not found', file=sys.stderr)
                exit(1)
        except IndexError:
            print('Error: Given name conflicts with website data', file=sys.stderr)
            exit(1)


def getRoom(roomID):
    with urllib.request.urlopen(f'https://wiimmfi.de/stats/mkw/room/{roomID}') as response:
        html = response.read().decode('utf-8')
        isr = html.find(roomID) - 8
        ier = html.find('</table>', isr)
        return html[isr:ier]


def inputNumber(inamefc):
    number = input('Number: ')
    if number.isdigit():
        if int(number) < len(inamefc):
            return getRoomIDByFC(inamefc[int(number)])
    else:
        print('invalid input, try again')
        inputNumber(inamefc)


def parseRoom(roomID, refresh):
    url = rf'https://wiimmfi.de/stats/mkw/room/{roomID}'
    tables = pandas.read_html(url, header=1, encoding='utf-8')  # Returns list of all tables on page
    table = tables[0]  # Select table of interest
    vr_avg, br_avg = '—', '—'
    if str(table['versuspoints'][0]).isdigit() and str(table['battlepoints'][0]).isdigit():
        vr_avg, br_avg = 0, 0
        for vr, br in zip(table['versuspoints'], table['battlepoints']):
            try:
                vr_avg += vr
                br_avg += br
            except TypeError:
                vr_avg += 5000
                br_avg += 5000
        vr_avg = round(vr_avg / len(table['versuspoints']))
        br_avg = round(br_avg / len(table['battlepoints']))
    loginregion = '-'
    for i in range(0, len(table['role'])):
        if 'HOST' in table['role'][i]:
            loginregion = table['loginregion'][i]
            break
    for lr in table['loginregion']:
        if lr != loginregion:
            loginregion = '—'
    table = table.append({'friend code': 'Average', 'role': '—', 'loginregion': loginregion, 'room,match': table['room,match'][0], 'world': '—', 'connfail': '—', 'versuspoints': vr_avg, 'battlepoints': br_avg, 'Mii name': '—'}, ignore_index=True)
    print(table)
    if refresh:
        try:
            time.sleep(10)
            sys.stdout.write('\x1B[1A\x1B[2K' * (len(table.index) + 1))
            sys.stdout.flush()
            parseRoom(roomID, refresh)
        except KeyboardInterrupt:
            print(' Exiting...')
            return table
    return table


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print(' Exiting...')
        exit(130)
