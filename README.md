# RSS Archiver
[WIP] Download and archive RSS feeds to Wayback Machine. Save a list of archived feed in locad db. I have little idea what I am doing. This is my learn to code project. Suggestion and comment are welcome and apricciated.

# To-do
- Implement a way to use Wayback Machine API (S3 Keys)
- Option to trigger saving outlinks from RSS links. Don't save outlinks to archive.db
- Find a way to better orginize local archive.db
- Make sure rss_feeds table should only allow unique entries.
- Use rss_feeds table in archive.db to retrive list of links.
- Check if the links is already archived on Wayback Machine. Better yet, if it isn't archived during specified timetable (last 7 days, 30 days...) trigger archving.
- Make custom timetables for retriving new feed for every rss link. For example, don't download feed if it was downloaded 1 hour, 1 day... ago. Useful for feeds that only post few times per month or less, so that the feed server doesn't get unnecesary traffic.
