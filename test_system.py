#!/usr/bin/env python3
"""
Script de prueba para el sistema de poesía
Prueba la generación con diferentes directrices
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def print_section(title):
    """Imprime un separador visual"""
    print("\n" + "="*60)
    print(f"  {title}")
    print("="*60 + "\n")

def check_server():
    """Verifica que el servidor esté corriendo"""
    try:
        response = requests.get(f"{BASE_URL}/api/health", timeout=2)
        if response.status_code == 200:
            print("✓ Servidor conectado")
            return True
    except Exception as e:
        print(f"✗ Error al conectar con el servidor: {e}")
        print("  Asegúrate de que el servidor esté corriendo:")
        print("  poetry run uvicorn poema_algoritmo.main:app --reload")
        return False
    return False

def check_lm_studio():
    """Verifica el estado de LM Studio"""
    try:
        response = requests.get(f"{BASE_URL}/api/lm-studio-status", timeout=2)
        if response.status_code == 200:
            data = response.json()
            if data.get("available") and data.get("using_lm_studio"):
                print("✓ LM Studio: ACTIVO")
                print("  Se usará para generar poesía de alta calidad")
            else:
                print("⚠ LM Studio: INACTIVO")
                print("  Se usará el modelo local (GPT-2)")
            return data
    except Exception as e:
        print(f"✗ Error al verificar LM Studio: {e}")
        return None

def generate_poem(prompt, max_length=200, temperature=0.7):
    """Genera un poema"""
    try:
        response = requests.post(
            f"{BASE_URL}/api/generate",
            json={
                "input_text": prompt,
                "max_length": max_length,
                "temperature": temperature,
                "use_agent": True,
                "prefer_lm_studio": True
            },
            timeout=60
        )
        
        if response.status_code == 200:
            data = response.json()
            return data
        else:
            print(f"✗ Error: {response.status_code}")
            print(f"  {response.text}")
            return None
    except Exception as e:
        print(f"✗ Error al generar poema: {e}")
        return None

def main():
    print_section("PRUEBA DEL SISTEMA DE POESÍA")
    
    # 1. Verificar servidor
    print("1. Verificando servidor...")
    if not check_server():
        return
    time.sleep(0.5)
    
    # 2. Verificar LM Studio
    print("\n2. Verificando LM Studio...")
    lm_status = check_lm_studio()
    time.sleep(0.5)
    
    # 3. Ejemplos de prueba
    print_section("EJEMPLOS DE PRUEBA")
    
    examples = [
        {
            "name": "Ejemplo 1: Concepto simple",
            "prompt": "casa",
            "description": "Prueba básica con un solo concepto"
        },
        {
            "name": "Ejemplo 2: Directriz con emoción",
            "prompt": "escribe un poema triste sobre la casa",
            "description": "Prueba con emoción específica"
        },
        {
            "name": "Ejemplo 3: Directriz compleja",
            "prompt": "soneto romántico sobre el amor, corto y con elementos de naturaleza",
            "description": "Prueba con múltiples directrices (estilo, emoción, longitud, elementos)"
        },
        {
            "name": "Ejemplo 4: Tema poético",
            "prompt": "la noche estrellada",
            "description": "Concepto más poético y evocador"
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n{example['name']}")
        print(f"  Prompt: '{example['prompt']}'")
        print(f"  Descripción: {example['description']}")
        print("\n  Generando...")
        
        result = generate_poem(example['prompt'])
        
        if result and result.get('success'):
            print("\n  ✓ Poema generado:")
            print("  " + "-"*56)
            poem = result.get('poem', '')
            # Imprimir con indentación
            for line in poem.split('\n'):
                print(f"  {line}")
            print("  " + "-"*56)
            
            # Mostrar directiva interpretada si está disponible
            if 'directive' in result:
                directive = result['directive']
                print("\n  📋 Directiva interpretada:")
                if directive.get('summary'):
                    for line in directive['summary'].split('\n'):
                        print(f"     {line}")
        else:
            print("  ✗ No se pudo generar el poema")
        
        if i < len(examples):
            print("\n  Presiona Enter para continuar con el siguiente ejemplo...")
            input()
    
    print_section("PRUEBA COMPLETADA")
    print("✓ Todos los ejemplos han sido probados")
    print("\n💡 Consejos:")
    print("  - Prueba con tus propias directrices")
    print("  - Experimenta con diferentes temperaturas (0.5-1.5)")
    print("  - Prueba directrices más complejas")
    print("  - Si tienes LM Studio, inícialo para mejor calidad")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n✗ Prueba interrumpida por el usuario")
    except Exception as e:
        print(f"\n\n✗ Error inesperado: {e}")

