import streamlit as st

# Configuración de página para respetar el diseño de ASISTENTE RENAL
st.set_page_config(page_title="ASISTENTE RENAL", layout="wide")

# --- BLOQUE DE CÓDIGO ÍNTEGRO (HTML/CSS/JS) ---
# Se utilizan f-strings con doble llave {{ }} para proteger el CSS del intérprete de Python
asistente_renal_app = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        /* ========================================================================
        BLOQUE DE PROTECCIÓN: PRINCIPIOS FUNDAMENTALES (PPIO FUNDAMENTAL)
        ======================================================================== */
        :root {{
            --purple-glow: 0 0 15px #a855f7;
            --black-box-bg: #1a1a1a;
            --yellow-warning: #fef08a;
            --border-color: #333;
        }}

        body {{
            background-color: #000;
            color: #fff;
            font-family: sans-serif;
            margin: 0;
            padding-bottom: 90px;
        }}

        /* [2026-02-08] Contador discreto superior izquierda (estilo v2.5) */
        #intentos-counter {{
            position: fixed;
            top: 10px;
            left: 10px;
            font-size: 0.75rem;
            color: #666;
            z-index: 2000;
        }}

        header {{
            text-align: center;
            padding: 30px 20px 10px 20px;
        }}

        /* [2026-02-19] Nombre ASISTENTE RENAL Inamovible */
        h1 {{ 
            margin: 0; 
            font-size: 1.8rem;
            letter-spacing: 2px;
        }}

        /* [2026-02-16] Versión pequeña debajo del título */
        .version-header {{
            font-size: 0.6rem;
            color: #888;
            display: block;
            margin-bottom: 15px;
        }}

        /* --- TABS SUPERIORES (BLINDADAS) --- */
        .tabs-container {{
            display: flex;
            justify-content: center;
            gap: 10px;
            margin-bottom: 20px;
            position: sticky;
            top: 0;
            background: #000;
            padding: 10px 0;
            z-index: 900;
        }}

        .tab-btn {{
            background: var(--black-box-bg);
            color: #aaa;
            border: 1px solid var(--border-color);
            padding: 8px 15px;
            cursor: pointer;
            font-size: 0.85rem;
        }}

        .tab-btn.active {{
            color: #fff;
            border-color: #a855f7;
            box-shadow: var(--purple-glow);
        }}

        /* --- INTERFAZ DUAL (BLINDADA) --- */
        .interfaz-dual {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            padding: 0 20px;
            max-width: 1200px;
            margin: 0 auto;
        }}

        .box-negro {{
            background: var(--black-box-bg);
            border: 1px solid var(--border-color);
            padding: 20px;
        }}

        /* Calculadora y Filtrado Glomerular (Purple Glow Box) */
        .filtrado-glomerular-box {{
            border: 1px solid #a855f7;
            box-shadow: var(--purple-glow);
        }}

        /* [2026-02-16] Yellow Shaded Warning (PPIO FUNDAMENTAL) */
        .warning-shaded {{
            background: var(--yellow-warning);
            color: #000;
            padding: 15px;
            margin: 20px;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
        }}

        /* --- EVOLUCIÓN: BARRA INFERIOR FLOTANTE --- */
        .nav-inferior {{
            position: fixed;
            bottom: 0;
            left: 0;
            width: 100%;
            background: rgba(15, 15, 15, 0.95);
            backdrop-filter: blur(10px);
            border-top: 1px solid #333;
            display: flex;
            justify-content: space-around;
            padding: 15px 0;
            z-index: 1000;
        }}

        .nav-inferior button {{
            background: none;
            border: none;
            color: #555;
            display: flex;
            flex-direction: column;
            align-items: center;
            cursor: pointer;
            font-size: 0.7rem;
        }}

        .nav-inferior button.active {{
            color: #a855f7;
        }}

        /* [2026-02-16] Marcador de versión inferior derecha */
        .version-tag-footer {{
            position: fixed;
            bottom: 75px;
            right: 15px;
            font-size: 0.55rem;
            color: #444;
            z-index: 999;
        }}
    </style>
</head>
<body>

    <div id="intentos-counter">2.5 Remanentes: 10</div>

    <header>
        <h1>ASISTENTE RENAL</h1>
        <span class="version-header">v. 2026-02-22</span>
    </header>

    <nav class="tabs-container">
        <button class="tab-btn active">Calculadora</button>
        <button class="tab-btn">Filtrado Glomerular</button>
        <button class="tab-btn">Pacientes</button>
    </nav>

    <main>
        <div class="interfaz-dual">
            <div class="box-negro" id="registro-paciente">
                <h3>Registro de Paciente</h3>
                <p style="color: #666; font-size: 0.7rem;">[ESTRUCTURA BLINDADA]</p>
            </div>
            
            <div class="box-negro filtrado-glomerular-box" id="calculadora-renal">
                <h3>Filtrado Glomerular</h3>
                <p style="color: #666; font-size: 0.7rem;">[ESTRUCTURA BLINDADA]</p>
            </div>
        </div>

        <div class="warning-shaded">
            PPIO FUNDAMENTAL: Esta herramienta es de apoyo clínico. La decisión final es del facultativo.
        </div>
    </main>

    <nav class="nav-inferior">
        <button class="active"><span>🏠</span><span>Inicio</span></button>
        <button><span>🧬</span><span>Filtrado</span></button>
        <button><span>👥</span><span>Pacientes</span></button>
    </nav>

    <div class="version-tag-footer">v. 2026-02-22 12:15</div>

    <script>
        /* ========================================================================
        SECCIÓN DE PRINCIPIOS FUNDAMENTALES (PPIO FUNDAMENTAL) - NO MODIFICAR
        ========================================================================
        [2026-02-19] Nunca cambiar el nombre "ASISTENTE RENAL".
        [2026-02-19] Siempre mostrar la versión con la fecha debajo del nombre.
        [2026-02-19] Nunca modificar "Calculadora" y "Filtrado Glomerular" (purple glow).
        [2026-02-16] Blindar cajas negras, títulos, tabs y registro de pacientes.
        [2026-02-16] Registro de versión en esquina inferior derecha.
        [2026-02-08] No mostrar nombre del modelo, solo intentos remanentes (v2.5).
        ======================================================================== */
        console.log("ASISTENTE RENAL cargado con éxito.");
    </script>
</body>
</html>
"""

# Renderizado final en Streamlit sin errores de sintaxis
st.markdown(asistente_renal_app, unsafe_allow_html=True)
