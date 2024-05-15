import os
import mysql.connector
import datetime
import configparser
import mysql.connector.errors
#os.environ['KIVY_GL_BACKEND'] = 'angle_sdl2'

import android # pylint: disable=import-error

from kivy import platform
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

if platform == "android":
    from android.permissions import Permission, request_permissions # pylint: disable=import-error
    request_permissions([Permission.INTERNET, Permission.ACCESS_NETWORK_STATE, Permission.ACCESS_WIFI_STATE, Permission.WRITE_EXTERNAL_STORAGE])



def db_connection():
    # Leer la configuración del archivo .ini
    config = configparser.ConfigParser()
    config.read('galapp.ini')
    
    # Obtener los valores de configuración
    host = config['DATABASE']['host']
    port = config['DATABASE']['port']
    user = config['DATABASE']['user']
    password = config['DATABASE']['password']
    database_name = config['DATABASE']['database_name']
    
    # Conectar a la base de datos
    db = mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database_name
    )
    
    cursor = db.cursor()
    return cursor, db

# Función para verificar las credenciales del usuario
def check_credentials(username, password):
        cursor, db = db_connection()
        cursor = db.cursor()
        query = "SELECT CUSUARIO, USUARIO, CLAVE FROM usuarios WHERE USUARIO = %s AND CLAVE = %s"
        cursor.execute(query, (username, password))
        result = cursor.fetchone()
        return result is not None

class LoginWindow(Screen):
    username_input = ObjectProperty(None)
    password_input = ObjectProperty(None)

    def on_enter(self):
        self.check_config()

    def login(self, username, password):
        if self.check_credentials(username, password):
            print("Inicio de sesión exitoso")
            # Aquí puedes cambiar a la pantalla principal o realizar otras acciones
        else:
            print("Credenciales incorrectas")

    def check_config(self):
        config = configparser.ConfigParser()
        config.read('galapp.ini')
        
        # Verificar si el archivo .ini contiene la sección DATABASE
        if 'DATABASE' in config:
            database_config = config['DATABASE']
            
            # Verificar si los campos requeridos están presentes
            required_fields = ['host', 'port', 'user', 'password', 'database_name']
            for field in required_fields:
                if field not in database_config:
                    self.root.current = "config"
                    return False
            return True
        else:
            print("La sección 'DATABASE' no está presente en el archivo de configuración.")
            self.root.current = "config"
            return False


class MainMenu(Screen):
    def on_enter(self):
        self.update_authorizations_table()
        Clock.schedule_interval(lambda dt: self.update_authorizations_table(), 5)

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
            table_layout = GridLayout(cols=4, spacing=1, size_hint_y=None) #spacing 10

            total_height = len(data) * (dp(100) + 15)  # altura de cada fila (30 dp) + espacio entre filas (10 dp)

            # Establecer la altura del GridLayout
            table_layout.height = total_height

            # Agregar la cabecera
            header_solicitante = Label(text="Usuario", size_hint_y=None, height=dp(30), font_size=20, bold=True)
            header_solicita = Label(text="Solicita", size_hint_y=None, height=dp(30), font_size=20, bold=True)
            header_fecha = Label(text="Fecha", size_hint_y=None, height=dp(30), font_size=20, bold=True)
            header_acciones = Label(text="", size_hint_y=None, height=dp(30), width=50, font_size=20, bold=True)
            
            table_layout.add_widget(header_solicitante)
            table_layout.add_widget(header_solicita)
            table_layout.add_widget(header_fecha)
            table_layout.add_widget(header_acciones)

            # Iterar sobre los datos y agregarlos al GridLayout
            for row_data in data:
                name_label = Label(text=str(row_data[1]), font_size= 16, size_hint_y=None, height=dp(30))
                action_label = Label(text=str(row_data[3]), font_size= 16, size_hint_y=None, height=dp(30))
                date_label = Label(text=str(row_data[2]), font_size= 16, size_hint_y=None, height=dp(30))
                action_button = Button(text="Administrar", font_size= 16, size_hint_x=None, width=100, size_hint_y=None, height=dp(30))
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
        cursor, db = db_connection()
        # Realizar la consulta SQL para obtener los datos de la base de datos
        cursor = db.cursor()
        sql = '''
        SELECT pa.CPEDIDO_AUTORIZACION, u.USUARIO AS NOMBRE_SOLICITANTE, pa.FALTA, pa.SOLICITA
        FROM pedido_autorizaciones pa
        INNER JOIN usuarios u ON pa.CUSUARIO_SOLICITANTE = u.CUSUARIO
        WHERE pa.VIGENTE = %s
        LIMIT 5
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
                    size_hint=(None, None), size=(400, 350)) #size=ancho, alto

        # Definir las acciones al presionar los botones
        confirm_button.bind(on_press=lambda instance, popup=popup, custom_id=custom_id: self.confirm_authorization(custom_id, popup))
        reject_button.bind(on_press=lambda instance, popup=popup, custom_id=custom_id: self.reject_authorization(custom_id, popup))

        # Agregar los botones al contenido de la ventana emergente
        content.add_widget(confirm_button)
        content.add_widget(reject_button)

        # Mostrar la ventana emergente
        popup.open()

    def confirm_authorization(self, custom_id, popup):
        cursor, db = db_connection()
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
        cursor, db = db_connection()
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

class ConfigScreen(Screen):
    def on_enter(self):
        self.load_config()

    def load_config(self):
        # Cargar la configuración desde el archivo .ini
        config = configparser.ConfigParser()
        config.read('galapp.ini')

        # Obtener la sección 'DATABASE' del archivo .ini
        if 'DATABASE' in config:
            database_config = config['DATABASE']

            # Obtener los valores de configuración
            host = database_config.get('host', '')
            port = database_config.get('port', '')
            user = database_config.get('user', '')
            password = database_config.get('password', '')
            database_name = database_config.get('database_name', '')

            # Actualizar los campos de texto en la pantalla de configuración
            self.ids.host_input.text = host
            self.ids.port_input.text = port
            self.ids.user_input.text = user
            self.ids.password_input.text = password
            self.ids.database_name_input.text = database_name

    def save_config(self):
        host = self.ids.host_input.text
        port = self.ids.port_input.text
        user = self.ids.user_input.text
        password = self.ids.password_input.text
        database_name = self.ids.database_name_input.text
        
        config = configparser.ConfigParser()
        config['DATABASE'] = {
            'host': host,
            'port': port,
            'user': user,
            'password': password,
            'database_name': database_name
        }
        with open('galapp.ini', 'w') as configfile:
            config.write(configfile)
        app = MDApp.get_running_app()
        app.root.current = "main"

    def cancel_edition(self):
        # Aquí puedes agregar lógica para limpiar los campos o cualquier otra acción que desees realizar
        app = MDApp.get_running_app()
        app.root.current = "main"

class MainApp(MDApp):
    authorizing_user = None
    def build(self):
        self.theme_cls.theme_style = "Dark"
        self.theme_cls.primary_pallete = "BlueGray"

        kv = Builder.load_file('app.kv')
        
        return kv
    
    def config_screen_load(self, *args):
        app = MDApp.get_running_app()
        app.root.current = "config"   

    #Definir funcionalidad del boton login
    # Método para iniciar sesión
    def login(self, username, password):
        #try:
        if username.lower() == "configurar":  # Verificar si se ingresó "configurar"
            self.config_screen_load() # Abrir la pantalla de configuración
            return
        else:
            cursor, db = db_connection()
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
#########COMMENTED IN ORDER TO BE ABLE TO VISUALIZE CONNECTION ERRORS ON DEVELOPMENT. MUST UNCOMMENT FOR RELEASE            
        # except (mysql.connector.errors.InterfaceError, mysql.connector.errors.ProgrammingError) as e:
        #     if isinstance(e, mysql.connector.errors.InterfaceError):
        #         # Redirigir a la pantalla de configuración
        #         wrong_config = Popup(title='Error de configuración', size_hint=(None, None), size=(400, 200))
        #         content = BoxLayout(orientation='vertical')
        #         label1 = Label(text='La configuración es incorrecta!')
        #         label2 = Label(text='Se abrirá la ventana de configuración!')
        #         content.add_widget(label1)
        #         content.add_widget(label2)
        #         wrong_config.content = content
        #         wrong_config.open()
        #         # Programar el cierre automático del nuevo Popup después de 3 segundos
        #         Clock.schedule_once(lambda dt: wrong_config.dismiss(), 3)
        #         Clock.schedule_once(self.config_screen_load, 2)
        #     elif "Access denied for user" in str(e):
        #         # Manejar el error de acceso denegado
        #         login_screen = self.root.get_screen('main')
        #         wrong_credentials = login_screen.ids.wrong_credentials
        #         wrong_credentials.text = "No se pudo establecer la conexión, verifique la configuración."
        #         wrong_credentials.color = (1, 0, 0, 1)  # Cambiar color a rojo
        #         wrong_credentials.size_hint_y = None  # Mostrar el label
        #         wrong_credentials.height = 50  # Establecer altura del label para que sea visible
        #         wrong_credentials.opacity = 1  # Establecer altura del label para que sea visible
        #         Clock.schedule_once(self.hide_label, 3)
        #         Clock.schedule_once(self.config_screen_load, 2)
        
        # def config_screen_load(self, *args):
        #     MDApp.get_running_app()
        #     app.root.current = "config"
        # except mysql.connector.errors.InterfaceError:
        #     # Redirigir a la pantalla de configuración
        #     wrong_config = Popup(title='Error de configuración', size_hint=(None, None), size=(400, 200))

        #     content = BoxLayout(orientation='vertical')
        #     label1 = Label(text='La configuración es incorrecta!')
        #     label2 = Label(text='Se abrirá la ventana de configuración!')
        #     content.add_widget(label1)
        #     content.add_widget(label2)

        #     wrong_config.content = content
        #     wrong_config.open()
        #     # Programar el cierre automático del nuevo Popup después de 3 segundos
        #     Clock.schedule_once(lambda dt: wrong_config.dismiss(), 2)
        #     app = MDApp.get_running_app()
        #     app.root.current = "config"

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