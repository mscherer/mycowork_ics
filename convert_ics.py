#!/usr/bin/python3
import requests
import locale
from datetime import date, datetime, time
import re
from zoneinfo import ZoneInfo
from ics import Calendar, Event
import os
import hashlib

DOC_ID="1P2Y8euVlHhi8cacK-lJhlLg72hnTMMWPnmkZpd94gk4"
URL="https://docs.google.com/document/export"

OUTPUT = 'mycowork.ics'

payload = {
    "format": "txt",
    "id": DOC_ID,
    "includes_info_params": 'true',
    "usp": "sharing",
}


def convert_hour(t):
    h,m = t.upper().split('H')
    if not m:
        m = '0'
    return time(int(h), int(m))

def convert_iso(day, t):
    tz = ZoneInfo('Europe/Paris')
    return datetime.combine(day, t, tz)

def convert_accent(s):
    convert = {
        'é':'e',
        'û':'u'
    }

    for c in convert.keys():
        s=s.replace(c, convert[c])
    return s.upper()[:3]

# should use a external lib, but months are not gonna change that often
locale.setlocale(locale.LC_TIME, "fr_FR.utf8")

months=[]
for i in range(1,13):
    m = date(2008, i, 1).strftime('%B')
    months.append({
            'abbr': convert_accent(m),
            'num': i
            })

days=[]
for i in range(1,8):
    m = date(2008, 11, i).strftime('%A')
    days.append(convert_accent(m))


year = int(datetime.utcnow().strftime('%Y'))
events = []

current_month = 0

r = requests.get(URL, params = payload)
for l in r.text.split("\n"):
    for m in months:
        if l.startswith(m['abbr']) and not '-' in l:
            if current_month > m['num'] and current_month != 0:
                year += 1
            current_month = m['num']

    for d in days:
        if l.startswith(d):
            day, event = l.split('-', 1)
            day = day.strip()[4:]
            day = int(re.search(r'^\d+', day).group())
            events.append({'date': date(year, current_month, day), 'event_raw': event.strip()})

if os.path.exists(OUTPUT):
    c = Calendar(open(OUTPUT).read())
elif "URL_ICS" in os.environ:
    ics = requests.get(os.environ['URL_ICS']).text
    c = Calendar(ics)
else:
    c = Calendar()

for e in events:
    d = e['date']
    heure, name = e['event_raw'].split(' ', 1)
    debut, fin = heure.split('-')
    debut_iso = convert_iso(d, convert_hour(debut))
    fin_iso = convert_iso(d, convert_hour(fin))

    uid = hashlib.md5((debut_iso.isoformat() + name).encode()).hexdigest()
    ev = Event(name=name,
               uid=uid,
               begin=debut_iso,
               end=fin_iso)
    c.events.add(ev)

with open(OUTPUT, 'w') as f:
    f.write(str(c))
