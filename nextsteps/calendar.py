from icalendar import Calendar, Event
from datetime import datetime
from typing import Iterable


def export_ical(deadlines: Iterable[str]) -> bytes:
    cal = Calendar()
    cal.add('prodid', '-//Legal Lens//iCal Export//EN')
    cal.add('version', '2.0')
    for d in deadlines:
        try:
            # naive parse: dd/mm/yyyy or dd-mm-yyyy
            parts = d.replace('-', '/').split('/')
            if len(parts) == 3:
                day, month, year = map(int, parts)
                if year < 100:
                    year += 2000
                ev = Event()
                ev.add('summary', 'Legal Deadline')
                ev.add('dtstart', datetime(year, month, day))
                ev.add('dtend', datetime(year, month, day))
                cal.add_component(ev)
        except Exception:
            continue
    return cal.to_ical()
