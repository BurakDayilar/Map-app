import streamlit as st
import folium
import pandas as pd
from streamlit_folium import folium_static

# Sayfa başlığı
st.set_page_config(page_title="Network Coverage Map", layout="wide")
st.title("📡 Network Coverage Map by Vendor")

# Harita boyutunu artırmak için özel CSS
st.markdown(
    """
    <style>
        .reportview-container .main .block-container{
            max-width: 95%;
            padding-top: 20px;
        }
    </style>
    """,
    unsafe_allow_html=True
)

# Kullanıcıdan Excel dosyası yüklemesini iste
uploaded_file = st.file_uploader("Lütfen Cell_Db dosyanızı yükleyin", type=["xlsx"])
if uploaded_file is not None:
    # Excel dosyasını oku
    cell_db = pd.ExcelFile(uploaded_file)
    
    # Harita oluştur
    m = folium.Map(location=[40.40, 49.86], zoom_start=8, tiles="https://{s}.basemaps.cartocdn.com/rastertiles/voyager_nolabels/{z}/{x}/{y}{r}.png", attr="CARTO")
    
    # Teknoloji, vendor ayrımı ve renk tanımları
    types_vendors_colors = {
        "2G": {"column": "BSC", "eri": "E", "hwi": "H", "eri_color": "orange", "hwi_color": "gray"},
        "3G": {"column": "RNC", "eri": "E", "hwi": "H", "eri_color": "yellow", "hwi_color": "pink"},
        "4G": {"column": "RBS", "eri": "6", "hwi": ["MTS9604B", "DBS5900", "MTS9303A", "Nokia Ps"], "eri_color": "green", "hwi_color": "red"},
        "5G": {"column": "DU_TYPE", "eri": ["BBU5216", "BBU6630", "BBU6631"], "hwi": ["BBU5900"], "eri_color": "purple", "hwi_color": "black"}
    }
    
    # Teknoloji bazlı veri sayısını hesaplayan fonksiyon
    def count_filtered_data(df, column, eri_criteria, hwi_criteria):
        count_eri = df[df[column].astype(str).isin(eri_criteria)].shape[0] if isinstance(eri_criteria, list) else df[df[column].astype(str).str.startswith(eri_criteria, na=False)].shape[0]
        count_hwi = df[df[column].astype(str).isin(hwi_criteria)].shape[0] if isinstance(hwi_criteria, list) else df[df[column].astype(str).str.startswith(hwi_criteria, na=False)].shape[0]
        return count_eri, count_hwi
    
    # Haritaya tüm teknolojileri ekle
    legend_counts = {}
    for tech, filters in types_vendors_colors.items():
        if tech in cell_db.sheet_names:
            df = cell_db.parse(tech)
            df.columns = df.columns.str.strip().str.upper()
            
            # Latitude ve Longitude isim düzeltme
            df.rename(columns={"LATIDUDE": "LATITUDE", "LONGTITUDE": "LONGITUDE"}, inplace=True)
            
            if "LATITUDE" not in df.columns or "LONGITUDE" not in df.columns:
                st.warning(f"⚠️ Hata: {tech} sayfasında 'LATITUDE' veya 'LONGITUDE' sütunu eksik!")
                continue
            
            count_eri, count_hwi = count_filtered_data(df, filters["column"], filters["eri"], filters["hwi"])
            legend_counts[tech] = {"ERI": count_eri, "HWI": count_hwi}
            
            df_eri = df[df[filters["column"]].astype(str).isin(filters["eri"])] if isinstance(filters["eri"], list) else df[df[filters["column"]].astype(str).str.startswith(filters["eri"], na=False)]
            df_hwi = df[df[filters["column"]].astype(str).isin(filters["hwi"])] if isinstance(filters["hwi"], list) else df[df[filters["column"]].astype(str).str.startswith(filters["hwi"], na=False)]
            
            for dataset, color in [(df_eri, filters["eri_color"]), (df_hwi, filters["hwi_color"])]:
                if not dataset.empty:
                    for _, row in dataset.iterrows():
                        if pd.isnull(row["LATITUDE"]) or pd.isnull(row["LONGITUDE"]):
                            continue
                        folium.CircleMarker(
                            [row["LATITUDE"], row["LONGITUDE"]],
                            radius=3,  # Nokta boyutu büyütüldü
                            color=color,
                            fill=True,
                            fill_color=color,
                            fill_opacity=1
                        ).add_to(m)
    
    # Legend HTML oluştur
    legend_html = """
        <div style="position: fixed; top: 50px; right: 50px; z-index: 9999; 
                    background-color: white; padding: 20px; border:2px solid grey; 
                    border-radius:5px; font-size:16px;">
    """
    for tech, counts in legend_counts.items():
        legend_html += f"<b>{tech} Number of Cells by Vendor</b><br>"
        legend_html += f"<i style='background: {types_vendors_colors[tech]['eri_color']}; width: 15px; height: 15px; display: inline-block;'></i> Ericsson ({counts['ERI']})<br>"
        legend_html += f"<i style='background: {types_vendors_colors[tech]['hwi_color']}; width: 15px; height: 15px; display: inline-block;'></i> Huawei ({counts['HWI']})<br>"
    legend_html += "</div>"
    m.get_root().html.add_child(folium.Element(legend_html))
    
    # Haritayı ekranda daha büyük göster
    folium_static(m, width=1200, height=700)
    
    st.success("✅ Harita başarıyla oluşturuldu!")
