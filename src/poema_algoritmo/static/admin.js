// Panel de Administración - JavaScript

// Helper para obtener nombre sin extensión
function Path(filename) {
    return {
        stem: filename.replace(/\.[^/.]+$/, '')
    };
}

// Navegación entre secciones
function showSection(sectionName) {
    // Ocultar todas las secciones
    document.querySelectorAll('.admin-section').forEach(section => {
        section.classList.remove('active');
    });
    
    // Mostrar la sección seleccionada
    document.getElementById(`${sectionName}-section`).classList.add('active');
    
    // Actualizar botones de navegación
    document.querySelectorAll('.nav-btn').forEach(btn => {
        btn.classList.remove('active');
    });
    event.target.classList.add('active');
    
    // Cargar datos de la sección
    loadSectionData(sectionName);
}

// Cargar datos según la sección
function loadSectionData(sectionName) {
    switch(sectionName) {
        case 'datasets':
            loadDatasets();
            break;
        case 'training':
            loadTrainingForm();
            loadTrainingStatus();
            break;
        case 'models':
            loadModels();
            break;
        case 'stats':
            loadStats();
            break;
    }
}

// ========== DATASETS ==========

async function loadDatasets() {
    try {
        const response = await fetch('/admin/api/datasets');
        const data = await response.json();
        
        const listDiv = document.getElementById('datasets-list');
        const select = document.getElementById('poem-dataset-select');
        
        // Cargar datasets en el select
        select.innerHTML = '<option value="">Selecciona un dataset...</option>';
        if (data.datasets.length > 0) {
            data.datasets.forEach(dataset => {
                const option = document.createElement('option');
                option.value = dataset.name;
                option.textContent = `${dataset.name} (${dataset.poems_count || 0} poemas)`;
                select.appendChild(option);
            });
        } else {
            select.innerHTML = '<option value="">No hay datasets disponibles</option>';
        }
        
        if (data.datasets.length === 0) {
            listDiv.innerHTML = '<p>No hay datasets disponibles</p>';
            return;
        }
        
        listDiv.innerHTML = data.datasets.map(dataset => `
            <div class="dataset-item" data-dataset-name="${dataset.name}">
                <div class="dataset-info">
                    <div class="dataset-name-container">
                        <span class="dataset-name" id="name-${dataset.name.replace(/\./g, '-')}">${dataset.name}</span>
                        <input type="text" class="dataset-name-edit" id="edit-${dataset.name.replace(/\./g, '-')}" value="${dataset.name.replace('.txt', '')}" style="display: none;">
                    </div>
                    <div class="dataset-meta">
                        ${formatBytes(dataset.size)} | 
                        ${dataset.poems_count || 'N/A'} poemas | 
                        Creado: ${new Date(dataset.created).toLocaleDateString('es-ES')}
                    </div>
                </div>
                <div class="dataset-actions">
                    <button class="btn-secondary" onclick="viewDataset('${dataset.name}')">Ver</button>
                    <button class="btn-secondary" onclick="startEditDatasetName('${dataset.name}')">Editar nombre</button>
                    <button class="btn-danger" onclick="deleteDataset('${dataset.name}')">Eliminar</button>
                </div>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error al cargar datasets:', err);
        document.getElementById('datasets-list').innerHTML = 
            '<p style="color: red;">Error al cargar datasets</p>';
    }
}

// Upload de archivos
const uploadArea = document.getElementById('upload-area');
const fileInput = document.getElementById('file-input');

uploadArea.addEventListener('click', () => fileInput.click());

uploadArea.addEventListener('dragover', (e) => {
    e.preventDefault();
    uploadArea.classList.add('dragover');
});

uploadArea.addEventListener('dragleave', () => {
    uploadArea.classList.remove('dragover');
});

uploadArea.addEventListener('drop', async (e) => {
    e.preventDefault();
    uploadArea.classList.remove('dragover');
    
    const file = e.dataTransfer.files[0];
    if (file && (file.name.endsWith('.txt') || file.name.endsWith('.epub'))) {
        await handleFileUpload(file);
    } else {
        alert('Por favor, sube un archivo .txt o .epub');
    }
});

fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
        await handleFileUpload(file);
    }
});

let pendingEPUBFile = null;

async function handleFileUpload(file) {
    if (file.name.endsWith('.epub')) {
        // Guardar archivo pendiente
        pendingEPUBFile = file;
        
        // Mostrar campo para nombre del dataset
        const epubNameGroup = document.getElementById('epub-name-group');
        const epubNameInput = document.getElementById('epub-dataset-name');
        epubNameGroup.style.display = 'block';
        epubNameInput.value = Path(file.name).stem || file.name.replace('.epub', '');
        epubNameInput.focus();
    } else {
        await uploadDataset(file);
    }
}

// Procesar EPUB cuando el usuario confirma
document.getElementById('process-epub-btn').addEventListener('click', async () => {
    if (!pendingEPUBFile) return;
    
    const datasetName = document.getElementById('epub-dataset-name').value.trim();
    await uploadEPUB(pendingEPUBFile, datasetName || null);
    
    // Limpiar
    pendingEPUBFile = null;
    document.getElementById('epub-name-group').style.display = 'none';
    document.getElementById('epub-dataset-name').value = '';
    fileInput.value = '';
});

// Cancelar procesamiento de EPUB
document.getElementById('cancel-epub-btn').addEventListener('click', () => {
    pendingEPUBFile = null;
    document.getElementById('epub-name-group').style.display = 'none';
    document.getElementById('epub-dataset-name').value = '';
    fileInput.value = '';
});

// Crear nuevo dataset
const createDatasetBtn = document.getElementById('create-dataset-btn');
const newDatasetGroup = document.getElementById('new-dataset-group');
const newDatasetName = document.getElementById('new-dataset-name');
const createDatasetConfirm = document.getElementById('create-dataset-confirm');
const cancelCreateDataset = document.getElementById('cancel-create-dataset');

createDatasetBtn.addEventListener('click', () => {
    newDatasetGroup.style.display = 'block';
    newDatasetName.focus();
});

cancelCreateDataset.addEventListener('click', () => {
    newDatasetGroup.style.display = 'none';
    newDatasetName.value = '';
});

createDatasetConfirm.addEventListener('click', async () => {
    const name = newDatasetName.value.trim();
    
    if (!name) {
        alert('Por favor, ingresa un nombre para el dataset');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('name', name);
        
        const response = await fetch('/admin/api/datasets/create', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            // Ocultar el formulario de creación
            newDatasetGroup.style.display = 'none';
            newDatasetName.value = '';
            // Recargar datasets para actualizar el select
            loadDatasets();
            // Seleccionar el nuevo dataset
            setTimeout(() => {
                document.getElementById('poem-dataset-select').value = data.filename;
            }, 500);
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al crear dataset: ${err.message}`);
    }
});

// Formulario para agregar poema manualmente
document.getElementById('add-poem-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const datasetName = document.getElementById('poem-dataset-select').value;
    const poemText = document.getElementById('poem-text').value.trim();
    
    if (!datasetName) {
        alert('Por favor, selecciona un dataset o crea uno nuevo');
        return;
    }
    
    if (!poemText) {
        alert('Por favor, escribe o pega un poema');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('poem', poemText);
        
        const response = await fetch(`/admin/api/datasets/${datasetName}/add-poem`, {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            // Limpiar el textarea
            document.getElementById('poem-text').value = '';
            // Recargar datasets para actualizar contadores
            loadDatasets();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al agregar poema: ${err.message}`);
    }
});

async function uploadDataset(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    try {
        const response = await fetch('/admin/api/datasets/upload', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            loadDatasets();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al subir archivo: ${err.message}`);
    }
}

async function uploadEPUB(file, datasetName = null) {
    const formData = new FormData();
    formData.append('file', file);
    if (datasetName) {
        formData.append('dataset_name', datasetName);
    }
    
    // Mostrar indicador de carga
    const uploadArea = document.getElementById('upload-area');
    const originalText = uploadArea.querySelector('p').textContent;
    uploadArea.querySelector('p').textContent = 'Procesando EPUB...';
    uploadArea.style.opacity = '0.6';
    uploadArea.style.pointerEvents = 'none';
    
    try {
        const response = await fetch('/admin/api/datasets/upload-epub', {
            method: 'POST',
            body: formData
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}\nDataset creado: ${data.filename}`);
            loadDatasets();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al procesar EPUB: ${err.message}`);
    } finally {
        // Restaurar estado
        uploadArea.querySelector('p').textContent = originalText;
        uploadArea.style.opacity = '1';
        uploadArea.style.pointerEvents = 'auto';
        fileInput.value = ''; // Limpiar input
    }
}

async function deleteDataset(filename) {
    if (!confirm(`¿Estás seguro de eliminar ${filename}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/datasets/${filename}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            loadDatasets();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al eliminar: ${err.message}`);
    }
}

let editingDatasetName = null;

function startEditDatasetName(filename) {
    // Si ya hay uno editando, cancelarlo primero
    if (editingDatasetName && editingDatasetName !== filename) {
        cancelEditDatasetName(editingDatasetName);
    }
    
    editingDatasetName = filename;
    const safeId = filename.replace(/\./g, '-');
    const nameSpan = document.getElementById(`name-${safeId}`);
    const nameInput = document.getElementById(`edit-${safeId}`);
    
    if (!nameSpan || !nameInput) return;
    
    nameSpan.style.display = 'none';
    nameInput.style.display = 'inline-block';
    nameInput.focus();
    nameInput.select();
    
    // Agregar eventos
    const handleKeyPress = (e) => {
        if (e.key === 'Enter') {
            saveDatasetName(filename);
        } else if (e.key === 'Escape') {
            cancelEditDatasetName(filename);
        }
    };
    
    const handleBlur = () => {
        // Pequeño delay para permitir que el click en "Guardar" funcione
        setTimeout(() => {
            if (editingDatasetName === filename) {
                saveDatasetName(filename);
            }
        }, 200);
    };
    
    nameInput.onkeydown = handleKeyPress;
    nameInput.onblur = handleBlur;
}

function cancelEditDatasetName(filename) {
    if (!filename) return;
    
    const safeId = filename.replace(/\./g, '-');
    const nameSpan = document.getElementById(`name-${safeId}`);
    const nameInput = document.getElementById(`edit-${safeId}`);
    
    if (nameSpan && nameInput) {
        nameSpan.style.display = '';
        nameInput.style.display = 'none';
        nameInput.value = filename.replace('.txt', '');
    }
    
    if (editingDatasetName === filename) {
        editingDatasetName = null;
    }
}

async function saveDatasetName(filename) {
    if (!editingDatasetName || editingDatasetName !== filename) return;
    
    const safeId = filename.replace(/\./g, '-');
    const nameInput = document.getElementById(`edit-${safeId}`);
    
    if (!nameInput) return;
    
    const newName = nameInput.value.trim();
    
    if (!newName) {
        alert('El nombre no puede estar vacío');
        cancelEditDatasetName(filename);
        return;
    }
    
    if (newName === filename.replace('.txt', '')) {
        // No cambió, solo cancelar
        cancelEditDatasetName(filename);
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('new_name', newName);
        
        const response = await fetch(`/admin/api/datasets/${filename}/rename`, {
            method: 'PUT',
            body: formData
        });
        
        if (!response.ok) {
            const error = await response.json();
            alert(`Error: ${error.detail}`);
            cancelEditDatasetName(filename);
            return;
        }
        
        const data = await response.json();
        
        // Si el dataset actual está siendo visualizado, actualizar
        if (currentDataset === filename) {
            currentDataset = data.new_name;
        }
        
        // Recargar lista de datasets
        await loadDatasets();
        
        editingDatasetName = null;
    } catch (err) {
        console.error('Error al renombrar dataset:', err);
        alert('Error al renombrar dataset');
        cancelEditDatasetName(filename);
    }
}

// ========== ENTRENAMIENTO ==========

async function loadTrainingForm() {
    // Cargar lista de datasets para el select
    try {
        const response = await fetch('/admin/api/datasets');
        const data = await response.json();
        
        const select = document.getElementById('poems-file');
        select.innerHTML = '<option value="">Selecciona un dataset...</option>';
        
        data.datasets.forEach(dataset => {
            const option = document.createElement('option');
            option.value = dataset.path;
            option.textContent = `${dataset.name} (${dataset.poems_count || 'N/A'} poemas)`;
            select.appendChild(option);
        });
    } catch (err) {
        console.error('Error al cargar datasets:', err);
    }
}

document.getElementById('training-form').addEventListener('submit', async (e) => {
    e.preventDefault();
    
    const formData = {
        poems_file: document.getElementById('poems-file').value,
        output_dir: document.getElementById('output-dir').value,
        epochs: parseInt(document.getElementById('epochs').value),
        batch_size: parseInt(document.getElementById('batch-size').value),
        learning_rate: parseFloat(document.getElementById('learning-rate').value),
        base_model: document.getElementById('base-model').value || null
    };
    
    if (!formData.poems_file) {
        alert('Por favor, selecciona un archivo de poemas');
        return;
    }
    
    try {
        const response = await fetch('/admin/api/train', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(formData)
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Entrenamiento iniciado');
            loadTrainingStatus();
            // Actualizar estado cada 5 segundos
            const interval = setInterval(() => {
                loadTrainingStatus().then(status => {
                    if (status.status !== 'training') {
                        clearInterval(interval);
                    }
                });
            }, 5000);
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al iniciar entrenamiento: ${err.message}`);
    }
});

async function loadTrainingStatus() {
    try {
        const response = await fetch('/admin/api/training/status');
        const data = await response.json();
        
        const statusDiv = document.getElementById('training-status');
        const contentDiv = document.getElementById('training-status-content');
        
        if (data.status === 'idle') {
            statusDiv.style.display = 'none';
            return;
        }
        
        statusDiv.style.display = 'block';
        statusDiv.className = `training-status status-${data.status}`;
        
        let html = `<p><strong>Estado:</strong> ${getStatusLabel(data.status)}</p>`;
        
        if (data.started_at) {
            html += `<p><strong>Iniciado:</strong> ${new Date(data.started_at).toLocaleString('es-ES')}</p>`;
        }
        
        if (data.completed_at) {
            html += `<p><strong>Completado:</strong> ${new Date(data.completed_at).toLocaleString('es-ES')}</p>`;
        }
        
        if (data.error) {
            html += `<p style="color: red;"><strong>Error:</strong> ${data.error}</p>`;
        }
        
        if (data.status === 'training') {
            html += `<button class="btn-danger" onclick="cancelTraining()">Cancelar Entrenamiento</button>`;
        }
        
        contentDiv.innerHTML = html;
        
        return data;
    } catch (err) {
        console.error('Error al cargar estado:', err);
    }
}

function getStatusLabel(status) {
    const labels = {
        'training': '🔄 Entrenando...',
        'completed': '✓ Completado',
        'error': '✗ Error',
        'cancelled': '⏸️ Cancelado',
        'idle': '⏸️ Inactivo'
    };
    return labels[status] || status;
}

async function cancelTraining() {
    if (!confirm('¿Estás seguro de cancelar el entrenamiento?')) {
        return;
    }
    
    try {
        const response = await fetch('/admin/api/training/cancel', {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✓ Entrenamiento cancelado');
            loadTrainingStatus();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error: ${err.message}`);
    }
}

// ========== MODELOS ==========

async function loadModels() {
    try {
        const response = await fetch('/admin/api/models');
        const data = await response.json();
        
        const listDiv = document.getElementById('models-list');
        
        if (data.models.length === 0) {
            listDiv.innerHTML = '<p>No hay modelos entrenados</p>';
            return;
        }
        
        listDiv.innerHTML = data.models.map(model => `
            <div class="model-item">
                <div class="model-info">
                    <div class="model-name">${model.name}</div>
                    <div class="model-meta">
                        ${formatBytes(model.size)} | 
                        Creado: ${new Date(model.created).toLocaleDateString('es-ES')}
                    </div>
                </div>
                <button class="btn-danger" onclick="deleteModel('${model.name}')">🗑️ Eliminar</button>
            </div>
        `).join('');
    } catch (err) {
        console.error('Error al cargar modelos:', err);
        document.getElementById('models-list').innerHTML = 
            '<p style="color: red;">Error al cargar modelos</p>';
    }
}

async function deleteModel(modelName) {
    if (!confirm(`¿Estás seguro de eliminar el modelo ${modelName}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/models/${modelName}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            loadModels();
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al eliminar: ${err.message}`);
    }
}

// ========== ESTADÍSTICAS ==========

async function loadStats() {
    try {
        const response = await fetch('/admin/api/stats');
        const data = await response.json();
        
        const statsDiv = document.getElementById('stats-content');
        
        statsDiv.innerHTML = `
            <div class="stat-card">
                <div class="stat-label">Datasets</div>
                <div class="stat-value">${data.datasets.count}</div>
                <div class="stat-label">${formatBytes(data.datasets.total_size)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Modelos</div>
                <div class="stat-value">${data.models.count}</div>
                <div class="stat-label">${formatBytes(data.models.total_size)}</div>
            </div>
            <div class="stat-card">
                <div class="stat-label">Archivos EPUB</div>
                <div class="stat-value">${data.epub_files.count}</div>
                <div class="stat-label">${formatBytes(data.epub_files.total_size)}</div>
            </div>
        `;
    } catch (err) {
        console.error('Error al cargar estadísticas:', err);
        document.getElementById('stats-content').innerHTML = 
            '<p style="color: red;">Error al cargar estadísticas</p>';
    }
}

// ========== UTILIDADES ==========

function formatBytes(bytes) {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return Math.round(bytes / Math.pow(k, i) * 100) / 100 + ' ' + sizes[i];
}

// Visualizador de dataset
let currentDataset = null;
let currentPage = 1;
let totalPages = 1;

async function viewDataset(filename, page = 1) {
    currentDataset = filename;
    currentPage = page;
    const viewer = document.getElementById('dataset-viewer');
    const viewerTitle = document.getElementById('viewer-title');
    const poemsList = document.getElementById('poems-list');
    
    viewerTitle.textContent = `${filename} (página ${page})`;
    viewer.style.display = 'block';
    poemsList.innerHTML = '<p>Cargando poemas...</p>';
    
    try {
        const response = await fetch(`/admin/api/datasets/${filename}/poems?page=${page}&per_page=50`);
        const data = await response.json();
        
        totalPages = data.pagination?.total_pages || 1;
        
        if (data.poems.length === 0) {
            poemsList.innerHTML = '<p>No hay poemas en este dataset</p>';
            return;
        }
        
        // Calcular índice global (considerando paginación)
        const globalStartIndex = (page - 1) * 50;
        
        poemsList.innerHTML = `
            ${data.poems.map(poem => `
                <div class="poem-item" data-poem-id="${poem.id}" onclick="togglePoemSelection(${poem.id}, event)">
                    <div class="poem-header">
                        <span class="poem-number">Poema ${globalStartIndex + poem.id + 1}</span>
                        <span class="poem-length">${poem.length} caracteres</span>
                        <div class="poem-item-actions" onclick="event.stopPropagation()">
                            <button class="btn-secondary" onclick="editPoem(${poem.id})">Editar</button>
                            <button class="btn-danger" onclick="deletePoem(${poem.id})">Eliminar</button>
                        </div>
                    </div>
                    <div class="poem-content">${escapeHtml(poem.text.substring(0, 200))}${poem.text.length > 200 ? '...' : ''}</div>
                </div>
            `).join('')}
            <div class="pagination-controls">
                ${page > 1 ? `<button class="btn-secondary" onclick="viewDataset('${filename}', ${page - 1})">← Anterior</button>` : ''}
                <span class="pagination-info">Página ${page} de ${totalPages} (${data.pagination?.total || 0} poemas)</span>
                ${page < totalPages ? `<button class="btn-secondary" onclick="viewDataset('${filename}', ${page + 1})">Siguiente →</button>` : ''}
            </div>
        `;
        
        // Actualizar UI de selección y aplicar modo si está activo
        updateSelectionUI();
        if (selectionModeActive) {
            applySelectionMode();
        }
    } catch (err) {
        console.error('Error al cargar poemas:', err);
        poemsList.innerHTML = '<p style="color: red;">Error al cargar poemas</p>';
    }
}

function escapeHtml(text) {
    const div = document.createElement('div');
    div.textContent = text;
    return div.innerHTML;
}

function closeViewer() {
    document.getElementById('dataset-viewer').style.display = 'none';
    currentDataset = null;
    // Limpiar selección y salir del modo al cerrar
    exitSelectionMode();
    updateSelectionUI();
}

document.getElementById('close-viewer-btn').addEventListener('click', closeViewer);

// Funciones de selección múltiple
let selectionModeActive = false;
let selectedPoemIds = new Set();

function getSelectedPoemIds() {
    return Array.from(selectedPoemIds);
}

function togglePoemSelection(poemId, event) {
    // Solo funciona si el modo de selección está activo
    if (!selectionModeActive) return;
    
    // Prevenir que se active si se hace clic en botones
    if (event && (event.target.tagName === 'BUTTON' || event.target.closest('.poem-item-actions'))) {
        return;
    }
    
    if (selectedPoemIds.has(poemId)) {
        selectedPoemIds.delete(poemId);
    } else {
        selectedPoemIds.add(poemId);
    }
    
    // Actualizar visualmente
    const poemItem = document.querySelector(`.poem-item[data-poem-id="${poemId}"]`);
    if (poemItem) {
        if (selectedPoemIds.has(poemId)) {
            poemItem.classList.add('selected');
        } else {
            poemItem.classList.remove('selected');
        }
    }
    
    updateSelectionUI();
}

function updateSelectionUI() {
    const selectedCount = selectedPoemIds.size;
    const selectionModeBtn = document.getElementById('selection-mode-btn');
    const selectAllBtn = document.getElementById('select-all-btn');
    const deselectAllBtn = document.getElementById('deselect-all-btn');
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    
    if (selectionModeActive) {
        selectionModeBtn.textContent = 'Salir modo selección';
        selectionModeBtn.classList.add('active');
        
        if (selectedCount > 0) {
            selectAllBtn.style.display = 'inline-block';
            deselectAllBtn.style.display = 'inline-block';
            deleteSelectedBtn.style.display = 'inline-block';
            deleteSelectedBtn.textContent = `Eliminar seleccionados (${selectedCount})`;
        } else {
            selectAllBtn.style.display = 'inline-block';
            deselectAllBtn.style.display = 'none';
            deleteSelectedBtn.style.display = 'none';
        }
    } else {
        selectionModeBtn.textContent = 'Modo selección';
        selectionModeBtn.classList.remove('active');
        selectAllBtn.style.display = 'none';
        deselectAllBtn.style.display = 'none';
        deleteSelectedBtn.style.display = 'none';
    }
}

function toggleSelectionMode() {
    selectionModeActive = !selectionModeActive;
    
    if (selectionModeActive) {
        applySelectionMode();
    } else {
        exitSelectionMode();
    }
    
    updateSelectionUI();
}

function applySelectionMode() {
    const poemItems = document.querySelectorAll('.poem-item');
    poemItems.forEach(item => {
        item.classList.add('selectable');
        const poemId = parseInt(item.dataset.poemId);
        if (selectedPoemIds.has(poemId)) {
            item.classList.add('selected');
        }
    });
}

function exitSelectionMode() {
    const poemItems = document.querySelectorAll('.poem-item');
    poemItems.forEach(item => {
        item.classList.remove('selectable', 'selected');
    });
    selectedPoemIds.clear();
}

function selectAllPoems() {
    const poemItems = document.querySelectorAll('.poem-item');
    poemItems.forEach(item => {
        const poemId = parseInt(item.dataset.poemId);
        selectedPoemIds.add(poemId);
        item.classList.add('selected');
    });
    updateSelectionUI();
}

function clearSelection() {
    selectedPoemIds.clear();
    const poemItems = document.querySelectorAll('.poem-item');
    poemItems.forEach(item => {
        item.classList.remove('selected');
    });
    updateSelectionUI();
}

async function deleteSelectedPoems() {
    const selectedIds = getSelectedPoemIds();
    
    if (selectedIds.length === 0) {
        alert('No hay poemas seleccionados');
        return;
    }
    
    if (!confirm(`¿Estás seguro de eliminar ${selectedIds.length} poema(s)?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/datasets/${currentDataset}/poems/batch-delete`, {
            method: 'DELETE',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ poem_ids: selectedIds })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            // Limpiar selección y recargar la vista actual
            selectedPoemIds.clear();
            await viewDataset(currentDataset, currentPage);
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        console.error('Error al eliminar poemas:', err);
        alert(`✗ Error al eliminar poemas: ${err.message}`);
    }
}

// Event listeners para botones de selección (se agregan cuando el DOM está listo)
document.addEventListener('DOMContentLoaded', () => {
    const selectionModeBtn = document.getElementById('selection-mode-btn');
    const selectAllBtn = document.getElementById('select-all-btn');
    const deselectAllBtn = document.getElementById('deselect-all-btn');
    const deleteSelectedBtn = document.getElementById('delete-selected-btn');
    
    if (selectionModeBtn) {
        selectionModeBtn.addEventListener('click', toggleSelectionMode);
    }
    if (selectAllBtn) {
        selectAllBtn.addEventListener('click', selectAllPoems);
    }
    if (deselectAllBtn) {
        deselectAllBtn.addEventListener('click', clearSelection);
    }
    if (deleteSelectedBtn) {
        deleteSelectedBtn.addEventListener('click', deleteSelectedPoems);
    }
});

async function editPoem(poemId) {
    if (!currentDataset) return;
    
    try {
        // Obtener poema específico por ID (sin paginación)
        const response = await fetch(`/admin/api/datasets/${currentDataset}/poems/${poemId}`);
        if (!response.ok) {
            alert('Poema no encontrado');
            return;
        }
        const poem = await response.json();
        
        // Crear modal de edición
        const modal = document.createElement('div');
        modal.className = 'edit-modal';
        modal.innerHTML = `
            <div class="edit-modal-content">
                <div class="edit-modal-header">
                    <h3>Editar Poema ${poemId + 1}</h3>
                    <button class="btn-danger" onclick="closeEditModal()">Cerrar</button>
                </div>
                <textarea id="edit-poem-text" rows="20" style="width: 100%; padding: var(--spacing-normal); background: var(--smoke); border: 1px solid var(--ash); color: var(--cold-white); font-family: var(--ui-font); font-size: 0.875rem; line-height: 1.6; resize: vertical; border-radius: 0;">${escapeHtml(poem.text)}</textarea>
                <div class="edit-modal-actions">
                    <button class="btn-primary" onclick="savePoem(${poemId})">Guardar</button>
                    <button class="btn-secondary" onclick="closeEditModal()">Cancelar</button>
                </div>
            </div>
        `;
        document.body.appendChild(modal);
        
        // Guardar referencia al modal
        window.currentEditModal = modal;
        window.currentEditPoemId = poemId;
        
    } catch (err) {
        alert(`✗ Error al cargar poema: ${err.message}`);
    }
}

function closeEditModal() {
    if (window.currentEditModal) {
        window.currentEditModal.remove();
        window.currentEditModal = null;
        window.currentEditPoemId = null;
    }
}

async function savePoem(poemId) {
    if (!currentDataset) return;
    
    const textarea = document.getElementById('edit-poem-text');
    const newText = textarea.value.trim();
    
    if (!newText) {
        alert('El poema no puede estar vacío');
        return;
    }
    
    try {
        const formData = new FormData();
        formData.append('poem', newText);
        
        const updateResponse = await fetch(`/admin/api/datasets/${currentDataset}/poems/${poemId}`, {
            method: 'PUT',
            body: formData
        });
        
        const updateData = await updateResponse.json();
        
        if (updateResponse.ok) {
            alert(`✓ ${updateData.message}`);
            closeEditModal();
            viewDataset(currentDataset); // Recargar
            loadDatasets(); // Actualizar contadores
        } else {
            alert(`✗ Error: ${updateData.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al guardar poema: ${err.message}`);
    }
}

async function deletePoem(poemId) {
    if (!currentDataset) return;
    
    if (!confirm(`¿Estás seguro de eliminar el poema ${poemId + 1}?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/datasets/${currentDataset}/poems/${poemId}`, {
            method: 'DELETE'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            viewDataset(currentDataset); // Recargar
            loadDatasets(); // Actualizar contadores
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al eliminar poema: ${err.message}`);
    }
}

async function cleanDataset() {
    if (!currentDataset) return;
    
    if (!confirm('¿Limpiar todas las notas de pie de página (números entre corchetes) del dataset?')) {
        return;
    }
    
    try {
        const response = await fetch(`/admin/api/datasets/${currentDataset}/clean`, {
            method: 'POST'
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert(`✓ ${data.message}`);
            viewDataset(currentDataset); // Recargar
            loadDatasets(); // Actualizar contadores
        } else {
            alert(`✗ Error: ${data.detail}`);
        }
    } catch (err) {
        alert(`✗ Error al limpiar dataset: ${err.message}`);
    }
}

document.getElementById('clean-dataset-btn').addEventListener('click', cleanDataset);

// Cargar datos iniciales
window.addEventListener('load', () => {
    loadSectionData('datasets');
});

