import socket

# inicializamos el socket

HOST = '127.0.0.1'
PORT = 65432
s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#s.connect((HOST,PORT))

# nos conectamos
s.connect((socket.gethostname(),PORT))

while True:

    # aca indicamos el comando que vamos a solicitar
    # esta funcion podria llegar a fallar en funcion de la version de python
    command = raw_input('Enter the command: ')
    s.send(command)
    
    # recibimos la respuesta en la variable reply y le damos un espacio 
    # de 4096, ya que los json pueden llegar a ser muy grandes
    reply = s.recv(4096)

    # adicionalmente, si la respuesta es END de parte del programa
    # se cierra la conexion
    if reply == 'END':
        break
    print (reply)



