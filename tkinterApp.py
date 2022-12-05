import tkinter as tk
from tkinter import ttk
from pymongo import MongoClient
import pandas as pd
from dateutil import parser
from neo4j import GraphDatabase
import networkx as nx
import random

LARGEFONT =("Verdana", 15)

CONNECTION_STRING = "mongodb://localhost:27017"
client = MongoClient(CONNECTION_STRING)
database = client['lab3']
users = database["users"]

loggedInUser = None
loggedInUserLabel = None


uri = "bolt://localhost:7687"
userName = "neo4j"
password = "kurierzy"
graphDb_Driver = GraphDatabase.driver(uri, auth=(userName, password))
session = graphDb_Driver.session(database="kurierzy")


def userDoesExist(login):
    user = {
        "login": login,
    }
    results = users.find(user)
    results_list = list(results)
    return len(results_list) > 0

def logIn(controller, login, password, statusLabel):
    user = {
        "login": login,
        "password": password
    }
    results = users.find(user)
    results_list = list(results)
    if len(results_list) > 0:
        global loggedInUser
        loggedInUser = login
        global loggedInUserLabel
        loggedInUserLabel.config(text= "Witaj " + login + "! Nadaj nową paczkę")
        controller.show_frame(SendNewPackage)
    else:
        statusLabel.config(text= "Username or password incorrect")


def register(login, password, statusLabel):
    if userDoesExist(login):
        statusLabel.config(text = "User already exists. Please choose different username.")
        return

    user = {
        "login": login,
        "password": password
    }
    users.insert_one(user)

    query="CREATE (u:User {id: '%s' })" % (login)
    q=session.run(query)
    statusLabel.config(text = "User " + login  + " saved to database")

def changePassword(login, newPassword, statusLabel):
    if not userDoesExist(login):
        statusLabel.config(text= "User " + login + " does not exist")
        return

    user = {
        "login": login
    }
    new_password = {
        "$set": {
            "password": newPassword
        }
    }
    users.update_one(user, new_password)
    statusLabel.config(text= "Password of user " + login + " has been changed")

def deleteUser(login, statusLabel):
    if not userDoesExist(login):
        statusLabel.config(text= "User " + login + " does not exist")
        return

    user = {
        "login": login
    }
    users.delete_one(user)
    statusLabel.config(text= "User " + login + " has been deleted")

class tkinterApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)

        container.grid_rowconfigure(0, weight= 1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, SendNewPackage, ShowAllPackages, AllUsers):
            frame = F(container,self)
            self.frames[F] = frame
            frame.grid(row=0, column=0, sticky="nsew")

        self.show_frame(StartPage)

    def show_frame(self, cont):
        frame = self.frames[cont]
        frame.tkraise()

class StartPage(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        loginLabel = ttk.Label(self, text="Login:")
        loginEntry = ttk.Entry(self, width=30)
        passwordLabel = ttk.Label(self, text="Password:")
        passwordEntry = ttk.Entry(self, width=30)
        loginButton = ttk.Button(self, text='Zaloguj się', command= lambda: logIn(controller, loginEntry.get(), passwordEntry.get(), statusLabel))
        registerButton = ttk.Button(self, text='Zarejestruj się', command= lambda: register(loginEntry.get(), passwordEntry.get(), statusLabel))
        changePasswordButton = ttk.Button(self, text="Zmień hasło", command= lambda: changePassword(loginEntry.get(), passwordEntry.get(), statusLabel))
        deleteUserButton = ttk.Button(self, text="Usuń użytkownika", command= lambda: deleteUser(loginEntry.get(), statusLabel))
        statusLabel = ttk.Label(self, text="")
        statusLabel.grid(row=2, column=1)
        loginLabel.grid(row=0, column=0)
        loginEntry.grid(row=0, column=1)
        passwordLabel.grid(row=1, column=0)
        passwordEntry.grid(row=1, column=1)
        loginButton.grid(row=3, column=0)
        registerButton.grid(row=3, column=1)
        changePasswordButton.grid(row=4,column=1)
        deleteUserButton.grid(row=5,column=1)

        allUsersPageButton = ttk.Button(self, text="Zobacz wszystkich użytkowników", command= lambda: controller.show_frame(AllUsers))
        allUsersPageButton.grid(row= 6, column= 2)

class AllUsers(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        group = {"$group": {"_id": "null", "count": {"$sum": 1}}}
        results_a = users.aggregate([group])
        for row in results_a:
            ttk.Label(self, text="Liczba wszystkich użytkowników: " + str(row['count'])).grid(row=0, column=0)

        group = {"$group": { "_id": "null", "pass_length": { "$avg": {"$strLenCP": "$password"} } }}
        results_a = users.aggregate([group])
        for row in results_a:
            ttk.Label(self, text="Średnia długość hasła użytkownika: " + str(row['pass_length'])).grid(row=1, column=0)

        ttk.Label(self, text="Lista użytkowników z długością hasła:").grid(row=2, column=0, pady=20)
        group = {"$group": { "_id": "$login", "pass_length": { "$sum": {"$strLenCP": "$password"} } }}
        sort = {"$sort": {"pass_length": -1}}
        results_a = users.aggregate([group, sort])
        i = 3
        for row in results_a:
            ttk.Label(self, text=str(row['_id'])+ " - " + str(row['pass_length'])).grid(row=i, column=0)
            i += 1
        

        button1 = ttk.Button(self, text="Wróć", command=lambda: controller.show_frame(StartPage))
        button1.grid(row=100, column=0, padx=10, pady=10)

class SendNewPackage(tk.Frame):

    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        def deliveryCostHandler(event):
            current = deliveryMethodEntry.current()
            if current != -1:
                x = deliveryMethodEntry.get()
                if x == 'Kurier Pocztex':
                    deliveryCostLabel.config(text= 7.99)
                if x == 'Kurier DPD':
                    deliveryCostLabel.config(text= 7.39)
                if x == 'Kurier DHL':
                    deliveryCostLabel.config(text= 8.99)
                if x == 'Paczkomaty InPost':
                    deliveryCostLabel.config(text= 9.99)
                


        global loggedInUserLabel
        loggedInUserLabel = ttk.Label(self, font= LARGEFONT)
        loggedInUserLabel.grid(row=0, column=0)
        isFragileVar = tk.IntVar()
        isFragileEntry = ttk.Checkbutton(self, text="Kruchy towar", variable=isFragileVar)
        isFragileEntry.grid(row=1,column=1)
        ttk.Label(self, text="Wartość przesyłki:").grid(row=2, column=0)
        shipmentValueEntry = ttk.Entry(self)
        shipmentValueEntry.grid(row=2,column=1)
        ttk.Label(self, text="Sposób dostawy:").grid(row=3, column=0)
        deliveryMethodEntry = ttk.Combobox(self, values = ['Kurier Pocztex', 'Kurier DPD', 'Kurier DHL', 'Paczkomaty InPost'])
        deliveryMethodEntry.bind('<<ComboboxSelected>>', deliveryCostHandler)
        deliveryMethodEntry.grid(row=3, column=1)
        ttk.Label(self, text="Koszt dostawy:").grid(row=4, column=0)
        deliveryCostLabel = ttk.Label(self)
        deliveryCostLabel.grid(row=4, column=1)
        ttk.Label(self, text="Sposób płatności:").grid(row=5, column=0)
        paymentMethodEntry = ttk.Combobox(self, values = ['Blik', 'Za pobraniem', 'Przelew tradycyjny'])
        paymentMethodEntry.grid(row=5, column=1)

        def clearPackageEntries():
            cityEntry.delete(0, 'end')
            streetEntry.delete(0, 'end')
            postCodeEntry.delete(0, 'end')
            houseNumberEntry.delete(0, 'end')
            apartmentNumberEntry.delete(0, 'end')
            countryEntry.delete(0, 'end')

        def addressHandler(event):
            query="MATCH (a:Address) RETURN a.city, a.street"
            results = session.run(query)
            nodes = list(results)
            current = addressEntry.current()
            if current != -1:
                x = addressEntry.get()
                if x == '':
                    clearPackageEntries()
                else:
                    clearPackageEntries()
                    id = addressEntry.get().split(sep=',')[0]
                    query="MATCH (a:Address) WHERE a.id='%s' RETURN a.city, a.street, a.postCode, a.houseNumber, a.apartmentNumber, a.country" % (id)
                    results = session.run(query)
                    nodes = list(results)
                    cityEntry.insert(0, str(nodes[0]['a.city']))
                    streetEntry.insert(0, str(nodes[0]['a.street']))
                    postCodeEntry.insert(0, str(nodes[0]['a.postCode']))
                    houseNumberEntry.insert(0, str(nodes[0]['a.houseNumber']))
                    apartmentNumberEntry.insert(0, str(nodes[0]['a.apartmentNumber']))
                    countryEntry.insert(0, str(nodes[0]['a.country']))


        def getAddressesList():
            query="MATCH (a:Address) RETURN a.id, a.city, a.street"
            results = session.run(query)
            nodes = list(results)
            addresses = []
            addresses.append('')
            for node in nodes:
                row = str(node['a.id'])
                row += ','
                row += str(node['a.city'])
                row += ' - '
                row += str(node['a.street'])
                addresses.append(row)
            return addresses
        
        def refreshAddressesList():
            addressEntry.config(values= getAddressesList())

        ttk.Label(self, text="Adres docelowy:").grid(row=6, column=0, pady=20)
        addressEntry = ttk.Combobox(self, values= getAddressesList())
        addressEntry.bind('<<ComboboxSelected>>', addressHandler)
        addressEntry.grid(row=6, column=1)
        addressRefreshButton = ttk.Button(self, text="Odśwież", command=refreshAddressesList)
        addressRefreshButton.grid(row=6,column=2)
        ttk.Label(self, text="Miasto:").grid(row=7, column=0)
        cityEntry = ttk.Entry(self)
        cityEntry.grid(row=7, column=1)
        ttk.Label(self, text="Ulica:").grid(row=8, column=0)
        streetEntry = ttk.Entry(self)
        streetEntry.grid(row=8, column=1)
        ttk.Label(self, text="Kod pocztowy:").grid(row=9, column=0)
        postCodeEntry = ttk.Entry(self)
        postCodeEntry.grid(row=9, column=1)
        ttk.Label(self, text="Numer domu:").grid(row=10, column=0)
        houseNumberEntry = ttk.Entry(self)
        houseNumberEntry.grid(row=10, column=1)
        ttk.Label(self, text="Numer mieszkania:").grid(row=11, column=0)
        apartmentNumberEntry = ttk.Entry(self)
        apartmentNumberEntry.grid(row=11, column=1)
        ttk.Label(self, text="Kraj:").grid(row=12, column=0)
        countryEntry = ttk.Entry(self)
        countryEntry.grid(row=12, column=1)
        statusLabel = ttk.Label(self)
        statusLabel.grid(row=13, column=1)


        def insertPackage():
            global loggedInUser

            number= random.randint(0, 1000000)
            isFragile = isFragileVar.get()
            shipmentValue = float(shipmentValueEntry.get())
            deliveryMethod = deliveryMethodEntry.get()
            deliveryCost = float(deliveryCostLabel['text'])
            paymentMethod = paymentMethodEntry.get()
            query="CREATE (p:Package {id: '%s', isFragile: '%s', shipmentValue: %f, deliveryMethod: '%s', deliveryCost: '%f', paymentMethod: '%s'})" % (number, isFragile, shipmentValue, deliveryMethod, deliveryCost, paymentMethod)
            q=session.run(query)

            query="MATCH (u:User), (p:Package) WHERE u.id='%s' AND p.id='%s' CREATE (u)-[:SENT]->(p)" % (loggedInUser, number)
            q=session.run(query)

            id = 0
            if(addressEntry.get() == ''):
                id = insertAddress()
            else:
                id = addressEntry.get().split(sep=',')[0]

            

            query="MATCH (a:Address), (p:Package) WHERE a.id='%s' AND p.id='%s' CREATE (p)-[:HAS_DESTINATION]->(a)" % (id, number)
            q=session.run(query)
            clearPackageEntries()
            addressEntry.set('')
            statusLabel.config(text="Zatwierdzono przesyłkę")
        
        def insertAddress():
            query="MATCH (a:Address) RETURN a"
            results = session.run(query)
            id = 'a' + str(len(list(results)))
            city = cityEntry.get()
            street = streetEntry.get()
            postCode = postCodeEntry.get()
            houseNumber = houseNumberEntry.get()
            apartmentNumber = apartmentNumberEntry.get()
            country = countryEntry.get()
            query = "CREATE (a:Address {id: '%s', city: '%s', street: '%s', postCode: '%s', houseNumber: '%s', apartmentNumber: '%s',country: '%s' })" % (id, city, street, postCode, houseNumber, apartmentNumber, country)
            q=session.run(query)
            return id

            


        button1 = ttk.Button(self, text="Zatwierdź", command=insertPackage)
        button1.grid(row=14, column=1, padx=10, pady=10)

            

        

        button1 = ttk.Button(self, text="Wróć", command=lambda: controller.show_frame(StartPage))
        button1.grid(row=20, column=0, padx=10, pady=10)
        button2 = ttk.Button(self, text="Wyświetl swoje przesyłki", command=lambda: controller.show_frame(ShowAllPackages))
        button2.grid(row=20, column=1, padx=10, pady=10)

        
class ShowAllPackages(tk.Frame):
    def __init__(self, parent, controller):
        tk.Frame.__init__(self, parent)

        headerRow = []
        packagesRows = []

        def refreshPackagesList():
            for row in packagesRows:
                for label in row:
                    label.destroy()

        def deletePackage(number):
            query = "MATCH (p:Package { id: '%d' })  DETACH DELETE p" % (int(number))
            q = session.run(query)
            getPackages()

        def showHeader():
            numberLabel = ttk.Label(self, text="numer" )
            numberLabel.grid(row=2, column=0)
            headerRow.append(numberLabel)
            isFragileLabel = ttk.Label(self, text="czy krucha")
            isFragileLabel.grid(row=2, column=1)
            headerRow.append(isFragileLabel)
            shipmentValueLabel = ttk.Label(self, text="wartość przesyłki")
            shipmentValueLabel.grid(row=2, column=2)
            headerRow.append(shipmentValueLabel)
            deliveryMethodLabel = ttk.Label(self, text="sposób dostawy")
            deliveryMethodLabel.grid(row=2, column=3)
            headerRow.append(deliveryMethodLabel)
            deliveryCostLabel = ttk.Label(self, text="koszt dostawy")
            deliveryCostLabel.grid(row=2, column=4)
            headerRow.append(deliveryCostLabel)
            paymentMethodLabel = ttk.Label(self, text="sposób płatności")
            paymentMethodLabel.grid(row=2, column=5)
            headerRow.append(paymentMethodLabel)
            cityLabel = ttk.Label(self, text="miasto")
            cityLabel.grid(row=2, column=6)
            headerRow.append(cityLabel)
            streetLabel = ttk.Label(self, text="ulica")
            streetLabel.grid(row=2, column=7)
            headerRow.append(streetLabel)
            postCodeLabel = ttk.Label(self, text="kod pocztowy")
            postCodeLabel.grid(row=2, column=8)
            headerRow.append(postCodeLabel)
            houseNumberLabel = ttk.Label(self, text="numer domu")
            houseNumberLabel.grid(row=2, column=9)
            headerRow.append(houseNumberLabel)
            apartmentNumberLabel = ttk.Label(self, text="numer mieszkania")
            apartmentNumberLabel.grid(row=2, column=10)
            headerRow.append(apartmentNumberLabel)
            countryLabel = ttk.Label(self, text="kraj")
            countryLabel.grid(row=2, column=11)
            headerRow.append(countryLabel)
        
        def getPackages():
            refreshPackagesList()
            query = "MATCH (u:User)-[r:SENT]->(p:Package) WHERE u.id = '%s' RETURN p" % (loggedInUser)
            results = session.run(query)
            nodes = list(results.graph()._nodes.values())

            showHeader()
            
            packageRow = []
            i = 3
            for node in nodes:
                id = node._properties['id']
                idLabel = ttk.Label(self, text=str(node._properties['id']))
                idLabelColumn = 0
                idLabel.grid(row=i, column=idLabelColumn)
                packageRow.append(idLabel)
                isFragileLabel = ttk.Label(self, text=str(node._properties['isFragile']))
                isFragileLabel.grid(row=i, column=1)
                packageRow.append(isFragileLabel)
                shipmentValueLabel = ttk.Label(self, text=str(node._properties['shipmentValue']))
                shipmentValueLabel.grid(row=i, column=2)
                packageRow.append(shipmentValueLabel)
                deliveryMethodLabel = ttk.Label(self, text=str(node._properties['deliveryMethod']))
                deliveryMethodLabel.grid(row=i, column=3)
                packageRow.append(deliveryMethodLabel)
                deliveryCostLabel = ttk.Label(self, text=str(node._properties['deliveryCost']))
                deliveryCostLabel.grid(row=i, column=4)
                packageRow.append(deliveryCostLabel)
                paymentMethodLabel = ttk.Label(self, text=str(node._properties['paymentMethod']))
                paymentMethodLabel.grid(row=i, column=5)
                packageRow.append(paymentMethodLabel)

                query = "MATCH (p:Package)-[r:HAS_DESTINATION]->(a:Address) WHERE p.id = '%s' RETURN a" % (node._properties['id'])
                addressResults = session.run(query)
                addressNodes = list(addressResults.graph()._nodes.values())

                for node in addressNodes:
                    cityLabel = ttk.Label(self, text=str(node._properties['city']))
                    cityLabel.grid(row=i, column=6)
                    packageRow.append(cityLabel)
                    streetLabel = ttk.Label(self, text=str(node._properties['street']))
                    streetLabel.grid(row=i, column=7)
                    packageRow.append(streetLabel)
                    postCodeLabel = ttk.Label(self, text=str(node._properties['postCode']))
                    postCodeLabel.grid(row=i, column=8)
                    packageRow.append(postCodeLabel)
                    houseNumberLabel = ttk.Label(self, text=str(node._properties['houseNumber']))
                    houseNumberLabel.grid(row=i, column=9)
                    packageRow.append(houseNumberLabel)
                    apartmentNumberLabel = ttk.Label(self, text=str(node._properties['apartmentNumber']))
                    apartmentNumberLabel.grid(row=i, column=10)
                    packageRow.append(apartmentNumberLabel)
                    countryLabel = ttk.Label(self, text=str(node._properties['country']))
                    countryLabel.grid(row=i, column=11)
                    packageRow.append(countryLabel)
                packagesRows.append(packageRow)
                i += 1

        button1 = ttk.Button(self, text ="Wróć", command = lambda : controller.show_frame(SendNewPackage))
        button1.grid(row = 1, column = 0, padx = 10, pady = 10)
        button2 = ttk.Button(self, text="Odśwież", command=getPackages)
        button2.grid(row=1, column=1)

        deleteLabel = ttk.Label(self, text="Wybierz numer przesyłki do usunięcia:")
        deleteLabel.grid(row=100,column=0)
        deleteEntry = ttk.Entry(self, width=10)
        deleteEntry.grid(row=101, column=0)
        deleteButton = ttk.Button(self, text="Usuń", command=lambda: deletePackage(deleteEntry.get()))
        deleteButton.grid(row=101, column=1)

        def mapPackageLabelTextToDatabaseFieldName(text):
            if text == 'numer':
                return 'p.number'
            elif text == 'czy krucha':
                return 'p.isFragile'
            elif text == 'wartość przesyłki':
                return 'p.shipmentValue'
            elif text == 'sposób dostawy':
                return 'p.deliveryMethod'
            elif text == 'koszt dostawy':
                return 'p.deliveryCost'
            elif text == 'sposób płatności':
                return 'p.paymentMethod'
            elif text == 'miasto':
                return 'a.city'
            elif text == 'ulica':
                return 'a.street'
            elif text == 'kod pocztowy':
                return 'a.postCode'
            elif text == 'numer domu':
                return 'a.houseNumber'
            elif text == 'numer mieszkania':
                return 'a.apartmentNumber'
            elif text == 'kraj':
                return 'a.country'



        def editPackage(number, field, newValue):
            query = "MATCH (p:Package)-[r:HAS_DESTINATION]->(a:Address) WHERE p.id = '%s' SET %s = '%s'" % (number, field, newValue)
            q = session.run(query)
            getPackages()

        editLabel = ttk.Label(self, text="Wybierz numer paczki i nazwę pola do edycji a następnie wprowadź nową wartość")
        editLabel.grid(row=102, column=0, pady=20)
        editNumberEntry = ttk.Entry(self)
        editNumberEntry.grid(row=103, column=0)
        editFieldEntry = ttk.Entry(self)
        editFieldEntry.grid(row=104, column=0)
        editNewValueEntry = ttk.Entry(self)
        editNewValueEntry.grid(row=105, column=0)
        editButton = ttk.Button(self, text="Edytuj", command=lambda:editPackage(editNumberEntry.get(), mapPackageLabelTextToDatabaseFieldName(editFieldEntry.get()), editNewValueEntry.get()))
        editButton.grid(row=106, column=0)



app = tkinterApp()
app.mainloop()