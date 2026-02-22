<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASISTENTE RENAL</title>
    <style>
        /* ========================================================================
        BLOQUE DE PROTECCIÓN: PRINCIPIOS FUNDAMENTALES (PPIO FUNDAMENTAL)
        ========================================================================
        */
        :root {
            --purple-glow: 0 0 15px #a855f7;
            --black-box-bg: #1a1a1a;
            --yellow-warning: #fef08a;
        }

        /* [2026-02-08] Contador discreto superior izquierda (estilo v2.5) */
        #intentos-counter {
            position: fixed;
            top: 10px;
            left: 10px;
            font-size: 0.75rem;
            color: #666;
            z-index: 2000;
        }

        /* [2026-02-16] Blindaje de Interfaz Dual y Cajas Negras */
        .interfaz-dual {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(320px, 1fr));
            gap: 20px;
            padding: 20px;
        }

        .box-negro {
            background: var(--black-box-bg);
            border: 1px solid #333;
            padding: 20px;
        }

        /* No modificar Filtrado Glomerular (purple glow box) */
        .purple-glow-box {
            border: 1px solid #a855f7;
            box-shadow: var(--purple-glow);
        }

        /* [2026-02-16] Yellow Shaded Warning */
        .warning-shaded {
            background: var(--yellow-warning);
            color: #000;
            padding: 15px;
            margin: 20px;
            border-radius: 4px;
            font-weight: bold;
            text-align: center;
        }

        /* --- ESTILOS ADICIONALES PARA LA EVOLUCIÓN --- */
        body { background: #000; color: #fff; font-family: sans-serif; margin: 0; padding-bottom: 80px; }
        header { text-align: center; padding: 20px; }
        
        .nav-inferior {
            position: fixed; bottom: 0; width: 100%; background: rgba(26,26,26,0.9);
            border-top: 1px solid #333; display: flex; justify-content: space-around; padding: 10px 0;
            z-index: 1000;
        }

        .nav-inferior button { background: none; border: none; color: #888; cursor: pointer; }
        .nav-inferior button.active { color: #a855f7; }

        /* [2026-02-16] Versión en esquina inferior derecha */
        .version-tag-footer {
            position: fixed;
            bottom: 70px;
            right: 15px;
            font-size: 0.6rem;
            color: #444;
        }
    </style>
</head>
<body>

    <div id="intentos-counter">2.5 Remanentes: 10</div>

    <header>
        <h1>ASISTENTE RENAL</h1>
        <div style="font-size: 0.6rem; color: #888;">v. 2026-02-22</div>
    </header>

    <main>
        <div class="interfaz-dual">
            <div class="box-negro">
                <h3>Paciente</h3>
                </div>
            <div class="box-negro purple-glow-box">
                <h3>Calculadora / Filtrado</h3>
                </div>
        </div>

        <div class="warning-shaded">
            PPIO FUNDAMENTAL: Esta herramienta es de apoyo clínico. La decisión final es del facultativo.
        </div>
    </main>

    <nav class="nav-inferior">
        <button onclick="cambiarSeccion('calc')" id="btn-calc" class="active">INICIO</button>
        <button onclick="cambiarSeccion('filtrado')" id="btn-filt">FILTRADO</button>
        <button onclick="cambiarSeccion('pac')" id="btn-pac">PACIENTES</button>
    </nav>

    <div class="version-tag-footer">v. 2026-02-22 12:15</div>

    <script>
        /* ========================================================================
        SECCIÓN DE PRINCIPIOS FUNDAMENTALES (PPIO FUNDAMENTAL) - NO MODIFICAR
        ========================================================================
        [2026-02-19] Nunca cambiar el nombre "ASISTENTE RENAL".
        [2026-02-19] Siempre mostrar la fecha debajo del nombre.
        [2026-02-19] No modificar "Calculadora" ni "Filtrado Glomerular" (purple glow).
        [2026-02-16] Prohibido mover o cambiar la estructura visual sin autorización.
        [2026-02-16] Blindar: Títulos, Tabs, Registro de pacientes y Estructura Clipping.
        [2026-02-16] Registro de versión en la esquina inferior derecha.
        [2026-02-08] No mostrar nombre del modelo, solo intentos remanentes (estilo v2.5).
        ========================================================================
        */

        function cambiarSeccion(id) {
            console.log("Cambio a: " + id);
            // Lógica de sincronización aquí...
        }
    </script>
</body>
</html>
