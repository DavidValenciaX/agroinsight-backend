class CropService:
    """Servicio para gestionar la lógica de negocio relacionada con los cultivos.

    Esta clase contiene constantes que representan los diferentes estados de los cultivos.

    Attributes:
        PROGRAMADO (str): Estado del cultivo cuando está programado para ser sembrado.
        SEMBRADO (str): Estado del cultivo cuando ha sido sembrado.
        GERMINANDO (str): Estado del cultivo cuando está en proceso de germinación.
        CRECIENDO (str): Estado del cultivo cuando está en crecimiento.
        FLORACION (str): Estado del cultivo cuando está en la fase de floración.
        MADURACION (str): Estado del cultivo cuando está en la fase de maduración.
        COSECHADO (str): Estado del cultivo cuando ha sido cosechado.
        ENFERMO (str): Estado del cultivo cuando presenta enfermedades.
        MUERTO (str): Estado del cultivo cuando ha muerto.
        DORMANTE (str): Estado del cultivo cuando está en estado de dormancia.
    """

    # Crop States
    PROGRAMADO = 'Programado'
    SEMBRADO = 'Sembrado'
    GERMINANDO = 'Germinando'
    CRECIENDO = 'Creciendo'
    FLORACION = 'Floración'
    MADURACION = 'Maduración'
    COSECHADO = 'Cosechado'
    ENFERMO = 'Enfermo'
    MUERTO = 'Muerto'
    DORMANTE = 'Dormante'
    
    def __init__(self):
        """Inicializa el servicio de cultivos.

        Este método no requiere parámetros y no realiza ninguna acción en la inicialización.
        """
        pass
