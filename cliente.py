from email.headerregistry import ContentTransferEncodingHeader
import logging
import asyncio
import os
from select import select
from webbrowser import get
import xmpp
import slixmpp
from getpass import getpass
from slixmpp.exceptions import IqError, IqTimeout

asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

class enviarMensaje(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, destino, mensaje):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.destination = destino
        self.mensaje = mensaje
        self.add_event_handler("session_start", self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        self.send_message(mto=self.destino, mbody=self.mensaje, mtype='chat')
        self.disconnect()

class agregarContacto(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, nombre):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.nombre = nombre
        self.add_event_handler("session_start", self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        self.send_presence(pto=self.nombre, pstatus=None, ptype='suscribe', pfrom=self.usuario)

class obtenerContactos(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.add_event_handler("session_start", self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        contacts = []
        roster = self.roster
        for usuario in roster:
            contacts.append(usuario)
        
        self.disconnect()

        for i in range(0,10):
            print('\nContactos: ')
        for j in contacts:
            print(i)
        print(roster)

class informacionContacto(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, contacto):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.contacto = contacto
        self.add_event_handler("session_start", self.iniciar)

    async def start(self, evento):
        self.send_presence()
        await self.get_roster()
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0077')
        self.register_plugin('xep_0199')
        self.register_plugin('xep_0054')
        contacts = []
        roster = self.client_roster
        for usuario in roster:
            contacts.append(usuario)
        if self.contacto in contacts:
            for i in range(0,10):
                print("\nEl contacto si se encuentra registrado")
                print("Informacion de contacto: " + self.contacto)
                print(roster[self.contacto])
        else:
            print('\nEl contacto no se encuentra registrado')
        self.disconnect()

class estadoContacto(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.add_event_handler("session_start", self.iniciar)
        self.add_event_handler('presence_available', self.presencia)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()

    def presencia(self, presencia):
        print("%s esta disponible" % presencia['from'])
    
class mcRoom(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, room, mensaje, apodo):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.room = room
        self.mensaje = mensaje
        self.apodo = apodo
        self.add_event_handler('session_start', self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        await self.plugin['xep_0045'].join_muc_wait(self.room, self.apodo)
    
class cambioEstado(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, estado, mensajeEstado):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.estado = estado
        self.mensajeEstado = mensajeEstado
        self.add_event_handler('session_start', self.iniciar)
    
    async def iniciar(self, evento):
        self.send_presence(pshow=self.estado, pstatus=self.mensajeEstado)
        await self.get_roster()
        print("El estado a cambiado a: %s" % self.estado)
        print("Mensaje del estado: %s" % self.mensajeEstado)

class eliminarUsuario(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.add_event_handler('session_start', self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        self.register_plugin('xep_0030')
        self.register_plugin('xep_0077')
        self.register_plugin('xep_0199')
        request = self.Iq()
        request['type'] = 'set'
        request['from'] = self.boundjid.bare
        request['register']['remove'] = True
        try:
            request.send(True)
        except IqError as e:
            print('Error al eliminar cuenta: %s' % e.iq['error'])
            self.disconnect()
        except IqTimeout:
            print('Error al eliminar cuenta: timeout')
            self.disconnect()

class Notificaciones(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.add_event_handler("session_start", self.iniciar)
        self.add_event_handler("message", self.mensaje)
        self.add_event_handler("presence_available", self.presenceDisponible)
        self.add_event_handler("presence_unavailable", self.presenceNoDisponible)
        self.add_event_handler("presence_subscribe", self.presenceAgregar)
        self.add_event_handler("presence_subscribed", self.presenceAgregado)
        self.add_event_handler("presence_unsubscribed", self.presenceEliminado)
        self.add_event_handler("groupchat_message", self.mensajeGrupal)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()

    def mensaje(self, msg):
        if msg['type'] in ('chat', 'normal'):
            print("%s dice: %s" % (msg['from'], msg['body']))

    def presenceDisponible(self, presence):
        print("%s esta disponible" % presence['from'])

    def presenceNoDisponible(self, presence):
        print("%s no esta disponible" % presence['from'])

    def presenceAgregar(self, presence):
        print("%s quiere agregarte" % presence['from'])
        print("Escribe 'si' para aceptar o 'no' para denegar la solicitud")
        op = input()
        if op == 'si':
            self.send_presence(pto=presence['from'], ptype='subscribed')
            self.send_presence(pto=presence['from'], ptype='subscribe')
        elif op == 'no':
            self.send_presence(pto=presence['from'], ptype='unsubscribed')
            self.send_presence(pto=presence['from'], ptype='unsubscribe')
        else:
            print("Opcion no valida")

    def presenceAgregado(self, presence):
        print("%s te ha agregado" % presence['from'])

    def presenceEliminado(self, presence):
        print("%s te ha eliminado" % presence['from'])

    def mensajeGrupal(self, msg):
        print("%s en %s dice: %s" % (msg['mucnick'], msg['from'], msg['body']))

class enviarArchivo(slixmpp.ClientXMPP):
    def __init__(self, usuario, contrasena, destino, archivo):
        slixmpp.ClientXMPP.__init__(self, usuario, contrasena)
        self.destino = destino
        self.archivo = archivo
        self.add_event_handler("session_start", self.iniciar)

    async def iniciar(self, evento):
        self.send_presence()
        await self.get_roster()
        self.register_plugin('xep_0066')

        iq = self.Iq()
        iq['type'] = 'set'
        iq['to'] = self.destino
        iq['si']['profile'] = 'http://jabber.org/protocol/si/profile/file-transfer'
        iq['si']['file']['name'] = self.archivo
        iq['si']['file']['size'] = os.stat(self.archivo).st_size
        iq['si']['feature'] = {'var': 'http://jabber.org/protocol/feature-neg'}
        iq['si']['feature']['x']['field'] = {
            'var': 'stream-method', 'value': 'http://jabber.org/protocol/bytestreams'}
        iq['si']['feature']['x']['field'] = {
            'var': 'stream-method', 'value': 'http://jabber.org/protocol/ibb'}

        self.disconnect()

def crearCuenta(usuario, contrasena):
    print("Creando cuenta nueva!")
    usuario_cuenta = xmpp.JID(usuario)
    contrasena_cuenta = contrasena
    client = xmpp.Client(usuario_cuenta.getDomain(), debug=[])
    client.connect()
    if xmpp.features.register(client, usuario_cuenta.getDomain(), {'username': usuario_cuenta.getNode(), 'password': contrasena_cuenta}):
        print("Cuenta creada")
    else:
        print("La cuenta no pudo ser creada")


def Inicio():
    print("""
    1. Crear cuenta nueva
    2. Inciar sesion\n
    """)


def menu():
    print("""
    1. Enviar mensaje
    2. Lista de contactos
    3. Estado de contactos
    4. Enviar mensaje grupal
    5. Detalles de contacto
    6. Eliminar cuenta
    7. Agregar contacto
    8. Cambiar estado
    9. Recibir notificaciones
    10. Desconectar
    """)

if __name__ == '__main__':


    print('Bienvenido a alumchat.fun')

    Inicio()
    opcion = input("Seleccione una opción: ")
    if opcion == "1":
        usuario = input("Introduzca su usuario con el dominio incluido: ")
        contrasena = getpass("Introduzca su contraseña: ")
        verificacion = getpass('Introduzca nuevamente su contraseña: ')
        if contrasena == verificacion:
            crearCuenta(usuario, contrasena)
        else:
            print("Las contraseñas no coinciden")
            print('Cuenta no creada')


    menu()
    opcion = input('Ingrese una opcion: ')
    while opcion != '10':
        if opcion == '1':
            to = input('Ingrese el destinatario: ')
            msg = input('Ingrese el mensaje: ')
            client = enviarMensaje(usuario, contrasena, to, msg)
            client.register_plugin('xep_0030') 
            client.register_plugin('xep_0199') 
            client.connect()
            client.process(forever=False)
        elif opcion == '2':
            client = obtenerContactos(usuario, contrasena)
            client.register_plugin('xep_0030')  
            client.register_plugin('xep_0199')  
            client.connect()
            client.process(forever=False)
        elif opcion == '3':
            print('Mostrando estado de los contactos')
            client = estadoContacto(usuario, contrasena)
            client.register_plugin('xep_0030') 
            client.register_plugin('xep_0199') 
            client.connect()
            client.process(timeout=10)
            client.disconnect()
        elif opcion == '4':
            room = input('Ingrese el nombre del sala: ')
            msg = input('Ingrese el mensaje: ')
            nick = input('Ingrese su nick: ')
            client = mcRoom(usuario, contrasena, room, msg, nick)
            client.register_plugin('xep_0030') 
            client.register_plugin('xep_0199')  
            client.register_plugin('xep_0045')  
            client.connect()
            client.process(timeout=10)
            client.disconnect()
        elif opcion == '5':
            contact = input('Ingrese el nombre del contacto: ')
            client = informacionContacto(usuario, contrasena, contact)
            client.connect()
            client.process(forever=False)
        elif opcion == '6':
            print('Borrando cuenta')
            print("Esta seguro de borrar su cuenta?")
            q = input('Ingrese "si" para borrar: ')
            if q == 'si':
                client = eliminarUsuario(usuario, contrasena)
                client.register_plugin('xep_0030')  
                client.register_plugin('xep_0199')  
                client.register_plugin('xep_0077') 
                client.register_plugin('xep_0100')
                client.connect()
                client.process(forever=False)
                print('Cuenta borrada')
                break
            else:
                print('Cancelado')
        elif opcion == '7':
            print('Agregando nuevo contacto')
            name = input('Ingrese el nombre: ')
            client = agregarContacto(usuario, contrasena, name)
            client.register_plugin('xep_0030')  
            client.register_plugin('xep_0199') 
            client.register_plugin('xep_0077')  
            client.register_plugin('xep_0100')
            client.connect()
            client.process(forever=False)
        elif opcion == '8':
            print('Cambiando estado')
            status = input(
                'Ingrese su estado:\n away \n chat \n dnd \n xa \n ')
            status_msg = input('Ingrese su mensaje de estado: ')
            client = cambioEstado(usuario, contrasena, status, status_msg)
            client.register_plugin('xep_0030')  
            client.register_plugin('xep_0199') 
            client.connect()
            client.process(timeout=20)
        elif opcion == '9':
            print('Encender notificaciones')
            tiempo = input(
                'Ingrese el tiempo en segundos que desea activar las notificaciones: ')
            if tiempo.isdigit():
                client = Notificaciones(usuario, contrasena)
                client.register_plugin('xep_0030')  
                client.register_plugin('xep_0199')  
                client.register_plugin('xep_0045') 
                client.connect()
                client.process(timeout=int(tiempo))
            else:
                print('Lo que ingreso no es un numero. Cancelando')

        menu()
        opcion = input('Ingrese una opcion: ')

    print("Client disconnected.")
    exit(0)