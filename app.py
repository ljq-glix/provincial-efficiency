import streamlit as st
import pandas as pd
import plotly.express as px

# 1. 页面配置
st.set_page_config(page_title="省际效率分析", layout="wide")
st.title("公共管理项目：省际效率与碳排放分析 📊")


# 2. 读取合并后的数据
# 找到读取数据的这一行，改成读取 'data.xlsx'
# 建议用我之前给你的“绝对路径”写法，或者直接写文件名也行（云端默认在根目录）

@st.cache_data
def load_data():
    return pd.read_excel("data.xlsx") # <--- 确保这里改成了新名字

try:
    df_all = load_data()
except FileNotFoundError:
    st.error("❌ 找不到 'final_project_data.xlsx'。请先运行数据合并脚本。")
    st.stop()

# 3. 侧边栏交互
st.sidebar.header("筛选条件")
years = sorted(df_all['Year'].unique())
year_selected = st.sidebar.select_slider("选择年份", options=years, value=years[-1])

# 选择模型（对应不同的效率列）
model_map = {
    "SFA (随机前沿/DEA参考)": "DEA_Score",  # 对应你的 DEA 文件
    "BANN (贝叶斯神经网络)": "BANN_Score"  # 对应你的 BANN 文件
}
model_label = st.sidebar.radio("选择评估模型", list(model_map.keys()))
efficiency_col = model_map[model_label]

# 选择 X 轴变量 (因为你有多个投入变量)
x_axis_map = {
    "资本投入 (Capital)": "Capital",
    "劳动投入 (Labor)": "Labor",
    "能源投入 (Energy)": "Energy",
    "金融投入 (Finance)": "Finance"
}
x_label = st.sidebar.selectbox("选择X轴投入指标", list(x_axis_map.keys()))
x_col = x_axis_map[x_label]

# 4. 数据筛选
df_filtered = df_all[df_all['Year'] == year_selected].copy()

# 5. 可视化展示
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader(f"{year_selected}年 投入产出效率分布")

    # 检查是否有数据缺失
    if df_filtered.empty:
        st.warning(f"{year_selected} 年没有数据。")
    else:
        # 散点图
        fig = px.scatter(
            df_filtered,
            x=x_col,  # 用户选择的投入变量
            y="Carbon_Emission",  # 你的输出变量
            size="Carbon_Emission",  # 气泡大小
            color=efficiency_col,  # 颜色深浅代表效率值
            hover_name="Province",  # 鼠标悬停显示省份
            title=f"{x_label} vs 碳排放 (颜色表示 {model_label.split(' ')[0]} 效率)",
            color_continuous_scale="Viridis",  # 颜色盘
            template="plotly_white"
        )
        st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("效率排名 Top 5")
    # 按当前选中的效率值排序
    top_5 = df_filtered.sort_values(by=efficiency_col, ascending=False).head(5)
    st.table(top_5[['Province', efficiency_col]])

# 6. (可选) 数据详情
with st.expander("查看当前年份详细数据"):
    st.dataframe(df_filtered)

st.divider() # 分割线
st.subheader("📈 单省份历史趋势分析")

# 选择省份
prov_list = df_all['Province'].unique()
selected_prov = st.selectbox("选择要分析的省份", prov_list)

# 筛选该省份所有年份的数据
df_prov = df_all[df_all['Province'] == selected_prov].sort_values("Year")

# 画双轴图：左轴看效率，右轴看碳排放
import plotly.graph_objects as go
from plotly.subplots import make_subplots

fig_trend = make_subplots(specs=[[{"secondary_y": True}]])

# 1. 效率曲线
fig_trend.add_trace(
    go.Scatter(x=df_prov['Year'], y=df_prov['BANN_Score'], name="BANN 效率", mode='lines+markers'),
    secondary_y=False,
)
fig_trend.add_trace(
    go.Scatter(x=df_prov['Year'], y=df_prov['DEA_Score'], name="SFA 效率", mode='lines+markers', line=dict(dash='dot')),
    secondary_y=False,
)

# 2. 碳排放曲线
fig_trend.add_trace(
    go.Bar(x=df_prov['Year'], y=df_prov['Carbon_Emission'], name="碳排放量", opacity=0.3),
    secondary_y=True,
)

# 设置标题和轴
fig_trend.update_layout(title=f"{selected_prov}：效率与排放演变 (2010-2022)")
fig_trend.update_yaxes(title_text="效率值 (0-1)", secondary_y=False)
fig_trend.update_yaxes(title_text="碳排放 (标准化)", secondary_y=True)

st.plotly_chart(fig_trend, use_container_width=True)