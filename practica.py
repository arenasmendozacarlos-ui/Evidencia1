
from datetime import datetime, timedelta
import itertools
import textwrap


print("hola")
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
        d = datetime.strptime(fecha_str, "%Y-%m-%d").date()
        return d
    except ValueError:
        return None

def date_a_str(d):
    return d.strftime("%Y-%m-%d")

def cliente_nombre_completo(cid):
    c = clientes.get(cid)
    if not c:
        return "(cliente eliminado)"
    return f"{c['apellidos']}, {c['nombre']}"

def sala_display_name(sid):
    s = salas.get(sid)
    if not s:
        return "(sala eliminada)"
    return f"{s['nombre']} (cupo {s['cupo']})"

def mostrar_linea():
    print("-" * 60)

# -------------------------
# Funcionalidades principales
# -------------------------
def registrar_cliente():
    """Pide datos y registra un cliente con clave automática."""
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
    clientes[cid] = {'nombre': nombre, 'apellidos': apellidos}
    print(f"Cliente registrado con clave: {cid}")

def listar_clientes_ordenados():
    print("Hola")
    """Devuelve lista de tuplas (clave, nombre completo) ordenada por apellidos, nombre."""
    items = [(k, v['apellidos'], v['nombre']) for k, v in clientes.items()]
    items.sort(key=lambda x: (x[1].lower(), x[2].lower()))
    return [(k, f"{ap} , {nm}") for (k, ap, nm) in items]

def elegir_cliente_o_cancelar():
    """Muestra clientes ordenados; permite elegir clave o cancelar. Devuelve cliente_id o None."""
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
        if sel in clientes:
            return sel
        print("La clave ingresada no existe. Vuelve a intentarlo o presiona 'C' para cancelar.")

def registrar_sala():
    """Registra una sala nueva con clave automática."""
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
    salas[sid] = {'nombre': nombre, 'cupo': cupo}
    print(f"Sala registrada con clave: {sid}")

def salas_disponibles_para_fecha(fecha):
    """Devuelve dict sala_id -> lista de turnos disponibles para esa fecha."""
    disponible = {}
    for sid in salas:
        # todos los turnos inicialmente disponibles
        turnos_libres = set(TURNOS)
        for r in reservaciones.values():
            if r['sala_id'] == sid and r['fecha'] == date_a_str(fecha):
                # turno reservado -> quitarlo
                turnos_libres.discard(r['turno'])
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
        fecha_input = input(f"Ingrese fecha de la reservación (YYYY-MM-DD). Hoy: {date_a_str(hoy())} : ").strip()
        d = validar_fecha_input(fecha_input)
        if not d:
            print("Formato inválido. Use YYYY-MM-DD.")
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
        s = salas[sid]
        print(f"  {sid} -> {s['nombre']} (cupo {s['cupo']}), turnos disponibles: {', '.join(turnos)}")

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
    reservaciones[folio] = {
        'cliente_id': cid,
        'sala_id': sel_sala,
        'fecha': date_a_str(d),
        'turno': sel_turno,
        'evento': evento
    }
    print(f"\nReservación registrada con folio: {folio}")
    print(f"Cliente: {cliente_nombre_completo(cid)}")
    print(f"Sala: {sala_display_name(sel_sala)}")
    print(f"Fecha: {date_a_str(d)}  Turno: {sel_turno}")
    print(f"Evento: {evento}")
    print("Nota: Una vez hecha la reservación no puede cancelarse (solo puede editarse el nombre del evento).")

def consultar_reservaciones_por_fecha():
    """Muestra reporte tabular similar a la figura 1 para una fecha específica."""
    print("\nConsultar reservaciones para una fecha específica")
    fecha_input = input("Ingresa la fecha (YYYY-MM-DD): ").strip()
    d = validar_fecha_input(fecha_input)
    if not d:
        print("Fecha inválida.")
        return
    fecha_str = date_a_str(d)
    matches = []
    for folio, r in reservaciones.items():
        if r['fecha'] == fecha_str:
            matches.append((folio, r['sala_id'], r['cliente_id'], r['turno'], r['evento']))
    if not matches:
        print("No hay reservaciones para esa fecha.")
        return

    # Mostrar tabla simple
    mostrar_linea()
    print(f"Reservaciones para la fecha {fecha_str}")
    mostrar_linea()
    print(f"{'Folio':12} {'Sala':30} {'Cliente':30} {'Turno':10} {'Evento'}")
    mostrar_linea()
    for folio, sid, cid, turno, evento in matches:
        sala_nom = salas.get(sid, {}).get('nombre', sid)
        cliente_nom = cliente_nombre_completo(cid)
        print(f"{folio:12} {sala_nom[:28]:30} {cliente_nom[:28]:30} {turno:10} {evento}")
    mostrar_linea()

def editar_nombre_evento_por_rango():
    """Pregunta rango de fechas, muestra eventos en ese rango y permite editar nombre de evento por folio."""
    print("\nEditar nombre del evento de una reservación")
    # pedir rango
    while True:
        inicio = input("Fecha inicio (YYYY-MM-DD): ").strip()
        d_ini = validar_fecha_input(inicio)
        if not d_ini:
            print("Fecha inicio inválida.")
            continue
        fin = input("Fecha fin (YYYY-MM-DD): ").strip()
        d_fin = validar_fecha_input(fin)
        if not d_fin:
            print("Fecha fin inválida.")
            continue
        if d_fin < d_ini:
            print("La fecha fin debe ser igual o posterior a la fecha inicio.")
            continue
        break

    # listar reservaciones dentro del rango (inclusivo)
    listado = []
    for folio, r in reservaciones.items():
        d_r = validar_fecha_input(r['fecha'])
        if d_r and d_ini <= d_r <= d_fin:
            listado.append((folio, r['fecha'], r['evento']))
    if not listado:
        print("No hay eventos en ese rango de fechas.")
        return

    listado.sort(key=lambda x: (x[1], x[0]))  # ordenar por fecha, folio
    print("\nEventos en el rango seleccionado:")
    mostrar_linea()
    print(f"{'Folio':12} {'Fecha':12} {'Evento'}")
    mostrar_linea()
    for folio, fecha, evento in listado:
        print(f"{folio:12} {fecha:12} {evento}")
    mostrar_linea()

    # elegir folio válido dentro del listado
    folios_validos = {f for f, _, _ in listado}
    while True:
        sel = input("Ingresa la clave (folio) del evento a modificar o 'C' para cancelar: ").strip()
        if sel.upper() == 'C':
            print("Operación cancelada.")
            return
        if sel not in folios_validos:
            print("Folio no válido para el rango mostrado. Intenta de nuevo.")
            continue
        break

    # editar nombre del evento (no permitir vacío)
    while True:
        nuevo = input("Nuevo nombre del evento (no puede quedar vacío): ").strip()
        if not nuevo:
            print("Nombre inválido. Intenta de nuevo.")
            continue
        break

    reservaciones[sel]['evento'] = nuevo
    print(f"Evento {sel} actualizado correctamente. Nuevo nombre: {nuevo}")

def mostrar_menu():
    print(textwrap.dedent("""
    ========= SISTEMA DE RESERVACIONES - COWORKIN =========
    1) Registrar la reservación de una sala
    2) Editar el nombre del evento de una reservación (por rango de fechas)
    3) Consultar las reservaciones existentes para una fecha específica
    4) Registrar a un nuevo cliente
    5) Registrar una sala
    6) Listar clientes (orden alfabético)
    7) Listar salas
    8) Listar todas las reservaciones
    0) Salir
    =======================================================
    """))

def listar_todas_reservaciones():
    if not reservaciones:
        print("No hay reservaciones registradas.")
        return
    mostrar_linea()
    print(f"{'Folio':12} {'Fecha':12} {'Turno':10} {'Sala':20} {'Cliente':25} {'Evento'}")
    mostrar_linea()
    for folio, r in sorted(reservaciones.items(), key=lambda x: (x[1]['fecha'], x[0])):
        sid = r['sala_id']
        cid = r['cliente_id']
        print(f"{folio:12} {r['fecha']:12} {r['turno']:10} {salas.get(sid, {}).get('nombre','?')[:18]:20} {cliente_nombre_completo(cid)[:23]:25} {r['evento']}")
    mostrar_linea()

def listar_salas():
    
    if not salas:
        print("No hay salas registradas.")
        return
    print("\nSalas registradas:")
    for sid, s in sorted(salas.items()):
        print(f"  {sid} -> {s['nombre']} (cupo {s['cupo']})")

def cargar_datos_ejemplo():
    # clientes
    clientes['C001'] = {'nombre': 'Ana', 'apellidos': 'Gómez'}
    clientes['C002'] = {'nombre': 'Luis', 'apellidos': 'Pérez'}
    clientes['C003'] = {'nombre': 'María', 'apellidos': 'Zúñiga'}
   
    for _ in range(3):
        next(_cliente_counter)
    # salas
    salas['S001'] = {'nombre': 'Sala A', 'cupo': 6}
    salas['S002'] = {'nombre': 'Sala B', 'cupo': 10}
    salas['S003'] = {'nombre': 'Sala C', 'cupo': 4}
    for _ in range(3):
        next(_sala_counter)
    
    print("Se cargaron datos de ejemplo: 3 clientes y 3 salas.\n")


def main():
    print("Iniciando sistema de reservaciones (memoria RAM).")
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
        elif opcion == '6':
           
            lista = listar_clientes_ordenados()
            print("\nClientes registrados:")
            for k, n in lista:
                print(f"  {k} -> {n}")
       
        elif opcion == '7':
            
            listar_salas()
        elif opcion == '8':
            listar_todas_reservaciones()
        elif opcion == '0':
            print("Saliendo. Todos los datos se perderán al cerrar el programa (solo RAM).")
            break
        else:
            print("Opción no válida. Intenta de nuevo.")

if __name__ == "__main__":
    main()
