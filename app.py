import streamlit as st
import pandas as pd
from datetime import datetime
import json

# Configuración de la página
st.set_page_config(
    page_title="Analizador de Ruleta Americana",
    page_icon="🎰",
    layout="wide"
)

# Definir colores y propiedades de la ruleta americana
ROJOS = [1, 3, 5, 7, 9, 12, 14, 16, 18, 19, 21, 23, 25, 27, 30, 32, 34, 36]
NEGROS = [2, 4, 6, 8, 10, 11, 13, 15, 17, 20, 22, 24, 26, 28, 29, 31, 33, 35]

# Posibilidades específicas
POSIBILIDAD_1 = [1, 2, 4, 5, 8, 9, 11, 12, 13, 14, 16, 17, 20, 21, 23, 24, 25, 26, 28, 29, 32, 33, 35, 36]
POSIBILIDAD_2 = [3, 5, 6, 7, 8, 10, 11, 14, 15, 17, 18, 19, 20, 22, 23, 26, 27, 29, 30, 31, 32, 34, 35]

def inicializar_session_state():
    """Inicializa las variables de session state"""
    if 'numeros_registrados' not in st.session_state:
        st.session_state.numeros_registrados = []
    
    if 'parametros' not in st.session_state:
        st.session_state.parametros = {
            'patron_basico_consecutivos': 5,
            'docenas_consecutivos': 10,
            'numeros_especificos_consecutivos': 5
        }

def obtener_propiedades_numero(numero):
    """Obtiene las propiedades de un número de ruleta"""
    if numero == 0 or numero == 37:  # 0 y 00 en ruleta americana
        return {
            'color': 'Verde',
            'par_impar': 'Especial',
            'rango': 'Especial',
            'docena': 'Especial',
            'posibilidad': 'Ninguna'
        }
    
    propiedades = {
        'color': 'Rojo' if numero in ROJOS else 'Negro',
        'par_impar': 'Par' if numero % 2 == 0 else 'Impar',
        'rango': '1-18' if numero <= 18 else '19-36',
        'docena': f'Docena {(numero - 1) // 12 + 1}',
        'posibilidad': 'Ninguna'
    }
    
    if numero in POSIBILIDAD_1:
        propiedades['posibilidad'] = 'Posibilidad 1'
    elif numero in POSIBILIDAD_2:
        propiedades['posibilidad'] = 'Posibilidad 2'
    
    return propiedades

def detectar_patron_basico(numeros, propiedad, consecutivos_requeridos):
    """Detecta patrones básicos (color, par/impar, rango)"""
    if len(numeros) < consecutivos_requeridos:
        return None, 0
    
    ultimos_numeros = numeros[-consecutivos_requeridos:]
    propiedades = [obtener_propiedades_numero(num)[propiedad] for num in ultimos_numeros]
    
    # Filtrar números especiales (0, 00)
    propiedades_validas = [p for p in propiedades if p != 'Especial']
    
    if len(propiedades_validas) < consecutivos_requeridos:
        return None, 0
    
    if len(set(propiedades_validas)) == 1:
        patron_actual = propiedades_validas[0]
        
        # Contar cuántos consecutivos llevamos
        contador = 0
        for i in range(len(numeros) - 1, -1, -1):
            prop = obtener_propiedades_numero(numeros[i])[propiedad]
            if prop == patron_actual and prop != 'Especial':
                contador += 1
            else:
                break
        
        return patron_actual, contador
    
    return None, 0

def detectar_patron_docenas(numeros, consecutivos_requeridos):
    """Detecta patrones de docenas"""
    if len(numeros) < consecutivos_requeridos:
        return None, 0, []
    
    ultimos_numeros = numeros[-consecutivos_requeridos:]
    docenas = []
    
    for num in ultimos_numeros:
        if num == 0 or num == 37:
            continue
        docenas.append((num - 1) // 12 + 1)
    
    if len(docenas) < consecutivos_requeridos:
        return None, 0, []
    
    docenas_unicas = set(docenas)
    
    # Verificar si solo han salido 2 docenas
    if len(docenas_unicas) == 2:
        # Contar consecutivos
        contador = 0
        docenas_actuales = set()
        
        for i in range(len(numeros) - 1, -1, -1):
            if numeros[i] == 0 or numeros[i] == 37:
                continue
            docena = (numeros[i] - 1) // 12 + 1
            if len(docenas_actuales) == 0:
                docenas_actuales.add(docena)
                contador += 1
            elif docena in docenas_actuales or len(docenas_actuales) == 1:
                docenas_actuales.add(docena)
                contador += 1
                if len(docenas_actuales) > 2:
                    break
            else:
                break
        
        if contador >= consecutivos_requeridos and len(docenas_actuales) == 2:
            docena_faltante = ({1, 2, 3} - docenas_actuales).pop()
            return list(docenas_actuales), contador, docena_faltante
    
    return None, 0, []

def detectar_patron_posibilidades(numeros, consecutivos_requeridos):
    """Detecta patrones de posibilidades específicas"""
    if len(numeros) < consecutivos_requeridos:
        return None, 0
    
    ultimos_numeros = numeros[-consecutivos_requeridos:]
    posibilidades = [obtener_propiedades_numero(num)['posibilidad'] for num in ultimos_numeros]
    
    # Filtrar números que no pertenecen a ninguna posibilidad
    posibilidades_validas = [p for p in posibilidades if p != 'Ninguna']
    
    if len(posibilidades_validas) < consecutivos_requeridos:
        return None, 0
    
    if len(set(posibilidades_validas)) == 1:
        patron_actual = posibilidades_validas[0]
        
        # Contar consecutivos
        contador = 0
        for i in range(len(numeros) - 1, -1, -1):
            prop = obtener_propiedades_numero(numeros[i])['posibilidad']
            if prop == patron_actual and prop != 'Ninguna':
                contador += 1
            else:
                break
        
        return patron_actual, contador
    
    return None, 0

def generar_recomendaciones(numeros, parametros):
    """Genera recomendaciones basadas en los patrones detectados"""
    recomendaciones = []
    
    # Patrones básicos
    patrones_basicos = ['color', 'par_impar', 'rango']
    nombres_patrones = {
        'color': 'Color',
        'par_impar': 'Par/Impar',
        'rango': 'Rango'
    }
    
    contrarios = {
        'Rojo': 'Negro',
        'Negro': 'Rojo',
        'Par': 'Impar',
        'Impar': 'Par',
        '1-18': '19-36',
        '19-36': '1-18'
    }
    
    for patron in patrones_basicos:
        patron_actual, contador = detectar_patron_basico(
            numeros, patron, parametros['patron_basico_consecutivos']
        )
        
        if patron_actual and contador >= parametros['patron_basico_consecutivos']:
            recomendacion = f"🎯 **APUESTA A: {contrarios[patron_actual]}**"
            detalle = f"Han salido {contador} {nombres_patrones[patron]} consecutivos ({patron_actual})"
            recomendaciones.append((recomendacion, detalle, 'patron_basico'))
    
    # Patrón de docenas
    docenas_actuales, contador_docenas, docena_faltante = detectar_patron_docenas(
        numeros, parametros['docenas_consecutivos']
    )
    
    if docenas_actuales and contador_docenas >= parametros['docenas_consecutivos']:
        recomendacion = f"🎯 **APUESTA A: Docena {docena_faltante}**"
        detalle = f"Han salido {contador_docenas} números consecutivos en Docenas {docenas_actuales}"
        recomendaciones.append((recomendacion, detalle, 'docenas'))
    
    # Patrón de posibilidades
    posibilidad_actual, contador_pos = detectar_patron_posibilidades(
        numeros, parametros['numeros_especificos_consecutivos']
    )
    
    if posibilidad_actual and contador_pos >= parametros['numeros_especificos_consecutivos']:
        contrario_pos = 'Posibilidad 2' if posibilidad_actual == 'Posibilidad 1' else 'Posibilidad 1'
        recomendacion = f"🎯 **APUESTA A: {contrario_pos}**"
        detalle = f"Han salido {contador_pos} números consecutivos de {posibilidad_actual}"
        recomendaciones.append((recomendacion, detalle, 'posibilidades'))
    
    return recomendaciones

def main():
    inicializar_session_state()
    
    st.title("🎰 Analizador de Ruleta Americana")
    st.markdown("---")
    
    # Sidebar para configuración
    with st.sidebar:
        st.header("⚙️ Configuración")
        
        st.subheader("Parámetros de Detección")
        
        nuevo_patron_basico = st.number_input(
            "Consecutivos para patrones básicos (Color, Par/Impar, Rango)",
            min_value=3,
            max_value=20,
            value=st.session_state.parametros['patron_basico_consecutivos']
        )
        
        nuevo_docenas = st.number_input(
            "Consecutivos para patrón de docenas",
            min_value=5,
            max_value=30,
            value=st.session_state.parametros['docenas_consecutivos']
        )
        
        nuevo_especificos = st.number_input(
            "Consecutivos para números específicos",
            min_value=3,
            max_value=20,
            value=st.session_state.parametros['numeros_especificos_consecutivos']
        )
        
        if st.button("Actualizar Parámetros"):
            st.session_state.parametros = {
                'patron_basico_consecutivos': nuevo_patron_basico,
                'docenas_consecutivos': nuevo_docenas,
                'numeros_especificos_consecutivos': nuevo_especificos
            }
            st.success("Parámetros actualizados!")
        
        st.markdown("---")
        
        if st.button("🗑️ Limpiar Historial", type="secondary"):
            st.session_state.numeros_registrados = []
            st.success("Historial limpiado!")
            st.rerun()
    
    # Área principal
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Registrar Número")
        
        numero_input = st.number_input(
            "Ingresa el número que salió:",
            min_value=0,
            max_value=37,
            value=0,
            help="0 = 0, 37 = 00 (doble cero)"
        )
        
        if st.button("➕ Agregar Número", type="primary"):
            st.session_state.numeros_registrados.append(numero_input)
            st.success(f"Número {numero_input} agregado!")
            st.rerun()
        
        # Mostrar últimos números
        if st.session_state.numeros_registrados:
            st.subheader("🔢 Últimos 10 Números")
            ultimos = st.session_state.numeros_registrados[-10:]
            
            for i, num in enumerate(reversed(ultimos)):
                props = obtener_propiedades_numero(num)
                color_emoji = "🔴" if props['color'] == 'Rojo' else "⚫" if props['color'] == 'Negro' else "🟢"
                st.write(f"{len(ultimos)-i}. {color_emoji} **{num}** - {props['color']}")
    
    with col2:
        st.subheader("🎯 Recomendaciones de Apuesta")
        
        if len(st.session_state.numeros_registrados) >= 3:
            recomendaciones = generar_recomendaciones(
                st.session_state.numeros_registrados,
                st.session_state.parametros
            )
            
            if recomendaciones:
                for recomendacion, detalle, tipo in recomendaciones:
                    if tipo == 'patron_basico':
                        st.error(recomendacion)
                    elif tipo == 'docenas':
                        st.warning(recomendacion)
                    else:
                        st.info(recomendacion)
                    
                    st.caption(detalle)
                    st.markdown("---")
            else:
                st.info("🔍 No se detectaron patrones. Sigue registrando números...")
        else:
            st.info("📊 Registra al menos 3 números para comenzar el análisis")
    
    # Estadísticas generales
    if st.session_state.numeros_registrados:
        st.subheader("📊 Estadísticas Generales")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_numeros = len(st.session_state.numeros_registrados)
            st.metric("Total de Números", total_numeros)
        
        with col2:
            rojos_count = sum(1 for num in st.session_state.numeros_registrados if num in ROJOS)
            st.metric("Rojos", rojos_count)
        
        with col3:
            negros_count = sum(1 for num in st.session_state.numeros_registrados if num in NEGROS)
            st.metric("Negros", negros_count)
        
        with col4:
            verdes_count = sum(1 for num in st.session_state.numeros_registrados if num in [0, 37])
            st.metric("Verdes (0/00)", verdes_count)
        
        # Tabla detallada de los últimos números
        if st.checkbox("Ver tabla detallada"):
            df_data = []
            for i, num in enumerate(st.session_state.numeros_registrados[-20:], 1):
                props = obtener_propiedades_numero(num)
                df_data.append({
                    '#': len(st.session_state.numeros_registrados) - 20 + i,
                    'Número': num,
                    'Color': props['color'],
                    'Par/Impar': props['par_impar'],
                    'Rango': props['rango'],
                    'Docena': props['docena'],
                    'Posibilidad': props['posibilidad']
                })
            
            df = pd.DataFrame(df_data)
            st.dataframe(df, use_container_width=True)

if __name__ == "__main__":
    main()
