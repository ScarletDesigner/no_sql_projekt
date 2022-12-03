from tkinter import *
from pymongo import MongoClient
import pandas as pd
from dateutil import parser

def showUsersPage(usersInputs, button):
    button.grid_remove()
    for u in usersInputs:
        u.grid()

def hideUsersPage(usersInputs):
    for u in usersInputs:
        u.grid_remove()


def logIn(usersInputs):
    hideUsersPage(usersInputs)
    Button(root, text="Wróć", command= lambda: showUsersPage(usersInputs)).grid(row=0, column=0)


def register(users, login, password):
    user = {
        "login": login,
        "password": password
    }
    users.insert_one(user)

def changePassword(users, login, newPassword):
    user = {
        "login": login
    }
    new_password = {
        "$set": {
            "password": newPassword
        }
    }
    users.update_one(user, new_password)

def deleteUser(users, login):
    user = {
        "login": login
    }
    users.delete_one(user)






if __name__ == '__main__':
    CONNECTION_STRING = "mongodb://localhost:27017"
    client = MongoClient(CONNECTION_STRING)
    database = client['lab3']
    users = database["users"]

    usersInputs = []
    
    root = Tk()
    loginLabel = Label(root, text="Login:")
    usersInputs.append(loginLabel)
    loginEntry = Entry(root, width=30)
    usersInputs.append(loginEntry)
    passwordLabel = Label(root, text="Password:")
    usersInputs.append(passwordLabel)
    passwordEntry = Entry(root, width=30)
    usersInputs.append(passwordEntry)
    loginButton = Button(root, text='Zaloguj się', command= lambda: logIn(usersInputs))
    usersInputs.append(loginButton)
    registerButton = Button(root, text='Zarejestruj się', command= lambda: register(users, loginEntry.get(), passwordEntry.get()))
    usersInputs.append(registerButton)
    changePasswordButton = Button(root, text="Zmień hasło", command= lambda: changePassword(users, loginEntry.get(), passwordEntry.get()))
    usersInputs.append(changePasswordButton)
    deleteUserButton = Button(root, text="Usuń użytkownika", command= lambda: deleteUser(users, loginEntry.get()))
    usersInputs.append(deleteUserButton)
    loginLabel.grid(row=0, column=0)
    loginEntry.grid(row=0, column=1)
    passwordLabel.grid(row=1, column=0)
    passwordEntry.grid(row=1, column=1)
    loginButton.grid(row=2, column=0)
    registerButton.grid(row=2, column=1)
    changePasswordButton.grid(row=3,column=1)
    deleteUserButton.grid(row=4,column=1)
    

    root.mainloop()
