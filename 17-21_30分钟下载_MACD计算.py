'''
从Tushare上下载全市场股票从2017年1月1日至2021年12月31日的30分钟线行情,并计算5日均线与MACD指标
注: 由于数据量太大, Tushare一次只能返回8000条数据, 因此要分段下载, 并最后将其整合
'''

# 数据接口
from math import floor
import akshare as ak
import baostock as bs
import tushare as ts

# 基础模块
import datetime as dt
import numpy as np
import pandas as pd
import time
import os

# 基础函数
import utilsJ

stock_filelist = os.listdir('.\\Data\\17-21_30min')
last_download  = '000001.SZ'
year_list = [2017, 2018, 2019, 2020, 2021]
time_lag = 0.4
short = 12
long = 26
period = 9

if __name__ == '__main__':
    # 分段下载30分钟行情
    stock_list = utilsJ.get_stock_list()
    not_download = False
    for stock in stock_list:
        if stock.ts_code == last_download: #避免重复下载
            not_download = True
        if not_download:
            for i in year_list:
                file_name = '.\\Data\\17-21_30min\\'+stock+str(i)+'.csv'
                if not os.path.exists(file_name):
                    print(file_name)
                    startdate = dt.datetime(i,1,1)
                    enddate = dt.date(i,12,31)
                    df = utilsJ.stock_ts(stock.ts_code, startdate, enddate)
                    if len(df) != 0:
                        df.to_csv(file_name)
                    time.sleep(time_lag) # 避免访问次数过多导致被屏蔽

    # 对数据进行整合
    stock_list = utilsJ.get_stock_list()
    for stock in stock_list:
        df = pd.DataFrame()
        for i in [2017, 2018, 2019, 2020, 2021]:
            file_name = '.\\Data\\17-21_30min\\'+stock.ts_code+str(i)+'.csv'
            if os.path.exists(file_name):
                if len(df) == 0:
                    df = pd.read_csv(file_name)
                else:
                    df_new = pd.read_csv(file_name)
                    df = pd.concat([df, df_new])
        if len(df) != 0:       
            df.to_csv('.\\Data\\17-21_30min\\'+stock.ts_code+'.csv')

    # 计算 MA5和MACD
    stock_filelist = os.listdir('.\\Data\\17-21_30min\\')
    for stock_file in stock_filelist:
        stock_code = stock_file[:9]
        try:
            df = pd.read_csv('.\\Data\\17-21_30min\\Int\\'+stock_file, 
                            converters={'trade_date':lambda x:pd.to_datetime(x)}).set_index('trade_date')
            df.drop(columns=df.columns[[0, -1]], inplace=True)
            df['MA5'] = df.close.rolling(5).mean()
            EMA_short = np.full(len(df), np.nan)
            EMA_long = np.full(len(df), np.nan)
            DEA = np.full(len(df), np.nan)
            EMA_short[short-1] = df.close[short-1]
            EMA_long[long-1] = df.close[long-1]
            for i in range(short, len(df)):
                EMA_short[i] = 2 * df.close[i] / 13 + EMA_short[i-1] * (1 - 2 / 13)
                if i == long - 1:
                    DEA[i] = EMA_short[i] - EMA_long[i]
                else:
                    EMA_long[i] = 2 * df.close[i] / 27 + EMA_long[i-1] * (1 - 2 / 27)
                    DEA[i] = 2 * (EMA_short[i] - EMA_long[i]) / 10 + DEA[i-1] * (1 - 2/10)
            df['DIFF'] = EMA_short - EMA_long
            df['DEA'] = DEA
            df['MACD'] = 2 * (df.DIFF - df.DEA)
            df.to_csv('.\\Data\\17-21_30min\\Int\\MA5MACD\\' + stock_file)
        except:
            print(stock_file)
