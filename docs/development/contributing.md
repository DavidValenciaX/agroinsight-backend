# Contribuyendo a AgroInsight

¡Gracias por tu interés en contribuir a AgroInsight! Este documento proporciona una guía para aquellos que desean contribuir al proyecto.

## Configuración del entorno de desarrollo

1. Clona el repositorio:

   ```bash
   git clone https://github.com/AgroInsight/agroinsight.git
   cd agroinsight
   ```

2. Instala las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

3. Configura el entorno virtual (recomendado):

   ```bash
   python -m venv venv
   source venv/bin/activate  # En Windows: venv\Scripts\activate
   ```

## Flujo de trabajo de contribución

1. Crea una nueva rama para tu contribución:

   ```bash
   git checkout -b feature/nombre-de-tu-caracteristica
   ```

2. Realiza tus cambios y asegúrate de seguir las guías de estilo del proyecto.

3. Ejecuta las pruebas localmente:

   ```bash
   pytest
   ```

4. Haz commit de tus cambios:

   ```bash
   git add .
   git commit -m "Descripción concisa de tus cambios"
   ```

5. Sube tus cambios a tu fork:

   ```bash
   git push origin feature/nombre-de-tu-caracteristica
   ```

6. Crea un Pull Request en GitHub.

## Guías de estilo

- Sigue PEP 8 para el código Python.
- Utiliza nombres descriptivos para variables y funciones.
- Comenta tu código cuando sea necesario, especialmente para lógica compleja.
- Escribe pruebas unitarias para nuevas funcionalidades.

## Reportando problemas

Si encuentras un bug o tienes una sugerencia de mejora:

1. Verifica que el problema no haya sido reportado anteriormente.
2. Abre un nuevo issue en GitHub, proporcionando la mayor cantidad de detalles posible.

## Proceso de revisión de código

- Todos los Pull Requests serán revisados por al menos un miembro del equipo principal.
- Se pueden solicitar cambios o aclaraciones antes de la aprobación.
- Una vez aprobado, un mantenedor fusionará tu PR.

## Documentación

- Actualiza la documentación relevante cuando realices cambios.
- Utiliza MkDocs para la documentación del proyecto.
- Asegúrate de que tus cambios estén reflejados en la documentación.

## Licencia

Al contribuir a AgroInsight, aceptas que tus contribuciones se licenciarán bajo la misma licencia que el proyecto.

¡Gracias por contribuir a AgroInsight y ayudar a mejorar la agricultura con tecnología!
