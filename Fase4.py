import abc          # Clases abstractas
import logging      # Registro de logs en archivo
import datetime     # Manejo de fechas y horas
import re           # Expresiones regulares
import uuid         # Generar identificadores únicos
from typing import Optional, List  # Anotaciones de tipo

# Configuración de logs
logging.basicConfig(
    filename="software_fj.log",
    level=logging.DEBUG,
    format='%(asctime)s | %(levelname)s | %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    encoding='utf-8'
)
logger = logging.getLogger(__name__)     # Obtiene el objeto logger con el nombre del módulo actual

# Excepción base del sistema
class SoftwareFJError(Exception):        

    def __init__(self, mensaje: str, codigo: str = "ERR_GENERAL"):   # Llama al constructor de la clase padre
        super().__init__(mensaje)
        self.mensaje = mensaje      # Mensaje del error
        self.codigo = codigo        # Código del error
        self.timestamp = datetime.datetime.now()    # Momento del error

    def __str__(self):       # Define cómo se muestra el error
        return f"[{self.codigo}] {self.mensaje} (ocurrido: {self.timestamp.strftime('%H:%M:%S')})"

# Se lanza cuando los datos de un cliente son inválidos
class ClienteInvalidoError(SoftwareFJError):

    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_CLIENTE")

# Se lanza cuando un servicio no está disponible para reservar
class ServicioNoDisponibleError(SoftwareFJError):

    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_SERVICIO")

# Se lanza cuando una reserva no puede completarse
class ReservaInvalidaError(SoftwareFJError):

    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_RESERVA")

# Se lanza cuando falta un parámetro obligatorio
class ParametroFaltanteError(SoftwareFJError):

    def __init__(self, parametro: str):
        super().__init__(f"Parámetro obligatorio faltante: '{parametro}'", "ERR_PARAMETRO")

# Se lanza cuando el cálculo del costo produce un resultado inconsistente
class CalculoCostoError(SoftwareFJError):

    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_CALCULO")

# Se lanza cuando se intenta una operación prohibida
class OperacionNoPermitidaError(SoftwareFJError):

    def __init__(self, mensaje: str):
        super().__init__(mensaje, "ERR_OPERACION")

# Clase abstracta que representa cualquier entidad del sistema
class EntidadSistema(abc.ABC):
    # Verifica que el nombre no este vacío ni en None
    def __init__(self, nombre: str):
        if not nombre or not nombre.strip():
            raise ParametroFaltanteError("nombre")
        self._nombre = nombre.strip()          # Atributo protegido
        self._id = str(uuid.uuid4())[:8]       # ID único de 8 caracteres
        self._fecha_creacion = datetime.datetime.now()  # Fecha de registro

    # Propiedad de solo lectura para el ID de la entidad
    @property
    def id(self) -> str:        
        return self._id
    
    #Propiedad de solo lectura para el nombre
    @property
    def nombre(self) -> str:
        return self._nombre

    # Método abstracto: cada subclase implementa su propia descripción
    @abc.abstractmethod
    def describir(self) -> str:
        pass

    # Método abstracto: cada subclase implementa su propia validación
    @abc.abstractmethod
    def validar(self) -> bool:
        pass

    # Representación técnica del objeto
    def __repr__(self):
        return f"{self.__class__.__name__}(id={self._id}, nombre={self._nombre})"

# Representa un cliente, implementa encapsulación con atributos privados y propiedades con validación
class Cliente(EntidadSistema):

    # Constantes de clase para validaciones
    TELEFONO_REGEX = re.compile(r'^\+?[\d\s\-]{7,15}$')   # Patrón válido de teléfono
    EMAIL_REGEX = re.compile(r'^[\w\.-]+@[\w\.-]+\.\w{2,}$')  # Patrón válido de email

    # Constructor del cliente con validación de todos los campos
    def __init__(self, nombre: str, email: str, telefono: str, empresa: str = ""):

        try:
            # Inicializa la clase padre
            super().__init__(nombre)

            # Valida y asigna el email usando el setter
            self.email = email         # Llama a @email.setter automáticamente
            self.telefono = telefono   # Llama a @telefono.setter automáticamente

            # La empresa es opcional, se guarda directamente
            self.__empresa = empresa.strip() if empresa else "Independiente"

            # Lista privada de reservas asociadas al cliente
            self.__reservas: List = []

            # Registra en el log que el cliente fue creado exitosamente
            logger.info(f"Cliente creado: {self._nombre} | Email: {self.__email}")

        except SoftwareFJError:
            # Lanza excepciones propias del sistema sin modificarlas
            raise
        except Exception as e:
            # Captura cualquier otro error inesperado y lo convierte en error de cliente
            logger.error(f"Error inesperado al crear cliente '{nombre}': {e}")
            raise ClienteInvalidoError(f"Error al crear cliente: {str(e)}") from e
    # Retorna el valor privado
    @property
    def email(self) -> str:
        return self.__email
    # Setter del email con validación de formato
    @email.setter
    def email(self, valor: str):

        if not valor or not valor.strip():
            raise ClienteInvalidoError("El email no puede estar vacío")
        valor = valor.strip().lower()       # Normaliza a minúsculas
        if not self.EMAIL_REGEX.match(valor):
            # El formato no coincide con el patrón de email válido
            raise ClienteInvalidoError(f"Email inválido: '{valor}'. Formato esperado: usuario@dominio.com")
        self.__email = valor   # Solo se asigna si pasó la validación
    # Getter del teléfono
    @property
    def telefono(self) -> str:
        return self.__telefono
    # Setter del teléfono con validación de formato numérico
    @telefono.setter
    def telefono(self, valor: str):

        if not valor or not valor.strip():
            raise ClienteInvalidoError("El teléfono no puede estar vacío")
        valor = valor.strip()
        if not self.TELEFONO_REGEX.match(valor):
            raise ClienteInvalidoError(f"Teléfono inválido: '{valor}'. Solo números, espacios, guiones y +")
        self.__telefono = valor
    #Getter de la empresa
    @property
    def empresa(self) -> str:
        return self.__empresa
    # Retorna una copia de la lista de reservas
    @property
    def reservas(self) -> List:
        return list(self.__reservas)  # Copia defensiva para proteger la lista interna

    # Agrega una reserva a la lista interna del cliente
    def agregar_reserva(self, reserva) -> None:
        if reserva is None:
            raise ParametroFaltanteError("reserva")
        self.__reservas.append(reserva)
        logger.debug(f"Reserva {reserva.id} agregada al cliente {self._nombre}")
    # Descripción del cliente
    def describir(self) -> str:
        return (
            f"Cliente: {self._nombre}\n"
            f"  ID: {self._id}\n"
            f"  Email: {self.__email}\n"
            f"  Teléfono: {self.__telefono}\n"
            f"  Empresa: {self.__empresa}\n"
            f"  Reservas activas: {len(self.__reservas)}"
        )
    # Verificación datos válidos
    def validar(self) -> bool:
        try:
            return bool(
                self._nombre and           # Nombre no vacío
                self.__email and           # Email no vacío
                self.__telefono and        # Teléfono no vacío
                self.EMAIL_REGEX.match(self.__email)  # Email con formato válido
            )
        except Exception:
            return False

# Clase abstracta que representa el servicio ofrecido
class Servicio(EntidadSistema):

    # Estados posibles de un servicio
    ESTADOS_VALIDOS = {"disponible", "ocupado", "mantenimiento", "suspendido"}

    #Constructor base para todos los servicios
    def __init__(self, nombre: str, precio_base: float, capacidad_maxima: int = 1):

        super().__init__(nombre)  # Inicializa EntidadSistema

        # Valida que el precio sea un número positivo
        if precio_base <= 0:
            raise ServicioNoDisponibleError(f"El precio base debe ser mayor a 0, recibido: {precio_base}")

        # Valida que la capacidad sea un entero positivo
        if not isinstance(capacidad_maxima, int) or capacidad_maxima < 1:
            raise ServicioNoDisponibleError("La capacidad máxima debe ser un entero positivo")

        self._precio_base = float(precio_base)     # Precio por hora
        self._capacidad_maxima = capacidad_maxima  # Max. usuarios simultáneos
        self._estado = "disponible"                # Estado inicial siempre disponible
        self._reservas_activas = 0                 # Contador de reservas en curso

    # Getter del precio base
    @property
    def precio_base(self) -> float:
        return self._precio_base

    # Getter del estado actual del servicio
    @property
    def estado(self) -> str:
        return self._estado

    # Setter del estado con validación de valores permitidos
    @estado.setter
    def estado(self, nuevo_estado: str):
        if nuevo_estado not in self.ESTADOS_VALIDOS:
            raise ServicioNoDisponibleError(
                f"Estado '{nuevo_estado}' no válido. Permitidos: {self.ESTADOS_VALIDOS}"
            )
        self._estado = nuevo_estado
        logger.info(f"Servicio '{self._nombre}' cambió a estado: {nuevo_estado}")

    # Verifica si el servicio puede aceptar nuevas reservas
    def esta_disponible(self) -> bool:
        return (
            self._estado == "disponible" and
            self._reservas_activas < self._capacidad_maxima
        )

    # Calculo de costo de cada servicio
    @abc.abstractmethod
    def calcular_costo(self, horas: float, **kwargs) -> float:
        pass
    
    # Definición de cada servicio de sus reglas de validación
    @abc.abstractmethod
    def validar_parametros(self, horas: float, **kwargs) -> bool:
        pass
    
    # calculo del costo total con IVA
    def calcular_costo_con_impuesto(self, horas: float, tasa_impuesto: float = 0.19, **kwargs) -> float:
        try:
            # Valida la tasa del impuesto
            if not (0 <= tasa_impuesto <= 1):
                raise CalculoCostoError(f"Tasa de impuesto inválida: {tasa_impuesto}. Debe estar entre 0 y 1")

            costo_base = self.calcular_costo(horas, **kwargs)  # Costo sin impuesto
            impuesto = costo_base * tasa_impuesto              # Valor del impuesto
            total = costo_base + impuesto                      # Total con impuesto

            if total < 0:
                raise CalculoCostoError(f"El costo calculado es negativo: {total}")

            return round(total, 2)  # Redondea a 2 decimales

        except SoftwareFJError:
            raise  # Lanza excepciones propias
        except Exception as e:
            raise CalculoCostoError(f"Error al calcular costo con impuesto: {str(e)}") from e

    # Se aplica un porcentaje de descuento
    def calcular_costo_con_descuento(self, horas: float, descuento: float = 0.0, **kwargs) -> float:
        try:
            # Valida el descuento
            if not (0 <= descuento <= 0.5):
                raise CalculoCostoError(f"Descuento inválido: {descuento}. Debe ser entre 0 y 0.5 (50%)")

            costo_base = self.calcular_costo(horas, **kwargs)
            ahorro = costo_base * descuento          # Valor del descuento
            total = costo_base - ahorro              # Total con descuento aplicado

            return round(total, 2)

        except SoftwareFJError:
            raise
        except Exception as e:
            raise CalculoCostoError(f"Error al calcular costo con descuento: {str(e)}") from e

    # Implementación del método abstracto de EntidadSistema
    def validar(self) -> bool:
        return (
            bool(self._nombre) and
            self._precio_base > 0 and
            self._estado in self.ESTADOS_VALIDOS
        )

    # Descripción básica del servicio
    def describir(self) -> str:
        return (
            f"Servicio: {self._nombre}\n"
            f"  ID: {self._id}\n"
            f"  Precio base: ${self._precio_base:,.0f}/hora\n"
            f"  Estado: {self._estado}\n"
            f"  Capacidad: {self._capacidad_maxima} usuario(s)"
        )


# Servicio de reserva
class ReservaSala(Servicio):

    # Tipos de sala y multiplicadores de precio
    TIPOS_SALA = {
        "basica": 1.0,          # Sala estándar sin equipamiento especial
        "conferencia": 1.5,     # Sala con proyector y audio
        "capacitacion": 2.0,    # Sala con PCs y recursos educativos
        "ejecutiva": 3.0        # Sala premium con videoconferencia HD
    }

    # Constructor de ReservaSala con parámetros específicos
    def __init__(self, nombre: str, precio_base: float, tipo_sala: str = "basica",
                 capacidad_personas: int = 10):

        # Valida el tipo de sala antes de llamar al padre
        tipo_sala = tipo_sala.lower().strip()
        if tipo_sala not in self.TIPOS_SALA:
            raise ServicioNoDisponibleError(
                f"Tipo de sala '{tipo_sala}' no válido. Opciones: {list(self.TIPOS_SALA.keys())}"
            )

        # Valida la capacidad de personas
        if capacidad_personas < 1 or capacidad_personas > 200:
            raise ServicioNoDisponibleError("La capacidad de personas debe estar entre 1 y 200")

        super().__init__(nombre, precio_base)  # Llama al constructor de Servicio

        self.__tipo_sala = tipo_sala                      # Tipo de sala
        self.__capacidad_personas = capacidad_personas    # Máx. personas

        logger.info(f"Sala creada: {nombre} | Tipo: {tipo_sala} | Cap: {capacidad_personas} personas")

    # Implementación polimórfica del cálculo de costo para sala
    def calcular_costo(self, horas: float, **kwargs) -> float:

        # Valida los parámetros antes de calcular
        if not self.validar_parametros(horas):
            raise CalculoCostoError(f"Parámetros inválidos para reserva de sala: horas={horas}")

        multiplicador = self.TIPOS_SALA[self.__tipo_sala]   # Obtiene el multiplicador
        costo = self._precio_base * horas * multiplicador   # Fórmula del costo

        logger.debug(f"Costo sala '{self._nombre}': ${costo:,.0f} ({horas}h × multiplicador {multiplicador})")
        return round(costo, 2)
    # Valida que las horas estén dentro del rango permitido para salas
    def validar_parametros(self, horas: float, **kwargs) -> bool:
        try:
            return isinstance(horas, (int, float)) and 1 <= horas <= 24
        except Exception:
            return False

    # Descripción detallada de la sala
    def describir(self) -> str:
        return (
            f"=== RESERVA DE SALA ===\n"
            f"  Nombre: {self._nombre}\n"
            f"  Tipo: {self.__tipo_sala.capitalize()}\n"
            f"  Precio base: ${self._precio_base:,.0f}/hora\n"
            f"  Multiplicador: ×{self.TIPOS_SALA[self.__tipo_sala]}\n"
            f"  Capacidad personas: {self.__capacidad_personas}\n"
            f"  Estado: {self._estado}"
        )


# Servicio de alquiler de equipos
class AlquilerEquipo(Servicio):

    # Categorías de equipo con sus precios adicionales por hora
    CATEGORIAS_EQUIPO = {
        "laptop": 15000,         # Laptop estándar
        "laptop_premium": 35000, # Laptop de alto rendimiento
        "proyector": 20000,      # Proyector HD
        "servidor": 80000,       # Servidor temporal para desarrollo
        "tablet": 10000,         # Tablet para presentaciones
        "camara": 25000          # Cámara profesional para grabaciones
    }

    # Constructor con validación del tipo de equipo y unidades disponibles
    def __init__(self, nombre: str, precio_base: float, categoria: str,
                 unidades_disponibles: int = 5):

        categoria = categoria.lower().strip()
        if categoria not in self.CATEGORIAS_EQUIPO:
            raise ServicioNoDisponibleError(
                f"Categoría '{categoria}' no válida. Opciones: {list(self.CATEGORIAS_EQUIPO.keys())}"
            )

        if unidades_disponibles < 1:
            raise ServicioNoDisponibleError("Debe haber al menos 1 unidad disponible")

        # El parámetro capacidad_maxima representa las unidades disponibles
        super().__init__(nombre, precio_base, capacidad_maxima=unidades_disponibles)

        self.__categoria = categoria                                 # Tipo de equipo
        self.__precio_categoria = self.CATEGORIAS_EQUIPO[categoria]  # Precio adicional

        logger.info(f"Equipo creado: {nombre} | Categoría: {categoria} | Unidades: {unidades_disponibles}")

    # Costo alquiler
    def calcular_costo(self, horas: float, **kwargs) -> float:
        if not self.validar_parametros(horas):
            raise CalculoCostoError(f"Horas inválidas para alquiler: {horas}. Debe ser entre 1 y 72")

        precio_hora = self._precio_base + self.__precio_categoria   # Precio total por hora
        costo = precio_hora * horas                                 # Costo base

        # Aplica recargo por uso prolongado
        if horas > 8:
            recargo = costo * 0.10  # 10% de recargo
            costo += recargo
            logger.debug(f"Recargo del 10% aplicado por {horas}h de uso en equipo '{self._nombre}'")

        return round(costo, 2)
    
    # Equipos pueden alquilarse entre 1 y 72 horas
    def validar_parametros(self, horas: float, **kwargs) -> bool:
        try:
            return isinstance(horas, (int, float)) and 1 <= horas <= 72
        except Exception:
            return False
        
    # Descripción del equipo disponible
    def describir(self) -> str:
        return (
            f"=== ALQUILER DE EQUIPO ===\n"
            f"  Nombre: {self._nombre}\n"
            f"  Categoría: {self.__categoria.replace('_', ' ').capitalize()}\n"
            f"  Precio base: ${self._precio_base:,.0f}/hora\n"
            f"  Precio categoría: ${self.__precio_categoria:,.0f}/hora\n"
            f"  Unidades disponibles: {self._capacidad_maxima}\n"
            f"  Estado: {self._estado}"
        )

# Servicio asesoría especializada
class AsesoriaEspecializada(Servicio):

    # Áreas de asesoría disponibles
    AREAS_ASESORIA = {
        "tecnologia": 1.0,      # Desarrollo de software
        "negocios": 1.2,        # Estrategia empresarial
        "legal": 1.8,           # Consultoría jurídica
        "financiera": 1.5,      # Contabilidad
        "rrhh": 1.1             # Recursos humanos
    }

    # Niveles del asesor y su multiplicador de tarifa
    NIVELES_ASESOR = {
        "junior": 1.0,          # 0-2 años de experiencia
        "senior": 2.0,          # 3-7 años de experiencia
        "experto": 3.5          # +8 años o especialización avanzada
    }

    # Constructor con validación del área de asesoría y nivel del asesor
    def __init__(self, nombre: str, precio_base: float, area: str, nivel_asesor: str = "junior"):
        area = area.lower().strip()
        nivel_asesor = nivel_asesor.lower().strip()

        if area not in self.AREAS_ASESORIA:
            raise ServicioNoDisponibleError(
                f"Área '{area}' no válida. Opciones: {list(self.AREAS_ASESORIA.keys())}"
            )

        if nivel_asesor not in self.NIVELES_ASESOR:
            raise ServicioNoDisponibleError(
                f"Nivel '{nivel_asesor}' no válido. Opciones: {list(self.NIVELES_ASESOR.keys())}"
            )

        super().__init__(nombre, precio_base)

        self.__area = area                       # Área de especialización
        self.__nivel_asesor = nivel_asesor       # Nivel de experiencia
        self.__sesiones_realizadas = 0           # Contador de sesiones completadas

        logger.info(f"Asesoría creada: {nombre} | Área: {area} | Nivel: {nivel_asesor}")

    # Costo asesoría
    def calcular_costo(self, horas: float, **kwargs) -> float:
        if not self.validar_parametros(horas):
            raise CalculoCostoError(f"Horas inválidas para asesoría: {horas}. Debe ser entre 0.5 y 8")

        factor_area = self.AREAS_ASESORIA[self.__area]           # Multiplicador del área
        factor_nivel = self.NIVELES_ASESOR[self.__nivel_asesor]  # Multiplicador del nivel

        costo = self._precio_base * horas * factor_area * factor_nivel  # Fórmula base

        # Descuento automático por sesión extendida
        if horas > 4:
            descuento = costo * 0.15  # 15% de descuento por sesión larga
            costo -= descuento
            logger.debug(f"Descuento del 15% aplicado a asesoría larga ({horas}h) en '{self._nombre}'")

        return round(costo, 2)
    
    # Las asesorías van de 30 minutos a 8 horas
    def validar_parametros(self, horas: float, **kwargs) -> bool:
        try:
            return isinstance(horas, (int, float)) and 0.5 <= horas <= 8
        except Exception:
            return False
        
    # Descripción de la asesoría
    def describir(self) -> str:
        return (
            f" ASESORÍA ESPECIALIZADA \n"
            f"  Nombre: {self._nombre}\n"
            f"  Área: {self.__area.capitalize()}\n"
            f"  Nivel asesor: {self.__nivel_asesor.capitalize()}\n"
            f"  Precio base: ${self._precio_base:,.0f}/hora\n"
            f"  Factor área: ×{self.AREAS_ASESORIA[self.__area]}\n"
            f"  Factor nivel: ×{self.NIVELES_ASESOR[self.__nivel_asesor]}\n"
            f"  Sesiones realizadas: {self.__sesiones_realizadas}"
        )

    # Incrementa el contador de sesiones completadas
    def registrar_sesion_completada(self):
        self.__sesiones_realizadas += 1
        logger.info(f"Sesión completada en asesoría '{self._nombre}'. Total: {self.__sesiones_realizadas}")

# Clase Reserva gestiona el ciclo de vida de una reserva
class Reserva:

    # Estados válidos del ciclo de vida de una reserva
    ESTADOS = {
        "pendiente": "Esperando confirmación",
        "confirmada": "Confirmada, pendiente de ejecución",
        "en_proceso": "Servicio en curso",
        "completada": "Servicio finalizado exitosamente",
        "cancelada": "Reserva cancelada"
    }

    # Constructor que valida la disponibilidad del servicio y los datos del cliente
    def __init__(self, cliente: Cliente, servicio: Servicio,
                 horas: float, notas: str = ""):
        try:
            # Valida que se proporcionaron cliente y servicio
            if cliente is None:
                raise ParametroFaltanteError("cliente")
            if servicio is None:
                raise ParametroFaltanteError("servicio")

            # Verifica que el cliente tenga datos válidos
            if not cliente.validar():
                raise ReservaInvalidaError(f"El cliente '{cliente.nombre}' no tiene datos válidos")

            # Verifica que el servicio esté disponible
            if not servicio.esta_disponible():
                raise ServicioNoDisponibleError(
                    f"El servicio '{servicio.nombre}' no está disponible (estado: {servicio.estado})"
                )

            # Verifica que las horas sean válidas para el servicio específico
            if not servicio.validar_parametros(horas):
                raise ReservaInvalidaError(
                    f"Las horas ({horas}) no son válidas para el servicio '{servicio.nombre}'"
                )

            # Asigna todos los atributos de la reserva
            self.__id = str(uuid.uuid4())[:10]              # ID único de 10 caracteres
            self.__cliente = cliente                        # Referencia al cliente
            self.__servicio = servicio                      # Referencia al servicio
            self.__horas = float(horas)                     # Duración en horas
            self.__notas = notas.strip() if notas else ""   # Notas opcionales
            self.__estado = "pendiente"                     # Estado inicial
            self.__fecha_creacion = datetime.datetime.now() # Fecha de creación
            self.__fecha_confirmacion = None                # Se asigna al confirmar
            self.__costo_calculado = None                   # Se calcula al confirmar

            # Vincula la reserva al cliente
            cliente.agregar_reserva(self)

        except SoftwareFJError:
            logger.error(f"Error al crear reserva para cliente '{cliente.nombre if cliente else 'N/A'}'")
            raise  # Relanza la excepción para que sea manejada en el código llamante

        except Exception as e:
            # Error inesperado: lo envuelve en una excepción del sistema
            logger.critical(f"Error crítico al crear reserva: {e}")
            raise ReservaInvalidaError(f"Error inesperado al crear reserva: {str(e)}") from e

        finally:
            # El bloque finally siempre se ejecuta, haya error o no
            logger.debug("Intento de creación de reserva procesado (finally)")

    # ID único de la reserva
    @property
    def id(self) -> str:
        return self.__id

    # Estado actual de la reserva
    @property
    def estado(self) -> str:
        return self.__estado

    # Cliente asociado a la reserva
    @property
    def cliente(self) -> Cliente:
        return self.__cliente

    # Servicio asociado a la reserva
    @property
    def servicio(self) -> Servicio:
        return self.__servicio
    # Costo final calculado
    @property
    def costo_calculado(self) -> Optional[float]:
        return self.__costo_calculado

    # Confirma la reserva, calcula el costo y cambia el estado
    def confirmar(self, aplicar_descuento: float = 0.0, aplicar_impuesto: bool = True) -> float:
        try:
            # Verifica que la reserva esté en estado pendiente
            if self.__estado != "pendiente":
                raise OperacionNoPermitidaError(
                    f"No se puede confirmar una reserva en estado '{self.__estado}'. Solo se confirman reservas pendientes."
                )

            # Calcula el costo según los parámetros dados
            if aplicar_descuento > 0 and aplicar_impuesto:
                # Caso con descuento e impuesto: primero descuento, luego impuesto
                costo_con_descuento = self.__servicio.calcular_costo_con_descuento(
                    self.__horas, descuento=aplicar_descuento
                )
                # Calcula impuesto sobre el costo ya descontado
                self.__costo_calculado = round(costo_con_descuento * 1.19, 2)

            elif aplicar_descuento > 0:
                # Solo descuento, sin impuesto
                self.__costo_calculado = self.__servicio.calcular_costo_con_descuento(
                    self.__horas, descuento=aplicar_descuento
                )

            elif aplicar_impuesto:
                # Solo impuesto, sin descuento
                self.__costo_calculado = self.__servicio.calcular_costo_con_impuesto(self.__horas)

            else:
                # Sin descuento ni impuesto
                self.__costo_calculado = self.__servicio.calcular_costo(self.__horas)

        except SoftwareFJError:
            logger.error(f"Error al confirmar reserva {self.__id}")
            raise  # Propaga la excepción

        except Exception as e:
            # Encadenamiento de excepciones
            raise ReservaInvalidaError(f"Error inesperado al confirmar: {str(e)}") from e

        else:
            # El bloque else solo se ejecuta si no hubo excepción en try
            self.__estado = "confirmada"
            self.__fecha_confirmacion = datetime.datetime.now()
            logger.info(
                f"Reserva {self.__id} CONFIRMADA | "
                f"Cliente: {self.__cliente.nombre} | "
                f"Servicio: {self.__servicio.nombre} | "
                f"Costo: ${self.__costo_calculado:,.0f} | "
                f"Horas: {self.__horas}"
            )
            return self.__costo_calculado

    # Cancela la reserva con registro del motivo
    def cancelar(self, motivo: str = "Sin motivo especificado") -> None:

        # Verifica que la reserva sea cancelable
        if self.__estado in ("completada", "cancelada"):
            raise OperacionNoPermitidaError(
                f"No se puede cancelar una reserva en estado '{self.__estado}'"
            )

        self.__estado = "cancelada"
        logger.warning(
            f"Reserva {self.__id} CANCELADA | "
            f"Cliente: {self.__cliente.nombre} | "
            f"Motivo: {motivo}"
        )
        print(f"Reserva cancelada. Motivo: {motivo}")

    # Simula el procesamiento del servicio
    def procesar(self) -> None:
        try:
            if self.__estado != "confirmada":
                raise OperacionNoPermitidaError(
                    f"Solo se pueden procesar reservas confirmadas. Estado actual: '{self.__estado}'"
                )

            # Cambia el estado a en_proceso
            self.__estado = "en_proceso"
            logger.info(f"Reserva {self.__id} iniciada: servicio '{self.__servicio.nombre}' en proceso")
            print(f"Procesando servicio: {self.__servicio.nombre} durante {self.__horas}h...")

            # Simula la finalización del servicio
            self.__estado = "completada"

            # Si es una asesoría registra la sesión completada
            if isinstance(self.__servicio, AsesoriaEspecializada):
                self.__servicio.registrar_sesion_completada()

            logger.info(f"Reserva {self.__id} COMPLETADA exitosamente")
            print(f"Servicio completado exitosamente.")

        except SoftwareFJError:
            raise
        except Exception as e:
            self.__estado = "cancelada"  # Cancela automáticamente si hay error
            logger.error(f"Error al procesar reserva {self.__id}: {e}")
            raise ReservaInvalidaError(f"Error durante el procesamiento: {str(e)}") from e

        finally:
            # Registra el estado final al terminar el procesamiento
            logger.debug(f"Estado final de reserva {self.__id}: {self.__estado}")

    # Descripción del estado actual de la reserva
    def describir(self) -> str:
        costo_str = f"${self.__costo_calculado:,.0f}" if self.__costo_calculado else "Pendiente de cálculo"
        return (
            f" RESERVA {self.__id} \n"
            f"  Cliente: {self.__cliente.nombre}\n"
            f"  Servicio: {self.__servicio.nombre}\n"
            f"  Duración: {self.__horas} hora(s)\n"
            f"  Estado: {self.__estado.upper()}\n"
            f"  Costo: {costo_str}\n"
            f"  Creada: {self.__fecha_creacion.strftime('%Y-%m-%d %H:%M')}\n"
            f"  Notas: {self.__notas or 'Sin notas'}"
        )

# Sistema central que gestiona todos los recursos 
class SistemaGestionFJ:

    # Inicializa las listas internas vacías del sistema
    def __init__(self):
        self.__clientes: List[Cliente] = []       # Lista de todos los clientes
        self.__servicios: List[Servicio] = []     # Lista de todos los servicios
        self.__reservas: List[Reserva] = []       # Lista de todas las reservas
        logger.info("=" * 60)
        logger.info("Sistema Software FJ iniciado")
        logger.info("=" * 60)
        print("\n" + "=" * 60)
        print("SISTEMA DE GESTIÓN - SOFTWARE FJ")
        print("=" * 60)

    # Registra un nuevo cliente con manejo completo de excepciones
    def registrar_cliente(self, nombre: str, email: str, telefono: str,
                           empresa: str = "") -> Optional[Cliente]:

        print(f"\n Registrando cliente: {nombre}...")
        try:
            # Verifica si el email ya está registrado
            if any(c.email == email.lower().strip() for c in self.__clientes):
                raise ClienteInvalidoError(f"Ya existe un cliente registrado con el email: {email}")

            # Intenta crear el cliente
            cliente = Cliente(nombre, email, telefono, empresa)
            self.__clientes.append(cliente)  # Solo se agrega si no hubo error

            print(f"Cliente registrado exitosamente. ID: {cliente.id}")
            return cliente

        except ClienteInvalidoError as e:
            # Error esperado datos inválidos del cliente
            logger.warning(f"Cliente no registrado (datos inválidos): {e}")
            print(f"Error de cliente: {e}")
            return None

        except SoftwareFJError as e:
            # Otros errores del sistema
            logger.error(f"Error del sistema al registrar cliente: {e}")
            print(f"Error del sistema: {e}")
            return None

        except Exception as e:
            # Error inesperado
            logger.critical(f"Error crítico al registrar cliente '{nombre}': {e}")
            print(f"Error inesperado: {e}")
            return None

    # Agrega un servicio al catálogo del sistema
    def registrar_servicio(self, servicio: Servicio) -> bool:

        print(f"\n Registrando servicio: {servicio.nombre}...")
        try:
            if not servicio.validar():
                raise ServicioNoDisponibleError(f"El servicio '{servicio.nombre}' no superó la validación")

            self.__servicios.append(servicio)
            print(f"Servicio registrado. ID: {servicio.id}")
            logger.info(f"Servicio registrado: {servicio.nombre} | ID: {servicio.id}")
            return True

        except SoftwareFJError as e:
            logger.error(f"Servicio no registrado: {e}")
            print(f"Error: {e}")
            return False

        except Exception as e:
            logger.critical(f"Error crítico al registrar servicio: {e}")
            print(f"Error inesperado: {e}")
            return False

    # Crea y procesa una reserva completa
    def crear_reserva(self, cliente: Cliente, servicio: Servicio, horas: float,
                       notas: str = "", descuento: float = 0.0,
                       con_impuesto: bool = True) -> Optional[Reserva]:
        print(f"\n Creando reserva: {cliente.nombre if cliente else 'N/A'} → {servicio.nombre if servicio else 'N/A'}...")
        reserva = None
        try:
            # Etapa 1: Crear la reserva
            reserva = Reserva(cliente, servicio, horas, notas)
            print(f"Reserva creada. ID: {reserva.id}")

            # Etapa 2: Confirmar y calcular el costo
            costo = reserva.confirmar(aplicar_descuento=descuento, aplicar_impuesto=con_impuesto)
            print(f"Reserva confirmada. Costo total: ${costo:,.0f} COP")

            # Etapa 3: Procesar el servicio
            reserva.procesar()

            # Agrega la reserva a la lista del sistema
            self.__reservas.append(reserva)
            return reserva

        except ParametroFaltanteError as e:
            logger.error(f"Parámetro faltante en reserva: {e}")
            print(f"Parámetro faltante: {e}")

        except ServicioNoDisponibleError as e:
            logger.warning(f"Servicio no disponible: {e}")
            print(f"Servicio no disponible: {e}")

        except ReservaInvalidaError as e:
            logger.error(f"Reserva inválida: {e}")
            print(f"Reserva inválida: {e}")

        except OperacionNoPermitidaError as e:
            logger.error(f"Operación no permitida: {e}")
            print(f"Operación no permitida: {e}")
            if reserva:
                reserva.cancelar("Error durante el proceso de reserva")

        except CalculoCostoError as e:
            logger.error(f"Error en cálculo de costo: {e}")
            print(f"Error de cálculo: {e}")

        except SoftwareFJError as e:
            logger.error(f"Error general del sistema: {e}")
            print(f"Error del sistema: {e}")

        except Exception as e:
            logger.critical(f"Error crítico no manejado en reserva: {e}")
            print(f"Error crítico: {e}")

        return None

    # Muestra un resumen del estado actual del sistema
    def mostrar_resumen(self) -> None:
        print("\n" + "=" * 60)
        print("    RESUMEN DEL SISTEMA - SOFTWARE FJ")
        print("=" * 60)
        print(f"  Clientes registrados:  {len(self.__clientes)}")
        print(f"  Servicios disponibles: {len(self.__servicios)}")
        print(f"  Reservas completadas:  {len(self.__reservas)}")

        # Calcula el total de ingresos de las reservas completadas
        ingresos = sum(r.costo_calculado for r in self.__reservas if r.costo_calculado)
        print(f"  Ingresos totales:      ${ingresos:,.0f} COP")
        print("=" * 60)

# Operaciones del sistema
# Función principal
def ejecutar_demostracion():

    # Instancia el sistema de gestión principal
    sistema = SistemaGestionFJ()

    print("\n" + "━" * 60)
    print("FASE 1: REGISTRO DE CLIENTES")
    print("━" * 60)

    # ── OPERACIÓN 1: Cliente válido ────────────────────────────────────────────
    c1 = sistema.registrar_cliente(
        "Laura Lopez", "laura.lopez@empresa.com", "+57 300 123 4567", "TechCorp S.A.S"
    )

    # ── OPERACIÓN 2: Cliente válido ────────────────────────────────────────────
    c2 = sistema.registrar_cliente(
        "Luis Martínez", "luis.martinez@gmail.com", "3151234567", "Freelancer"
    )

    # ── OPERACIÓN 3: Cliente con email inválido (sin @) ────────────────────────
    c3 = sistema.registrar_cliente(
        "Carlos Ruiz", "email-invalido-sin-arroba", "310-987-6543"
    )

    # ── OPERACIÓN 4: Cliente con nombre vacío ──────────────────────────────────
    c4 = sistema.registrar_cliente(
        "", "valido@correo.com", "3009876543"
    )

    # ── OPERACIÓN 5: Cliente válido con empresa ────────────────────────────────
    c5 = sistema.registrar_cliente(
        "Sofía Herrera", "sofia.h@consultores.co", "+57 1 234 5678", "Consultores Unidos"
    )

    print("\n" + "━" * 60)
    print("FASE 2: CREACIÓN DE SERVICIOS")
    print("━" * 60)

    # ── OPERACIÓN 6: Sala de conferencias válida ───────────────────────────────
    try:
        sala_conf = ReservaSala("Sala Innovación", 50000, "conferencia", capacidad_personas=20)
        sistema.registrar_servicio(sala_conf)
    except SoftwareFJError as e:
        logger.error(f"No se pudo crear sala: {e}")
        print(f" {e}")
        sala_conf = None

    # ── OPERACIÓN 7: Equipo (laptop premium) válido ────────────────────────────
    try:
        laptop = AlquilerEquipo("Laptop Dell XPS 15", 20000, "laptop_premium", unidades_disponibles=5)
        sistema.registrar_servicio(laptop)
    except SoftwareFJError as e:
        logger.error(f"No se pudo crear equipo: {e}")
        print(f" {e}")
        laptop = None

    # ── OPERACIÓN 8: Asesoría válida ───────────────────────────────────────────
    try:
        asesoria = AsesoriaEspecializada("Consultoría TI Senior", 80000, "tecnologia", "senior")
        sistema.registrar_servicio(asesoria)
    except SoftwareFJError as e:
        logger.error(f"No se pudo crear asesoría: {e}")
        print(f" {e}")
        asesoria = None

    # ── OPERACIÓN 9: Servicio con precio negativo (INVÁLIDO) ───────────────────
    print(f"\n Registrando servicio con precio negativo (caso inválido)...")
    try:
        sala_invalida = ReservaSala("Sala Fantasma", -5000, "basica")  # Precio negativo
        sistema.registrar_servicio(sala_invalida)
    except ServicioNoDisponibleError as e:
        logger.warning(f"Servicio inválido rechazado: {e}")
        print(f"Servicio inválido rechazado: {e}")

    # ── OPERACIÓN 10: Tipo de sala inexistente (INVÁLIDO) ──────────────────────
    print(f"\n Registrando sala con tipo inexistente (caso inválido)...")
    try:
        sala_tipo_malo = ReservaSala("Sala VIP", 100000, "penthouse")  # Tipo no existe
        sistema.registrar_servicio(sala_tipo_malo)
    except ServicioNoDisponibleError as e:
        logger.warning(f"Tipo de sala rechazado: {e}")
        print(f"Tipo de sala no válido: {e}")

    print("\n" + "━" * 60)
    print("FASE 3: CREACIÓN Y GESTIÓN DE RESERVAS")
    print("━" * 60)

    # ── OPERACIÓN 11: Reserva exitosa con descuento e impuesto ─────────────────
    if c1 and sala_conf:
        r1 = sistema.crear_reserva(
            c1, sala_conf, horas=3,
            notas="Reunión de directivos - requiere proyector",
            descuento=0.10,         # 10% de descuento
            con_impuesto=True       # Con IVA del 19%
        )

    # ── OPERACIÓN 12: Reserva exitosa sin impuesto ─────────────────────────────
    if c2 and laptop:
        r2 = sistema.crear_reserva(
            c2, laptop, horas=8,
            notas="Desarrollo de prototipo",
            con_impuesto=False      # Sin IVA
        )

    # ── OPERACIÓN 13: Reserva de asesoría larga (con descuento automático) ─────
    if c5 and asesoria:
        r3 = sistema.crear_reserva(
            c5, asesoria, horas=6,
            notas="Revisión de arquitectura de software"
        )

    # ── OPERACIÓN 14: Reserva con cliente inválido (None) ─────────────────────
    if sala_conf:
        r4 = sistema.crear_reserva(
            None, sala_conf, horas=2  # Cliente None debe fallar
        )

    # ── OPERACIÓN 15: Reserva con duración inválida ────────────────────────────
    if c1 and asesoria:
        r5 = sistema.crear_reserva(
            c1, asesoria, horas=25,   # 25 horas para asesoría es inválido
            notas="Reserva con horas fuera de rango"
        )

    # ── OPERACIÓN 16: Muestra la descripción detallada de un servicio ──────────
    print("\n" + "━" * 60)
    print("FASE 4: INFORMACIÓN DETALLADA DE SERVICIOS")
    print("━" * 60)
    if sala_conf:
        print(f"\n{sala_conf.describir()}")
    if laptop:
        print(f"\n{laptop.describir()}")
    if asesoria:
        print(f"\n{asesoria.describir()}")

    # ── OPERACIÓN 17: Demostración de métodos sobrecargados de costo ───────────
    print("\n" + "━" * 60)
    print("FASE 5: DEMOSTRACIÓN DE CÁLCULOS DE COSTO")
    print("━" * 60)
    if sala_conf:
        try:
            horas_ejemplo = 4
            print(f"\nCálculos para '{sala_conf.nombre}' ({horas_ejemplo} horas):")
            costo_base = sala_conf.calcular_costo(horas_ejemplo)
            costo_iva = sala_conf.calcular_costo_con_impuesto(horas_ejemplo)
            costo_desc = sala_conf.calcular_costo_con_descuento(horas_ejemplo, descuento=0.20)
            print(f"  Costo base:           ${costo_base:>12,.0f} COP")
            print(f"  Con IVA (19%):        ${costo_iva:>12,.0f} COP")
            print(f"  Con descuento (20%):  ${costo_desc:>12,.0f} COP")
        except SoftwareFJError as e:
            logger.error(f"Error calculando costos de demostración: {e}")
            print(f"Error: {e}")

    # ── OPERACIÓN 18: Intenta cancelar un descuento con impuesto inválido ──────
    if laptop:
        try:
            print(f"\nCalculando con tasa de impuesto inválida (2.5 = 250%)...")
            costo_invalido = laptop.calcular_costo_con_impuesto(3, tasa_impuesto=2.5)
        except CalculoCostoError as e:
            logger.error(f"Tasa de impuesto inválida rechazada: {e}")
            print(f"Tasa inválida rechazada: {e}")

    # ── RESUMEN FINAL ──────────────────────────────────────────────────────────
    sistema.mostrar_resumen()

    print("\n Todos los eventos han sido registrados en: software_fj.log")
    print("   (Abre el archivo para ver el registro completo)\n")

# Punto de entrada del programa
if __name__ == "__main__":
    # Este bloque solo se ejecuta cuando el script se corre directamente
    try:
        ejecutar_demostracion()
    except KeyboardInterrupt:
        # Maneja Ctrl+C
        logger.warning("Programa interrumpido por el usuario")
        print("\n\n Programa interrumpido por el usuario.")
    except Exception as e:
        # Captura cualquier error fatal que escape del sistema
        logger.critical(f"Error fatal no manejado: {e}", exc_info=True)
        print(f"\n Error fatal: {e}")
