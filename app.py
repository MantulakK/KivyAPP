import os
import mysql.connector
import datetime
os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.recycleview import RecycleView
from kivy.clock import Clock
from kivymd.uix.datatables import MDDataTable
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivymd.uix.button import MDFlatButton
from kivymd.uix.dialog import MDDialog
from kivy.uix.popup import Popup
from kivy.core.window import Window
from kivy.uix.recyclegridlayout import RecycleGridLayout
from kivy.properties import ObjectProperty
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.button import Button

db = mysql.connector.connect(
    host = "localhost",
    user = "root",
    password = "delphi$73",
    database = "fe"
)
cursor = db.cursor()

# Función para verificar las credenciales del usuario
def check_credentials(username, password):
    cursor = db.cursor()
    query = "SELECT CUSUARIO, USUARIO, CLAVE FROM usuarios WHERE USUARIO = %s AND CLAVE = %s"
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


class MainMenu(Screen):
    def on_enter(self):
        self.update_authorizations_table()
        Clock.schedule_interval(lambda dt: self.update_authorizations_table(), 15)

    def update_authorizations_table(self):
        # Limpiar el layout de datos antes de actualizarlo
        self.ids.data_layout.clear_widgets()

        # Obtener los datos de la base de datos
        data = self.get_autorizations()

        # Crear un BoxLayout vertical para organizar los componentes
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, None))

        if not data:
            none_label = Label(text="No hay pedidos de autorizaciones", size_hint_y=None, height=dp(600), font_size=20, bold=True)
            main_layout.add_widget(none_label)
            
        else:
            # Crear un GridLayout para la tabla
            table_layout = GridLayout(cols=4, spacing=10, size_hint_y=None)

            total_height = len(data) * (dp(100) + 10)  # altura de cada fila (30 dp) + espacio entre filas (10 dp)

            # Establecer la altura del GridLayout
            table_layout.height = total_height

            # Agregar la cabecera
            header_solicitante = Label(text="Usuario", size_hint_y=None, height=dp(30), font_size=16, bold=True)
            header_solicita = Label(text="Solicita", size_hint_y=None, height=dp(30), font_size=16, bold=True)
            header_fecha = Label(text="Fecha", size_hint_y=None, height=dp(30), font_size=16, bold=True)
            header_acciones = Label(text="", size_hint_y=None, height=dp(30), width=50, font_size=16, bold=True)
            
            table_layout.add_widget(header_solicitante)
            table_layout.add_widget(header_solicita)
            table_layout.add_widget(header_fecha)
            table_layout.add_widget(header_acciones)

            # Iterar sobre los datos y agregarlos al GridLayout
            for row_data in data:
                name_label = Label(text=str(row_data[1]), size_hint_y=None, height=dp(30))
                action_label = Label(text=str(row_data[3]), size_hint_y=None, height=dp(30))
                date_label = Label(text=str(row_data[2]), size_hint_y=None, height=dp(30))
                action_button = Button(text="Administrar", size_hint_x=None, width=100, size_hint_y=None, height=dp(30))
                # Asignar el identificador personalizado al botón
                action_button.custom_id = str(row_data[0])
                action_button.bind(on_press=lambda instance, custom_id=action_button.custom_id: self.show_confirmation_popup(instance, custom_id))
                table_layout.add_widget(name_label)
                table_layout.add_widget(action_label)
                table_layout.add_widget(date_label)
                table_layout.add_widget(action_button)

            # Agregar la tabla al layout principal
            main_layout.add_widget(table_layout)
            main_layout.height = table_layout.height
        # Agregar el layout principal al layout de la pantalla
        self.ids.data_layout.add_widget(main_layout)

    def get_autorizations(self):
        # Realizar la consulta SQL para obtener los datos de la base de datos
        cursor = db.cursor()
        sql = '''
        SELECT pa.CPEDIDO_AUTORIZACION, u.USUARIO AS NOMBRE_SOLICITANTE, pa.FALTA, pa.SOLICITA
        FROM pedido_autorizaciones pa
        INNER JOIN usuarios u ON pa.CUSUARIO_SOLICITANTE = u.CUSUARIO
        WHERE pa.VIGENTE = %s
        '''
        cursor.execute(sql, (1,))
        rows = cursor.fetchall()
        
        # Convertir los datos obtenidos en el formato adecuado
        data = []
        for row in rows:
            data.append(row)
        return data

    def show_confirmation_popup(self, instance, custom_id):
        # Crear el contenido de la ventana emergente
        content = BoxLayout(orientation='vertical')
        content.add_widget(Label(text="¿Desea confirmar o rechazar esta autorización?"))

        # Crear los botones de confirmar y rechazar
        confirm_button = Button(text="Confirmar")
        reject_button = Button(text="Rechazar")

        # Crear el Popup
        popup = Popup(title='Confirmar/Rechazar',
                    content=content,
                    size_hint=(None, None), size=(350, 200))

        # Definir las acciones al presionar los botones
        confirm_button.bind(on_press=lambda instance, popup=popup, custom_id=custom_id: self.confirm_authorization(custom_id, popup))
        reject_button.bind(on_press=lambda instance, popup=popup, custom_id=custom_id: self.reject_authorization(custom_id, popup))

        # Agregar los botones al contenido de la ventana emergente
        content.add_widget(confirm_button)
        content.add_widget(reject_button)

        # Mostrar la ventana emergente
        popup.open()

    def confirm_authorization(self, custom_id, popup):
        cursor = db.cursor()
        sql_auth_check = "SELECT AUTORIZADO, VIGENTE FROM pedido_autorizaciones WHERE CPEDIDO_AUTORIZACION = %s"
        cursor.execute(sql_auth_check, (custom_id,))
        result = cursor.fetchone()
        if result[0] == 0 or result[0] == 1 and result[1] == 0:
            # Cerrar el Popup anterior
            popup.dismiss()
            # Mostrar un nuevo Popup
            no_petition = Popup(title='Error al autorizar',
                                content=Label(text='La solicitud fue autorizada o cancelada desde el sistema!'),
                                size_hint=(None, None), size=(400, 200))
            no_petition.open()
            # Programar el cierre automático del nuevo Popup después de 3 segundos
            Clock.schedule_once(lambda dt: no_petition.dismiss(), 3)
        
        else:
            # Aquí deberías ejecutar la consulta SQL para confirmar la autorización
            fmodi_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fhauth_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = db.cursor()
            sql = "UPDATE pedido_autorizaciones SET CUSUARIO_AUTORIZANTE = %s, AUTORIZADO = 1, VIGENTE = 0, FH_AUTORIZACION = %s, FMODI = %s WHERE CPEDIDO_AUTORIZACION = %s"
            cursor.execute(sql, (self.authorizing_user, fhauth_datetime, fmodi_datetime, custom_id,))
            db.commit()
            popup.dismiss()
        # Actualizar la tabla
        self.update_authorizations_table()

    def reject_authorization(self, custom_id, popup):
        cursor = db.cursor()
        sql_auth_check = "SELECT AUTORIZADO, VIGENTE FROM pedido_autorizaciones WHERE CPEDIDO_AUTORIZACION = %s"
        cursor.execute(sql_auth_check, (custom_id,))
        result = cursor.fetchone()
        if result[0] == 0 or result[0] == 1 and result[1] == 0:
            # Cerrar el Popup anterior
            popup.dismiss()
            # Mostrar un nuevo Popup
            no_petition = Popup(title='Error al autorizar',
                                content=Label(text='La solicitud fue autorizada o cancelada desde el sistema!'),
                                size_hint=(None, None), size=(400, 200))
            no_petition.open()
            # Programar el cierre automático del nuevo Popup después de 3 segundos
            Clock.schedule_once(lambda dt: no_petition.dismiss(), 3)

        else:
            # Aquí deberías ejecutar la consulta SQL para rechazar la autorización
            fmodi_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            fhauth_datetime = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor = db.cursor()
            sql = "UPDATE pedido_autorizaciones SET CUSUARIO_AUTORIZANTE = %s, AUTORIZADO = 0, VIGENTE = 0, FH_AUTORIZACION = %s, FMODI = %s WHERE CPEDIDO_AUTORIZACION = %s"
            cursor.execute(sql, (self.authorizing_user, fhauth_datetime, fmodi_datetime, custom_id,))
            db.commit()
            popup.dismiss()
        # Actualizar la tabla
        self.update_authorizations_table()


class WindowManager(ScreenManager):
    pass


class MainApp(MDApp):
    authorizing_user = None
    #Cargar app/primero login.kv
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_pallete = "BlueGray"

        kv = Builder.load_file('app.kv')
        
        return kv
    
    #Definir funcionalidad del boton login
    # Método para iniciar sesión
    def login(self, username, password):
        cursor = db.cursor()
        if check_credentials(username, password):
            cursor = db.cursor()
            query = "SELECT CUSUARIO, ADMINISTRADOR FROM usuarios WHERE USUARIO = %s"
            cursor.execute(query, (username,))
            result = cursor.fetchone()
            if result[1] == 1:
                MainMenu.authorizing_user = result[0]
                self.root.current = 'second'
            else:
                login_screen = self.root.get_screen('main')
                is_not_admin = login_screen.ids.is_not_admin
                is_not_admin.text = "El usuario debe ser Administrador!"
                is_not_admin.color = (1, 0, 0, 1)  # Cambiar color a rojo
                is_not_admin.size_hint_y = None  # Mostrar el label
                is_not_admin.height = 50  # Establecer altura del label para que sea visible
                is_not_admin.opacity = 1  # Establecer altura del label para que sea visible
                Clock.schedule_once(self.hide_label, 3)
                
        else:
            login_screen = self.root.get_screen('main')
            wrong_credentials = login_screen.ids.wrong_credentials
            wrong_credentials.text = "Credenciales de Usuario incorrectas!"
            wrong_credentials.color = (1, 0, 0, 1)  # Cambiar color a rojo
            wrong_credentials.size_hint_y = None  # Mostrar el label
            wrong_credentials.height = 50  # Establecer altura del label para que sea visible
            wrong_credentials.opacity = 1  # Establecer altura del label para que sea visible
            Clock.schedule_once(self.hide_label, 3)
        cursor.close()

    def hide_label(self, dt):
        login_screen = self.root.get_screen('main')
        is_not_admin = login_screen.ids.is_not_admin
        wrong_credentials = login_screen.ids.wrong_credentials
        is_not_admin.opacity = 0  # Ocultar el label
        wrong_credentials.opacity = 0  # Ocultar el label
        
    def logout(self):
        self.root.get_screen("second").ids.data_layout.clear_widgets()
        self.root.current = "main"


if __name__ == "__main__":
    MainApp().run()