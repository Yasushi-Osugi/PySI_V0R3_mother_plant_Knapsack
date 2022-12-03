# make_mother_plant_ship_week_lots_test_sub010.py


# 入力ファイル
#    file_name = 'common_plan_unit.csv'
#    df = pd.read_csv(file_name)


# 出力ファイル
#    file_name_out = 'common_plan_unit_VALUEonSC_flag_planweek.csv'
#    df.to_csv(file_name_out)


#
#@221026 CPUの列assignの確認
#    df.assign( Value_on_SC = 0 ) # サプライチェーン上のnode valueの加重平均
#    df.assign( Confirm_flag_counter = 0 )  # マザープラントの確定POフラグ
#    df.assign( Plan_week = 0 ) #マザープラントの出荷計画用 ナップサック漏れ用


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



#@221019 
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
#
#


# TODO@221016 済み
# node_year_value_listのappendがloopの中で、都度、更新されてしまう
# loopの外に渡して、node_year_value_listをappendするには?
# => return xxxxするとlist indexが別に付番される

# TODO@221014 node_value_on_SCの生成について
# CPU:Common Plan Unitの中にLOT単位のvalueを生成したが、

# そのままではサプライチェン上のnode間のvalue連鎖を表現していないので、
# node_value_onSCを定義する。
# 

#@221015 下記のvalue_listの定義では不十分では?
#outboundであれば、postorderingのnode treeに対応したtree上にvalueを置くのでは?

#    node_value_list = [] #return用にリスト型を宣言
#    # 末端から該当nodeまでのSCの階層分のvalue list , summaryがtotal value
#    # node_value_list = [ val_leaf, val_node1, val_node2, val_root ] 
#
#    node_value = {} #return用に辞書型を宣言
#    # node_value = {[node1: value_list1], [node2: value_list2],,, }


# node_value_onSC

# valueの平均値の算定

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

#
# coding: utf-8
#
#
#            Copyright (C) 2020 Yasushi Ohsugi
#            Copyright (C) 2021 Yasushi Ohsugi
#            Copyright (C) 2022 Yasushi Ohsugi
#
#            license follows MIT license

import numpy as np
import matplotlib.pyplot as plt

from scipy import stats # for trimmean

#  # メモリ解放
#  import gc
#  del tmp_data
#  del bulk
#  gc.collect()

# ******************************
# PySI related module
# ******************************
from PySILib.PySI_library_V0R1_070 import *

from PySILib.PySI_env_V0R1_080_value2 import *

from PySILib.PySI_PlanLot_SCMTREE_060_NyearB_value2_CPU import *
#from PySILib.PySI_PlanLot_SCMTREE_GC_060 import *

from PySILib.PySI_search_LEAF_in_SCMTREE import *




# ********************************************************
# csv_write2common_plan_header 共通計画単位のヘッダー書き出し
# ********************************************************
def csv_write2common_plan_header_N(): 

    l = []
    r = []

    #seq_no, control_flag , priority_no, modal, LT , from_x , from_Wxx , step_xx , to_y , to_Wyy , step_yy 

    # ********* ヘッダーのみ先に書き出す 各PSI計画の出力の前に
    r = ['seq_no','control_flag','priority_no','modal','LT','Dpt_entity','Dpt_year','Dpt_week','Dpt_step','Arv_entity','Arv_year','Arv_week','Arv_step','Value'] #@221009@221010


    # lot_noで出力するcsv file nameを作成
    csv_file_name = "common_plan_unit.csv"

    l.append(r)

# ****************************************
# CSV ファイル書き出し
# ****************************************

    #print('l',l)

    with open( csv_file_name , 'w', newline="") as f:

        writer = csv.writer(f)
        writer.writerows(l)



def calc_value_on_SC( file_name, node, year ):
#def read_common_plan_unit_N( file_name, node, year ):

    df = pd.read_csv('common_plan_unit.csv')
    #df = pd.read_csv('common_plan_unit.csv',encoding='shift-jis',sep=',')
    
    #print(df)

    if df['value'] > 0:
        df['value'] = df['value']
    else:
        df['value'] = 0

    print(df)




# ******************************
# node別 year別にloopを回す
# ******************************

# **********************************
# calc_value_on_SC @221015
# **********************************

#   1. データクレンジング　　valueゼロのとマイナスをゼロに

# 値の演算 df[列名] = df[列名] を含む演算という方法




#def double_then_minus_5(x):
#    x *= 2
#    x -= 5
#    return x
#
#df['col_int'] = df['col_int'].apply(double_then_minus_5)






#def check_value_set_zero( file_name):
##def read_common_plan_unit_N( file_name, node, year ):
#
#    df = pd.read_csv(file_name)
#    #df = pd.read_csv('common_plan_unit.csv')
#    #df = pd.read_csv('common_plan_unit.csv',encoding='shift-jis',sep=',')
#    
#    #print(df)
#
#    if df['value'] > 0:
#
#        df['value'] = df['value']
#
#    else:
#
#        df['value'] = 0
#
#
#    print(df)


def check_value_set_zero(x):

    if x > 0:

        pass

    else:

        x = 0

    return x



def calc_node_year_value(node,year,df):

    node_year_value = [ 0, 0, 0, [] ]

    print('node year',node, year)

    df_n_y = df.query("Arv_year == @year & Arv_entity == @node")


    value_trimed_ave = stats.trim_mean(df_n_y['Value'], 0.2) 

    node_year_value[0] = node
    node_year_value[1] = year
    node_year_value[2] = value_trimed_ave

    return node_year_value


def calc_node_year_volume(node,year,df):

    node_year_volume = [ 0, 0, 0, [] ]


    df_n_y = df.query("Arv_year == @year & Arv_entity == @node")




    #print('df_n_y',df_n_y)


    #df[['氏名', 'カテゴリ', '売上金額']].groupby(['氏名', 'カテゴリ']).mean()

    #@221017ココは、mainの中で直接、count して、リスト化できる???
    #values.tolistでリスト化


#@221018 「要求数が同じ」なのはPSIのSが同じなのでP=LOT数が同じ
#         計算が変 dfのダンプからチェック=> Sを増やすとP=LOT数も増える
#         ので、当面、このvolumeの計算ままで良しとして、加重平均に行くとする。

    n_y_vol =len(df_n_y)

    if ( node == 'JPN' and year == 2023 ) :

        print( 'dump YTOLEAF 2023 df', node, year, df )

        pd.set_option('display.max_rows', 5000)
        pd.set_option('display.max_columns',1000)
        print( 'dump YTOLEAF 2023 df_n_y', df_n_y )
        print( 'len(df_n_y)', n_y_vol )

    if ( node == 'YTOLEAF' and year == 2023 ) :

        print( 'dump YTOLEAF 2023 df', node, year, df )

        pd.set_option('display.max_rows', 5000)
        pd.set_option('display.max_columns',1000)
        print( 'dump YTOLEAF 2023 df_n_y', df_n_y )
        print( 'len(df_n_y)', n_y_vol )


#['RUHLEAF', 2023, 221, []], 
#['RUHLEAF', 2024, 221, []], 
#['RUHLEAF', 2025, 221, []], 
#['RUHLEAF', 2026, 221, []], 
#['RUH', 2023, 12, []], 
#['RUH', 2024, 12, []], 
#['RUH', 2025, 12, []], 
#['RUH', 2026, 12, []], 
#['SWELEAF', 2023, 221, []], 
#['SWELEAF', 2024, 221, []], 
#['SWELEAF', 2025, 221, []], 
#['SWELEAF', 2026, 221, []], 



    #n_y_vol =df_n_y[['Arv_entity', 'Arv_step']].groupby(['Arv_entity']).count()

    #n_y_vol = df_n_y[['Arv_entity', 'Arv_year', 'Arv_step']].groupby(['Arv_entity', 'Arv_year']).count().values.tolist()

    print('n_y_vol',n_y_vol)


#    volume_n_y = stats.trim_mean(df_n_y['Value'], 0.2) 
##    Dpt_S = df_node[['Dpt_week','Dpt_step']].groupby('Dpt_week').count()


    node_year_volume[0] = node
    node_year_volume[1] = year
    node_year_volume[2] = n_y_vol

    print('node_year_volume',node, year,node_year_volume)

    return node_year_volume


def search_childs_get_val_vol(node, parent_childs, year, n_y_value_list, n_y_volume_list):

# parent_childsは、親子関係を配列で表したデータ
# parent_childs = [['JPN', 'YTO'], ['JPN', 'NYC'], ['JPN', 'LAX'], ,,,]

    children_value  = []
    children_volume = []

    for pc in parent_childs:

        if pc[0] == node:

            child_node = pc[1]

            # ***** VALUE *****
            for n_y_value in n_y_value_list:

                if ( n_y_value[0] == child_node and n_y_value[1] == year ):

                    children_value.append(n_y_value)

         #children_value.append(n_y_value)


            # ***** VOLUME *****
            for n_y_volume in n_y_volume_list:

                if ( n_y_volume[0] == child_node and n_y_volume[1] == year ):

                    children_volume.append(n_y_volume)



    return children_value, children_volume



def search_childs_get_value(node, parent_childs, year, n_y_value_list):

# parent_childsは、親子関係を配列で表したデータ
# parent_childs = [['JPN', 'YTO'], ['JPN', 'NYC'], ['JPN', 'LAX'], ,,,]

    children_value = []

    for pc in parent_childs:

        if pc[0] == node:

            child_node = pc[1]

            for n_y_value in n_y_value_list:

                if ( n_y_value[0] == child_node and n_y_value[1] == year ):

                    children_value.append(n_y_value)

         #children_value.append(n_y_value)


    return children_value


#@221019
# ***************************************************************************
# 以下は、加重平均計算の関数の中に入れる
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
    #for val, vol in zip( child_n_y_value, child_n_y_vol ):

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

    # *** STOP ***
    #value_onSC = val[2]

    #value_onSC += ny_wt_avg


# ***************************************************************************


#def set_n_y_value_onSC(
#
#df.loc[ ( df['Arv_entity'] == node) & (df['Arv_year'] == year), 'Vaule_onSC'] =  value_onSC




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

    #本来は、profileの'year'をkeyにuniqeして、years_listを作成する
    years_list = [2023, 2024, 2025, 2026]
    #years_list = [2022, 2023, 2024, 2025]

    # planningでは
    # 注: current_year=Nは使わない。N+1,N+2,N+3の末端市場S_outlookを使用する。
    # adjustingでは、crrent_year=Nの'S_actual'でadjust計算する。

    # SC_activity_table   S-I-P( node, time ) + lot_step  cost_profile(node)

    # 制約
    # 部分問題(ネットワーク、配分)のsolver modelと制約 
    #  => 供給ネットワーク定義、最適配分、　　　ら
    # Supply_chain activity全体の表現、planning結果、評価



    #check_value_set_zero( file_name)


    file_name = 'common_plan_unit.csv'

    df = pd.read_csv(file_name)

    df['Value'] = df['Value'].apply(check_value_set_zero)

    print(df)


    print('end of process')

# ******************************
# end of main process
# ******************************

## trimmean_test.py
#
#import pandas as pd
#
##define DataFrame
#
#    df = pd.DataFrame({'points': [25, 12, 15, 14, 19, 23, 25, 29],
#                       'assists': [5, 7, 7, 9, 12, 9, 9, 4],
#                       'rebounds': [11, 8, 10, 6, 6, 5, 9, 12]})
#
#
##calculate 5% trimmed mean of points
#
#    ans = stats.trim_mean(df.points, 0.2) 
#
#    print('stats.trim_mean',ans)
#20.25


#@221018 STOP
#    n_y_vol = df[['Arv_entity', 'Arv_year', 'Arv_step']].groupby(['Arv_entity', 'Arv_year']).count().values.tolist()
#
#    print('n_y_vol',n_y_vol)



#@221020 Value_on_SCの追加
#@221023 マザープランとの確定POフラグConfirm_flag_counterの追加

    df = df.assign( Value_on_SC = 0 ) #サプライチェーン上のnode valueの加重平均

    df = df.assign( Confirm_flag_counter = 0 )  # マザープラントの確定POフラグ

    df = df.assign( Plan_week = 0 ) #マザープラント出荷計画 ナップサック漏れ用

    print('at df assign +flag and plan_week',df)


#@221016 MEMO
# 1. data構造の見直し。node_year_valueのリスト?


    node_year_value = [0, 0, 0, [] ] # 最後のリストは子供nodeのvalueリスト
    n_y_value_list = []


    node_year_volume = [0, 0, 0, [] ] # 最後のリストは子供nodeのvolumeリスト
    n_y_volume_list = []


    #node_value = {} #辞書

    for node in node_name:  #### SCM tree nodes are postordering 

        for year in years_list:


            if is_leaf(node):

                print('test YES is_leaf',node)


                # **************************
                # node year value 価値
                # **************************
                node_year_value = calc_node_year_value(node,year,df)

                print('node_year_value',node_year_value)
#
#['YTOLEAF', 2026, 23.266416039774438], 

                #@221019 LEAFの場合、ココでnode,year別のvalue_on_SCがでる
                value_on_SC = node_year_value[2]
                print('value_on_SC on LEAF', node, year, value_on_SC)


                # ***************************************
                # value_on_SCを求めたらその場で、dfを更新
                # ***************************************
                df.loc[ ( df['Arv_entity'] == node) & (df['Arv_year'] == year),                 'Value_on_SC'] =  value_on_SC


                n_y_value_list.append(node_year_value)

                print('node_year_value_list',n_y_value_list)



                # **************************
                # node year volume 数量
                # **************************
                node_year_volume = calc_node_year_volume(node,year,df)
#
#['YTOLEAF', 2026, 23.266416039774438], 

                print('node_year_volume',node_year_volume)

                n_y_volume_list.append(node_year_volume)

                print('node_year_volume_list',n_y_volume_list)


            else:

                print('test NO is_NOT_leaf',node)

                # **************************
                # node year value 価値
                # **************************
                # ひとまずnodeのvalueを出す
                node_year_value = calc_node_year_value(node,year,df)
#
#['YTO', 2023, 11.483333334125], 

                print('node_year_value',node_year_value)

                #@221019 NON_LEAFの場合も、ココでnode,year別のvalue_on_SCセット
                value_on_SC = node_year_value[2]
                print('value_on_SC on NON_LEAF', node, year, value_on_SC)


                # **************************
                # node year volume 数量
                # **************************

                node_year_volume = calc_node_year_volume(node,year,df)
#
#['YTOLEAF', 2026, 23.266416039774438], 

                print('node_year_volume',node_year_volume)

                n_y_volume_list.append(node_year_volume)

                print('node_year_volume_list',n_y_volume_list)






                children_value, children_vol = search_childs_get_val_vol(node, parent_childs, year, n_y_value_list, n_y_volume_list)

                print('children_value',children_value)
                print('children_vol',children_vol)

                #@221019 ココで子nodeのyearのvalue, volumeが入っている

#children_value [['NYC_N', 2024, 24.23784461152882, []], ['NYC_D', 2024, 24.23784461152882, []], ['NYC_I', 2024, 24.237844611528814, []]]

#children_vol [['NYC_N', 2024, 221, []], ['NYC_D', 2024, 221, []], ['NYC_I', 2024, 221, []]]

                # 加重平均したサプライチェーン上の価値value_on_SCを生成する
                children_value_on_SC = calc_weight_average_value(children_value,children_vol)

                value_on_SC += children_value_on_SC

                print('value + children on NON_LEAF', node, year, value_on_SC)

                # ***************************************
                # value_on_SCを求めたらその場で、dfを更新
                # ***************************************
                df.loc[ ( df['Arv_entity'] == node) & (df['Arv_year'] == year),                 'Value_on_SC'] =  value_on_SC


                #children_value = search_childs_get_value(node, parent_childs, year, n_y_value_list)

# parent_childsは、親子関係を配列で表したデータ
# parent_childs = [['JPN', 'YTO'], ['JPN', 'NYC'], ['JPN', 'LAX'], ,,,]

                # 自分のnode valueと子供nodeのvalueをリストで生成しておく

                node_year_value[3] = children_value  # 子供node_value保管
                node_year_volume[3]   = children_vol    # 子供node_volume保管

                n_y_value_list.append(node_year_value)
                n_y_volume_list.append(node_year_volume)

                print('node_year_value_list',n_y_value_list)
                print('node_year_volume_list',n_y_volume_list)

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
#
#



##
#            PySI_Y(df_prof, df, PSI_LIST, years_list, node, 'LEAF')
#            #PSI_LIST_node = PySI_Y(df_prof, df, PSI_LIST, years_list, node, 'LEAF')

#            # monitor
#            PSI_LIST[0][7] = 11
#            print('monitor in node loop after PySI_Y(',PSI_LIST[:50])
#
            #print('year node_year_value_list',node, year,node_year_value_list)

            #else:   #### root node処理が必要な場合はelif is_root分岐

            #for year in years_list:

            #df_n_y = df.query("Arv_year == @year & Arv_entity == @node")

            #value_trimed_ave = stats.trim_mean(df_n_y['Value'], 0.2) 

            #node_year_value[0] = node
            #node_year_value[1] = year
            #node_year_value[2] = value_trimed_ave

            #node_year_value_list.append(node_year_value)

            #print('node_year_value',node_year_value)

        print('year node_year_value_list',node, year,n_y_value_list)


        #@221019 node+yearのvalue&volume listを使って
        # 加重平均したサプライチェーン上の価値value_on_SCを生成する


        

#        if n_y_value_list[3] == []:
#
#            value_on_SC = n_y_value_list[2]
#
#        else:
#
#            value_on_SC = n_y_value_list[2]
#
#            # 加重平均したサプライチェーン上の価値value_on_SCを生成する
#            children_value_on_SC = calc_weight_average_value(n_y_value_list,n_y_volume_list)

#            value_on_SC += children_value_on_SC
#
#        #@221019
#        #* サプライチェーン上の価値value_on_SCをcommon plan unitにセットする
#        #* mother plantの出荷配分 knapsack_solverで月別、週別で生産配分最適化






    print('node node_year_value_volume_list value_on_SC',node, year,n_y_value_list, n_y_volume_list,value_on_SC)


    # *********************************
    # Plan_weekの初期設定
    # *********************************

    # ***** 初期セットは、これで良いが、本処理では年を跨る場合は、
    # 0週は前年の52週に、-1週は前年の51週になる。

    df['Plan_week'] = df['Dpt_week'] + df['Confirm_flag_counter']

    print('at csv OUT +flag and plan_week',df)



    # *********************************
    # common plan unitをcsv出力
    # *********************************

    file_name_out = 'common_plan_unit_VALUEonSC_flag_planweek.csv'

    df.to_csv(file_name_out)



#    df_n_y = df.query("Dpt_year == @year & Dpt_entity == @node")
#
#    ans = stats.trim_mean(df_n_y['Value'], 0.2) 
#
#    print('stats.trim_mean',ans)

    #print('node_year_value_list',node_year_value_list)

# ******************************
# node_year_total_volume = [node, year, volume]
# ******************************

#    node_year_total_volume = []
#
#    node_year_total_volume = calc_node_year_total_volume(df, node, year)
#
#    Dpt_S = df_node[['Dpt_week','Dpt_step']].groupby('Dpt_week').count()
#
#    #Dpt_S = df_node[['Dpt_week','Dpt_step']].groupby('Dpt_week').sum()



