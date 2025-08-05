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
            'patron_basico_consecutivos': 5,  # Cambiar de 5 a 3 para pruebas
            'docenas_consecutivos': 9,        # Cambiar de 15 a 6 para pruebas  
            'numeros_especificos_consecutivos': 7  # Cambiar de 8 a 3 para pruebas
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
    
    contador = 0
    patron_actual = None
    
    print(f"DEBUG: Analizando {len(numeros)} números para propiedad '{propiedad}'")
    print(f"DEBUG: Últimos 5 números: {numeros[-5:] if len(numeros) >= 5 else numeros}")
    
    for i in range(len(numeros) - 1, -1, -1):
        prop = obtener_propiedades_numero(numeros[i])[propiedad]
        print(f"DEBUG: Número {numeros[i]} -> {propiedad}: {prop}")
        
        # 0/00 rompen la racha:
        if prop == 'Especial' or (propiedad == 'color' and prop == 'Verde'):
            print(f"DEBUG: {numeros[i]} rompe la racha para '{propiedad}'. Reiniciar.")
            break  # <- corte de la racha
            
        if patron_actual is None:
            patron_actual = prop
            contador = 1
            print(f"DEBUG: Iniciando patrón {patron_actual}, contador = {contador}")
        elif prop == patron_actual:
            contador += 1
            print(f"DEBUG: Continuando patrón {patron_actual}, contador = {contador}")
        else:
            print(f"DEBUG: Patrón roto. Era {patron_actual}, ahora {prop}")
            break
    
    print(f"DEBUG: Resultado final - Patrón: {patron_actual}, Contador: {contador}, Requeridos: {consecutivos_requeridos}")
    if contador >= consecutivos_requeridos:
        return patron_actual, contador
    return None, 0
    
def detectar_patron_docenas(numeros, consecutivos_requeridos):
    """Detecta patrones de docenas (el 0/00 rompe la racha)"""
    if len(numeros) < consecutivos_requeridos:
        return None, 0, []
    
    docenas_recientes = []
    for i in range(len(numeros) - 1, -1, -1):
        # 0/00 ROMPEN la racha
        if numeros[i] in [0, 37]:
            print(f"DEBUG: {numeros[i]} (0/00) rompe la racha de docenas.")
            break
        
        docena = (numeros[i] - 1) // 12 + 1
        docenas_recientes.append(docena)
        
        if len(docenas_recientes) >= consecutivos_requeridos:
            break
    
    if len(docenas_recientes) < consecutivos_requeridos:
        return None, 0, []
    
    docenas_unicas = set(docenas_recientes)
    if len(docenas_unicas) == 2:
        docena_faltante = ({1, 2, 3} - docenas_unicas).pop()
        return list(docenas_unicas), len(docenas_recientes), docena_faltante
    
    return None, 0, []


def detectar_patron_posibilidades(numeros, consecutivos_requeridos):
    """Detecta patrones de posibilidades específicas"""
    if len(numeros) < consecutivos_requeridos:
        return None, 0
    
    contador = 0
    patron_actual = None
    
    for i in range(len(numeros) - 1, -1, -1):
        prop = obtener_propiedades_numero(numeros[i])['posibilidad']
        
        # 0/00 (Ninguna) rompen la racha
        if prop == 'Ninguna':
            # Si veníamos contando, el 0/00 corta el conteo actual
            if contador > 0:
                print(f"DEBUG: {numeros[i]} rompe la racha de {patron_actual} (posibilidades).")
                break
            else:
                print(f"DEBUG: {numeros[i]} es 'Ninguna' y está al final. No hay racha activa.")
                break  # también corta si es el último número

        if patron_actual is None:
            patron_actual = prop
            contador = 1
        elif prop == patron_actual:
            contador += 1
        else:
            break
    
    if contador >= consecutivos_requeridos:
        return patron_actual, contador
    return None, 0


def generar_recomendaciones(numeros, parametros):
    """Genera recomendaciones basadas en los patrones detectados"""
    recomendaciones = []
    
    print(f"DEBUG: Generando recomendaciones para {len(numeros)} números")
    print(f"DEBUG: Parámetros: {parametros}")
    
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
        print(f"DEBUG: Analizando patrón {patron}")
        patron_actual, contador = detectar_patron_basico(
            numeros, patron, parametros['patron_basico_consecutivos']
        )
        
        if patron_actual and contador >= parametros['patron_basico_consecutivos']:
            recomendacion = f"🎯 **APUESTA A: {contrarios[patron_actual]}**"
            detalle = f"Han salido {contador} {nombres_patrones[patron]} consecutivos ({patron_actual})"
            recomendaciones.append((recomendacion, detalle, 'patron_basico'))
            print(f"DEBUG: ¡Recomendación agregada! {recomendacion}")
    
    # Patrón de docenas
    docenas_actuales, contador_docenas, docena_faltante = detectar_patron_docenas(
        numeros, parametros['docenas_consecutivos']
    )
    
    if docenas_actuales and contador_docenas >= parametros['docenas_consecutivos']:
        recomendacion = f"🎯 **APUESTA A: Docena {docena_faltante}**"
        detalle = f"Han salido {contador_docenas} números consecutivos en Docenas {docenas_actuales}"
        recomendaciones.append((recomendacion, detalle, 'docenas'))
        print(f"DEBUG: ¡Recomendación de docena agregada! {recomendacion}")
    
    # Patrón de posibilidades
    posibilidad_actual, contador_pos = detectar_patron_posibilidades(
        numeros, parametros['numeros_especificos_consecutivos']
    )
    
    if posibilidad_actual and contador_pos >= parametros['numeros_especificos_consecutivos']:
        contrario_pos = 'Posibilidad 2' if posibilidad_actual == 'Posibilidad 1' else 'Posibilidad 1'
        recomendacion = f"🎯 **APUESTA A: {contrario_pos}**"
        detalle = f"Han salido {contador_pos} números consecutivos de {posibilidad_actual}"
        recomendaciones.append((recomendacion, detalle, 'posibilidades'))
        print(f"DEBUG: ¡Recomendación de posibilidad agregada! {recomendacion}")
    
    print(f"DEBUG: Total de recomendaciones generadas: {len(recomendaciones)}")
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
        
        # DEBUG: Mostrar información del estado actual
        st.subheader("🔍 Debug Info")
        st.write(f"Números registrados: {len(st.session_state.numeros_registrados)}")
        st.write(f"Últimos 5: {st.session_state.numeros_registrados[-5:] if len(st.session_state.numeros_registrados) >= 5 else st.session_state.numeros_registrados}")
        
        if st.button("🗑️ Limpiar Historial", type="secondary"):
            st.session_state.numeros_registrados = []
            st.success("Historial limpiado!")
            st.rerun()
    
    # Área principal
    col1, col2 = st.columns([1, 2])
    
    with col1:
        st.subheader("📝 Registrar Número")

        # Crear un formulario para permitir Enter
        with st.form("numero_form", clear_on_submit=True):
            numero_input = st.number_input(
                "Ingresa el número que salió:",
                min_value=0,
                max_value=37,
                value=0,
                help="0 = 0, 37 = 00 (doble cero). Presiona Enter o el botón para agregar."
            )
            
            col_btn1, col_btn2 = st.columns(2)
            
            with col_btn1:
                submitted = st.form_submit_button("➕ Agregar", type="primary", use_container_width=True)
            
            with col_btn2:
                if st.form_submit_button("🗑️ Borrar Último", type="secondary", use_container_width=True):
                    if st.session_state.numeros_registrados:
                        numero_borrado = st.session_state.numeros_registrados.pop()
                        st.success(f"Número {numero_borrado} borrado!")
                        st.rerun()
                    else:
                        st.warning("No hay números para borrar")
            
            if submitted:
                st.session_state.numeros_registrados.append(numero_input)
                st.success(f"Número {numero_input} agregado!")
                st.rerun()

        # Botones de prueba para generar patrones rápidamente
        st.markdown("---")
        st.subheader("🧪 Pruebas Rápidas")
        
        col_test1, col_test2 = st.columns(2)
        with col_test1:
            if st.button("3 Rojos", help="Agregar 1, 3, 5 (3 rojos consecutivos)"):
                st.session_state.numeros_registrados.extend([1, 3, 5])
                st.success("3 rojos agregados!")
                st.rerun()
        
        with col_test2:
            if st.button("3 Negros", help="Agregar 2, 4, 6 (3 negros consecutivos)"):
                st.session_state.numeros_registrados.extend([2, 4, 6])
                st.success("3 negros agregados!")
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
        
        # DEBUG: Mostrar siempre información de debug
        if st.session_state.numeros_registrados:
            with st.expander("🔍 Información de Debug", expanded=False):
                st.write(f"**Total números:** {len(st.session_state.numeros_registrados)}")
                st.write(f"**Parámetros actuales:** {st.session_state.parametros}")
                
                if len(st.session_state.numeros_registrados) >= 3:
                    ultimos_5 = st.session_state.numeros_registrados[-5:]
                    st.write(f"**Últimos 5 números:** {ultimos_5}")
                    
                    # Mostrar propiedades de los últimos números
                    for num in ultimos_5:
                        props = obtener_propiedades_numero(num)
                        st.write(f"Número {num}: {props}")
        
        if len(st.session_state.numeros_registrados) >= 3:
            recomendaciones = generar_recomendaciones(
                st.session_state.numeros_registrados,
                st.session_state.parametros
            )
            
            # Siempre mostrar el resultado de la generación
            st.write(f"**Recomendaciones encontradas:** {len(recomendaciones)}")
            
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
                
                # Mostrar por qué no hay recomendaciones
                with st.expander("¿Por qué no hay recomendaciones?"):
                    if len(st.session_state.numeros_registrados) >= 3:
                        # Analizar cada patrón
                        for patron in ['color', 'par_impar', 'rango']:
                            patron_actual, contador = detectar_patron_basico(
                                st.session_state.numeros_registrados, 
                                patron, 
                                st.session_state.parametros['patron_basico_consecutivos']
                            )
                            st.write(f"**{patron.replace('_', '/')}:** {contador} consecutivos (necesitas {st.session_state.parametros['patron_basico_consecutivos']})")
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
