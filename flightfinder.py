import json
import time

import requests

import globals


class finder:

    def __init__(self, originCountry="US", currency="USD", locale="en-US",
                 rootURL="https://skyscanner-skyscanner-flight-search-v1.p.rapidapi.com"):
        self.session = requests.Session()
        self.currency = currency
        self.locale = locale
        self.rootURL = rootURL
        self.originCountry = originCountry
        self.airports = {}
        self.quotes = []
        self.places = []
        self.carriers = {}

    def setHeaders(self, headers):
        self.headers = headers
        self.createSession()

    def createSession(self):
        self.session.headers.update(self.headers)
        return self.session

    def browseQuotes(self, source, destination, date, shouldPrint = True):
        quoteRequestPath = "/apiservices/browsequotes/v1.0/"
        browseQuotesURL = self.rootURL + quoteRequestPath + self.originCountry + "/" + self.currency + "/" + self.locale + "/" + source + "/" + destination + "/" + date.strftime(
            "%Y-%m-%d")
        response = self.session.get(browseQuotesURL)
        globals.callCount += 1
        if globals.pause==1:
            time.sleep(60)
        if globals.callCount % 45 == 0:
            globals.pause=1
            time.sleep(60)
        #print("i'm getting here")
        # response = requests.request("GET", url = browseQuotesURL, headers = self.headers)
        resultJSON = json.loads(response.text)
        if "You have exceeded the rate limit per minute for your plan, BASIC, by the API provider" in response.text:
            globals.pause=1
            time.sleep(60)
        globals.pause=0
        if "Quotes" in resultJSON:
            self.quotes.append(resultJSON["Quotes"])
            # self.quotes.append(resultJSON["Carriers"]["Name"])
            for Places in resultJSON["Places"]:
                # Add the airport in the dictionary.
                self.airports[Places["PlaceId"]] = Places["Name"]
            # robert adding this bit
        if "Carriers" in resultJSON:
            for Carriers in resultJSON["Carriers"]:
                self.carriers[Carriers["CarrierId"]] = Carriers["Name"]
            # end
            if (shouldPrint):
                self.printResult(resultJSON, date)


    def printResult(self, resultJSON, date):
        for Quotes in resultJSON["Quotes"]:
            source = Quotes["OutboundLeg"]["OriginId"]
            dest = Quotes["OutboundLeg"]["DestinationId"]
            # print("%s --> to  -->%s" %(origin,destination))
            # Look for Airports in the dictionary                
            print(date.strftime("%d-%b %a") + " | " + "%s  --> %s" % (self.airports[source], self.airports[dest]) + " | " + "%s USD" % Quotes["MinPrice"])

    def getQuotes(self):
        return self.quotes

    def getAirports(self):
        return self.airports

    def getCarriers(self):
        return self.carriers
