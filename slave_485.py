# Importamos las librerias del proyecto

import smbus2
import serial
import serial.rs485
import time
import sys
import crcmod
import threading
import RPi.GPIO as GPIO


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



bus = smbus2.SMBus(1)

# Estos son los comandos para verificar el envio del mensajes

address = 0x01
init    = 0xAA
end     = 0xEE
ACK     = 0xFF
NACK    = 0xF0

#485 GPIO Pines

GPIO_485 = 4            # High for transmission, Low for receiving
GPIO_Request_bus = 23   # Pin for slave to indicate that it wants to send a message

#Lista de comandos
RPi_Mode      = 0x00
RPi_Status    = 0x01
RPi_Ingresos    = 0x02
Rpi_Salidas = 0x03
Rpi_Aforo = 0x04
Rpi_Reboot = 0x05
Rpi_Newdata = 0x06



"""
MCU_Events    = 0x01
MCU_I_O       =  0x02
SINAPSIS_Temp = 0x03
MCU_Program   = 0x04
"""

Normal_Mode = 0x10
Report_Mode = 0x20

# definimos las caracteristicas para transmision por serial
ser = serial.Serial(
    port='/dev/serial0',        ###colocar el nombre del puerto
    baudrate = 9600,
    parity=serial.PARITY_NONE,
    stopbits=serial.STOPBITS_ONE,
    bytesize=serial.EIGHTBITS,
    timeout=1
)



# Este es el loop en el que nos mantenemos hasta que termina el programa

def receiveEvent():
    if (GPIO.input(GPIO_Request_bus) == GPIO.HIGH):
        block = commandAnswer()
        sendCommand(block)
        print (answer)

# Calculamos el crc
def crc(string):
    crc8_func = crcmod.predefined.mkPredefinedCrcFun('crc-8')
    crc = (hex(crc8_func(bytearray((string)))))
    return crc

"""
Aca activamos el pin para hacer envio de datos por 485
hacemos la estructura de la data
arreglamos la data con el crc
hacemos ser.write para enviar la data
"""
def sendCommand(command):
    GPIO.GPIO_485 = GPIO.HIGH

    to_send = Normal_Mode

    data = [0xAA, to_send,0xCC, 0xEE] 
    crc8=crc(data[1:2]) # Se envia command a crc, command es Rpi_Mode 0x00 
    data[2]=int(crc8,0)
    ser.write(bytes(data),'UTF-8')
    time.sleep(1)

def commandRead():
    GPIO.GPIO_485 = GPIO.LOW
    #GPIO.GPIO_Request_bus = GPIO.HIGH
        block = serial.read() 
       
        #Check data received
        if(block[0]==init and block[3]==end):
            getcrc = crc(block[1:2])
            if(block[1]==NACK): print("Error in sent data")
            if(hex(block[2])==getcrc): print("Correct data")
        return block

"""
La idea del codigo es:
Hacemos el set de los pines, y leemos a traves del comando block
En funcion del comando block leido damos una respuesta en sendCommand
y nos quedamos en la funcion de receiveEvent()
"""


def main():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_Request_bus, GPIO.IN)
    GPIO.setup(GPIO_485, GPIO.OUT)

    block = commandRead()

    sendCommand(block)

    while 1:       
        receiveEvent()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print ('Interrupted')
        sys.exit(0)


