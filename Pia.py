from datetime import datetime, timedelta
import itertools
import textwrap
import json
import os
import pandas as pd
import openpyxl
import sqlite3

print("hola")

ARCHIVO_ESTADO = 'estado_sistema.json'
clientes = {}
salas = {}
reservaciones = {}

_cliente_counter = itertools.count(1)
_sala_counter = itertools.count(1)
_folio_counter = itertools.count(1)

TURNOS = ['Matutino', 'Vespertino', 'Nocturno']

# -------------------------
# Helpers / utilidades
# -------------------------
def crear_tablas():
    conn = sqlite3.connect("coworking.db")
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS clientes (
            id_cliente TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            apellidos TEXT NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS salas (
            id_sala TEXT PRIMARY KEY,
            nombre TEXT NOT NULL,
            cupo INTEGER NOT NULL
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS reservaciones (
            folio TEXT PRIMARY KEY,
            cliente_id TEXT NOT NULL,
            sala_id TEXT NOT NULL,
            fecha TEXT NOT NULL,
            turno TEXT NOT NULL,
            evento TEXT NOT NULL,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id_cliente),
            FOREIGN KEY (sala_id) REFERENCES salas(id_sala)
        )
    ''')
    conn.commit()
    conn.close()

def guardar_estado():
    """
    Guarda el estado actual del sistema (clientes, salas, reservaciones y contadores)
    en un archivo JSON.
    """
    estado = {
        'clientes': clientes,
        'salas': salas,
        'reservaciones': reservaciones,
        'contadores': {
            'cliente': next(_cliente_counter) - 1,
            'sala': next(_sala_counter) - 1,
            'folio': next(_folio_counter) - 1
        }
    }
    with open(ARCHIVO_ESTADO, 'w') as archivo:
        json.dump(estado, archivo, indent=4)
    print(f"Estado guardado en {ARCHIVO_ESTADO}.")

def cargar_estado():
    """
    Carga el estado del sistema desde un archivo JSON.
    Devuelve True si se cargó correctamente, False si no existe el archivo.
    """
    if os.path.exists(ARCHIVO_ESTADO):
        with open(ARCHIVO_ESTADO, 'r') as archivo:
            estado = json.load(archivo)
            global clientes, salas, reservaciones, _cliente_counter, _sala_counter, _folio_counter
            clientes = estado['clientes']
            salas = estado['salas']
            reservaciones = estado['reservaciones']
            # Reiniciar los contadores al valor guardado + 1
            _cliente_counter = itertools.count(estado['contadores']['cliente'] + 1)
            _sala_counter = itertools.count(estado['contadores']['sala'] + 1)
            _folio_counter = itertools.count(estado['contadores']['folio'] + 1)
            print("Estado cargado correctamente.")
            return True
    return False


def exportar_reservaciones_a_csv(fecha_str, reservaciones_fecha):
    """
    Exporta las reservaciones a un archivo CSV.

    Args:
        fecha_str (str): Fecha en formato "YYYY-MM-DD".
        reservaciones_fecha (list): Lista de tuplas con los datos de las reservaciones.
    """
    # Crear un DataFrame de pandas con los datos
    df = pd.DataFrame(
        reservaciones_fecha,
        columns=["Folio", "Sala", "Cliente", "Turno", "Evento"]
    )
    # Guardar el DataFrame en un archivo CSV
    df.to_csv(f"reservaciones_{fecha_str}.csv", index=False)
    print(f"Reporte exportado a reservaciones_{fecha_str}.csv")

def consultar_reservaciones_por_fecha():
    """Muestra las reservaciones para una fecha específica y permite exportarlas."""
    print("\nConsultar reservaciones para una fecha específica")
    fecha_input = input("Ingresa la fecha (MM-DD-YYYY) o presiona Enter para usar la fecha actual: ").strip()
    if not fecha_input:
        d = hoy()
    else:
        d = validar_fecha_input(fecha_input)
        if not d:
            print("Fecha inválida.")
            return
    fecha_str = date_a_str(d)

    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.folio, s.nombre, c.apellidos || ', ' || c.nombre, r.turno, r.evento
            FROM reservaciones r
            JOIN salas s ON r.sala_id = s.id_sala
            JOIN clientes c ON r.cliente_id = c.id_cliente
            WHERE r.fecha = ?
            ORDER BY r.folio
        ''', (fecha_str,))
        reservaciones_fecha = cursor.fetchall()

    if not reservaciones_fecha:
        print(f"No hay reservaciones para la fecha {fecha_str}.")
        return

    # Mostrar las reservaciones en la consola
    mostrar_linea()
    print(f"Reservaciones para la fecha {fecha_str}")
    mostrar_linea()
    print(f"{'Folio':12} {'Sala':30} {'Cliente':30} {'Turno':10} {'Evento'}")
    mostrar_linea()
    for folio, sala, cliente, turno, evento in reservaciones_fecha:
        print(f"{folio:12} {sala[:28]:30} {cliente[:28]:30} {turno:10} {evento}")
    mostrar_linea()

    # Preguntar si desea exportar
    while True:
        exportar = input("¿Deseas exportar este reporte? (CSV/JSON/Excel/N): ").strip().upper()
        if exportar in ['CSV', 'JSON', 'EXCEL', 'N']:
            break
        print("Opción no válida. Intenta de nuevo.")

    # Exportar según la opción elegida
    if exportar == 'CSV':
        exportar_reservaciones_a_csv(fecha_str, reservaciones_fecha)
    elif exportar == 'JSON':
        exportar_reservaciones_a_json(fecha_str, reservaciones_fecha)
    elif exportar == 'EXCEL':
        exportar_reservaciones_a_excel(fecha_str, reservaciones_fecha)


def exportar_reservaciones_a_csv(fecha_str, reservaciones_fecha):
    df = pd.DataFrame(
        reservaciones_fecha,
        columns=["Folio", "Sala", "Cliente", "Turno", "Evento"]
    )
    df.to_csv(f"reservaciones_{fecha_str}.csv", index=False)
    print(f"Reporte exportado a reservaciones_{fecha_str}.csv")

def exportar_reservaciones_a_json(fecha_str, reservaciones_fecha):
    with open(f"reservaciones_{fecha_str}.json", 'w') as f:
        json.dump(reservaciones_fecha, f, indent=4)
    print(f"Reporte exportado a reservaciones_{fecha_str}.json")

def exportar_reservaciones_a_excel(fecha_str, reservaciones_fecha):
    df = pd.DataFrame(
        reservaciones_fecha,
        columns=["Folio", "Sala", "Cliente", "Turno", "Evento"]
    )
    with pd.ExcelWriter(f"reservaciones_{fecha_str}.xlsx", engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reservaciones')
        worksheet = writer.sheets['Reservaciones']
        workbook = writer.book
        # Formato para Excel: negritas y borde grueso en los encabezados
        header_format = workbook.add_format({'bold': True, 'bottom': 2})
        for cell in ['A1', 'B1', 'C1', 'D1', 'E1']:
            worksheet[cell].font = header_format.font
            worksheet[cell].set_border(bottom=header_format.bottom)
        # Centrar datos en las columnas
        for column in ['A', 'B', 'C', 'D', 'E']:
            worksheet.set_column(f'{column}:{column}', 20)
    print(f"Reporte exportado a reservaciones_{fecha_str}.xlsx")

def exportar_reservaciones_a_excel(fecha_str, reservaciones_fecha):
    """
    Exporta las reservaciones a un archivo Excel con formato específico.
    """
    df = pd.DataFrame(
        reservaciones_fecha,
        columns=["Folio", "Sala", "Cliente", "Turno", "Evento"]
    )
    with pd.ExcelWriter(f"reservaciones_{fecha_str}.xlsx", engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='Reservaciones')
        worksheet = writer.sheets['Reservaciones']
        workbook = writer.book
        # Formato para Excel: negritas y borde grueso en los encabezados
        header_format = workbook.add_format({'bold': True, 'bottom': 2})
        for cell in ['A1', 'B1', 'C1', 'D1', 'E1']:
            worksheet[cell].font = header_format.font
            worksheet[cell].set_border(bottom=header_format.bottom)
        # Centrar datos en las columnas
        for column in ['A', 'B', 'C', 'D', 'E']:
            worksheet.set_column(f'{column}:{column}', 20)
    print(f"Reporte exportado a reservaciones_{fecha_str}.xlsx")

def next_cliente_id():
    return f"C{next(_cliente_counter):03d}"

def next_sala_id():
    return f"S{next(_sala_counter):03d}"

def next_folio():
    return f"RES-{next(_folio_counter):05d}"

def hoy():
    return datetime.now().date()

def validar_fecha_input(fecha_str):
    """Valida formato YYYY-MM-DD y devuelve date o None."""
    try:
        d = datetime.strptime(fecha_str, "%m-%d-%Y").date()
        return d
    except ValueError:
        return None

def date_a_str(d):
    return d.strftime("%m-%d-%Y")

def cliente_nombre_completo(cid):
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT apellidos, nombre FROM clientes WHERE id_cliente = ?", (cid,))
        cliente = cursor.fetchone()
    if not cliente:
        return "(cliente eliminado)"
    return f"{cliente[0]}, {cliente[1]}"



def sala_display_name(sid):
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT nombre, cupo FROM salas WHERE id_sala = ?", (sid,))
        sala = cursor.fetchone()
    if not sala:
        return "(sala eliminada)"
    return f"{sala[0]} (cupo {sala[1]})"



def mostrar_linea():
    print("-" * 60)

# -------------------------
# Funcionalidades principales
# -------------------------
def registrar_cliente():
    """Pide datos y registra un cliente en SQLite."""
    print("\nRegistrar nuevo cliente")
    nombre = input("Nombre: ").strip()
    if not nombre:
        print("Nombre no puede quedar vacío. Operación cancelada.")
        return
    apellidos = input("Apellidos: ").strip()
    if not apellidos:
        print("Apellidos no puede quedar vacío. Operación cancelada.")
        return
    cid = next_cliente_id()
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO clientes (id_cliente, nombre, apellidos) VALUES (?, ?, ?)", (cid, nombre, apellidos))
        conn.commit()
    print(f"Cliente registrado con clave: {cid}")



def listar_clientes_ordenados():
    """Devuelve lista de tuplas (clave, nombre completo) ordenada por apellidos, nombre desde SQLite."""
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_cliente, apellidos, nombre FROM clientes ORDER BY apellidos, nombre")
        clientes = cursor.fetchall()
    return [(cid, f"{apellidos}, {nombre}") for (cid, apellidos, nombre) in clientes]



def elegir_cliente_o_cancelar():
    """Muestra clientes ordenados desde SQLite; permite elegir clave o cancelar. Devuelve cliente_id o None."""
    while True:
        lista = listar_clientes_ordenados()
        if not lista:
            print("No hay clientes registrados. Debes registrar al menos un cliente.")
            return None
        print("\nClientes registrados (orden alfabético por apellidos, nombres):")
        for k, nombre in lista:
            print(f"  {k} -> {nombre}")
        sel = input("Ingresa la clave del cliente (o 'C' para cancelar): ").strip()
        if sel.upper() == 'C':
            return None
        # Verificar si el cliente existe en SQLite
        with sqlite3.connect("coworking.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM clientes WHERE id_cliente = ?", (sel,))
            existe = cursor.fetchone() is not None
        if existe:
            return sel
        print("La clave ingresada no existe. Vuelve a intentarlo o presiona 'C' para cancelar.")



def registrar_sala():
    """Registra una sala nueva en SQLite."""
    print("\nRegistrar nueva sala")
    nombre = input("Nombre de la sala: ").strip()
    if not nombre:
        print("Nombre de sala no puede quedar vacío. Operación cancelada.")
        return
    while True:
        cupo_str = input("Cupo (número entero > 0): ").strip()
        if not cupo_str.isdigit() or int(cupo_str) <= 0:
            print("Cupo inválido. Intenta de nuevo.")
        else:
            cupo = int(cupo_str)
            break
    sid = next_sala_id()
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("INSERT INTO salas (id_sala, nombre, cupo) VALUES (?, ?, ?)", (sid, nombre, cupo))
        conn.commit()
    print(f"Sala registrada con clave: {sid}")


def cancelar_reservacion():
    """Cancela una reservación (marcándola como cancelada y liberando su disponibilidad)."""
    print("\nCancelar una reservación")

    # 1) Solicitar rango de fechas
    while True:
        inicio = input("Fecha inicio (MM-DD-YYYY): ").strip()
        d_ini = validar_fecha_input(inicio)
        if not d_ini:
            print("Fecha inicio inválida.")
            continue
        fin = input("Fecha fin (MM-DD-YYYY): ").strip()
        d_fin = validar_fecha_input(fin)
        if not d_fin:
            print("Fecha fin inválida.")
            continue
        if d_fin < d_ini:
            print("La fecha fin debe ser igual o posterior a la fecha inicio.")
            continue
        break

    inicio_str = date_a_str(d_ini)
    fin_str = date_a_str(d_fin)

    # 2) Mostrar reservaciones en ese rango que NO estén canceladas
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.folio, r.fecha, s.nombre, c.apellidos || ', ' || c.nombre, r.turno, r.evento
            FROM reservaciones r
            JOIN salas s ON r.sala_id = s.id_sala
            JOIN clientes c ON r.cliente_id = c.id_cliente
            WHERE r.fecha BETWEEN ? AND ?
            AND (r.evento NOT LIKE '[CANCELADO]%' OR r.evento IS NULL)
            ORDER BY r.fecha, r.folio
        ''', (inicio_str, fin_str))
        reservaciones_rango = cursor.fetchall()

    if not reservaciones_rango:
        print("No hay reservaciones activas en ese rango de fechas.")
        return

    # 3) Mostrar resultados
    print("\nReservaciones disponibles para cancelar:")
    mostrar_linea()
    print(f"{'Folio':12} {'Fecha':12} {'Sala':25} {'Cliente':30} {'Turno':10} {'Evento'}")
    mostrar_linea()
    for folio, fecha, sala, cliente, turno, evento in reservaciones_rango:
        print(f"{folio:12} {fecha:12} {sala[:23]:25} {cliente[:28]:30} {turno:10} {evento}")
    mostrar_linea()

    # 4) Seleccionar folio
    folios_validos = {folio for folio, *_ in reservaciones_rango}
    while True:
        sel = input("Ingresa el folio de la reservación a cancelar (o 'C' para cancelar): ").strip()
        if sel.upper() == 'C':
            print("Operación cancelada.")
            return
        if sel not in folios_validos:
            print("Folio inválido. Intenta nuevamente.")
            continue
        break

    # 5) Validar que la fecha sea al menos 2 días posterior a hoy
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT fecha FROM reservaciones WHERE folio = ?", (sel,))
        resultado = cursor.fetchone()
        if not resultado:
            print("No se encontró la reservación seleccionada.")
            return
        fecha_res = datetime.strptime(resultado[0], "%m-%d-%Y").date()

    if fecha_res <= hoy() + timedelta(days=1):
        print("Solo pueden cancelarse reservaciones con al menos dos días de anticipación.")
        return

    # 6) Confirmar cancelación
    confirmar = input(f"¿Confirmas la cancelación de la reservación {sel}? (S/N): ").strip().upper()
    if confirmar != 'S':
        print("Operación cancelada por el usuario.")
        return

    # 7) Registrar como cancelada (sin borrar)
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reservaciones SET evento = '[CANCELADO] ' || evento WHERE folio = ?", (sel,))
        conn.commit()
    print(f"Reservación {sel} cancelada correctamente.")

def salas_disponibles_para_fecha(fecha):
    """Devuelve dict sala_id -> lista de turnos disponibles para esa fecha desde SQLite."""
    disponible = {}
    fecha_str = date_a_str(fecha)

    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        # Obtener todas las salas
        cursor.execute("SELECT id_sala, nombre, cupo FROM salas")
        salas = cursor.fetchall()
        # Obtener reservaciones para la fecha
        cursor.execute("SELECT sala_id, turno FROM reservaciones WHERE fecha = ?", (fecha_str,))
        reservaciones_fecha = cursor.fetchall()

    for sid, _, _ in salas:
        turnos_libres = set(TURNOS)
        for sala_id, turno in reservaciones_fecha:
            if sala_id == sid:
                turnos_libres.discard(turno)
        if turnos_libres:
            disponible[sid] = sorted(list(turnos_libres), key=lambda t: TURNOS.index(t))

    return disponible



def registrar_reservacion():
    """Registra una reservación validando todas las condiciones."""
    print("\nRegistrar reservación de sala")
    # 1) elegir cliente (solo clientes registrados)
    cid = elegir_cliente_o_cancelar()
    if not cid:
        print("Operación cancelada o no hay clientes.")
        return
    # 2) fecha: al menos 2 días después de la fecha del sistema
    while True:
        fecha_input = input(f"Ingrese fecha de la reservación (MM-DD-YYYY). Hoy: {date_a_str(hoy())} : ").strip()
        d = validar_fecha_input(fecha_input)
        if not d:
            print("Formato inválido. Usa MM-DD-YYYY.")
            continue
        if d.weekday() == 6:  # Domingo
            lunes_siguiente = d + timedelta(days=1)
            print(f"No se permiten reservaciones en domingo. Se propone el {date_a_str(lunes_siguiente)}.")
            opcion = input("¿Deseas usar esta fecha? (S/N): ").strip().upper()
            if opcion == "S":
                d = lunes_siguiente
            else:
                continue
        if d < hoy() + timedelta(days=2):
            print("La fecha debe ser, como mínimo, dos días posteriores a la fecha actual del sistema.")
            continue
        break
    # 3) mostrar salas con algún turno disponible para esa fecha
    disponibles = salas_disponibles_para_fecha(d)
    if not disponibles:
        print("No hay salas con turnos disponibles para esa fecha.")
        return
    print("\nSalas con al menos un turno disponible para", date_a_str(d))
    for sid, turnos in disponibles.items():
        with sqlite3.connect("coworking.db") as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT nombre, cupo FROM salas WHERE id_sala = ?", (sid,))
            sala = cursor.fetchone()
            if sala:
                print(f"  {sid} -> {sala[0]} (cupo {sala[1]}), turnos disponibles: {', '.join(turnos)}")
    # 4) elegir sala
    while True:
        sel_sala = input("Ingresa la clave de la sala que deseas reservar (o 'C' para cancelar): ").strip()
        if sel_sala.upper() == 'C':
            print("Operación cancelada.")
            return
        if sel_sala not in disponibles:
            print("Clave inválida o la sala no tiene turnos disponibles en esa fecha. Intenta de nuevo.")
            continue
        break
    # 5) mostrar y elegir turno disponible para esa sala
    turnos_libres = disponibles[sel_sala]
    print("Turnos disponibles para esa sala:", ", ".join(turnos_libres))
    while True:
        sel_turno = input("Selecciona turno (Matutino/Vespertino/Nocturno) o 'C' para cancelar: ").strip().capitalize()
        if sel_turno.upper() == 'C':
            print("Operación cancelada.")
            return
        if sel_turno not in turnos_libres:
            print("Turno inválido o no disponible. Intenta de nuevo.")
            continue
        break
    # 6) nombre del evento (no puede estar vacío ni solo espacios)
    while True:
        evento = input("Nombre del evento (no puede quedar vacío): ").strip()
        if not evento:
            print("Nombre inválido. Debe contener al menos un carácter distinto de espacios.")
            continue
        break
    # 7) generar folio único y registrar
    folio = next_folio()
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO reservaciones (folio, cliente_id, sala_id, fecha, turno, evento) VALUES (?, ?, ?, ?, ?, ?)",
            (folio, cid, sel_sala, date_a_str(d), sel_turno, evento)
        )
        conn.commit()
    print(f"\nReservación registrada con folio: {folio}")
    print(f"Cliente: {cliente_nombre_completo(cid)}")
    print(f"Sala: {sala_display_name(sel_sala)}")
    print(f"Fecha: {date_a_str(d)}  Turno: {sel_turno}")
    print(f"Evento: {evento}")
    print("Nota: Una vez hecha la reservación no puede cancelarse (solo puede editarse el nombre del evento).")





def editar_nombre_evento_por_rango():
    """Pregunta rango de fechas, muestra eventos en ese rango y permite editar nombre de evento por folio."""
    print("\nEditar nombre del evento de una reservación")
    # Pedir rango
    while True:
        inicio = input("Fecha inicio (MM-DD-YYYY): ").strip()
        d_ini = validar_fecha_input(inicio)
        if not d_ini:
            print("Fecha inicio inválida.")
            continue
        fin = input("Fecha fin (MM-DD-YYYY): ").strip()
        d_fin = validar_fecha_input(fin)
        if not d_fin:
            print("Fecha fin inválida.")
            continue
        if d_fin < d_ini:
            print("La fecha fin debe ser igual o posterior a la fecha inicio.")
            continue
        break

    inicio_str = date_a_str(d_ini)
    fin_str = date_a_str(d_fin)

    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT folio, fecha, evento
            FROM reservaciones
            WHERE fecha BETWEEN ? AND ?
            ORDER BY fecha, folio
        ''', (inicio_str, fin_str))
        reservaciones_rango = cursor.fetchall()

    if not reservaciones_rango:
        print("No hay eventos en ese rango de fechas.")
        return

    print("\nEventos en el rango seleccionado:")
    mostrar_linea()
    print(f"{'Folio':12} {'Fecha':12} {'Evento'}")
    mostrar_linea()
    for folio, fecha, evento in reservaciones_rango:
        print(f"{folio:12} {fecha:12} {evento}")
    mostrar_linea()

    folios_validos = {folio for folio, _, _ in reservaciones_rango}
    while True:
        sel = input("Ingresa la clave (folio) del evento a modificar o 'C' para cancelar: ").strip()
        if sel.upper() == 'C':
            print("Operación cancelada.")
            return
        if sel not in folios_validos:
            print("Folio no válido para el rango mostrado. Intenta de nuevo.")
            continue
        break

    # Editar nombre del evento (no permitir vacío)
    while True:
        nuevo = input("Nuevo nombre del evento (no puede quedar vacío): ").strip()
        if not nuevo:
            print("Nombre inválido. Intenta de nuevo.")
            continue
        break

    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("UPDATE reservaciones SET evento = ? WHERE folio = ?", (nuevo, sel))
        conn.commit()
    print(f"Evento {sel} actualizado correctamente. Nuevo nombre: {nuevo}")


def mostrar_menu():
    print(textwrap.dedent("""
    ========= SISTEMA DE RESERVACIONES - COWORKIN =========
    1) Registrar la reservación de una sala
    2) Editar el nombre del evento de una reservación (por rango de fechas)
    3) Consultar las reservaciones existentes para una fecha específica
    4) Registrar a un nuevo cliente
    5) Registrar una sala
    6) Cancelar reservacion (orden alfabético)
    7) salir
   
    =======================================================
    """))

def listar_todas_reservaciones():
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute('''
            SELECT r.folio, r.fecha, r.turno, s.nombre, c.apellidos, c.nombre, r.evento
            FROM reservaciones r
            JOIN salas s ON r.sala_id = s.id_sala
            JOIN clientes c ON r.cliente_id = c.id_cliente
            ORDER BY r.fecha, r.folio
        ''')
        reservaciones = cursor.fetchall()

    if not reservaciones:
        print("No hay reservaciones registradas.")
        return
    mostrar_linea()
    print(f"{'Folio':12} {'Fecha':12} {'Turno':10} {'Sala':20} {'Cliente':25} {'Evento'}")
    mostrar_linea()
    for folio, fecha, turno, sala_nombre, apellidos, nombre, evento in reservaciones:
        cliente_nombre = f"{apellidos}, {nombre}"
        print(f"{folio:12} {fecha:12} {turno:10} {sala_nombre[:18]:20} {cliente_nombre[:23]:25} {evento}")
    mostrar_linea()



def listar_salas():
    with sqlite3.connect("coworking.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id_sala, nombre, cupo FROM salas ORDER BY id_sala")
        salas = cursor.fetchall()

    if not salas:
        print("No hay salas registradas.")
        return
    print("\nSalas registradas:")
    for sid, nombre, cupo in salas:
        print(f"  {sid} -> {nombre} (cupo {cupo})")


    
    

def cargar_datos_ejemplo():
    
    # salas
    pass


def main():
    print("Iniciando sistema de reservaciones (memoria RAM).")
    crear_tablas()
    if cargar_estado():
        print("Se cargó el estado anterior del sistema.")
    else:
        print("No se encontró estado anterior. Iniciando con datos vacíos.")
    # cargar datos de ejemplo para facilitar pruebas:
    cargar_datos_ejemplo()

    while True:
        mostrar_menu()
        opcion = input("Selecciona una opción: ").strip()
        if opcion == '1':
            registrar_reservacion()
        elif opcion == '2':
            editar_nombre_evento_por_rango()
        elif opcion == '3':
            consultar_reservaciones_por_fecha()
        elif opcion == '4':
            registrar_cliente()
        elif opcion == '5':
            registrar_sala()
        elif opcion == '20':
           
            lista = listar_clientes_ordenados()
            print("\nClientes registrados:")
            for k, n in lista:
                print(f"  {k} -> {n}")
       
        elif opcion == '75':
            
            listar_salas()
        elif opcion == '8':
            listar_todas_reservaciones()
        elif opcion == '6':
          cancelar_reservacion()
        elif opcion == '7':
            confirmar = input("¿Estás seguro de que deseas salir? (S/N): ").strip().upper()
            if confirmar == 'S':
              #guardar_estado()  # Guarda el estado antes de salir
              print("Estado guardado. Saliendo.")
              break
            else:
                 print("Regresando al menú principal.")

if __name__ == "__main__":
    main()