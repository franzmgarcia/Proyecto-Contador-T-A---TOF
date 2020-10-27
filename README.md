# Proyecto-Contador-T-A-con-camara-ToF

## Funcionamiento general

Las cámaras de tiempo de vuelo son equipos que funcionan emitiendo un haz de luz infrarrojo, mediante el cual puede calcular la distancia que hay desde la cámara al haz. 

En este caso la cámara Terabee posee este funcionamiento. Para el desarrollo del algoritmo lo primero que se hace es conectar y abrir el dispositivo en el código. Una vez hecho esto leemos el frame, la data del frame es mapeada en un arreglo de 60x80. Cada uno de estos puntos, (por ejemplo el frame_data[2440]) lo que nos va a indicar es la distancia que hay entre la cámara y ese punto medido por el sensor. Debemos notar también, que si se mapea en dimensiones de 60x80, el tamaño total será de 4800 y un valor como 2440 estará justo en la mitad de la imagen captada por la cámara. 

Otro punto importante son las distancias que estamos considerando. La idea del algoritmo consiste en primera instancia en eliminar ruido. Para esto, aprovechando que estamos desde un punto de vista cenital, y que no necesitamos identificar puntos que estén muy alejados de la cámara (es decir, deberíamos identificar la cabeza y los hombros de las personas, pero puntos más alejados no son necesarios) podemos eliminar los elementos no deseados poniendo un filtro de distancia. 

En el código además, se mapean las distancias obtenidas de 0 a 255, y después con estos valores y haciendo uso de cv2.applyColorMap, aunque al final no se trabaje con la imagen a color sino con la imagen en escala de grises.

Posteriormente, la idea general del código consiste en reconocer los movimientos ocurridos dentro de la imagen. Para esto, cada vez que se enciende el dispositivo se toma una imagen de fondo, que es la que vamos a restar con todas los frames siguientes que aparezcan en la imagen, de esta manera obtendremos "el movimiento". Esta imagen es pasada por distintos filtros que buscan determinar los contornos de la figura, que después nos servirán para determinar si lo que paso realmente fue una persona o no. 

A su vez utilizaremos diversos puntos tomados por la distancia, para determinar si efectivamente alguien pasó o no a través de la detección de la cámara. Así, habrán puntos de referencia a la entrada y a la salida, y no se contará una entrada o una salida, a menos que el contorno detectado no pase por los 2 puntos.

Otro punto de interés es la detección de los contornos, que en este caso se buscan sean de formas circulares, similares a los de la cabeza de las personas vistas desde una posición cenital, además de tener que cumplir un tamaño mínimo para incluirlo como contorno valido. A través de esta detección, podemos reconocer cuantos contornos hay en un frame tomado por la cámara.

Todos estos valores son almacenados en diversos diccionarios que poseen la siguiente estructura:

Conteo posee el numero de ingresos y el numero de salidas asi como el aforo
Depende de si estas en modo conteo o en modo volumen lo que significa aforo
Si estas en modo conteo aforo = ingresos-salidas
Si estas en modo volumen es el numero de personas que son detectadas por la 
camara ToF

conteo_dic = {
    'ingresos': '0',
    'salidas': '0',
    'aforo': '0',
    'timestamp':'0'}



Status responde con un codigo que lee de la funcion get_autodiagnostic
Los codigos son:
200: ok
301: problemas de temperatura
302: problemas temperatura gpu
303: problemas de uso de cpu

status_dic = {
    'codigo':'200',
    'timestamp':'0'
    }

En el reporte se establecen todos los cambios producidos durante el dia
Se indica la fecha y hora del evento para despues, cuando sea solicitado
Hacer un reporte mensual y uno diario 

reporte_dic = {
    'reporte':'',
    'timestamp':'0'
}

Nos indica si hay nuevos datos en la parte del contador
Codigo 100 nos indica que no hay nueva data 
Codigo 200 hay nueva data

La idea de este codigo es ayudar en el envio de datos, ya que seria una manera 
de reconocer cuando estan ingresando pasajeron por ejemplo, asi que esta junto con
otras variables podrian ayudar a establecer si efectivamente el autobus se detuvo
y esta contando pasajeros nuevamente

newData_dic = {
    'codigo':'100',
    'timestamp':'0'
}

indica si esta en modo contador o en modo volumen, esto es lo que cambia el parametro volumen 
en conteo

mode_dic = {
    'modo':'700',
    'timestamp':'0'
}


Estos diccionarios, son después transformados en json y se envían en los protocolos: MQTT, TCP-IP y RS 485, cada uno implementado a través de sus propias librerías para tales fines


