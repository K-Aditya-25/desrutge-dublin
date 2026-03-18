import subprocess
import time
from .FARM import farm
import xml.etree.ElementTree as ET
import os
import random


def find_det(det):

    Ruta = det + "/detectors.add.xml"

    # Ruta al archivo XML
    file_path = []
    # Extraer los atributos 'lane' de cada elemento 'inductionLoop'
    tree = ET.parse(Ruta)
    root = tree.getroot()
    for induction_loop in root.findall('inductionLoop'):
        file = induction_loop.get('lane')
        if file:
            file_path.append(file[0:-2])

    return file_path


def find_net_file(det):

    ruta = det + "/sim.sumocfg"
    tree = ET.parse(ruta)
    root = tree.getroot()
    net_file = root.find("./input/net-file")
    if net_file is None:
        raise RuntimeError("sim.sumocfg is missing the configured net-file.")

    value = net_file.get("value")
    if not value:
        raise RuntimeError("sim.sumocfg has an empty net-file value.")

    return det + "/" + value


############### Crear el archivo OD ##########################
def crear_OD( cant_coches, det ):
    
    # Nombre del archivo
    
    file_name = det + "/od_file.od"
    
    # Contenido del archivo, con el valor de X reemplazado
    content = f"""$OR;D2
0.00 1.00
1.0
taz taz {cant_coches}"""
    
    # Crear y escribir el contenido en el archivo
    with open(file_name, "w") as file:
        file.write(content)

def crear_trips(det):
    # Definir los argumentos del comando
    
    taz_file = det + "/miniTAZ.xml"
    od_file = det + "/od_file.od"
    output_file = det + "/trips.xml"
    
    command = [
        "od2trips",        # Comando
        "-n", taz_file, # Archivo de red de TAZ
        "-d", od_file, # Archivo de demanda OD
        "-o", output_file   # Archivo de salida para los trips generados
    ]

    # Ejecutar el comando
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("Error estándar:", e.stderr)
    #   Se genera trips.xml


def validar_trips(det):
    #VAlidar Trips:

    # Define el edge ID que deseas usar como vía
    edge_id = find_det(det)
    
    input_file = det + "/trips.xml"       # Archivo generado por od2trips
    output_file = det + "/trips_via.xml"  # Nuevo archivo con el atributo via

    # Cargar el archivo trips.xml
    tree = ET.parse(input_file)
    root = tree.getroot()

    cant = 0
    total = len(edge_id)

    # Agregar el atributo via a cada trip
    for trip in root.findall('trip'):
        trip.set("departLane", "random")
        if ( cant % (total + 1) < total ):
            trip.set('via', edge_id[cant % (total+1)])
        
        cant += 1

    # Guardar el archivo con las modificaciones
    tree.write(output_file)


def crear_rutas(det):
    # Definir el comando y sus argumentos
    network_file = find_net_file(det)
    trips_file = det + "/trips_via.xml"
    output_routes = det + "/routes.rou.xml"
    additional_file = det + "/miniTAZ.xml"

    command = [
        "duarouter",                                    # Comando a ejecutar
        "-n", network_file,                             # Archivo de red
        "-t", trips_file,                               # Archivo de trips
        "-o", output_routes,                            # Archivo de salida de rutas
        "--routing-algorithm", "astar",                 # Algoritmo de enrutamiento
        "--additional-files", additional_file,          # Archivo adicional
        "--ignore-errors",                              # Ignorar errores de ruta
        "--no-warnings"                                 #No warning in terminal
    ]

    # Ejecutar el comando
    try:
        result = subprocess.run(command, check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print("Error estándar duaroute:", e.stderr)
    #   Se genera routes.rou.xml

def llamar_SUMO(det):
    # Ejecutas SUMO:
    sumocfg_file = det + "/sim.sumocfg"
    command = [
        "sumo",                             # puedes usar "sumo" o "sumo-gui" si deseas la GUI
        "-c", sumocfg_file,    # Ruta al archivo de configuración .sumocfg
        "--no-warnings"                     #No warning in terminal
    ]
  
    # Ejecutar el comando usando subprocess
    try:
        subprocess.run(command, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except subprocess.CalledProcessError as e:
        print(f"Error al ejecutar la simulación: {e}")
    except FileNotFoundError:
        print("SUMO no está instalado o no se puede encontrar el ejecutable.")
    #   Se ebtienen las salidas de los detectores


def simulacion(cant_coches, det):

    det = "./src/machine_learning/training/" + det
    
    crear_OD(cant_coches, det)
    crear_trips(det)
    validar_trips(det)
    crear_rutas(det)
    llamar_SUMO(det)

    #Recolectar:
    while (True):
        res = farm(det)
        if (res != None):
            break
    
    return res
