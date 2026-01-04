import streamlit as st
import zipfile
import json
import os
import pandas as pd
import plotly.express as px
import shutil

st.set_page_config(page_title="PBIX Insight Explorer", layout="wide")

st.title("📊 PBIX Key Insight Explorer")
st.write("Upload your AdventureWorks or any Power BI file to see its underlying structure.")

uploaded_file = st.file_uploader("Choose a .pbix file", type="pbix")

def parse_pbix(file):
    # Temporary directory for extraction
    extract_path = "temp_pbix"
    if os.path.exists(extract_path):
        shutil.rmtree(extract_path)
    
    with zipfile.ZipFile(file, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    
    layout_path = os.path.join(extract_path, "Report", "Layout")
    
    visual_data = []
    
    if os.path.exists(layout_path):
        with open(layout_path, 'r', encoding='utf-16-le') as f:
            data = json.load(f)
            
        for section in data.get('sections', []):
            page_name = section.get('displayName')
            visuals = section.get('visualContainers', [])
            
            for vis in visuals:
                config_str = vis.get('config')
                if config_str:
                    config = json.loads(config_str)
                    vis_type = config.get('singleVisual', {}).get('visualType')
                    if vis_type:
                        visual_data.append({
                            "Page": page_name,
                            "Visual Type": vis_type
                        })
    return pd.DataFrame(visual_data)

if uploaded_file:
    with st.spinner('Analyzing PBIX structure...'):
        df = parse_pbix(uploaded_file)
        
    if not df.empty:
        # --- Metrics ---
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Pages", df['Page'].nunique())
        col2.metric("Total Visuals", len(df))
        col3.metric("Unique Visual Types", df['Visual Type'].nunique())
        
        st.divider()

        # --- Charts ---
        left_chart, right_chart = st.columns(2)
        
        with left_chart:
            st.subheader("Visual Distribution")
            fig_bar = px.bar(df['Visual Type'].value_counts().reset_index(), 
                             x='Visual Type', y='count', color='Visual Type',
                             labels={'count': 'Frequency'})
            st.plotly_chart(fig_bar, use_container_width=True)
            
        with right_chart:
            st.subheader("Visuals per Page")
            fig_pie = px.pie(df, names='Page', hole=0.4)
            st.plotly_chart(fig_pie, use_container_width=True)

        # --- Data Table ---
        st.subheader("Raw Metadata View")
        selected_page = st.selectbox("Filter by Page", options=["All"] + list(df['Page'].unique()))
        
        if selected_page != "All":
            st.dataframe(df[df['Page'] == selected_page], use_container_width=True)
        else:
            st.dataframe(df, use_container_width=True)
            
    else:
        st.error("No visual metadata could be extracted. The file might be protected or empty.")