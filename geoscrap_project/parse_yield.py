
airport_list = ["airport1", "airport2", "airport3", "airport4"]

def parse_page_departure(airport, next_url, page_urls):

    print(airport, " / ", next_url)


    if not page_urls:
        return

    next_url = page_urls.pop()

    yield from parse_page_departure(airport, next_url, page_urls)

###################################
# PARSE EACH AIRPORT OF COUNTRY
###################################
def parse_schedule(next_airport, airport_list):

    ## GET EACH DEPARTURE PAGE

    departures_list = ["p1", "p2", "p3", "p4"]

    next_departure_url = departures_list.pop()
    yield parse_page_departure(next_airport,next_departure_url, departures_list)

    if not airport_list:
        print("no new airport")
        return

    next_airport_url = airport_list.pop()

    yield from parse_schedule(next_airport_url, airport_list)

next_airport_url = airport_list.pop()
result = parse_schedule(next_airport_url, airport_list)

for i in result:
    print(i)
    for d in i:
        print(d)