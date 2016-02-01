import urllib, json, arrow

def get_broadcast_data(day):
    url = "http://www.bbc.co.uk/radio4/programmes/schedules/fm/%s.json" % (day,)
    try:
        response = urllib.urlopen(url)
    except:
        print "Network error."
    try:
        data = json.loads(response.read())
    except:
        print "Invalid JSON returned."

    return data['schedule']['day']['broadcasts']

def parse_broadcasts(data):
    spans = []
    for broadcast in data:
        pid = broadcast['programme']['pid']
        title = broadcast['programme']['display_titles']['title']
        try:
            start = arrow.get(broadcast['start'])
            end = start.replace(seconds=broadcast['duration'])
            spans.append((start,end,pid,title))
        except:
            pass
    spans.sort()
    return spans

def get_shifted_program(spans):
    timeshift = arrow.now().replace(tzinfo="Europe/London")
    for span in spans:
        if span[0] < timeshift and span[1] > timeshift:
            return span

data = get_broadcast_data("yesterday")
data.extend(get_broadcast_data("today"))