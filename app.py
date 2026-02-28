# v. 28 feb 08:01
import streamlit as st
import pandas as pd
import io
from datetime import datetime
import google.generativeai as genai

# =================================================================
# # PRINCIPIOS FUNDAMENTALES:
# #
# # GEMINI SIEMPRE TENDRA RIGOR, RESPETARA Y VERIFICARA QUE SE CUMPLAN
# # ESTOS PRINCIPIOS ANTES Y DESPUES DE REALIZAR CUALQUIER CAMBIO.
# #
# # 1. NUNCA BORRAR NI MODIFICAR ESTA CLÁUSULA. 
# #
# # 2. No puedes mover nada, ni cambiar ni una sola línea de la
# # estructura visual (RIGOR Y SERIEDAD). Cero modificaciones sin
# # autorización.
# #
# # 3. Antes de cualquier evolución técnica, explicar el "qué",
# # "por qué" y "cómo", and esperar aprobación
# # ("adelante" o "procede").
# #
# #
# # I. ESTRUCTURA VISUAL PROTEGIDA:
# #
#    1. Cuadros negros superiores (ZONA y ACTIVO).
# #
#    2. Título "ASISTENTE RENAL" y Versión inmediatamente
# debajo (Blindado).
# #
#    3. Título principal y pestañas (Tabs).
# #
#    4. Registro de paciente y función: TODO EN UNA LÍNEA (Centro,
# Edad, ID Alfa, Res, Fecha + Botón Borrado Registro).
# #
#    -> REFUERZO: DEBAJO DE LA LÍNEA DE REGISTRO DEBE APARECER SIEMPRE 
# EL "ID REGISTRO" DINÁMICO (CENTRO-EDAD-ALFA).
# #
#    5. Interfaz Dual (Calculadora y caja de FG (Purple Glow): lógica
# Cockcroft-Gault.
# #
#        -> REFUERZO: NO SE TOCA LA CALCULADORA, NO SE TOCA EL GLOW
# MORADO.
# #
#    6. Layout Medicamentos: Título y Aviso RGPD (estilo ampliado) en
# la misma línea.
# #
#    7. Cuadro de listado de medicamentos (TextArea).
# #
#    8. Barra dual de botones (VALIDAR / RESET TOTAL) y Reset de
# Registro.
# #
#    9. Aviso amarillo de apoyo legal inferior CON EL TEXTO: ⚠️
# Esta herramienta es de apoyo a la revisión farmacoterapéutica.
# Verifique siempre con fuentes oficiales.
# #
# #
# # II. FUNCIONALIDADES CRÍTICAS PROTEGIDAS:
# #
#    1. Cascada de Modelos (2.5 Flash > flash-latest > 1.5 Pro >
# Otros).
# #
#    2. Detección dinámica de modelos vivos en la cuenta.
# #
#    3. Actualización de feedback neón en tiempo real (Badge ACTIVO).
# #
# #
# # III. BLINDAJE DE SÍNTESIS DINÁMICA (Glow System) - ANTI-ALUCINACIONES:
# #
#    1. Títulos Permitidos: SOLO "Medicamentos afectados:" o
# "Fármacos correctamente dosificados".
# #
#    2. Prohibición Textual: Prohibido usar "SÍNTESIS",
# "DETALLE", "RESUMEN" o similares.
# #
#    3. RESTRICCIÓN AGRESIVA: Prohibido escribir sobre metabolismo o
# eliminación en este bloque.
# #
#    4. Regla de Contenido Estricta: Solo se listan medicamentos
# afectados (⚠️ o⛔).
# #
#    5. Exclusión: NUNCA listar nombres de fármacos correctamente
# dosificados en la síntesis.
# #
#    6. Formato de Línea (OBLIGATORIO): [Icono ⚠️ o ⛔] + [Nombre] + [Frase corta] + [Siglas Fuente: AEMPS, FDA, EMA, etc]. 
# #
#    7. Lógica de Color (Jerarquía de Gravedad):
# #
#        7.1. ROJO (glow-red): Si aparece al menos un icono ⛔ (Contraindicado).
# #
#        7.2. NARANJA (glow-orange): Si no hay ⛔ pero aparece al menos un icono ⚠️ (Ajuste).
# #
#        7.3. VERDE (glow-green): Si no hay iconos ⚠️ ni ⛔ (Todo correcto).
# #
#    8. REGLA DE FUENTES Y ALCANCE: El análisis debe centrarse ÚNICA Y EXCLUSIVAMENTE
# en la adecuación del fármaco según el Filtrado Glomerular (FG) del paciente.
# Se deben priorizar fuentes oficiales (.gov, AEMPS, FDA) and Open Evidence.
# Cada línea DEBE terminar con la sigla de la fuente oficial consultada.
# #
# #
# # IV. BLINDAJE DEL BLOQUE AZUL (blue-detail-container):
# #
#    1. Prohibición de Fragmentación: Detalle y Nota en el mismo div CSS.
# #
#    2. Estilo Fijo: Fondo (#f0f7ff), borde (#bee3f8).
# #
#    3. NOTA IMPORTANTE (4 PUNTOS ESTÁTICOS):
# #
#      3.1. Verifique siempre con la ficha técnica oficial (AEMPS/EMA).
# #
#      3.2. Los ajustes propuestos son orientativos según filtrado glomerular actual.
# #
#      3.3. La decisión final corresponde siempre al prescriptor médico.
# #
#      3.4. Considere la situación clínica global del paciente antes de modificar dosis.
# #
# #
# # V. PROTECCIÓN INTEGRAL PESTAÑA 1 (💊 VALIDACIÓN):
# #
#    1. Blindaje Total: Prohibida cualquier modificación en el layout,
# orden de columnas o funciones.
# #
#    2. Componentes Congelados: Registro de paciente (fila única),
# Calculadora dual (Glow morado), Área de texto y Botonera.
# #
#    3. Lógica Funcional: El sistema de callbacks y el prompt de IA no
# admiten cambios de sintaxis.
# #
# #
# # VI. BLINDAJE PESTAÑA 2 (📄 INFORME - SOIP & IC):
# #
#    1. ESTRUCTURA SOIP: 4 cuadros de texto verticales con etiquetas de cabecera discretas.
# #
#    2. FRASES FIJAS POR DEFECTO:
# #
#      2.1. Subjetivo (S): "Revisión farmacoterapéutica según función renal."
# #
#      2.2. Objetivo (O): Solo valores > 0. Formato: "Edad: X | Peso: Y | Cr: Z | FG: W".
# #
#      2.3. Interpretación (I): Se anotará automáticamente la síntesis de medicamentos afectados.
# #
#      2.4. Plan (P): "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
# #
#    3. ESTRUCTURA INTERCONSULTA (IC): Un cuadro bajo el otro (Layout Vertical).
# #
#    4. TEXTO IC OBLIGATORIO: "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente." 
# #
#      4.1. [Se listará automáticamente lo que aparezca en la sección "I"].
# #
# #
# # VII. BLINDAJE ENTRADA MANUAL LAB Y VOLCADO EXCEL:
# #
#    1. Se protegen los campos FG CKD-EPI y FG MDRD-4 situados bajo el Glow Morado.
# #
#    2. El texto del placeholder debe desaparecer al escribir y mostrar la unidad 
# "mL/min/1,73m²" de forma discreta.
# #
#    3. Se blinda el botón "GUARDAR CAMBIOS EN EXCEL" centrado en la base de la Pestaña 2.
# #
# =================================================================

st.set_page_config(page_title="Asistente Renal", layout="wide", initial_sidebar_state="collapsed")

if "active_model" not in st.session_state:
     st.session_state.active_model = "BUSCANDO..."

# Inicialización de estados con textos fijos (Principio VI)
if "soip_s" not in st.session_state: st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
if "soip_o" not in st.session_state: st.session_state.soip_o = ""
if "soip_i" not in st.session_state: st.session_state.soip_i = ""
if "soip_p" not in st.session_state: st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
if "ic_motivo" not in st.session_state: st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
if "ic_info" not in st.session_state: st.session_state.ic_info = ""
if "main_meds" not in st.session_state: st.session_state.main_meds = ""

def reset_registro():
     st.session_state["reg_centro"] = ""; st.session_state["reg_edad"] = None
     st.session_state["reg_id"] = ""; st.session_state["reg_res"] = "No"
     # Reset sincrónico
     if "calc_e" in st.session_state: st.session_state.calc_e = None

def reset_meds():
     st.session_state.main_meds = ""
     st.session_state.soip_s = "Revisión farmacoterapéutica según función renal."
     st.session_state.soip_o = ""
     st.session_state.soip_i = ""
     st.session_state.soip_p = "Se hace interconsulta al MAP para valoración de ajuste posológico y seguimiento de función renal."
     st.session_state.ic_motivo = "Se solicita valoración médica tras la revisión de la adecuación del tratamiento a la función renal del paciente."
     st.session_state.ic_info = ""

try:
     API_KEY = st.secrets["GEMINI_API_KEY"]
     genai.configure(api_key=API_KEY)
except:
     API_KEY = None

def verificar_datos_completos():
     campos = {
         "Centro": "reg_centro",
         "Edad": "reg_edad",
         "ID Alfa": "reg_id",
         "Residencia": "reg_res",
         "Calc. Edad": "calc_e",
         "Calc. Peso": "calc_p",
         "Calc. Creatinina": "calc_c",
         "Calc. Sexo": "calc_s",
         "FG CKD-EPI": "fgl_ckd",
         "FG MDRD-4": "fgl_mdrd"
     }
     campos_vacios = []
     for nombre, key in campos.items():
         valor = st.session_state.get(key)
         if valor is None or valor == "":
             campos_vacios.append(nombre)
     return campos_vacios

def llamar_ia_en_cascada(prompt):
     disponibles = [m.name.replace('models/', '').replace('gemini-', '') for m in genai.list_models() if 'generateContent' in m.supported_generation_methods] if API_KEY else ["2.5-flash"]
     orden = ['2.5-flash', 'flash-latest', '1.5-pro']
     for mod_name in orden:
         if mod_name in disponibles:
             try:
                 st.session_state.active_model = mod_name.upper()
                 model = genai.GenerativeModel(f'models/gemini-{mod_name}')
                 return model.generate_content(prompt).text
             except: continue
     return "⚠️ Error."

def inject_styles():
     st.markdown("""
     <style>
     .block-container { max-width: 100% !important; padding-top: 1rem !important; padding-left: 4% !important; padding-right: 4% !important; }
     .black-badge-zona { background-color: #000000; color: #888; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 15px; z-index: 999999; }
     .black-badge-activo { background-color: #000000; color: #00FF00; padding: 6px 14px; border-radius: 4px; font-family: monospace; font-size: 0.7rem; border: 1px solid #333; position: fixed; top: 10px; left: 145px; z-index: 999999; text-shadow: 0 0 5px #00FF00; }
     .main-title { text-align: center; font-size: 2.5rem; font-weight: 800; color: #1E1E1E; margin-bottom: 0px; margin-top: 20px; }
     .sub-version { text-align: center; font-size: 0.6rem; color: #bbb; margin-top: -5px; margin-bottom: 20px; font-family: monospace; }
     .fg-glow-box { background-color: #000000; color: #FFFFFF; border: 2.2px solid #9d00ff; box-shadow: 0 0 15px #9d00ff; padding: 15px; border-radius: 12px; text-align: center; height: 140px; display: flex; flex-direction: column; justify-content: center; }
     .unit-label { font-size: 0.65rem; color: #888; margin-top: -10px; margin-bottom: 5px; font-family: sans-serif; text-align: center; }
     .synthesis-box { padding: 15px; border-radius: 12px; margin-bottom: 15px; border-width: 2.2px; border-style: solid; font-size: 0.95rem; }
     .glow-green { background-color: #f1f8e9; color: #2e7d32; border-color: #a5d6a7; box-shadow: 0 0 12px #a5d6a7; }
     .glow-orange { background-color: #fff3e0; color: #e65100; border-color: #ffcc80; box-shadow: 0 0 12px #ffcc
