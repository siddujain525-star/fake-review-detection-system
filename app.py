# --- LIME SECTION ---
        st.subheader("Visual Explanation")
        
        # We manually define the mapping to ensure the chart matches the verdict
        # 0 = Fake (CG), 1 = Real (OR)
        map_names = ['Fake (CG)', 'Real (OR)'] 
        
        explainer = LimeTextExplainer(class_names=map_names)
        
        with st.spinner("Generating feature importance..."):
            exp = explainer.explain_instance(
                review, 
                c.predict_proba, 
                num_features=10
            )
            
            # CSS for Dark Mode visibility
            lime_html = exp.as_html()
            custom_css = """
            <style>
                .lime { color: white !important; }
                text { fill: white !important; }
                .lime.label { color: #ffaa00 !important; font-weight: bold; }
                body { background-color: #0e1117; }
            </style>
            """
            # FIXED: Removed the extra ) at the end of this line
            components.html(custom_css + lime_html, height=600, scrolling=True)
