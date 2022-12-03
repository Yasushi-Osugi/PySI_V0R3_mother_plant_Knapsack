# coding: utf-8
#
#
#            Copyright (C) 2020 Yasushi Ohsugi
#            Copyright (C) 2021 Yasushi Ohsugi
#            Copyright (C) 2022 Yasushi Ohsugi
#
#            license follows MIT license
#


# PySI_mother_plant_Knapsack_80percent.py
#
# ******************************
# PULPのknapsack solverを使って、mother plantの生産配分・出荷優先の問題を解く
# ******************************

# ***************************
# Knapsackの容量設定は、週次の生産能力設定で、将来的にdashboardから指定
# ***************************

# 本コード中では、以下の式で固定の需給比率demand_supply_ratio = 0.8で解く
# 週次の出荷能力:weekly_capa = 需給比率:R * ( 年間総需要:anual demand / 52 )
# 需給比率:R = 80%
# demand_supply_ratio = 0.8

# 前処理で、
# 1. サプライチェーン上のnode value評価 value_onSCの生成済み
# 2. flag_counterの-1設定済み

# assignが使えるのは、common_plan_unit.csvを生成する最初の初期処理のみ
# 以降は、生成されたcommon_plan_unit_VALUEonSC_flag_planweekを読み込む

# 1. CPUの列assignの確認
#    df.assign( Value_on_SC = 0 ) # サプライチェーン上のnode valueの加重平均
#    df.assign( Confirm_flag_counter = 0 )  # マザープラントの確定POフラグ
#    df.assign( Plan_week = 0 ) #マザープラントの出荷計画用 ナップサック漏れ用

# 2. Confirm_flag_counterを見て、Plan_weekを設定

# 3. weight_limit = weekly_capaの計算と初期設定

# <以下に続く>

# 1. マザープラントの出荷週に出荷要求されているロット群を週次で抽出する。
#    抽出条件の考え方を例でみる

#    1. Dpt_entity='JPN', Arv_year=2023
#       とすることで、着荷側が2023年に入っているLOTが抽出される。
#       マザープラントJPN側は、2022年にLTシフトしているLOTも含まれることで、
#       PSI計画の対象を正しく抽出している。

#    2. Dpt_yearとDpt_weekをバックワードで抽出しながらknapsack問題として解く
#       Dpt_year=2023,Dpt_week=52,51,50,49,,,,3,2,1
#

# 2. 前処理で、Knapsack問題の入力形式、seq_no, weight, valueにするために、
#    1. pre_processで、CPU.csvの出荷週内のlotを0,1,2,3でnumberingし直す。
#    2. main_processで、knapsak問題を解く。
#    3. post_processで、seq_noに対応するLOT, Arv_entityに変換する。

# 3. マザープラントの出荷対象となったLOTをConfirm_PO 確定POとして、
#    confirm_flag = 0/1にフラグ=1を立てる

# node別、year別のloopの中で、
# 子nodeを見て、加重平均したサプライチェーン上の価値value_on_SCを生成している

# main処理で、
# common plan unitに、value_on_SCとして保管しておき、JPNの出荷週に最適配分する


# 1. 加重平均でSC上の価値計算
# 1-1.価値supply chain上の各nodeと子node_year_valueをn_y_value_listに生成する
# 1-2.数量supply chain上の各nodeと子node_year_volumeをn_y_value_listに生成する
#     search_childs_get_value_volumeとして、子nodeのvolumeサーチを追加する
# 1-3.子供のvalueの加重平均を算定する valueと年間の販売予定量(=年間供給要求量)
#    加重平均 = Σ( val_N * vol_N ) / Vol_total

#    年間供給要求量 node_year_total_volume = [node, year, volume]
#    dfをnote_to別　year別　での年間Volume(=step数のtotal)を求める


# knapsap_solverに渡す

# ***** output image *****ココから最後のリスト [node,year,value]のリスト
#
# n_y_value_listの中に、自身のnodeとその子供のnodeのvalueがby yearで入っている
#

# *****  value list image *****
#
#['NYC_I', 2023, 24.697744361203007, []],  # **** LEAF NODEのnode_year_value
#['NYC_I', 2024, 24.23784461120301, []], 
#['NYC_I', 2025, 23.781203007518794, []], 
#['NYC_I', 2026, 23.322556391353384, [    ]], 
#
#['NYC', 2023, 25.30833333375, [           # **** 中間と子供のnode_year_value
#    ['NYC_N', 2023, 24.684210526691732, []], 
#    ['NYC_D', 2023, 24.65739348398496, []], 
#    ['NYC_I', 2023, 24.697744361203007, []]   ]], 
#
#['NYC', 2024, 21.4312500001875, [
#    ['NYC_N', 2024, 24.235839598646617, []], 
#    ['NYC_D', 2024, 24.23784461112782, []], 
#    ['NYC_I', 2024, 24.23784461120301, []]    ]], 
#
#['NYC', 2025, 17.545833333125003, [
#    ['NYC_N', 2025, 23.781203007518794, []], 
#    ['NYC_D', 2025, 23.781203007518794, []], 
#    ['NYC_I', 2025, 23.781203007518794, []]    ]],
#
# ['NYC', 2026, 13.633333333750002, [
#    ['NYC_N', 2026, 23.322556391353384, []], 
#    ['NYC_D', 2026, 23.322556391353384, []], 
#    ['NYC_I', 2026, 23.322556391353384, []]    ]]    ]


# 1.LEAF NODEの場合
#
#   1. データクレンジング　　valueゼロのとマイナスをゼロに
#   2. 平均valueの算定は、下記のいずれかの計算式を使用する
#      1) trimmean( 範囲 , 0.2 )で、上位と下位の10% cutで平均をとる
#      2) QUARTILE.INC(範囲 ,2)     中央値をとる
#      3) QUARTILE.EXC(範囲 ,2)     0,100%を除いて中央値をとる

# 2.中間node / root nodeの場合
#
#   1. データクレンジング　　ゼロとマイナスをゼロに
#   2. 下位nodeのValue => 下位nodeのLOT数とvalue平均から加重平均とる
#   3. 自身のnodeの平均valueの算定は、下記のいずれかの計算式を使用する
#      1) trimmean( 範囲 , 0.2 )で、上位と下位の10% cutで平均をとる
#      2) QUARTILE.INC(範囲 ,2)     中央値をとる
#      3) QUARTILE.EXC(範囲 ,2)     0,100%を除いて中央値をとる
#   4. サプライチェーン・ネットワーク上の累積value
#       当nodeのvalue_accume = 当node_value中央値 + 下位node_加重平均value


# ***********************************
# データの持ち方
# ***********************************

# 0. 'year'で抽出しておく
# 1.LEAF NODEの場合
#
#   1. データクレンジング　　valueのゼロとマイナスをゼロに => df_clean = df(
#   2. 平均valueの算定は、下記のいずれかの計算式を使用する
#      1) trimmean( 範囲 , 0.2 )で、上位と下位の10% cutで平均をとる
#      2) QUARTILE.INC(範囲 ,2)     中央値をとる
#      3) QUARTILE.EXC(範囲 ,2)     0,100%を除いて中央値をとる

# 2.中間node / root nodeの場合
#
#   1. データクレンジング　　ゼロとマイナスをゼロに
#   2. 下位nodeのValue => 下位nodeのLOT数とvalue平均から加重平均とる
#   3. 自身のnodeの平均valueの算定は、下記のいずれかの計算式を使用する
#      1) trimmean( 範囲 , 0.2 )で、上位と下位の10% cutで平均をとる
#      2) QUARTILE.INC(範囲 ,2)     中央値をとる
#      3) QUARTILE.EXC(範囲 ,2)     0,100%を除いて中央値をとる
#   4. サプライチェーン・ネットワーク上の累積value
#       当nodeのvalue_accume = 当node_value中央値 + 下位node_加重平均value
# 

import numpy as np
import matplotlib.pyplot as plt

from scipy import stats # for trimmean

# ******************************
# PySI related module
# ******************************
from PySILib.PySI_library_V0R1_070 import *

from PySILib.PySI_env_V0R3_1 import *

from PySILib.PySI_PlanLot_V0R3_2 import *

from PySILib.PySI_search_LEAF_in_SCMTREE_V0R3 import *

# ***********************
# pulp for knapsack_solver
# ***********************
import pulp


## ********************************************************
## csv_write2common_plan_header 共通計画単位のヘッダー書き出し
## ********************************************************
#def csv_write2common_plan_header_N(): 
#
#    l = []
#    r = []
#
#    # ********* ヘッダーのみ先に書き出す 各PSI計画の出力の前に
#    r = ['seq_no','control_flag','priority_no','modal','LT','Dpt_entity','Dpt_year','Dpt_week','Dpt_step','Arv_entity','Arv_year','Arv_week','Arv_step','Value']
#    # lot_noで出力するcsv file nameを作成
#    csv_file_name = "common_plan_unit.csv"
#
#    l.append(r)
#
## ****************************************
## CSV ファイル書き出し
## ****************************************
#
#    #print('l',l)
#
#    with open( csv_file_name , 'w', newline="") as f:
#
#        writer = csv.writer(f)
#        writer.writerows(l)
#
#


#def calc_value_on_SC( file_name, node, year ):
#
#    df = pd.read_csv('common_plan_unit.csv')
#    #df = pd.read_csv('common_plan_unit.csv',encoding='shift-jis',sep=',')
#    
#    #print(df)
#
#    if df['value'] > 0:
#        df['value'] = df['value']
#    else:
#        df['value'] = 0
#
#    print(df)


# ***********************************
# data cleaning setting ZERO
# ***********************************
def check_value_set_zero(x):

    if x > 0:

        pass

    else:

        x = 0

    return x



#def make_flag_minus(x):
#
#    x += -1
#
#    return x



#def calc_node_year_value(node,year,df):
#
#    node_year_value = [ 0, 0, 0, [] ]
#
#    print('node year',node, year)
#
#    df_n_y = df.query("Arv_year == @year & Arv_entity == @node")
#
#
#   value_trimed_ave = stats.trim_mean(df_n_y['Value'], 0.2) 
#
#    node_year_value[0] = node
#    node_year_value[1] = year
#    node_year_value[2] = value_trimed_ave
#
#    return node_year_value


#def calc_node_year_volume(node,year,df):
#
#    node_year_volume = [ 0, 0, 0, [] ]
#
#
#    df_n_y = df.query("Arv_year == @year & Arv_entity == @node")
#
#    n_y_vol =len(df_n_y)
#
#
## monitor
##
##    if ( node == 'JPN' and year == 2023 ) :
##
##        print( 'dump YTOLEAF 2023 df', node, year, df )
##
##        pd.set_option('display.max_rows', 5000)
##        pd.set_option('display.max_columns',1000)
##        print( 'dump YTOLEAF 2023 df_n_y', df_n_y )
##        print( 'len(df_n_y)', n_y_vol )
##
##    if ( node == 'YTOLEAF' and year == 2023 ) :
##
##        print( 'dump YTOLEAF 2023 df', node, year, df )
##
##        pd.set_option('display.max_rows', 5000)
##        pd.set_option('display.max_columns',1000)
##        print( 'dump YTOLEAF 2023 df_n_y', df_n_y )
##        print( 'len(df_n_y)', n_y_vol )
#
#
##['RUHLEAF', 2023, 221, []], 
##['RUHLEAF', 2024, 221, []], 
##['RUHLEAF', 2025, 221, []], 
##['RUHLEAF', 2026, 221, []], 
##['RUH', 2023, 12, []], 
##['RUH', 2024, 12, []], 
##['RUH', 2025, 12, []], 
##['RUH', 2026, 12, []], 
##['SWELEAF', 2023, 221, []], 
##['SWELEAF', 2024, 221, []], 
##['SWELEAF', 2025, 221, []], 
##['SWELEAF', 2026, 221, []], 
#
#
#    print('n_y_vol',n_y_vol)
#
#
#    node_year_volume[0] = node
#    node_year_volume[1] = year
#    node_year_volume[2] = n_y_vol
#
#    print('node_year_volume',node, year,node_year_volume)
#
#    return node_year_volume


#def search_childs_get_val_vol(node, parent_childs, year, n_y_value_list, n_y_volume_list):
#
#    children_value  = []
#    children_volume = []
#
#    for pc in parent_childs:
#
#        if pc[0] == node:
#
#            child_node = pc[1]
#
#            # ***** VALUE *****
#            for n_y_value in n_y_value_list:
#
#                if ( n_y_value[0] == child_node and n_y_value[1] == year ):
#
#                    children_value.append(n_y_value)
#
#         #children_value.append(n_y_value)
#
#
#            # ***** VOLUME *****
#            for n_y_volume in n_y_volume_list:
#
#                if ( n_y_volume[0] == child_node and n_y_volume[1] == year ):
#
#                    children_volume.append(n_y_volume)
#
#    return children_value, children_volume



#def search_childs_get_value(node, parent_childs, year, n_y_value_list):
#
## parent_childsは、親子関係を配列で表したデータ
## parent_childs = [['JPN', 'YTO'], ['JPN', 'NYC'], ['JPN', 'LAX'], ,,,]
#
#    children_value = []
#
#    for pc in parent_childs:
#
#        if pc[0] == node:
#
#            child_node = pc[1]
#
#            for n_y_value in n_y_value_list:
#
#                if ( n_y_value[0] == child_node and n_y_value[1] == year ):
#
#                    children_value.append(n_y_value)
#
#         #children_value.append(n_y_value)
#
#    return children_value


# ***************************************************************************
# 加重平均計算の関数の中に入れる
# calc_weight_average_value(node_year_value_list,node_year_volume_list)
# ***************************************************************************
def weight_average( value, weight ):

    #value = [300, 200, 400, 100]
    #weight = [10, 2, 3, 5]

    wt_avg = sum([v*w for v,w in zip(value,weight)]) / sum(weight) 

    return  wt_avg


def calc_weight_average_value(children_value,children_vol):


#children_value [['NYC_N', 2024, 24.23784461152882, []], ['NYC_D', 2024, 24.23784461152882, []], ['NYC_I', 2024, 24.237844611528814, []]]

#children_vol [['NYC_N', 2024, 221, []], ['NYC_D', 2024, 221, []], ['NYC_I', 2024, 221, []]]


    #print('node_year_value_list',node_year_value_list)
    #print('node_year_volume_list',node_year_volume_list)

    #child_n_y_value = node_year_value_list
    #child_n_y_vol = node_year_volume_list

    #child_n_y_value = node_year_value_list[ 3 ]
    #child_n_y_vol = node_year_volume_list[ 3 ]

    ny_value = []
    ny_volume = []

    for val, vol in zip( children_value, children_vol ):

        print('val',val)
        print('vol',vol)

        ny_value.append( val[2]) #node,year,value
        ny_volume.append( vol[2]) #node,year,vol

    print('ny_value',ny_value)
    print('ny_volume',ny_volume)


    value = ny_value #子nodeのvalue list
    weight = ny_volume

    ny_wt_avg = weight_average( value, weight )

    print('ny_wt_avg',ny_wt_avg)

    return ny_wt_avg


def calc_anumal_demand(df, node, year):

    df_n_y = df.query("Arv_year == @year & Dpt_entity == @node")

    # annual total demandは、"Dpt_step"のロット総数=行数を求める
    annual_demand_lots = len(df_n_y)

    return annual_demand_lots


# ************************************
# knapsackの前処理  items_numberリストと変換辞書items_node_number_dicを生成
# ************************************
def pre4knapsack(df, node,  year, w ):

    items_node             = []
    items_key              = []

    items_number           = []
    items_node_number_dic  = {}

    mother_S_list = []

    df_n_y_w=df.query("Arv_year== @year & Dpt_entity== @node & Plan_week== @w")

    print('week & df_n_y_w', w, df_n_y_w)


    # 仕向け地の着荷週Arv_weekでのロット数を計画対象の粒度とする
    #mother_S = df_n_y_w[['Arv_week','Arv_step']].groupby('Arv_week').count()

    # *************
    # 週別ロットまるめのcount 仕向け地'Arv_entity'+着荷週'Arv_week'でgroupby
    # *************
    # 仕向地+着荷週別 になっている

    mother_S = df_n_y_w[['Arv_entity','Arv_week','Arv_step']].groupby(['Arv_entity','Arv_week']).count()

    # *************
    # ロット数のcount  仕向け地'Arv_entity'ではなくロット番号'seq_no'でgroupby
    # *************
    # LOTのseq_noになっている

    #mother_S = df_n_y_w[['seq_no','Arv_step']].groupby('seq_no').count() 

    #mother_S = df_n_y_w[['Arv_entity','Arv_step']].groupby('Arv_entity').cou

    # *************
    # 仕向け地をリスト出力
    # *************
    mother_S_list = mother_S.reset_index().values.tolist()

    print('mother_S_list',mother_S_list)

    #mother_S_list.append(df_n_y_w)

    item     = []
    arv      = []
    arv_key  = []

    #@221109 着荷週別のArv_weekになっている
    #@221107 LOTのseq_noになっている
    for arv in mother_S_list:  

# data image
# mother_S_list [['BRU', 4, 1, 36.01522556], ['CAN', 4, 1, 50.05731516], ['HAM', 4, 1, 51.78369588], ['LED', 4, 1, 36.09357769], ['MEX', 4, 1, 35.9985589], ['NYC', 4, 1, 50.13231516], ['SGN', 4, 1, 36.05689223], ['SHA', 4, 2, 52.28281816], ['SYD', 4, 1, 36.08189223]]



        # ******************************
        # valueを抽出する・・・最初はvalueが入っていない、検索してappendする
        # arv = ['BRU', 4, 1, 36.01522556]
        # ******************************

        arv_node = arv[0]
        arv_week = arv[1] # [0]はnode [1]はarv_week
        #arv_lot = arv[0]

        df_arv = df_n_y_w.query(' (Arv_entity == @arv_node) & (Arv_week == @arv_week) ') 
        #df_arv = df_n_y_w.query(' Arv_entity == @arv_node ')

        arv_list = df_arv.reset_index().values.tolist()
        
        print('arv_list',arv_list)

#arv_list [[43278, 43278, 'BRU202301001', 'F', 1202301001, 'B', 4, 'JPN', 2022, 0, 0, 'BRU', 2023, 4, 0, 0.0, 36.01522556, 0, 52]]

        arv_raw = arv_list[0]           # 0でリストから取り出す

        arv_value_on_SC = arv_raw[16]   # value_on_SC

        print('arv_value_on_SC',arv_value_on_SC)

#arv_value_on_SC 36.01522556


        # ******************************
        # ココでvalueをappendする・・・最初はvalueが入っていない
        # arv = ['BRU', 4, 1, 36.01522556]
        # ******************************
        arv.append(arv_value_on_SC)


        # ************************************
        # arvがitems_keyの要素 [key, weight, value]
        # ************************************
        # arv_key = [ ['BRU', 4] , 1, 36.01522556] となるように変換

        item = []
        item.append( arv[0:2] ) 
        item.append( arv[2] ) 
        item.append( arv[3] ) 
        

        items_node.append( item )
        #items_node.append(arv_key)


    #mother_S = df_n_y_w[['Arv_entity','Arv_step']].groupby('Arv_entity').count().values.tolist()

    print('mother_S',mother_S)

    print('mother_S_list',mother_S_list)

#mother_S                      Arv_step
#Arv_entity Arv_week
#BRU        4                1
#CAN        4                1
#HAM        4                1
#LED        4                1
#MEX        4                1
#NYC        4                1
#SGN        4                1
#SHA        4                2
#SYD        4                1

#mother_S_list [['BRU', 4, 1, 36.01522556], ['CAN', 4, 1, 50.05731516], ['HAM', 4, 1, 51.78369588], ['LED', 4, 1, 36.09357769], ['MEX', 4, 1, 35.9985589], ['NYC', 4, 1, 50.13231516], ['SGN', 4, 1, 36.05689223], ['SHA', 4, 2, 52.28281816], ['SYD', 4, 1, 36.08189223]]



    # メモ
    #df_n_y_w[ 'Arv_entity' , 'Arv_step'.count , 'Value_on_SC' ]

#mother_S             Arv_step
#Arv_entity
#BRU                1
#CAN                2
#mother_S_list [       Unnamed: 0        seq_no control_flag  priority_no modal  ...  Arv_step      Value  Value_on_SC  Confirm_flag_counter  Plan_week
#41377       41377  CAN202306001            F   1202306001     B  ...         0  33.233333    50.057315                     0         20
#41378       41378  CAN202306003            F   1202306003     B  ...         1  30.866667    50.057315                     0         20
#43283       43283  BRU202306001            F   1202306001     B  ...         0  25.000000    36.015226                     0         20
#
#[3 rows x 18 columns]]
#items []
#items []



    print('items_node', items_node )

# items_node [['BRU', 4, 1, 36.01522556], ['CAN', 4, 1, 50.05731516], ['HAM', 4, 1, 51.78369588], ['LED', 4, 1, 36.09357769], ['MEX', 4, 1, 35.9985589], ['NYC', 4, 1, 50.13231516], ['SGN', 4, 1, 36.05689223], ['SHA', 4, 2, 52.28281816], ['SYD', 4, 1, 36.08189223]]
#items_node[i][0] BRU
#items_node[i][0] CAN
#items_node[i][0] HAM
#items_node[i][0] LED
#items_node[i][0] MEX
#items_node[i][0] NYC
#items_node[i][0] SGN
#items_node[i][0] SHA
#items_node[i][0] SYD

#items [['AKL', 1, 36.00181704260651], ['BRU', 1, 36.015225563909766], ['BUE', 1, 36.04855889724311], ['CAN', 1, 50.05731516290726], ['DEL', 1, 36.04022556390977], ['GOT', 2, 50.06939223057644], ['HAM', 1, 51.78369587823286], ['IST', 1, 36.09483082706767], ['JKT', 1, 36.1360588972431], ['LAX', 3, 51.26102756892231], ['LED', 1, 36.093577694235584], ['LON', 1, 36.13903508771929], ['MEX', 1, 35.9985588972431], ['MXP', 1, 36.21105889724311], ['NYC', 1, 50.13231516290726], ['PAR', 1, 36.04749373433584], ['RUH', 1, 36.0985588972431], ['SEL', 1, 36.21105889724311], ['SHA', 4, 52.28281815650236], ['SIN', 1, 36.08189223057644], ['WAW', 1, 36.06403508771929], ['YTO', 1, 37.03829075425791], ['ZRH', 1, 36.08605889724311]]

    #items_number = items_nodeのキーが[arv_node,arv_week]のリスト

    items_number = copy.deepcopy(items_node)       # items_lisをnodeでコピー
    #items_number = copy.copy(items_node)           # items_lisをnodeでコピー

    for i, item in enumerate(items_node):

    # node+weekの場合
    # [ ['BRU', 4 ], 1, 36.01522556] [['Arv_entity','Arv_week'],'weight','value']

        items_number[i][0] = i                  # knapsack_solver用itemに付番

        # *** value *** value_on_SC
        items_number[i][1] = items_node[i][2]   # knapsack_solver用にvalue付加

        # *** weight **** LOTs count
        items_number[i][2] = items_node[i][1]   # knapsack_solver用itemに付番


        print('items_node[i]',items_node[i])

        #items_node_number_dic[i] = items_node[i][0:2] # node+arv_weekとseq_noの対応辞書

        items_node_number_dic[i] = items_node[i][0] # nodeとseq_noの対応辞書


    return items_number, items_node_number_dic



# ******************************
# knapsack_solverで生産配分・出荷優先を解く
# ******************************
def knapsack_solver(weight_limit, items_number):

    # 容量の制約数

    W = weight_limit

    #W = 10000 
    #W = 5000 d

    ## アイテム毎の容量と価値 入力データ読み込み
    #df = pd.read_csv('items.csv')


    # リストからdf生成

    df = pd.DataFrame( items_number, columns=['Num','Value','Weight'] )


#l_2d = [[0, 1, 2], [3, 4, 5]]
#
#df = pd.DataFrame(l_2d)
#print(df)
##    0  1  2
## 0  0  1  2
## 1  3  4  5
#
#df = pd.DataFrame(l_2d,
#                  index=['row1', 'row2'],
#                  columns=['col1', 'col2', 'col3'])
#print(df)
##       col1  col2  col3
## row1     0     1     2
## row2     3     4     5



    # アイテム数
    N = len(df) 

    # 変数の定義

    df['Var'] = [pulp.LpVariable(f'x{L}', cat="Binary") for L in df.index]

    x = [pulp.LpVariable("x_{}".format(i), cat=pulp.LpBinary) for i in range(N)]

    print(df)


    # 問題の定義
    p = pulp.LpProblem('ナップサック問題', sense=pulp.LpMaximize)


    print('x',x)
    print('df.Var',df.Var)


    # 目的関数と制約の定義
    p += pulp.lpDot(df.Value , x )         # 目的関数
    p += pulp.lpDot(df.Weight, x ) <= W    # 容量制約

    # solverの実行
    result = p.solve()

    # ***************************************
    print('入力データ',df)

    # LpStatus='optimal'で最適解
    print('LpStatus',pulp.LpStatus[result])

    # 目的関数(価値の合計)
    print('')
    print('objective',pulp.value(p.objective))


    # **************************************

    print("最適な選択 = {}".format(list(int(pulp.value(x[i])) for i in range(N))))

# **************************************
# リストで出力処理
# **************************************
    select_l = list(int(pulp.value(x[i])) for i in range(N))

    v_selected = []
    w_selected = []

    for i, S in enumerate( select_l ) :

        if S == 1 :

            print( 'Value =', df.Value[i]  , 'Weight=', df.Weight[i] )

            v_selected.append( df.Value[i]  ) 
            w_selected.append( df.Weight[i] )

    print( 'sum weight =',sum(w_selected) )

# **************************************


    # **************************************
    # pandasで出力処理
    # **************************************
    # 'Var'変数の結果の値をまとめて'Select'列にコピー
    df['Select'] = select_l

    # 選んだアイテムの一覧
    print('')
    print('output with pandas')
    print(df[df.Select > 0])

    # 選んだアイテムの総量
    print('total weight:', sum(df['Weight'][df.Select > 0]))


    solved_items = select_l


    return solved_items





# ******************************
# start point
# ******************************
if __name__ == '__main__':


# ******************************
# csv_write2common_plan_header　計画共通単位のヘッダー初期設定
# ******************************

    #csv_write2common_plan_header_N()
    #csv_write2common_plan_header()

    # 修正メモ 'year'+'node'キーを追加したCSVファイルに対応@220918

    # read_profile()

    #df_prof = pd.read_to_csv('PySI_Profile_std_Y.csv')

    #本来は、入力データ PSIとprofileの'year'をkeyにuniqeして、years_listを作成
    years_list = [2023, 2024, 2025, 2026]

    # planningでは
    # 注: current_year=Nは使わない。N+1,N+2,N+3の末端市場S_outlookを使用する。
    # adjustingでは、crrent_year=Nの'S_actual'でadjust計算する。

    # SC_activity_table   S-I-P( node, time ) + lot_step  cost_profile(node)

    # 制約
    # 部分問題(ネットワーク、配分)のsolver modelと制約 
    #  => 供給ネットワーク定義、最適配分、　　　ら
    # Supply_chain activity全体の表現、planning結果、評価


    file_name = 'common_plan_unit_VALUEonSC_flag_planweek.csv'

    df = pd.read_csv(file_name)

    df['Value'] = df['Value'].apply(check_value_set_zero)

    print(df)



# ***************************
# Knapsack_slover
# ***************************

# node year でloop
# node = mother_plant = 'JPN'を指定

# years_listでloop [2023, 2024, 2025, 2026]これも降順
# for year in reversed( years_list ): # [2026,2025,2024,2023]

mother_plant = 'JPN'

node = mother_plant

year= 2023 # for test


# *********************
# yearが異なる=前年ならば、出発週を52週マイナスする
# *********************
# SAMPLE
#df['D'].where((df['D'] % 2 == 0) & (df['A'] < 0), df['D'] * 100, inplace=True)

df['Dpt_week'].where(df['Dpt_year']==year, df['Dpt_week']-52, inplace=True)


# ***************************
# Knapsackの容量設定 / setting the mother plant capacity limitation
# ***************************

# 週次の出荷能力:weekly_capa = 需給比率:R * ( 年間総需要:anual demand / 52 )
# 需給比率:R = 80%

demand_supply_ratio = 0.8

#demand_supply_ratio = 1.0

#demand_supply_ratio = 1.2

#demand_supply_ratio = 1.5

annual_demand_lots = calc_anumal_demand(df, node, year)

print('annual_demand_lots',annual_demand_lots)

# 容量の制約 by LOTs
# 例えば、週間の生産上限は、30 LOTsなど

weekly_capa = int ( demand_supply_ratio * annual_demand_lots / 52 ) + 1 #ロット数

# W:weight_constraint ナップサックの重量制限

weight_limit = weekly_capa

print('weight_limit',weight_limit)


## *******************
## TEST for mother plant shipping week 
## *******************
#
##w = 52
#w = 15

# 抽出する対象週は、Plan_week = Dpt_week + confirm_flag_counter
# knapsack_solver用に、まずは、指定した週のitemsを生成する
# dfの初期設定で、Plan_week = Dpt_week + confirm_flag_counterは計算されている


# *******************
# 計画週のend週  = mother_plant nodeの前年(year-1)の出荷週の最小値 - 52
# *******************
def min_Dpt_week(df, node, year):

    pre_year = year -1

    #マザープラントnodeで、前年(year-1)の出荷週
    df_pre_y = df.query("Dpt_year == @pre_year & Dpt_entity == @node")


    print('df_pre_y',df_pre_y)

    # 出荷週の最小を求める
    min_Dpt_week = df_pre_y['Plan_week'].min()

    return min_Dpt_week

min_Dpt_week =  min_Dpt_week(df, node, year)

end_week = min_Dpt_week - 52

print('end_week',end_week)

# ++++++++++++++++++++++++
# 例えば、需要供給ratio = 150%の場合
# 供給生産capaが需要に対して十分なので、end_weekが有効となるが、
#
# 需要供給ratio = 100%の場合、
# 供給生産capaが需要に対して不十分になるため、end_weekが使えない。
# 先行生産の前倒しが進むので、想定週として半年前の26週前まで出力する
# ++++++++++++++++++++++++

min_Dpt_week = 26

end_week = min_Dpt_week - 52  # -26 = 26 - 52


# *******************
# apply Knapsack_solver with backward planning
# *******************

for  w  in  range( 52, end_week-1, -1 ):

#for  w  in  range( 52, -5, -1 ):
#for  w  in  range( 52, 0, -1 ):
    
#    items = pre4knapsack( node,  year, w )

# **********************
# ナップサック問題の前処理
# **********************

# itemsリストを「node名」から「連番」に変更する。
# items_number = [seq_no, weight, value] 下記のdata imageを参照

# 同時に、「node名」と「連番」の辞書を作成しておくことで、
# knapsack_solverの結果(最適な出荷先の組み合せ)をnode名に変換する。

    items_number, items_node_number_dic = pre4knapsack(df, node,  year, w )

    print('items_number',items_number)
    print('items_node_number_dic',items_node_number_dic)

# ***************
# data image
# ***************

#items_number [[0, 50.05731516, 1], [1, 36.13903509, 1], [2, 36.06403509, 1]]

# items_node_number_dic {0: ['CAN', 46], 1: ['LON', 46], 2: ['WAW', 46]}


#items_number [[0, 1, 36.00181704260651], [1, 1, 36.015225563909766], [2, 1, 36.04855889724311], [3, 1, 50.05731516290726], [4, 1, 36.04022556390977], [5, 2, 50.06939223057644], [6, 1, 51.78369587823286], [7, 1, 36.09483082706767], [8, 1, 36.1360588972431], [9, 3, 51.26102756892231], [10, 1, 36.093577694235584], [11, 1, 36.13903508771929], [12, 1, 35.9985588972431], [13, 1, 36.21105889724311], [14, 1, 50.13231516290726], [15, 1, 36.04749373433584], [16, 1, 36.0985588972431], [17, 1, 36.21105889724311], [18, 4, 52.28281815650236], [19, 1, 36.08189223057644], [20, 1, 36.06403508771929], [21, 1, 37.03829075425791], [22, 1, 36.08605889724311]]

#items_node_number_dic {0: 'AKL', 1: 'BRU', 2: 'BUE', 3: 'CAN', 4: 'DEL', 5: 'GOT', 6: 'HAM', 7: 'IST', 8: 'JKT', 9: 'LAX', 10: 'LED', 11: 'LON', 12: 'MEX', 13: 'MXP', 14: 'NYC', 15: 'PAR', 16: 'RUH', 17: 'SEL', 18: 'SHA', 19: 'SIN', 20: 'WAW', 21: 'YTO', 22: 'ZRH'}


#        # common_plan_unitのdfからJPN出荷の計画週 == wで抽出
#        # ロットの仕向け地Arv_entity、ロット数lot_count、価値value_onSC
#
#        # 出荷最適化の対象ロットの「仕向け地」に付番する {}辞書またはリスト
#
#        # lot_noをKnapsackのnum, Knumberに変換
#        # 抽出した計画対象lot_noをナップサック問題のseq_numberに変換
#        Knum = convert_lot_no2Knumber(lot_no) 
#

#        # item = [ lot_seq_no, lot_count, value_onSC ]
#        # item = [ Knum, weight, value ]
#        items = make_items4knapsack()



# ************************
# Knapsack solver
# ************************
    solved_items = knapsack_solver(weight_limit, items_number)

    print('solved_items',solved_items)

    non_selected_node = []
    selected_node     = []

    for i, item in enumerate(solved_items):

        if item == 0 :

            non_selected_node.append( items_node_number_dic[i] )
            #pass

        else:

            #selected_arv_node_week.append( items_node_number_dic[i] )
            selected_node.append( items_node_number_dic[i] )

    print('selected_node',selected_node)
    print('non_selected_node',non_selected_node)


# image of "items.csv"
#
#Num    Value   Weight
#1      7       750
#2      6       700
#3      10      900
#4      10      600
#5      22      1200

# ***STOP***
#    post4knapsack()


# ***STOP***ココは無視してよい
#        # Knapsackのnum, Knumberをlot_noに変換 
#         # => ロット数に集計しているので、一対一に対応しない
#        lot_no = convert_Knumber2lot_no(Knum)

 
# ************************
# flag_counterで「選択」と「未選択の前週送り」を行う
# Post Knapsack solver 選択LOTにフラグ=1、未選択LOTはflag_counter+= -1で減算
# ************************

# ******************
# CPUにflagを立てる query and update with [node, year, plan_week, Arv_entity]
# ******************
#@221027
# dfから、node, year, plan_week, Arv_entityでlotを特定して、
# dfの"Confirm_flag_counter"に、flag=1 または-1の追加で減少させる

        # solved_itemsの0/1の判定から、ロット別confirm_flag_counterをセット
        # solved_items 0前週に戻りの時、confirm_flag_counter+= -1 追加
        # solved_items 1選択の時、confirm_flag_counter = 1


    dpt_node = mother_plant


# ************************
# Post Knapsack solver 選択LOTにフラグ=1
# ************************
    for item in selected_node:
    #for arv_node_week in selected_node:

    # [['BRU', 4 ], 1, 36.01522556] 
    # [['Arv_entity','Arv_week'],'weight','value]

    #@221110 arv_node_week ['Arv_entity','Arv_week']

    #for lot_no in selected_node:
    #for arv_node in selected_node:


        #set_flag4CPU(df, dpt_node,  year, w, arv_node )

        #@221109
        print('Confirm_flag_counter setting item',item)

        df.loc[ ( df['Dpt_entity'] == dpt_node ) &
                ( df['Arv_year']   == year ) &
                ( df['Plan_week']  == w ) & 

                ( df['Arv_entity'] == item[0]) &
                ( df['Arv_week']   == item[1]) 

                , 'Confirm_flag_counter'] = 1


        #@221107
        #df.loc[ ( df['Dpt_entity'] == dpt_node ) & ( df['Arv_year'] == year ) & ( df['Plan_week'] == w ) & ( df['seq_no'] == lot_no ) ,'Confirm_flag_counter'] = 1

        #df.loc[ ( df['Dpt_entity'] == dpt_node ) & ( df['Arv_year'] == year ) & ( df['Plan_week'] == w ) & ( df['Arv_entity'] == arv_node ) ,'Confirm_flag_counter'] = 1

        #df.loc[ ( df['Dpt_entity'] == dpt_node ) & ( df['Arv_year'] == year ) & ( df['Plan_week'] == w ) & ~( df['Arv_entity'] == arv_node ) ,'Confirm_flag_counter'].apply(lambda x: x-1)


##
## dump df
##
#    df_temp = df.values.tolist()
#
#    for l in df_temp:
#
#        print('flagged df list by list', l )



# ************************
# Post Knapsack solver 未選択LOTはflag_counter+= -1で減算
# ************************
    for item in non_selected_node:

        print('item',item)

        df.loc[ ( df['Dpt_entity'] == dpt_node ) & 
                ( df['Arv_year']   == year ) &  
                ( df['Plan_week']  == w ) & 

                ( df['Arv_entity'] == item[0] ) & 
                ( df['Arv_week']   == item[1] ) 
                , ['Confirm_flag_counter'] ] += -1


# *********************
# flag_counterの適用して、Plan_weekを新しい状態に更新する
# flagとcounterが混在しているので、選択済みflag=1の条件で対象から外す
# *********************
    # 否定 選択された=1 <=> 選択されていない
    df.loc[~(df['Confirm_flag_counter']==1),'Plan_week'] =  df['Dpt_week'] +  df['Confirm_flag_counter']

    # *********************************
    # animation用に毎週の計画状態を出力 common plan unitをcsv出力
    # *********************************
    file_name_out = 'common_plan_unit_knapsack' + "_W" + str(w)+ '.csv'

    df.to_csv(file_name_out)

        # plan_weekの再計算 
        # 生産配分から漏れたロットを(backward planningなので)前週に入れる

        # 詰め残したlotについて、CPUのdf中のplan_weekを更新する

        # knapsack_solverで「漏れたロット」not_fit_lotの場合
        # 例えば、confirm_flag_counter = -1の時、
        # 出荷計画週 = 当初の出荷週 - 1
        # plan_week = dept_week + confirm_flag_counter


# *********************************
# common plan unitをcsv出力
# *********************************

file_name_out = 'common_plan_unit_knapsack.csv'

df.to_csv(file_name_out)

print('end of shipping allocation mother plant with Knapsack solver')

# ******************************
# PySI graph with using "plotly"
# ******************************

# making graph on "mother plant ship week"
from PySI_mother_plant_png2gif import *

print('end of graph for mother plant ship allocation with png')

# make gif 
from png2gif import *

print('end of png2gif')


# ******************************
# end of code
# ******************************
