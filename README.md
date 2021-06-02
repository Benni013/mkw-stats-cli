# wiimmfi-cli
command-line interface to display the stats of a Wiimmfi room in Mario Kart Wii

* [REQUIREMENTS](#requirements)
* [USAGE](#usage)

## Requirements
* Python version 3.7.1 and above
#### Python libraries
* [pandas and its dependencies](https://pandas.pydata.org/docs/getting_started/install.html):
  * beautifulsoup4
  * html5lib or lxml
  * numexpr (recommended)
  * bottleneck (recommended)

## Usage
`./wiimmfi-cli.py (-fc FRIENDCODE | -n NAME) [-c COLUMNS] [--no-min] [--no-max] [--no-avg] [--no-color] [-r] [-h] [-v]`

| option (short) | option (long)               | description                                                                                                                                                                    |
|----------------|-----------------------------|--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
|  `-h`          |  `--help`                   | print help message                                                                                                                                                             |
|  `-v`          |  `--version`                | print program's version number                                                                                                                                                 |
|  `-fc`         |  `--friendcode FRIENDCODE`  | set friend code                                                                                                                                                                |
|  `-n`          |  `--name NAME`              | set name                                                                                                                                                                       |
|  `-c`          |  `--columns COLUMNS`        | select columns either comma separated ("x,y,z") or as a range ("x-z") or exclude columns either comma separated ("^x,y,z") or as a range ("^x-z") with values between 0 and 8  |
|                |  `--no-min`                 | hide "Max loss" row                                                                                                                                                            |
|                |  `--no-max`                 | hide "Max gain" row                                                                                                                                                            |
|                |  `--no-avg`                 | hide "Average rating" row                                                                                                                                                      |
|                |  `--no-color`               | disable colored output                                                                                                                                                         |
|  `-r`          |  `--refresh`                | set automatic refresh (every 10s)                                                                                                                                              |
