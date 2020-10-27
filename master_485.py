# Importamos las librerias del proyecto

import smbus2
import serial
import serial.rs485
import time
import sys
import crcmod
import threading
import RPi.GPIO as GPIO

bus = smbus2.SMBus(1)

# Estos son los comandos para verificar el envio del mensaje
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
Rpi_Newdata = 0x06
"""
MCU_Events    = 0x01
MCU_I_O       =  0x02
SINAPSIS_Temp = 0x03
MCU_Program   = 0x04
"""

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
        sendCommand(RPi_Mode)
        answer = commandAnswer()
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
    data = [0xAA, command,0xCC, 0xEE] 
    crc8=crc(data[1:2]) # Se envia command a crc, command es Rpi_Mode 0x00 
    data[2]=int(crc8,0)
    ser.write(bytes(data),'UTF-8')
    time.sleep(1)


def commandAnswer():
    GPIO.GPIO_485 = GPIO.LOW
    #GPIO.GPIO_Request_bus = GPIO.HIGH
        block = serial.read() ###buscar funcion de libreria serial para leer
        #print("block[2]", hex(block[2]), "getcrc", getcrc)
        #GPIO.GPIO_485 = GPIO.HIGH
        #Check data received
        if(block[0]==init and block[3]==end):
            getcrc = crc(block[1:2])
            if(block[1]==NACK): print("Error in sent data")
            if(hex(block[2])==getcrc): print("Correct data")
        return block

""" 

La idea del codigo es: 
Activamos los puertos GPIO_Request_bus como entrada
GPIO_485 como salida

enviamos los comandos a traves de la funcion sendCommand() del comando requerido
Recibimos una respuesta a traves de la funcion commandAnswer() y finalmente 
hacemos print para verificar que la respuesta sea correcta

"""

def main():

    GPIO.setmode(GPIO.BCM)
    GPIO.setup(GPIO_Request_bus, GPIO.IN)
    GPIO.setup(GPIO_485, GPIO.OUT)

    sendCommand(RPi_Mode)
    answer = commandAnswer()
    print (answer)

# Finalmente nos quedamos en este loop infinito enviando y esperando respuestas de parte del esclavo

    while 1:       
        receiveEvent()


if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print ('Interrupted')
        sys.exit(0)


