# SalienSnake
A simple bot to play at the summer sale 2018 of Steam. Multi-Account Support.

# Requirements
* Python 3
* requests

# Usage

## Single account
```
python3 SalienSnake.py [--token <token>] [--planet <planet id>] [--list-planets] [--language <language>]
```
Arguments:
* **-t, --token (required)** - Token value from https://steamcommunity.com/saliengame/gettoken
* **-p, --planet** - Planet ID
* **-l, --list-planets** - Print list with planets names and IDs
* **--language** - Language (english, russian, etc.)

## Multi-account
```
python3 SalienSnake.py [--file <filename with extension>]
```
Arguments:
* **-f, --file (required)** - File with tokens one per line

Example of file with tokens:
```
00112233445566778899aabbccbbeeff
00112233445566778899aabbccddeeff
00112233445566778899aabbccbdeeff
```
Example of a run command:
```
python3 SalienSnake.py [--file <filename with extension>]
```

# License
GNU General Public License v3.0
