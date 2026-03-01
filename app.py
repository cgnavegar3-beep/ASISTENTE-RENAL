# --- FUNCION DE PROCESAMIENTO HÍBRIDO (RegEx + IA) ---
def procesar_y_limpiar_meds():
    texto = st.session_state.main_meds
    if texto:
        # 1. Limpieza inicial rápida con RegEx
        texto_limpio = re.sub(r"\s*-\s*|;\s*", "\n", texto)
        texto_limpio = re.sub(r"\n+", "\n", texto_limpio).strip()
        
        # 2. Prompt IA modificado para incluir Principio Activo, Dosis y Marca
        prompt = f"""
        Actúa como farmacéutico clínico. Reescribe el siguiente listado de medicamentos siguiendo estas reglas estrictas:
        1. Estructura cada línea como: [Principio Activo] + [Dosis] + (Marca Comercial).
        2. Si no identificas la marca, omite el paréntesis.
        3. Coloca cada medicamento en una línea independiente.
        4. Mantén exactamente el mismo texto original si no es necesario reestructurar, sin añadir ni inventar información.
        5. No agregues numeración ni explicaciones.
        Texto a procesar:
        {texto_limpio}
        """
        
        # 3. Llamada a la IA (en cascada)
        resultado = llamar_ia_en_cascada(prompt)
        
        # 4. Actualiza el mismo cuadro
        st.session_state.main_meds = resultado
# ----------------------------------------------------
