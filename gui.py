import datetime
import threading
import time
import tkinter
import tkinter as tk
from tkinter import CENTER, SUNKEN, ttk

import numpy as np
import globals
import planner


def getCarriers():
    global list_items
    carriers=globals.carriers
    if carriers:
        list_items.set(carriers)


def setExclude():
    for i in listbox.curselection():
        if globals.quitVar == 1: quit()
        globals.carriers_exclude.append(listbox.get(i))
        window.update_idletasks()
    globals.pause=0


def setCurrentDestination(destination):
    globals.currentDestination = destination


def submitFunctions(inputVars, runDaily, status):
    status.grid(row=1, column=1, pady=20)
    globals.running = 1
    background(returnInputVars, (inputVars, runDaily))
    background(updateStatus, ())


def updateStatus():
    global tempVar
    global list_items
    while globals.running:
        if globals.quitVar == 1: quit()
        tempVar.set(globals.statusVar)
        if globals.pause:
            getCarriers()
        time.sleep(1)
        window.update_idletasks()


def background(func, args):
    th = threading.Thread(target=func, args=args)
    th.start()


def validate(date):
    global tempVar
    try:
        datetime.datetime.strptime(date, '%Y-%m-%d')
    except ValueError:
        tempVar.set("Error: Please enter the date in the format YYYY-MM-DD")
        status.configure(fg='red')
        globals.running = 0
        return 0
    return 1


def quitWindow():
    globals.quitVar = 1
    window.quit()


def returnInputVars(inputVars, runDaily):
    obFlightInfo = formatAirlines(outboundFlightList.get())
    ibFlightInfo = formatAirlines(inboundFlightList.get())
    varDict = {
        'steps_days': 0,
        'reduceDays': 0,
        'extendDays': 0,
        'dLeavingDate': '',
        'datesFlexible': 0,
        'daysForward': 0,
        'dd': '',
        'strict': 0,
        'source_array': obFlightInfo,
        'destination_array': ibFlightInfo,
        'recipient_email': email.get(),
        'direct': direct.get(),
        'recentQuotes': recentQuotes.get()
    }

    for i in range(len(inputVars)):
        if inputQuestions[4][3].get()==0 and i==5:
            break
        if globals.quitVar == 1: quit()
        try:
            var = inputVars[i].get()
        except:
            var = inputQuestions[i][3].get()
        varDict[inputQuestions[i][1]] = var

    if not validate(varDict.get('dLeavingDate')):
        exit()
    status.configure(fg='white')
    if runDaily.get():
        while not globals.quitVar:
            globals.running=1
            for destination in ibFlightInfo:
                setCurrentDestination(destination)
                destination_array = set()
                destination_array.add(destination)
                planner.main(varDict, destination_array)
                destination_array.clear()
            time.sleep(3600)
    else:
        for destination in ibFlightInfo:
            setCurrentDestination(destination)
            destination_array = set()
            destination_array.add(destination)
            planner.main(varDict, destination_array)
            destination_array.clear()
    if globals.pause:
        while globals.pause:
            time.sleep(1)
        globals.running=0
    else:
        globals.running=0


def formatAirlines(airlines):
    arr = airlines.split(',')
    arr[:] = [airline.upper() + '-sky' for airline in arr]
    setList = set(arr)
    return setList


window = tk.Tk()
window.configure(bg='#e3f1f1')
tempVar = tkinter.StringVar()
list_items = tkinter.StringVar()
list_items.set(globals.carriers)

window.title('Flight Finder')
# window.geometry('{}x{}'.format(1000, 1000))

headerFrame = tk.Frame(master=window, bg='#63c8e4')
for i in range(3):
    headerFrame.columnconfigure(i, weight=1)
inputFrame = tk.Frame(master=window, bg='#e3f1f1')
buttonFrame = tk.Frame(master=window, bg='#e3f1f1')

# window.grid_rowconfigure(1, weight=1)
# window.grid_columnconfigure(0, weight=1)

headerFrame.grid(row=0, sticky="new",rowspan=1)
inputFrame.grid(row=1, sticky="nw")
buttonFrame.grid(row=2, rowspan=1)

flightInfoFrame = tk.Frame(master=inputFrame, bg='#e3f1f1')
formFrame = tk.Frame(master=inputFrame, bg='#e3f1f1')
personalInfoFrame = tk.Frame(master=inputFrame, bg='#e3f1f1')
flightCodes = tk.Frame(master=flightInfoFrame, bg='#e3f1f1')
carrierFrame = tk.Frame(master=flightInfoFrame, bg='#e3f1f1')

flightInfoFrame.grid(row=0, columnspan=3, stick="n")
flightCodes.grid(row=0,column=0)
carrierFrame.grid(row=0,column=1)

outboundFlightList = tk.Entry(width=45, master=flightCodes, bd=0)
outboundLabel = tk.Label(master=flightCodes,
                         text="Enter airlines codes you may want to leave from (comma delimited 3 letter codes)",
                         bg='#e3f1f1')
outboundLabel.grid(row=0, column=0, pady=0, padx=10)
outboundFlightList.grid(row=0, pady=0, column=1)

inboundFlightList = tk.Entry(width=45, master=flightCodes,bd=0)
inboundLabel = tk.Label(master=flightCodes,
                        text="Enter airlines codes you may want to arrive at (comma delimited 3 letter codes)",
                        bg='#e3f1f1')
inboundLabel.grid(row=1, column=0, padx=10, pady=10, sticky="N")
inboundFlightList.grid(row=1, column=1, pady=10, sticky="N")

scrollbar = tk.Scrollbar(carrierFrame)

listbox = tkinter.Listbox(carrierFrame, selectmode=tk.MULTIPLE,listvariable=list_items,
                          yscrollcommand=scrollbar.set)
listbox.grid(row=1, column=2, sticky="nse", padx=(50, 0))
scrollbar.config(command=listbox.yview)
scrollbar.grid(row=1, column=3, columnspan=2, sticky='nse', rowspan=2)

inboundLabel = tk.Label(master=carrierFrame, text="Airline carriers to exclude", bg='#e3f1f1')
inboundLabel.grid(row=0, column=2, padx=(50,0), pady=5, sticky="ne", columnspan=3)

#listbox.insert(END, "Carrier List")


formFrame.grid(row=1, column=0, pady=10, sticky="N")
personalInfoFrame.grid(row=1, column=1, pady=10, padx=(15,15), sticky="N",columnspan=1)
label = tk.Label(master=personalInfoFrame, text="Enter recipient email address: ", bg='#e3f1f1')
label.grid(row=0, column=0, pady=3)
email = tk.Entry(width=30, master=personalInfoFrame,
                 bd=0)
email.grid(row=0, column=1, pady=3)

runDaily = tkinter.IntVar()
label = tk.Label(master=personalInfoFrame, text="Check to run daily in background: ", bg='#e3f1f1')
label.grid(row=1, column=0, pady=3)
checkBox = tk.Checkbutton(master=personalInfoFrame, variable=runDaily, bg='#e3f1f1')
checkBox.grid(row=1, column=1, pady=3)

direct = tkinter.IntVar()
label = tk.Label(master=personalInfoFrame, text="Check to limit to direct flights: ", bg='#e3f1f1')
label.grid(row=2, column=0, pady=3)
checkBox = tk.Checkbutton(master=personalInfoFrame, variable=direct, bg='#e3f1f1')
checkBox.grid(row=2, column=1, pady=3)

recentQuotes = tkinter.IntVar()
label = tk.Label(master=personalInfoFrame, text="Check to limit to recent quotes (within 1 day): ", bg='#e3f1f1')
label.grid(row=3, column=0, pady=3)
checkBox = tk.Checkbutton(master=personalInfoFrame, variable=recentQuotes, bg='#e3f1f1')
checkBox.grid(row=3, column=1, pady=3)

datesFlexible = tkinter.IntVar()
dd = tkinter.StringVar()
strict = tkinter.IntVar()

inputQuestions = [
    ["Desired trip duration (in days):", 'steps_days', 0],
    ["How many days are you willing to shorten the trip?", 'reduceDays', 0],
    ["How many days are you willing to extend the trip?", 'extendDays', 0],
    ["What day do you want to leave on? (YYYY-MM-DD)", 'dLeavingDate', 0],
    ["Do you want to look forward to potential future dates?", 'datesFlexible', 1, datesFlexible],
    ["How many days do you want to look forward?", 'daysForward', 0],
    ["Enter the day of week you'd like to leave (if applicable):", 'dd', 1, dd],
    ["Do you want to filter to departure dates to match the entered day of week?", 'strict', 1, strict],
]
inputVars = np.empty(len(inputQuestions), dtype=object)


def addRows(i, inputQuestions):
    for i in range(i, len(inputQuestions)):
        if globals.quitVar == 1: quit()
        qFrame = tk.Frame(master=formFrame, bg='#e3f1f1')
        aFrame = tk.Frame(master=formFrame, bg='#e3f1f1')
        aFrame.grid(column=1, row=i, columnspan=1, sticky="n",padx=3,pady=3)
        qFrame.grid(column=0, row=i, columnspan=1, sticky="n",padx=3,pady=3)
        if inputQuestions[i][1]=='dd':
            label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
            label.grid(row=i, column=0)
            dd.set('')  # default value
            days=["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            inputQuestions[i][3].set("Select a day")
            dropdown = tkinter.OptionMenu(aFrame, inputQuestions[i][3], *days)
            dropdown.grid(row=i, column=1)
        elif inputQuestions[i][2] == 1:
            label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
            label.grid(row=i, column=0)
            inputVars[i] = tk.Checkbutton(master=aFrame, variable=inputQuestions[i][3], bg='#e3f1f1')
            inputVars[i].grid(row=i, column=1)
        else:
            label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
            label.grid(row=i, column=0)
            inputVars[i] = tk.Entry(width=30, master=aFrame, bd=0)
            inputVars[i].grid(row=i, column=1)


for i in range(len(inputQuestions)):
    if globals.quitVar == 1: quit()
    qFrame = tk.Frame(master=formFrame, bg='#e3f1f1')
    aFrame = tk.Frame(master=formFrame, bg='#e3f1f1')
    aFrame.grid(column=1, row=i, columnspan=1, sticky="n")
    qFrame.grid(column=0, row=i, columnspan=1, sticky="n")
    if i == 4:
        label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
        label.grid(row=i, column=0, padx=10, pady=3)
        inputVars[i] = tk.Checkbutton(master=aFrame, variable=inputQuestions[i][3],
                                      command=lambda: addRows(i, inputQuestions), bg='#e3f1f1')
        inputVars[i].grid(row=i, column=1, padx=10, pady=3)
        break
    if inputQuestions[i][2] == 1:
        label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
        label.grid(row=i, column=0, padx=10, pady=3)
        inputVars[i] = tk.Checkbutton(master=aFrame, variable=inputQuestions[i][3], bg='#e3f1f1')
        inputVars[i].grid(row=i, column=1, padx=10, pady=3)
    else:
        label = tk.Label(master=qFrame, text=inputQuestions[i][0], bg='#e3f1f1')
        label.grid(row=i, column=0, padx=10, pady=3)
        inputVars[i] = tk.Entry(width=30, master=aFrame, bd=0)
        inputVars[i].grid(row=i, column=1, padx=10, pady=3)

greeting = tk.Label(
    master=headerFrame,
    text="WELCOME TO BOBO'S MAGICAL FLIGHT FINDER WHERE ALL YOUR DREAMS COME TO DIE!",
    font=('Helvetica',16,'bold'),
    height=5,
    bg='#63c8e4',
    anchor=CENTER
)
greeting.grid(row=0, column=1, sticky="n")

status = tk.Label(
    master=headerFrame,
    textvariable=tempVar,
    height=2,
    bg='#63c8e4'
)

b2 = tk.Button(
    master=buttonFrame,
    text='Submit',
    command=lambda: background(submitFunctions, (inputVars, runDaily, status)),
    bg='#e3f1f1'
)
b2.grid(row=0, column=0, pady=10, padx=5)

b3 = tk.Button(
    master=buttonFrame,
    text='Quit',
    command=lambda: background(quitWindow, ()),
    bg='#e3f1f1'
)
b3.grid(row=0, column=1, pady=10, padx=5)

b4 = tk.Button(
    master=carrierFrame,
    text='Submit',
    command=lambda: background(setExclude, ()),
    bg='#e3f1f1'
)
b4.grid(row=3, column=2, pady=10, sticky="n", columnspan=3, padx=(40,0))

window.mainloop()
