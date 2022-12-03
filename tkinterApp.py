import tkinter as tk
from tkinter import ttk
from pymongo import MongoClient
import pandas as pd
from dateutil import parser

LARGEFONT =("Verdana", 35)

CONNECTION_STRING = "mongodb://localhost:27017"
client = MongoClient(CONNECTION_STRING)
database = client['lab3']
users = database["users"]


def logIn(controller, login, password):
    user = {
        "login": login,
        "password": password
    }
    results = users.find(user)
    results_list = list(results)
    if len(results_list) > 0:
        controller.show_frame(Page1)

    
    
def doesUserAlreadyExists(login):
    user = {
        "login": login,
    }
    results = users.find(user)
    results_list = list(results)
    return len(results_list) > 0
        

def register(login, password, statusLabel):
    if doesUserAlreadyExists(login):
        statusLabel.config(text = "User already exists. Please choose different username.")
        return

    user = {
        "login": login,
        "password": password
    }
    users.insert_one(user)
    statusLabel.config(text = "User " + login  + " saved to database")

def changePassword(login, newPassword):
    user = {
        "login": login
    }
    new_password = {
        "$set": {
            "password": newPassword
        }
    }
    users.update_one(user, new_password)

def deleteUser(login):
    user = {
        "login": login
    }
    users.delete_one(user)


class tkinterApp(tk.Tk):
    def __init__(self, *args, **kwargs):
        tk.Tk.__init__(self, *args, **kwargs)

        container = tk.Frame(self)
        container.pack(side = "top", fill = "both", expand = True)

        container.grid_rowconfigure(0, weight= 1)
        container.grid_columnconfigure(0, weight=1)

        self.frames = {}

        for F in (StartPage, Page1):
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
        loginButton = ttk.Button(self, text='Zaloguj się', command= lambda: logIn(controller, loginEntry.get(), passwordEntry.get()))
        registerButton = ttk.Button(self, text='Zarejestruj się', command= lambda: register(loginEntry.get(), passwordEntry.get(), statusLabel))
        changePasswordButton = ttk.Button(self, text="Zmień hasło", command= lambda: changePassword(loginEntry.get(), passwordEntry.get()))
        deleteUserButton = ttk.Button(self, text="Usuń użytkownika", command= lambda: deleteUser(loginEntry.get()))
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


class Page1(tk.Frame):

    def __init__(self, parent, controller):

        tk.Frame.__init__(self, parent)
        label = ttk.Label(self, text="Page 1", font=LARGEFONT)
        label.grid(row=0, column=4, padx=10, pady=10)

        button1 = ttk.Button(self, text="Wróć",
                             command=lambda: controller.show_frame(StartPage))

        button1.grid(row=1, column=1, padx=10, pady=10)


app = tkinterApp()
app.mainloop()