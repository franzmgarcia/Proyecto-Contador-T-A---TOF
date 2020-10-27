#import commands
import psutil

def get_diagnostic():
    """
    with open('/sys/class/thermal/thermal_zone0/temp', "r") as myfile:
        temperatura = int(myfile.read())
    
    temperatura_gpu = commands.getoutput('/opt/vc/bin/vcgencmd measure_temp' ).replace('temp=', '' ).replace(''C', '')
    
    cpu_uso = psutil.cpu_percent(interval=1, percpu=False)



    if temperatura>100:
        codigo= 301
    elif temperatura_gpu>100:
        codigo= 302
    elif cpu_uso>90:
        codigo = 303
    else:
        codigo = 200
    """
    codigo = 200

    return codigo

