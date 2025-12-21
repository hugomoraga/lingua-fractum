// Elementos del DOM
const poemInput = document.getElementById('poem-input');
const generateBtn = document.getElementById('generate-btn');
const outputSection = document.getElementById('output-section');
const poemOutput = document.getElementById('poem-output');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const copyBtn = document.getElementById('copy-btn');
const downloadBtn = document.getElementById('download-btn');
const newPoemBtn = document.getElementById('new-poem-btn');
const maxSentencesSlider = document.getElementById('max-sentences');
const maxSentencesValue = document.getElementById('max-sentences-value');
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');

// Actualizar valores de los sliders
maxSentencesSlider.addEventListener('input', (e) => {
    maxSentencesValue.textContent = e.target.value;
});

temperatureSlider.addEventListener('input', (e) => {
    temperatureValue.textContent = parseFloat(e.target.value).toFixed(1);
});

// Generar poema
generateBtn.addEventListener('click', async () => {
    const inputText = poemInput.value.trim();
    
    if (!inputText) {
        showError('Por favor, escribe algo sobre lo que quieres el poema');
        return;
    }
    
    // Ocultar secciones anteriores
    outputSection.style.display = 'none';
    error.style.display = 'none';
    
    // Mostrar loading
    loading.style.display = 'block';
    generateBtn.disabled = true;
    generateBtn.querySelector('.button-text').style.display = 'none';
    generateBtn.querySelector('.button-loader').style.display = 'inline';
    
    try {
        const response = await fetch('/api/generate', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                input_text: inputText,
                max_sentences: parseInt(maxSentencesSlider.value),
                temperature: parseFloat(temperatureSlider.value)
            })
        });
        
        const data = await response.json();
        
        if (!response.ok) {
            throw new Error(data.detail || 'Error al generar el poema');
        }
        
        if (data.success && data.poem) {
            poemOutput.textContent = data.poem;
            outputSection.style.display = 'block';
        } else {
            throw new Error('No se pudo generar el poema');
        }
        
    } catch (err) {
        showError(err.message || 'Error al conectar con el servidor');
    } finally {
        loading.style.display = 'none';
        generateBtn.disabled = false;
        generateBtn.querySelector('.button-text').style.display = 'inline';
        generateBtn.querySelector('.button-loader').style.display = 'none';
    }
});

// Copiar poema
copyBtn.addEventListener('click', () => {
    const poemText = poemOutput.textContent;
    navigator.clipboard.writeText(poemText).then(() => {
        copyBtn.textContent = 'Copiado';
        setTimeout(() => {
            copyBtn.textContent = 'Copiar';
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar:', err);
    });
});

// Descargar poema
downloadBtn.addEventListener('click', () => {
    const poemText = poemOutput.textContent;
    const inputText = poemInput.value.trim() || 'poema';
    
    // Crear nombre de archivo basado en el input
    const filename = inputText
        .toLowerCase()
        .replace(/[^a-z0-9áéíóúñü]/g, '_')
        .substring(0, 30) || 'poema';
    
    // Crear contenido del archivo
    const content = `Poema generado\n` +
                   `================\n\n` +
                   `Tema: ${poemInput.value.trim() || 'Sin tema específico'}\n\n` +
                   `${poemText}\n\n` +
                   `---\n` +
                   `Generado por Plataforma de Poesía\n` +
                   `Fecha: ${new Date().toLocaleString('es-ES')}\n`;
    
    // Crear blob y descargar
    const blob = new Blob([content], { type: 'text/plain;charset=utf-8' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `${filename}_${Date.now()}.txt`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
    
    // Feedback visual
    downloadBtn.textContent = 'Descargado';
    setTimeout(() => {
        downloadBtn.textContent = 'Descargar';
    }, 2000);
});

// Nuevo poema
newPoemBtn.addEventListener('click', () => {
    poemInput.value = '';
    outputSection.style.display = 'none';
    error.style.display = 'none';
    poemInput.focus();
});

// Permitir Enter para generar (Ctrl+Enter o Cmd+Enter)
poemInput.addEventListener('keydown', (e) => {
    if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
        generateBtn.click();
    }
});

// Mostrar error
function showError(message) {
    errorMessage.textContent = message;
    error.style.display = 'block';
    outputSection.style.display = 'none';
}

// Elementos del indicador LM Studio
const lmStudioIndicator = document.getElementById('lm-studio-indicator');
const lmStudioIcon = document.getElementById('lm-studio-icon');
const lmStudioText = document.getElementById('lm-studio-text');

// Verificar estado de LM Studio
async function checkLMStudioStatus() {
    try {
        const response = await fetch('/api/lm-studio-status');
        const data = await response.json();
        
        if (data.available && data.using_lm_studio) {
            // LM Studio activo
            lmStudioIndicator.className = 'lm-studio-indicator active';
            lmStudioIcon.textContent = '~';
            lmStudioText.textContent = 'LM Studio activo';
            lmStudioIndicator.title = 'LM Studio está activo y se usará para generar poesía de alta calidad';
        } else {
            // LM Studio inactivo
            lmStudioIndicator.className = 'lm-studio-indicator inactive';
            lmStudioIcon.textContent = '•';
            lmStudioText.textContent = 'LM Studio inactivo';
            lmStudioIndicator.title = 'LM Studio no está disponible. Se usará el modelo local.';
        }
    } catch (err) {
        console.error('Error al verificar LM Studio:', err);
        lmStudioIndicator.className = 'lm-studio-indicator inactive';
        lmStudioIcon.textContent = '≠';
        lmStudioText.textContent = 'Estado desconocido';
    }
}

// Verificar salud del servidor y estado de LM Studio al cargar
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('Servidor conectado:', data);
        
        // Verificar estado de LM Studio
        await checkLMStudioStatus();
        
        // Verificar cada 30 segundos
        setInterval(checkLMStudioStatus, 30000);
    } catch (err) {
        console.error('Error al conectar con el servidor:', err);
    }
});

