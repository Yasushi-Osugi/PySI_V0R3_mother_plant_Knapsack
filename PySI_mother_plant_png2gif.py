# coding: utf-8
#
#
#            Copyright (C) 2020 Yasushi Ohsugi
#            Copyright (C) 2021 Yasushi Ohsugi
#            Copyright (C) 2022 Yasushi Ohsugi
#
#            license follows MIT license
#

# PySI_mother_plant_png2gif.py

# ナップサック問題で生産配分を解く様子をアニメーション化するための方針
#
# <前提>
# 生産配分の問題をナップサック問題としてとらえて、weekly knapsack solverで
# 52週から降順に1週まで、出荷ポジションを算定し、各週のN_week_CPU.csvを出力する
# def write_N_week_CPU(week, )


# animationの画像framesを生成する際に、
# 週別の画像frameに渡す、dataframeとして、df_N_weekを都度、生成する。

# def make_df_N_week(week, )
# 毎週のCPU.csvを読込み、積み上げ棒グラフに渡すdf_N_weekを生成し、returnする
#
# animation処理のgo.Frame, 画像framesの生成処理内で、
# df_N_week = make_df_N_week(week, )
# N_week_CPU.csvから返されてくる描画用の入力dataframe, df_N_weekを使って、
# 描画framesを生成、appendする
# 
#
# アニメーションを描画する
# fig = go.Figure(data=, layout=, frames=)
# show.fig()
# write fig 2 html()



import plotly.express as px
import plotly.graph_objects as go

import pandas as pd

from plotly import offline



# ****************************************
# new column appying
# ****************************************
def make_arv_node_week(df):

    result = df['Arv_entity'] + "_" + str(df['Arv_week'])

    return result


# ****************************************
# make_CPU2bar_graph(node, year, file_name)
# ****************************************
def make_CPU2bar_graph(node, year, file_name, w):

    # [ 'name', 'month', 'return' ]
    # [ 'object', 'week', 'value' ]
    
    
    # make df4psi and table4psi
    # with Dpt_entity="JPN", Arv_year=2023
    

    # ****************************************
    # init setting
    # ****************************************
    #year = 2023
    #node = 'JPN'
    
    df_mother_plant = df.query("Arv_year== @year & Dpt_entity== @node ")
    
    # *****************
    # ロット数=1は、STEP=0なので補正する
    # *****************
    df_mother_plant['Arv_step'] = df_mother_plant['Arv_step'] + 1
    
    
    
    ## ****************************
    ## 積み上げ棒グラフの出力テスト step数を積み上げているので、LOT数ではない
    ## ****************************
    #
    #df_mother_plant[ [ 'Arv_entity', 'Plan_week', 'Arv_step' ] ]
    #
    #print(df_mother_plant)
    #
    #fig = px.bar(df_mother_plant, x='Plan_week', y='Arv_step',  color='Arv_enti    ty', barmode='relative')
    #
    #fig.write_html('mother_plant_bar_stuck_test.html')
    
    
    
    # make table4psi with pd.crosstab()
    
    # *********************************
    # crosstab用に新しい key = Arv_entity + Arv_weekを作る
    # *********************************

    df_mother_plant['Arv_node_week'] = df_mother_plant.apply(make_arv_node_week, axis=1)

    # *********************************
    # pd.crosstab() でLOT数をcountする
    # *********************************
    
    table4psi = pd.crosstab(df_mother_plant['Arv_node_week'], df_mother_plant['Plan_week'])

    #table4psi = pd.crosstab(df_mother_plant['seq_no'], df_mother_plant['Plan_week'])

    #table4psi = pd.crosstab(df_mother_plant['Arv_entity'], df_mother_plant['Plan_week'])
    
    # print( table4psi )
    
    
    list4psi = []
    
    list_index4psi  = table4psi.index.tolist()
    
    #print( list_index4psi )
    
    ##list_colmns4psi = table4psi.columns.tolist()
    ##list_values4psi = table4psi.values.tolist()
    
    ##print( list_colmns4psi )
    ##print( list_values4psi )
    
    l4psi = []
    
    # *******************************
    # 空のdfの定義
    # *******************************
    # 
    # カラム名を定義
    cols = ["object", "week", "value"]
    
    # dataframeの作成
    #df_base = pd.DataFrame(columns=cols)
    
    lst_base = []
    
    ### 出力
    #print( df_base.head() )
    
    

    #@221107 以下は、nodeではなくlot
    for node in list_index4psi:
    
        print( 'node in list_index4psi ',node )
        #print ( table4psi.loc[ node ] )
    
    # *******************************
    # 先頭の列に追加
    # *******************************
    # df.insert(0, 'new_column', 'value')
    
        node_planweek_steps = table4psi.loc[ node ]
    
        df_test = pd.DataFrame(node_planweek_steps)
    
        list_columns = df_test.columns.tolist()
        list_index   = df_test.index.tolist()

    #list_values  = df_test.values.tolist()
    
    
    # *******************************
    # index　行名リストを先頭の列の値として追加
    # *******************************
        df_test.insert(0, 'week', list_index)
    
        df_test.insert(0, 'object', node)
    
    # *******************************
    # "2"の列名 nodeを"value"に変更
    # *******************************
        df_test_new = df_test.rename(columns={node: 'value'})
    
        lst_test_new = df_test_new.values.tolist()
 
    # *******************************
    # list add リストの結合
    # *******************************
    #mylist = ["A", "B", "C"]
    #mylist[len(mylist):len(mylist)] = ["D", "E"]
    #print(mylist)
    #--> ["A", "B", "C", "D", "E"]
    
        lst_base[len(lst_base):len(lst_base)] = lst_test_new
    
# ************************
# setting dataframe 4 bar stuck as df_base
# ************************

    # カラム名を定義
    cols = ["object", "week", "value"]
    
    # dataframeの作成
    df_base = pd.DataFrame(lst_base, columns=cols)
    
    
# ************************
# making figure with plotly express
# ************************

    fig = px.bar(df_base, x='week', y='value',  color='object', barmode='relative')
    
    w += 100 #@221112 making  png files  reverse sequence

    file_name_out = 'month_N_CPU2bar_graph' + "_W" + str(w)+ '.png'
    fig.write_image(file_name_out)

    #file_name_out = 'month_N_CPU2bar_graph' + "_W" + str(w)+ '.html'
    #fig.write_html(file_name_out)
    
    
# an image of data
#
#Plan_week   -2   -1    0    1    2    3   ...   42   43   44   45   47   48
#Arv_entity                                ...                              
#AKL           0    0    1    0    1    0  ...    0    0    0    1    0    0
#AMS           0    0    1    0    1    0  ...    0    0    0    1    0    0
#BKK           0    0    1    0    1    0  ...    0    0    0    1    0    0
#BRU           0    0    0    1    0    0  ...    1    0    0    1    0    0
#BUE           1    0    0    0    0    0  ...    1    0    0    0    0    1
#CAN           0    0    1    1    0    1  ...    0    1    0    1    0    0
#DEL           0    0    1    0    1    0  ...    0    0    0    1    0    0
#GOT           1    0    1    0    1    0  ...    0    0    0    0    1    0
#HAM           0    2    0    1    1    0  ...    0    0    0    1    0    0
#IST           0    0    1    0    1    0  ...    0    0    0    1    0    0
#JKT           0    0    1    0    1    0  ...    0    0    0    0    1    0
#JNB           0    0    1    0    1    0  ...    0    0    0    1    0    0
#KUL           0    0    1    0    1    0  ...    0    0    1    0    0    1
#LAX           1    0    1    0    1    1  ...    0    0    0    1    0    0
#LED           0    0    0    1    1    0  ...    0    0    0    1    0    0
#LIS           1    0    0    0    1    0  ...    0    0    0    1    0    0
#LON           0    0    1    0    1    0  ...    0    1    0    0    0    1
#MAD           1    0    0    0    0    0  ...    0    0    0    1    0    0
#MEX           0    0    0    1    0    1  ...    0    0    0    1    0    0
#MXP           0    1    0    0    0    1  ...    0    0    0    1    0    0
#NYC           1    0    0    1    0    1  ...    0    0    0    1    0    0
#OSA           0    0    1    0    0    1  ...    0    0    0    1    0    0
#PAR           0    0    1    0    1    0  ...    0    0    0    1    0    0
#RUH           1    0    0    0    0    0  ...    0    0    0    1    0    0
#SAO           0    0    1    0    1    0  ...    0    0    0    1    0    0
#SEL           1    0    0    0    1    0  ...    0    0    0    1    0    0
#SGN           0    0    0    1    1    0  ...    0    0    0    1    0    0
#SHA           1    0    0    2    1    1  ...    0    0    0    1    0    0
#SIN           0    1    0    0    1    0  ...    0    0    0    1    0    0
#SYD           0    0    0    1    1    0  ...    0    0    0    1    0    0
#TYO           0    0    1    0    1    0  ...    0    0    0    0    1    0
#WAW           0    0    1    0    1    0  ...    0    1    0    1    0    0
#YTO           0    1    0    0    1    0  ...    0    0    0    1    0    0
#ZRH           0    0    1    0    1    0  ...    0    0    1    0    1    0
#
#[34 rows x 48 columns]
#
#

def min_Dpt_week(df, node, year):

    pre_year = year -1

    #マザープラントnodeで、前年(year-1)の出荷週
    df_pre_y = df.query("Dpt_year == @pre_year & Dpt_entity == @node")


    print('df_pre_y',df_pre_y)

    # 出荷週の最小を求める
    min_Dpt_week = df_pre_y['Plan_week'].min()

    return min_Dpt_week



### ******************************
### start point
### ******************************
#if __name__ == '__main__':
#
#
## ************************
## 初期データセット
## ************************
#
#    file_name = 'common_plan_unit_knapsack.csv' # input file name
#
#    df = pd.read_csv(file_name)
#
#    node = 'JPN'  # mother plane 
#
#    year = 2023   # Arv_year

# ************************
# 初期データセット
# ************************

file_name = 'common_plan_unit_knapsack.csv' # input file name

df = pd.read_csv(file_name)

node = 'JPN'  # mother plane 
year = 2023   # Arv_year


min_Dpt_week =  min_Dpt_week(df, node, year)

end_week = min_Dpt_week - 52

print('end_week',end_week)


# *******************
# set limit on end_week 
# *******************

if end_week < -26:

    end_week = -26



for  w  in  range( 52, end_week-1, -1 ):

    file_name = 'common_plan_unit_knapsack' + "_W" + str(w)+ '.csv'

    print('read and make fig',file_name)

    df = pd.read_csv(file_name)

    make_CPU2bar_graph(node, year, file_name, w)


# ******************************
# make graph png and gif
# ******************************




