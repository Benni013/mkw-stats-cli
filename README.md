# wiimmfi-cli
command line interface to display the stats of a wiimmfi room in Mario Kart Wii

- [REQUIREMENTS](#requirements)
- [USAGE](#usage)

## Requirements
* Python version 3.6 or newer
#### Python libraries
* pandas

## Usage
`./wiimmfi.py (-fc FRIENDCODE | -n NAME) [-r] [-h] [-v]`

| option (short) | option (long)               | description                        |
|----------------|-----------------------------|------------------------------------|
|  `-h`          |  `--help`                   | print help message                 |
|  `-v`          |  `--version`                | print program's version number     |
|  `-fc`         |  `--friendcode FRIENDCODE`  | set friend code                    |
|  `-n`          |  `--name NAME`              | set name                           |
|  `-r`          |  `--refresh`                | set automatic refresh (every 10s)  |
