from streamlit_option_menu import option_menu
from streamlit_apex_charts import bar_chart,area_chart,donut_chart,mixed_chart,scatter_chart,line_chart
from pymongo import MongoClient
import pandas as pd
from scipy.stats import percentileofscore
import tushare as ts
import datetime
import time
from config_package.config import *
pro = ts.pro_api("ab9bd05c38852f579af7c43978e914a93e242e19e760dedb310ed827")
set_page()

select_day=datetime.datetime.now().strftime('%Y-%m-%d')
select_day_str = ''.join(filter(str.isalnum, select_day))
select_day = datetime.date(int(str(select_day_str)[0:4]), int(str(select_day_str)[4:-2]),int(str(select_day_str)[-2:]))


with st.form("auth"):
    start_day = st.date_input("开始日期", value=datetime.date(2018, 1, 1))
    start_day = start_day.strftime('%Y-%m-%d')
    start_day_str = ''.join(filter(str.isalnum, start_day))
    start_day = datetime.date(int(str(start_day_str)[0:4]), int(str(start_day_str)[4:-2]), int(str(start_day_str)[-2:]))
    submitted = st.form_submit_button("提交")

    select_day = st.date_input("结束日期")
    select_day = select_day.strftime('%Y-%m-%d')
    select_day_str = ''.join(filter(str.isalnum, select_day))
    select_day = datetime.date(int(str(select_day_str)[0:4]), int(str(select_day_str)[4:-2]),int(str(select_day_str)[-2:]))

with st.spinner('数据加载中...'):
    df_future_concat=pd.DataFrame()
    client = MongoClient('localhost', 27017)
    db_stock = client['股票市场行情数据']

    ts_db_code = db_stock.list_collection_names(session=None)
    for code in ts_db_code:
        table_std=db_stock[code]
        df_std = pd.DataFrame(list(table_std.find())).iloc[1:,:]
        df_future_concat.append(df_std)

    df_std = pd.DataFrame(list(table_std.find()))
    df_std = df_std[(df_std["trade_date"] <= select_day_str) & (df_std["trade_date"] >= start_day_str)]

    df_std=df_std.loc[:, ["trade_date", "1_days_pct_change", "3_days_pct_change", "5_days_pct_change", "10_days_pct_change"]].set_index(["trade_date"])
    df_std.loc[:, "1_day_std"]=df_std.loc[:, "1_days_pct_change"]
    df_std.loc[:, "3_day_std"]=df_std.loc[:, "3_days_pct_change"]
    df_std.loc[:, "5_day_std"]=df_std.loc[:, "5_days_pct_change"]
    df_std.loc[:, "10_day_std"]=df_std.loc[:, "10_days_pct_change"]

    analyse_text="""
                ## 截面离散程度情况  
                截止{text_0}，截面收益率（1天）标准差为{text_1}%，截面收益率（3天）标准差为{text_2}%，截面收益率（5天）标准差为{text_3}%，截面收益率（10天）标准差为{text_4} % 
                自{text_5}以来，分别处于{text_6}，{text_7}，{text_8}，{text_9}分位
                  """.format(
                        text_0=df_std.index[-1],
                        text_1=round(df_std.loc[:,"1_day_std"][-1]*100,2),
                        text_2=round(df_std.loc[:,"3_day_std"][-1]*100,2),
                        text_3=round(df_std.loc[:,"5_day_std"][-1]*100,2),
                        text_4=round(df_std.loc[:,"10_day_std"][-1]*100,2),
                        text_5=df_std.index[0],
                        text_6=int(percentileofscore(df_std.loc[:,"1_day_std"],df_std.loc[:,"1_day_std"][-1])),
                        text_7=int(percentileofscore(df_std.loc[:, "3_day_std"], df_std.loc[:, "3_day_std"][-1])),
                        text_8= int(percentileofscore(df_std.loc[:, "5_day_std"], df_std.loc[:, "5_day_std"][-1])),
                        text_9=int(percentileofscore(df_std.loc[:, "10_day_std"], df_std.loc[:, "10_day_std"][-1])),)

    db_timeseries_std = client['指数时间序列标准差']
    table_timeseries = db_timeseries_std['时间序列标准差']
    df_timeseries_std = pd.DataFrame(list(table_timeseries.find())).loc[:,["trade_date","name","3_days_rolling_volatility","5_days_rolling_volatility","10_days_rolling_volatility"]]
    df_timeseries_std = df_timeseries_std[(df_timeseries_std["trade_date"] <= select_day_str) & (df_timeseries_std["trade_date"] >= start_day_str)]

    nhsp = df_timeseries_std[df_timeseries_std.loc[:, "name"] == "南华商品指数"].set_index(["trade_date"]).drop(['name'],axis=1)
    tab1, tab2= st.tabs(["▶️横截面", "▶️时间序列"])

    with tab1:
        time.sleep(1)
        st.markdown(analyse_text)
        time.sleep(1)
        line_chart("截面收益率（1天）标准差（%）",(df_std.loc[:, ["1_day_std"]]*100).round(2))
        time.sleep(1)
        line_chart("截面收益率（3天）标准差（%）",( df_std.loc[:, ["3_day_std"]]*100).round(2))
        time.sleep(1)
        line_chart("截面收益率（5天）标准差（%）",(df_std.loc[:, ["5_day_std"]]*100).round(2))
        time.sleep(1)
        line_chart("截面收益率（10天）标准差（%）", (df_std.loc[:, ["10_day_std"]]*100).round(2))
        time.sleep(1)
    with tab2:
        time.sleep(1)
        line_chart("时序（3天）标准差（%）", (nhsp * 100).round(2).loc[:,["3_days_rolling_volatility"]])
        time.sleep(2)
        line_chart("时序（5天）标准差（%）", (nhsp * 100).round(2).loc[:, ["5_days_rolling_volatility"]])
        time.sleep(2)
        line_chart("时序（10天）标准差（%）", (nhsp * 100).round(2).loc[:, ["10_days_rolling_volatility"]])
        time.sleep(1)
