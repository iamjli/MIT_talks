# MIT_talks
A way to consolidate MIT talks and seminar listings. 

Features: 

 * Parses listserve emails for date, time, and location.
 * Automatically generates Google Calendar event with this information for talks, seminars, and thesis defense announcements. 
 * If multiple emails were went for the same event, only one appears in Google Calendar (this works just okay).
 * Makes titles easier to read. 

Example: [mitml](https://calendar.google.com/calendar?cid=bGEzaXQ4NGZsM290azlyNGpqb2VncGEzNWNAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)


# Calendars

[CSAIL-seminars](https://calendar.google.com/calendar?cid=bHEzYjhoMGRsOGJpMGszNDkzdGh0M2pyOGNAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)
[bestudents](https://calendar.google.com/calendar?cid=ZmllNjZza2w0YjhkcmZkYm1hbDc2NTZrb2dAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)
[mitml](https://calendar.google.com/calendar?cid=ZmllNjZza2w0YjhkcmZkYm1hbDc2NTZrb2dAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)
[stats-events](https://calendar.google.com/calendar?cid=ZHV2ZWtwMXNhZWJuaG1raGc3aWJ1OGY5ZWdAZ3JvdXAuY2FsZW5kYXIuZ29vZ2xlLmNvbQ)


# Run 

`python update_calendar.py`


# Downloads

## Stanford CoreNLP

`wget http://nlp.stanford.edu/software/stanford-corenlp-full-2018-02-27.zip`

Then unzip. Then follow instructions for installing [SUTime wrapper](https://github.com/FraBle/python-sutime).
