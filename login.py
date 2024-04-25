import sql_connection as db

from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button
from kivy.properties import ObjectProperty

# Función para verificar las credenciales del usuario
def check_credentials(username, password):
    cursor = db.cursor
    query = "SELECT USUARIO, CLAVE FROM usuarios WHERE USUARIO = %s AND CLAVE = %s"
    cursor.execute(query, (username, password))
    result = cursor.fetchone()
    return result is not None

class LoginWindow(Screen):
    username_input = ObjectProperty(None)
    password_input = ObjectProperty(None)

    def login(self, username, password):
        if self.check_credentials(username, password):
            print("Inicio de sesión exitoso")
            # Aquí puedes cambiar a la pantalla principal o realizar otras acciones
        else:
            print("Credenciales incorrectas")


