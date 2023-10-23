import streamlit as st
from eastmoneyapi import EastmoneyApi
from extractor import *
from processor import *
import pandas as pd
FONT_CSS = """
<style>
    /* 定义全局英文字体为 Times New Roman */
    body {
        font-family: 'Times New Roman', sans-serif;
    }
    
    /* 定义标题的字体 */
    h1 {
        font-family: 'Times New Roman', sans-serif;
    }
    /* 定义Streamlit标题的字体 */
    .stMarkdown h1 {
        font-family: 'Times New Roman', sans-serif;
    }

    /* 定义Streamlit输入框的字体 */
    .stTextInput input {
        font-family: 'Times New Roman', sans-serif;
    }
    /* 定义输入框的字体 */
    st.text_input {
        font-family: 'Times New Roman', sans-serif;
    }

    /* 定义表格中的中文字体为楷体 */
    st.table {
        font-family: 'KaiTi', 'Times New Roman', sans-serif;
    }
    
</style>
"""
st.markdown(FONT_CSS, unsafe_allow_html=True)
mobile_css = """
<style>
    @media only screen and (max-width: 768px) {
        table {
            display: block;
            overflow-x: auto;
            white-space: nowrap;
        }
        th, td {
            font-size: 10px; /* 适当调整字体大小 */
            padding: 5px !important; /* 减少填充 */
        }
        body, .stTextInput input {
            font-size: 12px; /* 调整非表格文本的字体大小 */
        }
        .stTextInput input {
            height: 3em; /* 调整输入框大小 */
        }
    }
</style>
"""
st.markdown(mobile_css, unsafe_allow_html=True)
# 添加一个标题
st.markdown('### 基金持股')

# 用户输入
user_input = st.text_input('请输入基金代码:比如007119')

if  user_input:
    code = user_input
    quarter = '2023Q2'
    sl = [code]
    fields = ['基金名称', '季度', '股票代码', '股票名称','占净值比例', '持仓市值(亿元)','最新价','持股数（万股）','股息率', "市盈(动)","所属行业"]
    api = EastmoneyApi()

    try:
    # 假设 get_fund_basic_info 和 extract_manager_info 函数已经定义并可以使用
        fund_data = get_fund_basic_info(code)
        fund_name=fund_data['fS_name']
        fund_code=fund_data['fS_code']
        st.write(f"基金名称：{fund_name}")
        st.write(f"基金代码：{fund_code}")
        yield_rates = f"""
        收益率：
        - 1月：{fund_data['syl_1y']}%
        - 3月：{fund_data['syl_3y']}%
        - 6月：{fund_data['syl_6y']}%
        - 1年：{fund_data['syl_1n']}%
        """

        # 在Streamlit应用中显示格式化的字符串
        st.write(yield_rates)
        managers_data = fund_data['Data_currentFundManager']
        # 使用多线程进行并行处理
        with ThreadPoolExecutor() as executor:
            managers = list(executor.map(extract_manager_info, managers_data))
        fund_data = fetch_fund_data(code)
        ths_managers = process_fund_manager(fund_data)



    # 1. 创建一个从基金经理姓名到他们信息的映射
        managers_info = {manager['基金经理']: manager for manager in managers}
        # 2. 遍历新代码的基金经理列表，更新原始信息
        for new_manager in ths_managers:
            # 如果这个基金经理已经在原始数据中，我们就更新他们的记录
            if new_manager['姓名'] in managers_info:
                managers = managers_info[new_manager['姓名']]
                managers['起始时间'] = new_manager.get('起始时间')
                managers['结束时间'] = new_manager.get('结束时间')
                managers['简介'] = new_manager.get('简介')
                managers['年龄'] = new_manager.get('年龄')
                managers['学历'] = new_manager.get('学历')
                managers['其他基金'] = new_manager.get('其他基金')

        manager_html = ""

        for manager_name, manager_info in managers_info.items():
            manager_card = f"""
            <div class="card custom-card mb-3" style="position: relative; padding: 20px; overflow: hidden;">
                <img src="{manager_info['图片']}" class="card-img manager-image" alt="{manager_name}" style="width: 150px; height: 150px; position: absolute; top: 20px; right: 20px; z-index: 1;">
                <div class="card-body" style="z-index: 2; position: relative;">
                    <h5 class="card-title">{manager_name}</h5>
                    <p class="card-text">公司名称：{manager_info['公司名称']}</p>
                    <p class="card-text">年龄：{manager_info['年龄']}</p>
                    <p class="card-text">学历：{manager_info['学历']}</p>
                    <p class="card-text">在管基金：{manager_info['在管基金']}</p>
                    <p class="card-text">工作年限：{manager_info['工作时间']}</p>
                    <p class="card-text">基金规模：{manager_info['基金规模']}</p>
                    <p class="card-text">任职时间：{manager_info['起始时间']}</p>
                    <p class="card-text">简介：{manager_info['简介']}</p>
                </div>
            </div>
            """
            manager_html += manager_card
        st.markdown(manager_html, unsafe_allow_html=True)

    except Exception as e:
        st.error(f"出现错误: {str(e)}")


    # 获取股票代码列表
    #stock_codes =  ['002475','600309']
    df = get_fund_data(sl = sl)
    df= clean_fund_data(df=df,fields=fields)
    # 提取基金名称和基金代码
    fund_quarter = quarter

    # Get the previous quarter using the function
    previous_quarter = get_previous_quarter(quarter)
    # Merge the dataframe with itself to get current and previous quarter's holdings side by side
    merged_df = df[df['季度'] == quarter].merge(df[df['季度'] == previous_quarter], on='股票代码', how='left', suffixes=('', '_prev'))

    # Convert the relevant columns to numeric
    merged_df['持股数（万股）'] = pd.to_numeric(merged_df['持股数（万股）'], errors='coerce')
    merged_df['持股数（万股）_prev'] = pd.to_numeric(merged_df['持股数（万股）_prev'], errors='coerce')

    # Calculate the change rate
    merged_df['同比%'] = merged_df.apply(lambda row: "新增" if pd.isnull(row['持股数（万股）_prev']) else
                                        round((row['持股数（万股）'] - row['持股数（万股）_prev']) / row['持股数（万股）_prev'] * 100, 2), axis=1)

    import io
    import base64

    df_html = (merged_df[['股票代码', '股票名称', '所属行业', '占净值比例', '持仓市值(亿元)','持股数（万股）', '同比%', '股息率', '市盈(动)']]
                    .head(10)
                    .rename(columns={'持仓市值(亿元)': '持仓(亿元)','所属行业':'行业','持股数（万股）':'持股(万股)','股票代码':'代码','股票名称':'名称'})
                    .reset_index(drop=True)
                    .astype(str))
    df_html.columns.name = '序号'
    import pandas as pd
    from concurrent.futures import ThreadPoolExecutor
    st.markdown("### 持股数据")  # 添加标题
    st.table(df_html.set_index('代码'))  # 使用Streamlit的dataframe显示功能，并移除索引  # 使用 Streamlit 的 dataframe 显示功能
    
# 如果用户输入了股票代码
if user_input:
    from concurrent.futures import ThreadPoolExecutor
    column_rename = {
                'SECUCODE': '股票代码',
                'SECURITY_CODE': '股票代码',
                'SECURITY_NAME_ABBR': '股票简称',
                'RECEIVE_START_DATE': '调研日期',
                'RECEIVE_OBJECT': '接待对象',
                'RECEIVE_PLACE': '接待地点',
                'RECEIVE_WAY_EXPLAIN': '接待方式说明',
                'INVESTIGATORS': '调研人员',
                'NUMBERNEW': '参会人数',
                'CONTENT': '调研内容',
                'CLOSE_PRICE': '收盘价',
                'CHANGE_RATE': '涨跌幅',
            }
    # 定义任务函数
    def get_holdings_data():
        try:
            # 获取数据
            stock_codes = merged_df['股票代码'].head(10)
            return merged_df[['股票名称','股票代码']].head(10).merge(pd.DataFrame(fetch_data_concurrently(stock_codes)),left_on='股票代码',right_on='代码').drop(columns=['代码']).applymap(lambda x: x.replace('基金', '') if isinstance(x, str) else x), None  # 第二个元素用于潜在的错误消息
        except Exception as e:
            return None, str(e)  # 如果发生错误，返回 None 和错误消息

    def get_gscc():
        try:
            first_manager_name, first_manager_info = next(iter(managers_info.items()))
            return get_gscc_data(gs_id=first_manager_info['公司id']), None
        except Exception as e:
            return None, str(e)

    def get_survey_data():
        try:
            first_manager_name, first_manager_info = next(iter(managers_info.items()))
            return get_servey_data(RECEIVE_OBJECT=first_manager_info['公司名称'], columns="SECURITY_CODE,SECURITY_NAME_ABBR,RECEIVE_START_DATE,INVESTIGATORS,NUMBERNEW", pagesize=10), None
        except Exception as e:
            return None, str(e) # 如果发生错误，返回 None 和错误消息
    # 使用ThreadPoolExecutor来并行执行任务
    with ThreadPoolExecutor(max_workers=3) as executor:
        future1 = executor.submit(get_holdings_data)
        future2 = executor.submit(get_gscc)
        future3 = executor.submit(get_survey_data)

        # 等待所有任务完成并获取结果
        holdings_data, error1 = future1.result()
        gscc_data, error2 = future2.result()
        survey_data, error3 = future3.result()
    
    if not holdings_data.empty:
        st.markdown("## 持股主要基金")  # 添加标题
        st.table(holdings_data)  # 使用 Streamlit 的 dataframe 显示功能
    else:
        st.write("没有找到相关数据。")

    # 处理第二个任务的结果
    if not gscc_data.empty:
        st.markdown('### 基金公司整体持仓情况')
        st.table(gscc_data.head(10).astype(str))
    else:
        st.write("没有找到相关数据。")

    # 处理第三个任务的结果
    if not survey_data.empty:
        # 应用截断函数
        survey_data['RECEIVE_START_DATE'] = survey_data['RECEIVE_START_DATE'].str.split(' ').str[0]
        survey_data['INVESTIGATORS'] = survey_data['INVESTIGATORS'].replace({None: ''}).apply(truncate_text)
        survey_data_display = survey_data[['SECURITY_CODE', 'SECURITY_NAME_ABBR', 'RECEIVE_START_DATE', 
                                        'INVESTIGATORS', 'NUMBERNEW']].rename(columns=column_rename)
        st.markdown("### 调研信息")
        st.table(survey_data_display)
    else:
        st.write("没有找到相关数据。")



