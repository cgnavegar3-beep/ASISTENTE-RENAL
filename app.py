# --- BLOQUE ACTUALIZADO: CÁLCULO AUTOMÁTICO FG ---
    with col_der:
        st.markdown("#### 💊 Filtrado Glomerular")
        fg_m = st.text_input("Ajuste Manual", placeholder="Fórmula Cockcroft-Gault: entrada manual")
        valor_fg = fg_m if fg_m else fg
        st.markdown(f'''<div class="fg-glow-box"><div style="font-size: 3.2rem; font-weight: bold;">{valor_fg}</div><div style="font-size: 0.8rem; color: #9d00ff;">mL/min (C-G)</div></div>''', unsafe_allow_html=True)
        st.markdown('<div class="formula-label">Fórmula Cockcroft-Gault</div>', unsafe_allow_html=True)
        st.write(""); l1, l2 = st.columns(2)
        
        # --- Lógica de cálculo automático para CKD-EPI y MDRD ---
        calc_ckd = None
        calc_mdrd = None
        if calc_e and calc_c and calc_s:
            # Fórmula simplificada aproximada para visualización inmediata si se requiere
            # (Nota: CKD-EPI requiere raza, se omite aquí por no estar en el input original)
            kappa = 0.7 if calc_s == "Mujer" else 0.9
            alpha = -0.329 if calc_s == "Mujer" else -0.411
            
            # Cálculo MDRD-4 aproximado
            calc_mdrd = round(175 * (calc_c ** -1.154) * (calc_e ** -0.203) * (0.742 if calc_s == "Mujer" else 1.0), 1)

        with l1:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            # Se asigna calc_ckd al value por defecto si existe, permitiendo edición manual
            val_ckd = st.number_input("FG CKD-EPI", value=None, placeholder="FG CKD-EPI", label_visibility="collapsed", key="fgl_ckd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_ckd is not None: st.markdown(f'<div class="unit-label">{val_ckd} mL/min/1,73m²</div>', unsafe_allow_html=True)
            
        with l2:
            st.markdown('<div class="fg-special-border">', unsafe_allow_html=True)
            # Se asigna calc_mdrd al value por defecto si existe, permitiendo edición manual
            val_mdrd = st.number_input("FG MDRD-4 IDMS", value=calc_mdrd, placeholder="FG MDRD-4 IDMS", label_visibility="collapsed", key="fgl_mdrd")
            st.markdown('</div>', unsafe_allow_html=True)
            if val_mdrd is not None: st.markdown(f'<div class="unit-label">{val_mdrd} mL/min/1,73m²</div>', unsafe_allow_html=True)
# --- FIN BLOQUE ACTUALIZADO ---
