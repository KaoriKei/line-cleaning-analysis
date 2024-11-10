import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import re
import io

# ページ設定
st.set_page_config(
    page_title="清掃記録分析",
    page_icon="🧹",
    layout="centered"
)

# カスタムCSS
st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        margin-bottom: 1rem;
        color: #1F618D;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #2874A6;
        margin-bottom: 2rem;
    }
    .stButton>button {
        background-color: #2874A6;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 0.5rem;
        border: none;
        font-size: 1.2rem;
        transition: all 0.3s;
    }
    .stButton>button:hover {
        background-color: #1F618D;
    }
    .metric-card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# アプリケーションヘッダー
st.markdown('<p class="main-header">清掃記録分析 🧹</p>', unsafe_allow_html=True)
st.markdown('<p class="sub-header">LINEトーク履歴から清掃記録を簡単に分析</p>', unsafe_allow_html=True)

# サイドバー - 設定
with st.sidebar:
    st.header("⚙️ 設定")
    default_keyword = "いまから清掃を開始します"
    keyword = st.text_input(
        "検索キーワード",
        value=default_keyword,
        help="清掃開始を示すメッセージのキーワードを入力してください"
    )

# メインコンテンツ
st.markdown("### 📁 LINEトーク履歴をアップロード")
uploaded_file = st.file_uploader(
    "テキストファイル(.txt)を選択またはドラッグ＆ドロップしてください",
    type=['txt'],
    help="LINEアプリからエクスポートしたトーク履歴のテキストファイルをアップロードしてください"
)

if uploaded_file:
    try:
        # ファイル処理
        content = uploaded_file.read().decode('utf-8')
        lines = content.split('\n')
        records = []
        current_date = None
        
        with st.spinner('分析中...'):
            for line in lines:
                date_match = re.search(r'\d{4}/\d{2}/\d{2}', line)
                if date_match:
                    current_date = date_match.group()
                    continue
                    
                if keyword in line and current_date:
                    time_match = re.search(r'\d{2}:\d{2}', line)
                    if time_match:
                        records.append({
                            '日付': current_date,
                            '時間': time_match.group(),
                            'メッセージ': line.strip()
                        })

        if records:
            df = pd.DataFrame(records)
            df['日付'] = pd.to_datetime(df['日付'])
            df = df.sort_values('日付')

            # サマリー統計
            st.markdown("### 📊 分析結果")
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h3>総清掃回数</h3>
                        <h2>{len(df)}回</h2>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            with col2:
                last_month = df[df['日付'].dt.month == df['日付'].max().month]
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h3>今月の清掃回数</h3>
                        <h2>{len(last_month)}回</h2>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )
            
            with col3:
                avg_per_month = len(df) / df['日付'].dt.to_period('M').nunique()
                st.markdown(
                    f"""
                    <div class="metric-card">
                        <h3>月平均回数</h3>
                        <h2>{avg_per_month:.1f}回</h2>
                    </div>
                    """, 
                    unsafe_allow_html=True
                )

            # グラフ
            st.markdown("### 📈 月別推移")
            monthly = df.groupby(df['日付'].dt.strftime('%Y-%m')).size()
            fig = px.bar(
                monthly,
                title="月別清掃回数",
                labels={'value': '清掃回数', 'index': '月'},
                template='simple_white'
            )
            st.plotly_chart(fig, use_container_width=True)

            # 曜日別グラフ
            st.markdown("### 📅 曜日別集計")
            weekday = df.groupby(df['日付'].dt.strftime('%A')).size()
            fig_weekday = px.bar(
                weekday,
                title="曜日別清掃回数",
                labels={'value': '清掃回数', 'index': '曜日'},
                template='simple_white'
            )
            st.plotly_chart(fig_weekday, use_container_width=True)

            # Excelファイルの作成
            excel_buffer = io.BytesIO()
            with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                df.to_excel(writer, sheet_name='全記録', index=False)
                monthly.to_frame('清掃回数').to_excel(writer, sheet_name='月別集計')
                weekday.to_frame('清掃回数').to_excel(writer, sheet_name='曜日別集計')

            excel_buffer.seek(0)
            
            # ダウンロードボタン
            st.download_button(
                label="📥 Excelファイルをダウンロード",
                data=excel_buffer,
                file_name="清掃記録分析.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        else:
            st.warning(f"⚠️ キーワード「{keyword}」が見つかりませんでした。")

    except Exception as e:
        st.error(f"エラーが発生しました: {str(e)}")
        st.error("ファイルの形式を確認してください。")

# フッター
st.markdown("---")
st.markdown("Created with ❤️ using Streamlit")