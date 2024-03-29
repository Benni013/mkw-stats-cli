#!/usr/bin/env python3
import argparse
import re
import sys
import time
import urllib.request
from urllib.error import URLError

import pandas


class colors:
    reset = '\033[0m'
    bold = '\033[01m'
    dim = '\033[02m'
    italic = '\033[03m'
    underline = '\033[04m'
    slowblink = '\033[05m'
    fastblink = '\033[06m'
    invert = '\033[07m'
    hide = '\033[08m'
    strike = '\033[09m'

    class fg:
        black = '\033[30m'
        red = '\033[31m'
        green = '\033[32m'
        yellow = '\033[33m'
        blue = '\033[34m'
        magenta = '\033[35m'
        cyan = '\033[36m'
        white = '\033[37m'
        brightblack = '\033[90m'
        brightred = '\033[91m'
        brightgreen = '\033[92m'
        brightyellow = '\033[93m'
        brightblue = '\033[94m'
        brightmagenta = '\033[95m'
        brightcyan = '\033[96m'
        brightwhite = '\033[97m'

    class bg:
        black = '\033[40m'
        red = '\033[41m'
        green = '\033[42m'
        yellow = '\033[43m'
        blue = '\033[44m'
        magenta = '\033[45m'
        cyan = '\033[46m'
        white = '\033[47m'
        brightblack = '\033[100m'
        brightred = '\033[101m'
        brightgreen = '\033[102m'
        brightyellow = '\033[103m'
        brightblue = '\033[104m'
        brightmagenta = '\033[105m'
        brightcyan = '\033[106m'
        brightwhite = '\033[107m'


def main():
    parser = argparse.ArgumentParser(description='MKWii Statistics CLI\n')
    parser.add_argument('-v', '--version', action='version', version='0.2.1')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('-fc', '--friendcode', help='use friend code', nargs=1)
    group.add_argument('-n', '--name', help='use name', nargs=1)
    parser.add_argument('-c', '--columns', help='select columns either comma separated ("x,y,z") or as a range ("x-z") or exclude columns either comma separated ("^x,y,z") or as a range ("^x-z") with values between 0 and 8', nargs=1)
    parser.add_argument('--no-min', default=False, help='hide "Max loss" row', action='store_true')
    parser.add_argument('--no-max', default=False, help='hide "Max gain" row', action='store_true')
    parser.add_argument('--no-avg', default=False, help='hide "Average rating" row', action='store_true')
    parser.add_argument('--no-color', default=False, help='disable colored output', action='store_true')
    parser.add_argument('-r', '--refresh', default=False, help='set automatic refresh (every 10s)', action='store_true')
    args = parser.parse_args()
    # process user input
    selection = [0, 1, 2, 3, 4, 5, 6, 7, 8]
    disable = args.no_color, args.no_min, args.no_max, args.no_avg
    if args.columns:
        if re.match(r'^[0-8](,[0-8]){0,8}$', args.columns[0]) is not None:
            selection = [int(i) for i in list(args.columns[0].split(','))]
        elif re.match(r'^[0-8]-[0-8]$', args.columns[0]) is not None:
            start, end = args.columns[0].split('-')
            selection = list(range(int(start), int(end) + 1))
        elif re.match(r'^\^[0-8](,[0-8]){0,8}$', args.columns[0]) is not None:
            in_selection = [int(i) for i in list(args.columns[0][1:].split(','))]
            selection = list(set(selection) ^ set(in_selection))
        elif re.match(r'^\^[0-8]-[0-8]$', args.columns[0]) is not None:
            in_start, in_end = args.columns[0][1:].split('-')
            selection = list(set(selection) ^ set(range(int(in_start), int(in_end) + 1)))
        else:
            print('invalid selection input', file=sys.stderr)
            sys.exit(1)
    if args.friendcode:
        if re.match(r'^\d{4}-\d{4}-\d{4}$', args.friendcode[0]) is not None:
            try:
                room_id = getRoomIDByFC(args.friendcode[0])
            except URLError:
                print('No connection can be established to Wiimmfi', file=sys.stderr)
                sys.exit(1)
            out(room_id, args.friendcode[0], selection, disable, args.refresh)
        else:
            print('Format "XXXX-XXXX-XXXX" required', file=sys.stderr)
            sys.exit(1)
    elif args.name:
        try:
            fc = getFcByName(args.name[0])
            room_id = getRoomIDByFC(fc)
        except URLError:
            print('No connection can be established to Wiimmfi', file=sys.stderr)
            sys.exit(1)
        out(room_id, fc, selection, disable, args.refresh)
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
            sys.exit(1)
    else:
        print('Friend code not found', file=sys.stderr)
        sys.exit(1)


def getFcByName(name):
    with urllib.request.urlopen('https://wiimmfi.de/stats/mkw') as response:
        html = response.read().decode('utf-8')
    iname, inamefc = [], []
    for match in re.finditer(name, html):
        s = match.start()
        e = match.end()
        iname.append((s, e))
    try:
        if iname and len(iname) > 1:
            output = 'Input the correct corresponding number to the desired player\n'
            for i in range(0, len(iname)):
                isname, _ = iname[i]
                isidre = html.rfind('<tr class="tr', 0, isname)
                inamefc.append(re.findall(r'\d{4}-\d{4}-\d{4}', html[isidre:isname])[0])
                output += f'{i} for player "{name}" with friend code {inamefc[i]}\n'
            print(output, end='')
            return inputNumber(inamefc)
        elif iname:
            isname, _ = iname[0]
            isidre = html.rfind('<tr class="tr', 0, isname)
            inamefc.append(re.findall(r'\d{4}-\d{4}-\d{4}', html[isidre:isname])[0])
            return inamefc[0]
        else:
            print('Name not found', file=sys.stderr)
            sys.exit(1)
    except IndexError:
        print('Given name conflicts with website data', file=sys.stderr)
        sys.exit(1)


# function to select player if wanted player name occurs multiple times
def inputNumber(inamefc, line_count=2):
    number = input('Number: ')
    if number.isdigit() and int(number) < len(inamefc):
        sys.stdout.write('\x1B[1A\x1B[2K' * (len(inamefc) + line_count))
        sys.stdout.flush()
        return inamefc[int(number)]
    else:
        print('invalid input, try again')
        inputNumber(inamefc, line_count + 2)


def parseRoom(room_id, fc, selection, no_rows):
    # read HTML table from Wiimmfi
    try:
        tables = pandas.read_html(rf'https://wiimmfi.de/stats/mkw/room/{room_id}', header=1, encoding='utf-8')
    except ValueError:
        print('The room does not exist', file=sys.stderr)
        sys.exit(1)
    table = tables[0]

    # calculate Average line
    vr_avg = br_avg = additional_players = 0
    for vr, br, name in zip(table['versuspoints'], table['battlepoints'], str(table['Mii name'])):
        if (vr != '—') and (br != '—'):
            vr_avg += int(vr)
            br_avg += int(br)
            if '1. ' in name and '2. ' in name:
                additional_players += 1
                vr_avg += 5000
                br_avg += 5000
        else:
            additional_players -= 1
    if vr_avg == 0 and br_avg == 0:
        vr_avg = br_avg = '—'
    else:
        vr_avg = round(vr_avg / (table.shape[0] + additional_players))
        br_avg = round(br_avg / (table.shape[0] + additional_players))

    # get host index
    ihost = 0
    for i in range(0, table.shape[0]):
        if 'HOST' in table['role'][i]:
            ihost = i
            break

    # calculate Max loss and Max gain line
    iplayer = imin = imax = -1
    extra_line_count = 1
    try:
        iplayer = table[table['friend code'] == fc].index.item()
        player_vr = int(table['versuspoints'][iplayer])
        player_br = int(table['battlepoints'][iplayer])
        min_vr = max_vr = min_br = max_br = 0
        for i in range(0, len(table)):
            # separate guest with space
            name = str(table['Mii name'][i])
            if '1. ' in name and '2. ' in name:
                table.loc[table['Mii name'] == name, 'Mii name'] = name.replace('2. ', ' 2. ')
            # actual calculation
            try:
                if not any(x in table['role'][i] for x in ['viewer', 'connect']):
                    if '1. ' in name and '2. ' in name:
                        min_vr -= calcVR(5000, player_vr)
                        max_vr += calcVR(player_vr, 5000)
                        min_br -= calcVR(5000, player_br)
                        max_br += calcVR(player_br, 5000)
                    if i != iplayer:
                        min_vr -= calcVR(int(table['versuspoints'][i]), player_vr)
                        max_vr += calcVR(player_vr, int(table['versuspoints'][i]))
                        min_br -= calcVR(int(table['battlepoints'][i]), player_br)
                        max_br += calcVR(player_br, int(table['battlepoints'][i]))
            except ValueError:
                pass
        table = table.append({'friend code': 'Max loss', 'role': table['role'][iplayer], 'loginregion': table['loginregion'][iplayer], 'room,match': table['room,match'][iplayer], 'world': table['world'][iplayer], 'connfail': table['connfail'][iplayer], 'versuspoints': min_vr, 'battlepoints': min_br, 'Mii name': table['Mii name'][iplayer]}, ignore_index=True)
        table = table.append({'friend code': 'Max gain', 'role': table['role'][iplayer], 'loginregion': table['loginregion'][iplayer], 'room,match': table['room,match'][iplayer], 'world': table['world'][iplayer], 'connfail': table['connfail'][iplayer], 'versuspoints': max_vr, 'battlepoints': max_br, 'Mii name': table['Mii name'][iplayer]}, ignore_index=True)
        imin = table[table['friend code'] == 'Max loss'].index.item()
        imax = table[table['friend code'] == 'Max gain'].index.item()
    except ValueError:
        if not (vr_avg == '—' and br_avg == '—'):
            print('The wanted player is no longer in this room')
            extra_line_count += 1
    table = table.append({'friend code': 'Average rating', 'role': '—', 'loginregion': table['loginregion'][ihost], 'room,match': table['room,match'][ihost], 'world': '—', 'connfail': '—', 'versuspoints': vr_avg, 'battlepoints': br_avg, 'Mii name': '—'}, ignore_index=True)
    iavg = table[table['friend code'] == 'Average rating'].index.item()

    # output table
    output = table.iloc[:, selection].to_string().splitlines()
    no_color, no_min, no_max, no_avg = no_rows
    # This part of the code is a complete mess, but it works.
    for i in range(0, len(output)):
        # If the player is no longer in the room, iplayer will be equal to -1, so the header of the table will be blue.
        # If the player is in a private room, imax will be -1 but iplayer won't be -1 , so the header of the table will be green. It's not a bug, it's a feature.
        if i - 1 == iplayer:
            print(f'{colors.fg.brightblue}{output[i]}{colors.reset}') if not no_color else print(output[i])
        elif i - 1 == imax:
            if not no_max:
                print(f'{colors.fg.green}{output[i]}{colors.reset}') if not no_color else print(output[i])
            else:
                extra_line_count -= 1
        elif i - 1 == imin:
            if not no_min:
                print(f'{colors.fg.red}{output[i]}{colors.reset}') if not no_color else print(output[i])
            else:
                extra_line_count -= 1
        elif i - 1 == iavg:
            if not no_avg:
                print(f'{colors.fg.yellow}{output[i]}{colors.reset}') if not no_color else print(output[i])
            else:
                extra_line_count -= 1
        else:
            print(output[i])
    return table.shape[0] + extra_line_count


# function to process the refresh option
def out(room_id, fc, selection, disable, refresh):
    line_count = parseRoom(room_id, fc, selection, disable)
    while refresh:
        try:
            time.sleep(10)
            sys.stdout.write('\x1B[1A\x1B[2K' * line_count)
            sys.stdout.flush()
            line_count = parseRoom(room_id, fc, selection, disable)
        except KeyboardInterrupt:
            print('\nExiting...')
            sys.exit(0)


# vr function from http://wiki.tockdom.com/wiki/Player_Rating
def calcVR(P_Winner, P_Loser):
    D = P_Loser - P_Winner
    E = k(D)
    return int(E)


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
    for j in range(0, 10):
        vr += f(abs((x - 2) / 5000 - (j - 4))) * S[j]
    return vr


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print('\nInterrupt signal received')
        sys.exit(130)
