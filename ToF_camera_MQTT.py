# Importamos las librerias 
#openni es lo necesario para utilizar la camara de tiempo de vuelo 

from openni import openni2
from time import sleep
from datetime import date
from datetime import datetime
import platform
import numpy as np
import cv2
import time
import os
import json
import psutil
from get_date import get_day, get_month
from autodiagnostico import get_diagnostic

# get_day y get_month son funciones del archivo get_date.py
# estas funciones permiten insertar rapidamente la fecha para hacer los reportes
# get_diagnostic es una funcion de autodiagnostico que se ejecuta al iniciar el codigo 

# Dependiendo de si se usa MQTT o TCP las librerias necesarias seran

import paho.mqtt.client as mqttc # para MQTT
import socket # para TCP/IP

#Importamos las librerias
#paho.mqtt.client es lo necesario para usar MQTT


# Declaramos las variables del programa:

list_archivos = os.listdir()
max_distance_file = "max_distance.txt"
min_distance_file = "min_distance.txt"
none_background = True
salida=False
entrada=False
mark_distance=False
mark_size = False
Volumen = 0
Volumen_Total = 0
kernel_size = 3
kernel = np.ones((5,5),np.uint8)
nro_personas_entrada=0
nro_personas_salida=0
cX=0
cY=0
contador_final_entrada=0
contador_final_salida=0
path=r"C:\Users\Franz Garcia\Desktop\Raspberry-app\src\public"
modo=1



log = False

# Tenemos 5 diccionarios que se modifican a lo largo de la ejecucion del codigo

# Conteo posee el numero de ingresos y el numero de salidas asi como el aforo
# Depende de si estas en modo conteo o en modo volumen lo que significa aforo
# Si estas en modo conteo aforo = ingresos-salidas
# Si estas en modo volumen es el numero de personas que son detectadas por la 
# camara ToF

conteo_dic = {
    'ingresos': '0',
    'salidas': '0',
    'aforo': '0',
    'timestamp':'0'}

# 

# Status responde con un codigo que lee de la funcion get_autodiagnostic
# Los codigos son:
# 200: ok
# 301: problemas de temperatura
# 302: problemas temperatura gpu
# 303: problemas de uso de cpu

status_dic = {
    'codigo':'200',
    'timestamp':'0'
    }

# En el reporte se establecen todos los cambios producidos durante el dia
# Se indica la fecha y hora del evento para despues, cuando sea solicitado
# Hacer un reporte mensual y uno diario 

reporte_dic = {
    'reporte':'',
    'timestamp':'0'
}

# Nos indica si hay nuevos datos en la parte del contador
# Codigo 100 nos indica que no hay nueva data 
# Codigo 200 hay nueva data

# La idea de este codigo es ayudar en el envio de datos, ya que seria una manera 
# de reconocer cuando estan ingresando pasajeron por ejemplo, asi que esta junto con
# otras variables podrian ayudar a establecer si efectivamente el autobus se detuvo
# y esta contando pasajeros nuevamente

newData_dic = {
    'codigo':'100',
    'timestamp':'0'
}

# indica si esta en modo contador o en modo volumen, esto es lo que cambia el parametro volumen 
# en conteo

mode_dic = {
    'modo':'700',
    'timestamp':'0'
}

# definimos el envio de mensajes por MQTT

class MqttObject():

# La idea de usar MQTT es muy util, el mecanismo de envio de mensajes es tambien muy intuitivo
# consiste en conectarse a un broker, despues tendremos dos topicos, uno para enviar comandos y otro para enviar las respuestas
# Si nosotros desde nuestro telefono por ejemplo, nos metemos en la pagina nos suscribimos a ambos topicos 
# enviamos comandos a traves el topic_comando, recibiremos respuesta a traves del topic_respuesta
# Al hacerlo a traves de un server en internet, podria decirse que esto puede funcionar como un protocolo wifi, porque basicamente
# lo estamos revisando desde ahi (obviamente no es lo mismo)


    def __init__(self):

        # Primero definimos el broker al que nos queremos conectar, en este caso estamos usando esa pagina para
        # hacer comunicacion por mqtt, asi que ese es el broker

        self.broker = 'broker.mqttdashboard.com'

        # Definimos unos topicos de comando y respuesta, pueden tener cualquier nombre en realidad, esos que estan definidos
        # en realidad no importan tanto los nombres, lo que importa es que estes conectado a ambos para ver el funcionamiento

        self.topic_comando =  'vikua/prueba/contador/terabee/comando'
        self.topic_respuesta =  'vikua/prueba/contador/terabee/respuesta'
        self.connected = False
        
        self.client = mqttc.Client()
        


    def on_connect(self, client, userdata, flags, rc):
        # aca hacemos la prueba para conectarnos al topico y a MQTT
        
        if rc == 0:
            self.connected = True
            self.client.subscribe(self.topic_comando, 1) #aqui te subscribes al topico q quieres escuchar (topic_comando)
            print("Connected to topic {} OK".format(self.topic_comando))

        else:
            print('Trying to connect to MQTT')
            self.connected = False



    
    def on_disconnect(self, client, userdata, rc):
        # si se llega a caer la conexion, saldra este mensaje 
        
        print('MQTT Disconnected')
        self.connected = False


    def on_message(self, client, userdata, message): 
        # aqui llegan los mensajes enviados por el topico al que te subscribiste (topic_comando)
        # es aca donde seleccionamos que respuesta dar, de acuerdo al mensaje recibido
        # lo primero que se hace es leer el mensaje a traves de la variable comando 
        comando = message.payload.decode('utf-8')

        # lo otro que vamos a hacer es definir la variable log como False, ya que los comandos que
        # vamos a dar respuesta son los siguientes:
        
        # log(año,mes) o log(año,mes,dia) por ejemplo:
        # log2020Junio y log2020Junio1
        # Esto se hace asi

        # definimos este log = False, para que si se introduce el comando log2020Junio por ejemplo
        # no nos aparezca un mensaje de error comando no esta en la lista
        log = False
                
        # La idea del log es la siguiente, por cada mes del año creamos un archivo que se puede consultar en cualquier momento
        # es por esto que hacemos una revision dentro de la carpeta de ejecucion del codigo
        # si ves list_archivos esta definido como: os.listdir() entonces revisamos     
        for i in range (0,len(list_archivos)):
            
            # Estamos buscando el archivo txt dentro de la lista de archivos, si lo encontramos 
        
            if (comando +".txt") == list_archivos[i]:
                # hacemos log = True, de esta manera si vemos abajo en el elif creado
                # si log es True, vamos a hacer pass
                # si log es False nunca pasamos por ese if, por lo que asi no hay que hacer un if para cada fecha, sino que
                # directamente si entramos aca ya da por bueno el comando, y no nos aparece un mensaje de error
                log = True

                # definimos el timestamp

                time_count= time.strftime("%y/%m/%d %H:%M")
                reporte_dic['timestamp']=str(time_count)
                
                # abrimos el archivo que nos fue suministrado en comando y lo guardamos en la variable reporte_dic
                
                with open(comando + ".txt", "r") as myfile:
                    reporte_dic['reporte']=myfile.read()
                
                # finalmente el diccionario lo pasamos a un tipo json para poder enviar correctamente
                
                reporte_json=json.dumps(reporte_dic)

                # hacemos self.publisher que es lo que nos va a servir para enviar el mensaje

                self.publisher(reporte_json)

        if comando == 'conteo':
            
            # definimos timestamp

            time_count= time.strftime("%y/%m/%d %H:%M")
            conteo_dic['timestamp']=str(time_count)
             
            # convertimos a json

            conteo_json=json.dumps(conteo_dic)

            # hacemos self.publisher

            self.publisher(conteo_json)

        elif comando == 'status':
            
            # definimos timestamp

            time_status=time.strftime("%y/%m/%d %H:%M")
            
            status_dic['timestamp']=str(time_status)
            
            # si alguien pide el comando status, se lleva al valor retornado por la funcion get_diagnostic para
            # conocer el status actual del sistema

            status_dic['codigo'] = str(get_diagnostic())

            # se convierte a tipo json

            status_json=json.dumps(status_dic)
            
            # se hace self.publisher
            
            self.publisher(status_json)
        
        elif comando == 'newdata':

            # se define el timestamp

            time_status=time.strftime("%y/%m/%d %H:%M")
            
            newData_dic['timestamp']=str(time_status)
            
            # se convierte en json

            newData_json=json.dumps(newData_dic)
            self.publisher(newData_json)

            # al terminar se cambia siempre el codigo a 100 para asi significar que ya se reconocio si habia nueva data o no

            newData_dic['codigo']=str(100)
        
        elif comando == 'mode':

            # definimos el timestamp

            time_status=time.strftime("%y/%m/%d %H:%M")
            
            mode_dic['timestamp']=str(time_status)
            
            # se convierte a json

            mode_json=json.dumps(mode_dic)
            self.publisher(mode_json)
        
        elif comando == 'reboot':

            # este es un comando para hacer reinicio del sistema

            print("Reiniciar sistema")

        # esto era lo que decia del log, si es True haces pass y ya
        # si es False, no pasas por ese if, y aun puedes indicar si llega a haber algun problema con el comando enviado

        elif log:
            pass
        else:
            self.publisher('Comando invalido. Comandos disponibles "conteo", "status","log", "mode","newData", "reboot')


    # aca se publica el mensaje en el topico de respuesta

    def publisher(self, message): 
        self.client.publish(self.topic_respuesta, message, 1)

    # y aca se define la secuencia de loop del sistema que se va a ejecutar continuamente

    def run(self):
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        self.client.on_message = self.on_message
        try:
            self.client.connect(self.broker,1883,10)   
            self.client.loop_start()
            time.sleep(2)
        except Exception as e:
            print('MQTT Error :::::::',e)
            self.connected = False

# aca se definen funciones para leer el minimo y el maximo que va a aceptar la camara en distancia permitida
# estan en un archivo puesto que es mas facil despues, en caso de que a traves de un comando, por ejemplo
# quiera ser modificado

def get_max_distance(archivo):
    f = open(archivo,"r")
    max_distance = f.readline()
    f.close()
    return(max_distance)

def get_min_distance(archivo):
    f = open(archivo,"r")
    min_distance = f.readline()
    f.close()
    return(min_distance)

# esto es para obtener la imagen que vamos a tener de fondo

def get_image(rgb_frame):
    
# pasamos primero de rgb a escala de grises

    rgb_frame = cv2.cvtColor(rgb_frame, cv2.COLOR_BGR2GRAY)

# se aplica un filtro de mediana    
    rgb_frame=cv2.medianBlur(rgb_frame,9)

# posteriormente aplicamos un filtro gaussiano, ya que esto nos va a permitir tener menos ruido en la señal

    rgb_frame = cv2.GaussianBlur(rgb_frame, (3, 3), 0)

# finalmente hacemos un resize y aplicamos la interpolacion
# la interpolacion puede ser modificada para usar la que deseen

    rgb_frame = cv2.resize(rgb_frame, (800, 600), interpolation=cv2.INTER_AREA)
    return(rgb_frame)        



if __name__ == "__main__":
    # Initialize OpenNI
    if platform.system() == "Windows":
        openni2.initialize("C:/Program Files/OpenNI2/Redist")  # Specify path for Redist
    else:
        openni2.initialize()  # can also accept the path of the OpenNI redistribution

    # definimos el cliente MQTT y se corre el programa

    cliente_mqtt = MqttObject()
    cliente_mqtt.run()

    # Connect and open device
    dev = openni2.Device.open_any()

    depth_stream = dev.create_depth_stream()
    depth_stream.start()

    # definimos la ventana en la que se va a ver lo obtenido por la camara

    cv2.namedWindow("Depth View", cv2.WINDOW_NORMAL)

    # este proceso lo ejecutaremos siempre, a menos que exista una interrupcion de tipo control c por ejemplo

    while cv2.waitKey(1) == -1 and cv2.getWindowProperty("Depth View", cv2.WND_PROP_FULLSCREEN) != -1:

        # Esto viene directamente de la documentacion de terabee

        # leemos el frame
        frame=depth_stream.read_frame()
        frame_data=frame.get_buffer_as_uint16()
        
        # La data es mapeada en un array de 60x80 esto significa que cada punto, por ejemplo el punto 
        # frame_data[2440] es un punto que esta mas o menos a la mitad de la camara porque seria 
        # 30 x 80 son 2400, si nos desplazamos horizontalmente en el array 40 seria la mitad de 80
        # asi que un punto en frame_data[2440] nos daria la distancia que hay entre la camara y ese punto 

        depth_array = np.asarray(frame_data).reshape((60, 80))

        # aca leemos las distancias de los archivos y las distancias son muy importantes
        max_distance=int(get_max_distance(max_distance_file))

        min_distance=int(get_min_distance(min_distance_file))


        # La idea implementada es la siguiente, max_distance podria ser 3000, que serian unos 3 metros segun las especificaciones
        # pero para que necesitas leer 3 metros desde la camara hacia abajo en una aplicacion como esta
        # no lo necesitas, y eliminarlo te va a solventar muchos problemas de ruido, es por eso que 
        # todo lo que aparece como out_of_range no es importante para lo que determina la camara

        out_of_range = depth_array > max_distance
        too_close_range = depth_array < min_distance
        depth_array[out_of_range] = max_distance
        depth_array[too_close_range] = min_distance

        # Scaling depth array

        # esto es para hacer una escala

        depth_scale_factor = 255.0 / (max_distance - min_distance)
        depth_scale_offset = -(min_distance * depth_scale_factor)
        depth_array_norm = depth_array * depth_scale_factor + depth_scale_offset

        # aca se mapea el frame en color, haciendo cv2.COLORMAP_WINTER, hay otros tipos de mapeos si vas a applyColorMap

        # pero en general se trabaja el codigo pero en escala de grises

        rgb_frame = cv2.applyColorMap(depth_array_norm.astype(np.uint8), cv2.COLORMAP_WINTER)

        # aca verificamos si ya tenemos una imagen de fondo, al ejecutarse el codigo obviamente no vamos a tener una 
        # asi que siempre entramos aca


        if (none_background):
            # lo primero que vamos a hacer es registrar el dato en el archivo de reporte, tanto de dia como el mensual
            # aca obtenemos todo lo referente a la fecha
            año,mes_num,dia,dia_semana,hora,minuto,segundo = get_day()
            mes = get_month(mes_num)
            file_month ="log"+ str(año) + mes +".txt"
            file_day ="log"+ str(año) + mes + str(dia) +".txt"
            status = str(get_diagnostic())
            time_data=dia_semana+","+str(año)+"/"+str(mes_num)+"/"+str(dia)+","+str(hora)+":"+str(minuto)+":"+str(segundo)
            with open(file_month, "a") as myfile:

                # al final el primer registro quedaria como esto:
                # Inicio,Tuesday,2020/6/9,6:45:5,nodata
                # Status,Tuesday,2020/6/9,6:45:5,200

                myfile.write("Inicio,"+time_data+",nodata\n")
                myfile.write("Status,"+time_data+","+status+"\n")

            with open(file_day, "a") as myfile:
                myfile.write("Inicio,"+time_data+",nodata\n")
                myfile.write("Status,"+time_data+","+status+"\n")
            
            # posteriormente determinamos la imagen de fondo con la que vamos a detectar si hubo movimientos o no

            background_image = get_image(rgb_frame)  
            # hacemos esta variable False para no volver a pasar por este punto
            none_background = False

        # Ahora si, determinamos la imagen de lo que esta sucediendo en tiempo real usando la misma funcion get_image de rgb_frame

        img = get_image(rgb_frame)

        # usamos cv2.absdiff entre la imagen de fondo y la imagen en tiempo real y asi vemos que cambios se han producido, es decir
        # si tenemos movimiento en la imagen

        img_subs = cv2.absdiff(background_image,img)

        # para determinar los contornos usamos el gradiente morfologico que se obtiene a traves de cv2.MORPH_GRADIENT
        # y el kernel utilizado esta indicado como una variable 
        # kernel = np.ones((5,5),np.uint8)
        # hay que recordar que esto basicamente es una forma de determinar bordes, y el programa lo hara en estos pequeños
        # recuadros de 5x5

        img_subs = cv2.morphologyEx(img_subs, cv2.MORPH_GRADIENT, kernel)

        # ahora la idea del algoritmo es el siguiente
        # vamos a determinar puntos arriba y abajo sobre lo que detecta frame_data

        # debemos recordar que frame data es un arreglo de 60 x 80, 60 en altura 80 en ancho
        # de esta manera colocamos unos puntos en 20, 40 y 60, eso nos permitira estar muy seguros de que estamos detectando
        # realmente a la persona que este pasando


        arriba = frame_data[40]
        arriba_2=frame_data[40]

        arriba_2_2=frame_data[60]
        arriba_2_3=frame_data[20]

        arriba2 = frame_data[60]
        arriba3 = frame_data[20]

        # de igual manera pondremos puntos en 4740, 4760 y 4780 que seria al final del arreglo
        # recordemos que el tamaño es 60x80 = 4800 entonces, 4760 seria en el medio, 4740 en la parte inferior izquierda de 
        # lo que ve la camara y 4780 lo que esta en la parte inferior derecha 

         
        abajo2 = frame_data[4780]
        abajo3 = frame_data[4740]

        abajo=frame_data[4760]

        abajo_2=frame_data[4760]
        abajo_2_2=frame_data[4780]
        abajo_2_3=frame_data[4740]

        # Tambien por si acaso, ponemos una en el medio. 
        # La documentacion de terabee lo que te dice es frame_data[2440] y ya, y parece brujeria, pero eso lo que significa es
        # que es la posicion del todo el centro de lo que ve la camara por lo que indique antes
        # 30*80 = 2400, en todo el centro seria la mitad de 80, 2400+40 = 2440

        distancia=frame_data[2440]
        distancia_2=frame_data[2460]
        distancia_3=frame_data[2420]

        # aca verificamos si hubo o no una salida, basicamente si la distancia esta entre 300 y 1000 para alguno de estos puntos 
        # decimos que alguien entro o salio del sitio donde esta la camara
        # normalmente la camara sin que nadie este en su camino te va a marcar 1500, que es el valor maximo que indicamos anteriormente
        # si esta muy muy cerca este codigo habria que modificarlo, pero eso seria mas dependiendo de las condiciones que vayan a probar
        # en el laboratorio o en el autobus
        # es por esto que es buena idea que max_distance y min_distance sean valores indicados en archivos de texto, porque a traves
        # de ellos quizas puedan en el futuro con comandos hacer todas estas modificaciones de una manera mas versatil

        if (arriba>300 and arriba<1000) or (arriba2>300 and arriba2<1000) or (arriba3>300 and arriba3<1000):
             salida=True
        if (abajo_2>300 and abajo_2<1000) or (abajo_2_2>300 and abajo_2_2<1000) or (abajo_2_3>300 and abajo_2_3<1000):
             entrada=True

        # ahora si la persona pasa vamos a la parte en la que se puede determinar el volumen 

        if (distancia or distancia_2 or distancia_3)>300 and (distancia or distancia_2 or distancia_3)<1000:
            mark_distance=True
        
        if mark_distance==True:

            # Lo primero es hacer cv2.threshold sobre la resta de la imagen, esto es para determinar aun mejor los bordes
            # Luego dilatamos para que estos bordes sean mas gruesos, y asi el programa tiene menos problemas a la hora de
            # determinar los contornos  
            
            _,img_subs=cv2.threshold(img_subs,10,255,cv2.THRESH_BINARY)
            img_subs=cv2.dilate(img_subs,None,iterations=0)
            contours, hierarchy = cv2.findContours(img_subs,cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE) 
	
            # luego para cada contorno determinamos el perimetro

            for cnt in contours:
                
                # si este perimetro determinado con el metodo para las circunferencias, porque al final es lo que vamos a tratar
                # de determinar, es mayor a 600, sumamos 1 a la variable Volumen                 

                perimetro=cv2.arcLength(cnt,True)
                if perimetro>600:
                    Volumen = Volumen +1
                    M=cv2.moments(cnt)
                    cX=int(M["m10"]/M["m00"])
                    cY=int(M["m01"]/M["m00"])
                    mark_size=True
                    #print(Pos_inicial)
        
        # determinamos cual fue el volumen total y hacemos 0 la variable Volumen

        Volumen_Total=Volumen
        Volumen=0

        # al final si todas las condiciones se cumplieron para este punto, podemos sumar 1 al nro_personas_salida

        if salida == True and ((abajo>300 and abajo<1000) or (abajo2>300 and abajo2<1000) or (abajo3>300 and abajo3<1000)): 
            nro_personas_salida=nro_personas_salida+1
            salida=False
            mark_distance=False
            cY=0

        # De igual manera con las entradas

        if entrada==True and ((arriba_2>300 and arriba_2<1000) or (arriba_2_2>300 and arriba_2_2<1000) or (arriba_2_3>300 and arriba_2_3<1000)):
            nro_personas_entrada=nro_personas_entrada+1
            entrada=False
            mark_distance=False
            cY=0
        
        # Luego, contador_final_entrada y contador_final_salida van a ser los que llevaran el conteo de cuantas personas 
        # han ingresado, y cuantas personas han salido

        contador_final_entrada=contador_final_entrada+nro_personas_entrada
        
        # este valor se guarda en el diccionario conteo_dic en ingresos
        conteo_dic['ingresos']=str(contador_final_entrada)
        
        if nro_personas_entrada >1:
            
            # si hay nuevas entradas el codigo de newdata debe cambiar, es por esto que el codigo se modifica aca

            newData_dic['codigo']=str(200)
            año,mes_num,dia,dia_semana,hora,minuto,segundo = get_day()
            mes = get_month(mes_num)
            time_data=dia_semana+","+str(año)+"/"+str(mes_num)+"/"+str(dia)+","+str(hora)+":"+str(minuto)+":"+str(segundo)
            
            # aca ingresamos dentro del registro diario y mensual que hay nuevas entradas y salidas

            with open(file_month, "a") as myfile:
                myfile.write("Ingresos,"+time_data+","+str(contador_final_entrada)+"\n")
            
            with open(file_day, "a") as myfile:
                myfile.write("Ingresos,"+time_data+","+str(contador_final_entrada)+"\n")
            
        # es el mismo caso para el contador de salidas 
        
        contador_final_salida=contador_final_salida+nro_personas_salida
        
        conteo_dic['salidas']=str(contador_final_salida)

        if nro_personas_salida >1:
            # nuevamente indicamos si hay nueva data

            newData_dic['codigo']=str(200)
            año,mes_num,dia,dia_semana,hora,minuto,segundo = get_day()
            mes = get_month(mes_num)
            time_data=dia_semana+","+str(año)+"/"+str(mes_num)+"/"+str(dia)+","+str(hora)+":"+str(minuto)+":"+str(segundo)

            # y guardamos en los registros diarios y mensuales 

            with open(file_month, "a") as myfile:
                myfile.write("Salidas,"+time_data+","+str(contador_final_salida)+"\n")
            
            with open(file_day, "a") as myfile:
                myfile.write("Salidas,"+time_data+","+str(contador_final_salida)+"\n")
        
        # Finalmente registramos en el diccionario de conteo el aforo como contador_final_entrada - contador_final_salida)
        # Si estamos en modo contador, aforo es la resta de contador_entrada - contador_salida
        # Si no, es el valor de Volumen_Total que determinamos anteriormente 

        if mode_dic['ingresos'] == 700:

            conteo_dic['aforo']=str(contador_final_entrada-contador_final_salida)

        else:
            
            conteo_dic['aforo']=str(Volumen_Total)

        # Finalmente esto es para ver los resultados, se podria hacer sobre la imagen del imshow tambien

        print("Entradas")
        print(contador_final_entrada)
        print("Salidas")
        print(contador_final_salida)

        # Hacemos todas estas variables 0 nuevamente

        nro_personas_entrada=0
        nro_personas_salida=0
        cY=0
        
        #cv2.imwrite(os.path.join(path , 'camara2.jpg'), img_subs)
        cv2.imshow("Depth View",img_subs)
        
depth_stream.stop()
openni2.unload()