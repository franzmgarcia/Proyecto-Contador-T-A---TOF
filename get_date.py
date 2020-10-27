import time 
from datetime import date
from datetime import datetime

def get_day():
    today = date.today()
    año = today.year
    mes = today.month
    dia = today.day
    now = datetime.now()
    dia_semana = time.strftime("%A")
    hora = now.hour
    minuto = now.minute
    segundo = now.second
    return año,mes,dia,dia_semana,hora,minuto,segundo


def get_month(mes):
    switcher = {
        1: "Enero",
        2: "Febrero",
        3: "Marzo",
        4: "Abril",
        5: "Mayo",
        6: "Junio",
        7: "Julio",
        8: "Agosto",
        9: "Septiembre",
        10: "Octubre",
        11: "Noviembre",
        12: "Diciembre"
    }
    return switcher.get(mes)

