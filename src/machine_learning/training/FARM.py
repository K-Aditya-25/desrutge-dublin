from lxml import etree
from itertools import zip_longest
import xml.etree.ElementTree as ET

def extraer_nVeh(file_path, det):
    try:
        file_path = det + '/' + file_path
        # Parsear el archivo XML
        tree = ET.parse(file_path)
        root = tree.getroot()

        # Inicializar variables
        nVehContrib_values = []
        nVeh = [0] * 24

        # Verificar si el root es válido
        if root is not None:
            # Buscar todos los elementos <interval>
            intervals = root.findall('interval')
            if intervals:
                for interval in intervals:
                    # Obtener el atributo nVehContrib
                    nVehContrib = interval.get('nVehContrib')
                    if nVehContrib is not None:
                        nVehContrib_values.append(int(nVehContrib))
                        
                        # Calcular la hora del intervalo
                        intervalo = float(interval.get('begin', 0))  # Valor por defecto 0 si no se encuentra 'begin'
                        Hora = min(int(intervalo / 3600), 23)  # Asegurarse de que no supere 23
                        
                        # Incrementar el contador de vehículos por hora
                        nVeh[Hora] += int(nVehContrib)
            else:
                print("No se encontraron elementos <interval> en el archivo XML.")
        else:
            print("No se pudo cargar el archivo XML.")
        
        return nVeh

    except ET.ParseError as e:
        print("Error al parsear el archivo XML:", e)
    except FileNotFoundError:
        print(f"Archivo no encontrado: {file_path}")
    except Exception as e:
        print("Error inesperado:", e)

    # Devolver los resultados
    return None


def define_files(Detector_file):
    # Ruta al archivo XML
    file_path = []
    # Extraer los atributos 'lane' de cada elemento 'inductionLoop'
    tree = ET.parse(Detector_file)
    root = tree.getroot()
    for induction_loop in root.findall('inductionLoop'):
        file = induction_loop.get('file')
        if file:
            file_path.append(file)

    return file_path

def farm(det):

    Detector_file = det + "/detectors.add.xml"

    Detector = []

    file_path = define_files(Detector_file)

    for i in range(len(file_path)):
        nVeh = [0] * 24

        listVeh = extraer_nVeh(file_path[i], det)
        nVeh = [x + y for x, y in zip_longest(nVeh, listVeh, fillvalue=0)]

        Detector.append(nVeh)

    return Detector