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

        for F in (StartPage, SendNewPackage, ShowAllPackages):
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
        
        def getPackages():
            query = "MATCH (u:User)-[r:SENT]->(p:Package) WHERE u.id = '%s' RETURN p" % (loggedInUser)
            results = session.run(query)
            nodes = list(results.graph()._nodes.values())

            ttk.Label(self, text="numer", ).grid(row=2, column=0)
            ttk.Label(self, text="czy krucha", ).grid(row=2, column=1)
            ttk.Label(self, text="wartość przesyłki", ).grid(row=2, column=2)
            ttk.Label(self, text="sposób dostawy", ).grid(row=2, column=3)
            ttk.Label(self, text="koszt dostawy", ).grid(row=2, column=4)
            ttk.Label(self, text="sposób płatności", ).grid(row=2, column=5)
            ttk.Label(self, text="miasto", ).grid(row=2, column=6)
            ttk.Label(self, text="ulica", ).grid(row=2, column=7)
            ttk.Label(self, text="kod pocztowy", ).grid(row=2, column=8)
            ttk.Label(self, text="numer domu", ).grid(row=2, column=9)
            ttk.Label(self, text="numer mieszkania", ).grid(row=2, column=10)
            ttk.Label(self, text="kraj", ).grid(row=2, column=11)
            
            
            i = 3
            for node in nodes:
                ttk.Label(self, text=str(node._properties['id'])).grid(row=i, column=0)
                ttk.Label(self, text=str(node._properties['isFragile'])).grid(row=i, column=1)
                ttk.Label(self, text=str(node._properties['shipmentValue'])).grid(row=i, column=2)
                ttk.Label(self, text=str(node._properties['deliveryMethod'])).grid(row=i, column=3)
                ttk.Label(self, text=str(node._properties['deliveryCost'])).grid(row=i, column=4)
                ttk.Label(self, text=str(node._properties['paymentMethod'])).grid(row=i, column=5)

                query = "MATCH (p:Package)-[r:HAS_DESTINATION]->(a:Address) WHERE p.id = '%s' RETURN a" % (node._properties['id'])
                addressResults = session.run(query)
                addressNodes = list(addressResults.graph()._nodes.values())

                for node in addressNodes:
                    ttk.Label(self, text=str(node._properties['city'])).grid(row=i, column=6)
                    ttk.Label(self, text=str(node._properties['street'])).grid(row=i, column=7)
                    ttk.Label(self, text=str(node._properties['postCode'])).grid(row=i, column=8)
                    ttk.Label(self, text=str(node._properties['houseNumber'])).grid(row=i, column=9)
                    ttk.Label(self, text=str(node._properties['apartmentNumber'])).grid(row=i, column=10)
                    ttk.Label(self, text=str(node._properties['country'])).grid(row=i, column=11)
                i += 1

        button1 = ttk.Button(self, text ="Wróć", command = lambda : controller.show_frame(SendNewPackage))
        button1.grid(row = 1, column = 1, padx = 10, pady = 10)
        button2 = ttk.Button(self, text="Odśwież", command=getPackages)
        button2.grid(row=1, column=2)



app = tkinterApp()
app.mainloop()