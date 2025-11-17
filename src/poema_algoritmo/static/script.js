// Elementos del DOM
const poemInput = document.getElementById('poem-input');
const generateBtn = document.getElementById('generate-btn');
const outputSection = document.getElementById('output-section');
const poemOutput = document.getElementById('poem-output');
const loading = document.getElementById('loading');
const error = document.getElementById('error');
const errorMessage = document.getElementById('error-message');
const copyBtn = document.getElementById('copy-btn');
const newPoemBtn = document.getElementById('new-poem-btn');
const maxLengthSlider = document.getElementById('max-length');
const maxLengthValue = document.getElementById('max-length-value');
const temperatureSlider = document.getElementById('temperature');
const temperatureValue = document.getElementById('temperature-value');

// Actualizar valores de los sliders
maxLengthSlider.addEventListener('input', (e) => {
    maxLengthValue.textContent = e.target.value;
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
                max_length: parseInt(maxLengthSlider.value),
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
        copyBtn.textContent = '✓ Copiado!';
        setTimeout(() => {
            copyBtn.textContent = '📋 Copiar';
        }, 2000);
    }).catch(err => {
        console.error('Error al copiar:', err);
    });
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

// Verificar salud del servidor al cargar
window.addEventListener('load', async () => {
    try {
        const response = await fetch('/api/health');
        const data = await response.json();
        console.log('Servidor conectado:', data);
    } catch (err) {
        console.error('Error al conectar con el servidor:', err);
    }
});

