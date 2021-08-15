import calendar
import concurrent.futures
import datetime
import os
import smtplib
import ssl
import time
import sys
import subprocess
import pandas as pd
import pymongo
import flightfinder as ff
import globals

step = ""


def Convert(a):
    it = iter(a)
    res_dct = dict(zip(it, it))
    return res_dct


def updateStep(step):
    globals.statusVar = "Status of running job for destination " + globals.currentDestination + ": " + step
    print(globals.statusVar)


def findDay(dd, dLeavingDate):
    dd = dd.lower()
    dActualDay = calendar.day_name[dLeavingDate.weekday()].lower()
    if dd != dActualDay:
        while dd != calendar.day_name[dLeavingDate.weekday()].lower():
            dLeavingDate = dLeavingDate + datetime.timedelta(days=1)
    return dLeavingDate


def main(paramDict, destination_array):
    updateStep("storing variables...")

    keyDict = {
        'clientU': "<insert mongoDB username here>",
        'clientP': "<insert mongoDB password here>",
        'password': "<insert outgoing email password here>"
    }
    source_array = paramDict.get('source_array')
    steps_days = int(paramDict.get('steps_days'))
    reduceDays = int(paramDict.get('reduceDays'))
    extendDays = int(paramDict.get('extendDays'))
    dLeavingDate = paramDict.get('dLeavingDate')
    datesFlexible = paramDict.get('datesFlexible')
    email_recipient = paramDict.get('recipient_email')
    direct = paramDict.get('direct')
    recentQuotes = paramDict.get('recentQuotes')
    if datesFlexible:
        daysForward = int(paramDict.get('daysForward'))
        dd = paramDict.get('dd')
        strict = paramDict.get('strict')
    else:
        daysForward = 0
        strict = 0
        dd = ''

    # calculations and changes
    stayMin = steps_days - reduceDays
    stayMax = steps_days + extendDays
    dLeavingDate = datetime.datetime.strptime(dLeavingDate, "%Y-%m-%d")
    end_period = dLeavingDate + datetime.timedelta(days=steps_days)
    updateStep("connecting to database...")

    rapidapi_key = "<insert key here>"  # Your RapidAPI key
    # ae922034c6mshbd47a2c270cbe96p127c54jsnfec4819a7799

    headers = {
        'x-rapidapi-host': "skyscanner-skyscanner-flight-search-v1.p.rapidapi.com",
        'x-rapidapi-key': rapidapi_key
    }

    rootURL = "https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"
    originCountry = "US"
    currancy = "USD"
    locale = "en-US"
    globals.PID = os.getpid()

    airports = {}
    carriers = {}

    # authdb = "admin"
    clientU = keyDict.get('clientU')
    clientP = keyDict.get('clientP')
    client = pymongo.MongoClient(
        f"mongodb+srv://{clientU}:{clientP}@cluster0.skh8q.mongodb.net/SkyScanner?retryWrites=true&w=majority", 27017)
    db = client.admin
    serverStatus = db.command("serverStatus")
    print(serverStatus)

    updateStep("formatting database...")

    database = client['SkyScanner']
    mdbOutgoing = database['outgoingTable']
    mdbPlaces = database['placesTable']
    mdbIncoming = database['incomingTable']

    # check if you're up next
    queue = database['queue']
    queueSpot = {str(globals.PID): datetime.datetime.today().strftime("%y-%m-%d %H")}
    queue.insert_one(queueSpot)
    updateStep("waiting to be queued...")
    waiting = 1
    while waiting:
        cursor = queue.find()
        count = 0
        for doc in cursor:
            if not waiting:
                continue
            for key, value in doc.items():
                if key == '_id':
                    continue
                if not waiting:
                    continue
                if key == str(globals.PID):
                    if count == 0:
                        waiting = 0
                        continue
                count = count + 1
                difference = (datetime.datetime.today() - datetime.datetime.strptime(value,
                                                                                     "%y-%m-%d %H")).total_seconds()
                if divmod(difference, 3600)[0] > 1:
                    queue.delete_one(doc)
            if count != 0: updateStep("waiting to be queued, currently " + str(count - 1) + " in front of you...")
        cursor.rewind()
        if waiting:
            time.sleep(30)

    mdbOutgoing.drop()
    mdbPlaces.drop()
    mdbIncoming.drop()

    outgoing_flight_finder = ff.finder()
    outgoing_flight_finder.setHeaders(headers)

    incoming_flight_finder = ff.finder()
    incoming_flight_finder.setHeaders(headers)

    # All dates are YYYY-DD-MM
    source_begin_date = dLeavingDate.strftime("%Y-%m-%d")  # The begining of your outwards journy
    source_end_date = (dLeavingDate + datetime.timedelta(days=daysForward)).strftime("%Y-%m-%d")
    destination_begin_date = end_period.strftime("%Y-%m-%d")  # The begining of your inwards journy
    destination_end_date = (end_period + datetime.timedelta(days=daysForward)).strftime("%Y-%m-%d")

    processing_start = time.time()

    daterange_source = pd.date_range(source_begin_date, source_end_date)
    daterange_destination = pd.date_range(
        destination_begin_date, destination_end_date)

    updateStep("gathering outgoing quotes...")

    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for single_date in daterange_source:
            for destination in destination_array:
                for source in source_array:
                    if globals.quitVar == 1: quit()
                    request_start = time.time()
                    executor.submit(outgoing_flight_finder.browseQuotes, source, destination, single_date)

    outgoingQuotes = outgoing_flight_finder.getQuotes()

    for quote in outgoingQuotes:
        for entry in quote:
            mdbOutgoing.insert_one(entry)

    airports.update(outgoing_flight_finder.getAirports())
    carriers.update(outgoing_flight_finder.getCarriers())

    updateStep("gathering incoming quotes...")

    # We reverse the arrays here
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        for single_date in daterange_destination:
            for destination in source_array:
                for source in destination_array:
                    if globals.quitVar == 1: quit()
                    request_start = time.time()
                    executor.submit(incoming_flight_finder.browseQuotes, source, destination, single_date)

    incomingQuotes = incoming_flight_finder.getQuotes()

    for quote in incomingQuotes:
        for entry in quote:
            if globals.quitVar == 1: quit()
            mdbIncoming.insert_one(entry)

    airports.update(incoming_flight_finder.getAirports())
    carriers.update(incoming_flight_finder.getCarriers())

    for key, value in carriers.items():
        if globals.quitVar == 1: quit()
        globals.carriers.append(value)

    print(globals.carriers)
    updateStep("Please select airlines you wish to exclude!")

    if not globals.runOnce:
        globals.pause = 1
        while globals.pause == 1:
            if globals.quitVar == 1: quit()
            time.sleep(1)
        globals.runOnce = 1

    finalList = []

    updateStep("finding best fit for criteria...")

    incCursor = mdbIncoming.find()
    incCursor.rewind()
    outCursor = mdbOutgoing.find()

    for incomingQuote in incCursor:
        # if direct: incomingQuotes["Direct"] != 'False':
        outCursor.rewind()
        for outgoingQuote in outCursor:
            if globals.quitVar == 1: quit()
            if direct and (incomingQuote["Direct"] is False or outgoingQuote["Direct"] is False):
                continue
            else:
                finalListElement = {}
                finalListElement["TotalPrice"] = incomingQuote["MinPrice"] + \
                                                 outgoingQuote["MinPrice"]
                tempCarrier1 = outgoingQuote["OutboundLeg"]["CarrierIds"]
                finalListElement["Carrier1"] = carriers[tempCarrier1[0]]
                tempCarrier2 = incomingQuote["OutboundLeg"]["CarrierIds"]
                finalListElement["Carrier2"] = carriers[tempCarrier2[0]]
                finalListElement["TakeOff1"] = airports[outgoingQuote["OutboundLeg"]["OriginId"]]
                finalListElement["Land1"] = airports[outgoingQuote["OutboundLeg"]["DestinationId"]]
                finalListElement["TakeOff2"] = airports[incomingQuote["OutboundLeg"]["OriginId"]]
                finalListElement["Land2"] = airports[incomingQuote["OutboundLeg"]["DestinationId"]]
                finalListElement["Date1"] = outgoingQuote["OutboundLeg"]["DepartureDate"]
                finalListElement["Date2"] = incomingQuote["OutboundLeg"]["DepartureDate"]
                outDate = datetime.datetime.strptime(finalListElement["Date1"], "%Y-%m-%dT%H:%M:%S")
                inDate = datetime.datetime.strptime(finalListElement["Date2"], "%Y-%m-%dT%H:%M:%S")
                dateRange = (inDate - outDate).days

                if not (dateRange < stayMin or dateRange > stayMax):
                    # check quote recency
                    if recentQuotes and (
                            (datetime.datetime.today() - datetime.datetime.strptime(outgoingQuote["QuoteDateTime"],
                                                                                    "%Y-%m-%dT%H:%M:%S")).days > 1 or
                            (datetime.datetime.today() - datetime.datetime.strptime(incomingQuote["QuoteDateTime"],
                                                                                    "%Y-%m-%dT%H:%M:%S")).days > 1):
                        continue
                    if strict and not dd == calendar.day_name[outDate.weekday()].lower():
                        continue
                    if finalListElement["Carrier1"] in globals.carriers_exclude or \
                            finalListElement["Carrier2"] in globals.carriers_exclude:
                        continue
                    finalList.append(finalListElement)

    mdbFinal = database['FinalDatabase']
    mdbFinal.drop()
    if finalList:
        for element in finalList:
            if globals.quitVar == 1: quit()
            mdbFinal.insert_one(element)
    if mdbFinal.count_documents({}) == 0:
        print("Nothing in finalList")
        updateStep("No flights for selected criteria found!")
    else:
        msg = ""
        for quote in mdbFinal.find().sort('TotalPrice').limit(10):
            msg = msg + ("\n*****\nOnwards: " + quote.get("Carrier1") + " " + quote.get("Date1").split("T")[
                0] + " " + quote.get(
                "TakeOff1") + " --> " + quote.get("Land1") + " \nReturn: " +
                         quote.get("Carrier2") + " " + quote.get("Date2").split("T")[0] + " " + quote.get(
                        "TakeOff2") + " --> " + quote.get(
                        "Land2") + " \n \t   | " + "%s US" % quote.get("TotalPrice"))

        updateStep("connecting to email server...")

        smtp_server = "smtp.gmail.com"
        port = 587  # For starttls
        sender_email = "<outgoing email here>"
        password = keyDict.get('password')
        # input("Type your password and press enter: ")

        # Create a secure SSL context
        context = ssl.create_default_context()
        # Try to log in to server and send email
        try:
            server = smtplib.SMTP(smtp_server, port)
            server.ehlo()  # Can be omitted
            server.starttls(context=context)
            server.login(sender_email, password)

            msg = "Subject: Flight Scraper (Destination:" + destination_array.pop().strip("-sky") + ")\n\n " + msg
            server.sendmail(sender_email, email_recipient, msg)
            print('sent email.....')
            updateStep("Done! Email with cheapest flights sent!")

        except Exception as e:
            # Print any error messages to stdout
            print(e)
            server.quit()
        finally:
            server.quit()
    queue.delete_one(queueSpot)
    globals.running = 0
    print("\nBenchmark Stats :")
    print("Time spent in program: %f seconds" % (time.time() - processing_start))
