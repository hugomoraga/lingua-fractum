# Panel de Administración

Documentación completa del panel de administración para gestionar datasets, entrenar modelos y administrar el sistema.

## Acceso

El panel de administración está disponible en: `http://localhost:8000/admin`

## Secciones

### 1. Datasets

Gestión completa de datasets de poemas.

#### Agregar Poema Manualmente

1. Selecciona un dataset existente o crea uno nuevo
2. Pega el poema completo en el área de texto
3. Haz clic en "Agregar Poema"
4. El poema se agregará con el formato estándar `=== POEMA ===`

#### Subir Archivo

**Archivos TXT**:
- Formato: Texto plano con poemas separados por `=== POEMA ===`
- Se agregará al dataset seleccionado o creará uno nuevo

**Archivos EPUB**:
- El sistema procesará automáticamente el EPUB
- Extraerá poemas del contenido
- Opcionalmente puedes especificar un nombre para el dataset
- Si no especificas, usará el nombre del archivo EPUB

#### Visualizar Dataset

1. Haz clic en "Ver" junto al dataset
2. Se mostrará una lista paginada de poemas (50 por página)
3. Cada poema muestra:
   - Número de poema
   - Longitud en caracteres
   - Vista previa del contenido

#### Editar Poema

1. En la vista del dataset, haz clic en "Editar"
2. Se abrirá un modal con el poema completo
3. Modifica el contenido
4. Haz clic en "Guardar"
5. Los cambios se aplicarán inmediatamente

#### Eliminar Poemas

**Eliminación Individual**:
1. Haz clic en "Eliminar" junto al poema
2. Confirma la eliminación

**Eliminación Múltiple**:
1. Activa "Modo selección"
2. Haz clic en los poemas que quieres eliminar
3. Haz clic en "Eliminar seleccionados (X)"
4. Confirma la eliminación

#### Renombrar Dataset

1. Haz clic en "Editar nombre" junto al dataset
2. Ingresa el nuevo nombre
3. Presiona Enter o haz clic fuera para guardar

#### Eliminar Dataset

1. Haz clic en "Eliminar" junto al dataset
2. Confirma la eliminación
3. ⚠️ **Advertencia**: Esta acción no se puede deshacer

### 2. Entrenamiento

Gestión del proceso de entrenamiento de modelos.

#### Iniciar Entrenamiento

1. Selecciona el dataset de poemas
2. Configura los parámetros:
   - **Directorio de salida**: Donde se guardará el modelo (default: `models/poetry_model`)
   - **Épocas**: Número de iteraciones (recomendado: 5-7)
   - **Batch size**: Tamaño del lote (4 para CPU, 8 para GPU)
   - **Learning rate**: Tasa de aprendizaje (default: 5e-5)
   - **Modelo base**: Modelo base a usar (opcional)
3. Haz clic en "Iniciar Entrenamiento"
4. Monitorea el progreso en tiempo real

#### Estado del Entrenamiento

El panel muestra:
- Estado actual (pendiente, entrenando, completado, error)
- Progreso en porcentaje
- Época actual
- Pérdida actual
- Tiempo transcurrido

#### Cancelar Entrenamiento

Si un entrenamiento está en progreso, puedes cancelarlo haciendo clic en "Cancelar".

### 3. Modelos

Gestión de modelos entrenados.

#### Listar Modelos

El panel muestra todos los modelos disponibles en `models/` con:
- Nombre del modelo
- Tamaño en disco
- Fecha de creación
- Estado (activo/inactivo)

#### Usar Modelo

El modelo activo se usa automáticamente por el sistema. Para cambiar:

1. El sistema usa el modelo en `models/poetry_model` por defecto
2. Puedes cambiar la variable de entorno: `TRAINED_MODEL_PATH=models/nombre_modelo`

#### Eliminar Modelo

1. Haz clic en "Eliminar" junto al modelo
2. Confirma la eliminación
3. ⚠️ **Advertencia**: Esta acción no se puede deshacer

### 4. Estadísticas

Vista general del sistema.

Muestra:
- **Datasets**: Cantidad y tamaño total
- **Modelos**: Cantidad y tamaño total
- **Archivos EPUB**: Cantidad y tamaño total

## Características Avanzadas

### Procesamiento EPUB

El sistema puede procesar archivos EPUB y extraer poemas automáticamente:

1. Sube un archivo EPUB en la sección "Subir Archivo"
2. El sistema detectará si es EPUB
3. Opcionalmente especifica un nombre para el dataset
4. Haz clic en "Procesar EPUB"
5. El sistema extraerá poemas y los guardará en formato estándar

**Formato de salida**:
- Los poemas se guardan con separadores `=== POEMA ===`
- Se detectan automáticamente poemas en el contenido
- Se filtran metadatos y texto no poético

### Paginación

Los datasets grandes se muestran paginados:
- 50 poemas por página
- Navegación con botones "Anterior" y "Siguiente"
- Información de página actual y total

### Selección Múltiple

Para operaciones en lote:

1. Activa "Modo selección"
2. Haz clic en los poemas que quieres seleccionar
3. Los poemas seleccionados se marcan visualmente
4. Usa "Seleccionar todos" para seleccionar todos los poemas de la página
5. Haz clic en "Eliminar seleccionados" para eliminarlos

### Limpieza de Notas

El botón "Limpiar Notas" permite eliminar metadatos y notas del dataset:
- Elimina líneas que parecen notas o metadatos
- Preserva el contenido poético
- Útil para limpiar datasets importados

## API del Panel

El panel usa una API REST interna. Endpoints principales:

- `GET /admin/api/datasets` - Listar datasets
- `POST /admin/api/datasets` - Crear dataset
- `GET /admin/api/datasets/{filename}/poems` - Obtener poemas (con paginación)
- `PUT /admin/api/datasets/{filename}/poems/{poem_id}` - Actualizar poema
- `DELETE /admin/api/datasets/{filename}/poems/{poem_id}` - Eliminar poema
- `DELETE /admin/api/datasets/{filename}/poems/batch-delete` - Eliminar múltiples poemas
- `POST /admin/api/training/start` - Iniciar entrenamiento
- `GET /admin/api/training/status` - Estado del entrenamiento
- `GET /admin/api/models` - Listar modelos
- `GET /admin/api/stats` - Estadísticas del sistema

Ver [API.md](API.md) para documentación completa de la API.

## Solución de Problemas

### El panel no carga

- Verifica que el servidor esté corriendo
- Revisa la consola del navegador para errores
- Verifica que los archivos estáticos se sirvan correctamente

### Los poemas no se muestran

- Verifica el formato del dataset (debe tener separadores `=== POEMA ===`)
- Revisa que el archivo tenga codificación UTF-8
- Verifica los logs del servidor

### El entrenamiento falla

- Verifica que tengas suficiente espacio en disco
- Revisa que el dataset tenga al menos 50 poemas
- Verifica los logs del servidor para errores específicos

### Los cambios no se guardan

- Verifica permisos de escritura en el directorio `data/`
- Revisa los logs del servidor
- Asegúrate de que el archivo no esté bloqueado

