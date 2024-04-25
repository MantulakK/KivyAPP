import os
import mysql.connector

database = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "delphi$73",
    database = "fe"
)

cursor = database.cursor()
