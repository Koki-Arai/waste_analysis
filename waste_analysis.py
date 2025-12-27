import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# --- 設定・定数 ---
# グラフのフォント設定（環境に合わせて変更可能）
# 日本語フォントが利用できない環境を考慮し、デフォルトは英語表記とする
sns.set_style("whitegrid")

# 入力ファイル名定義
FILES = {
    "kanazawa": "金沢ごみ.csv",
    "sakai": "堺市ごみ.csv",
    "toyama": "富山ごみ.csv",
    "chiba": "千葉ごみ処理費用.csv"
}

# --- ユーティリティ関数 ---

def convert_year(year_str):
    """
    和暦・西暦・数値が混在する年度データを西暦（int）に統一する関数
    """
    if pd.isna(year_str):
        return None
    if isinstance(year_str, (int, float)):
        return int(year_str)
    
    year_str = str(year_str).strip()
    if year_str.lower() == 'nan': return None
    
    if year_str.isdigit():
        return int(year_str)
    
    # 和暦対応
    if year_str.startswith('平成'):
        try:
            return 1988 + int(year_str.replace('平成', '').replace('年', '').strip())
        except:
            pass
    if year_str.startswith('令和'):
        try:
            val = year_str.replace('令和', '').replace('年', '').strip()
            if val == '元':
                return 2019
            return 2018 + int(val)
        except:
            pass
    return None

def clean_num(x):
    """
    カンマ付き文字列やハイフンなどを数値(float)に変換する関数
    """
    if pd.isna(x) or str(x).strip() in ['―', '-', 'nan']: return np.nan
    if isinstance(x, str):
        x = x.replace(',', '')
        try:
            return float(x)
        except:
            return np.nan
    return float(x)

# --- 各都市の読み込みロジック ---

def load_kanazawa(path):
    records = []
    try:
        df = pd.read_csv(path, header=None)
        # 年度、人口、排出量の抽出
        years_row = df.iloc[1, 21:].values
        years = [convert_year(y) for y in years_row]
        pop = [clean_num(x) for x in df.iloc[2, 21:].values]
        waste = [clean_num(x) for x in df.iloc[3, 21:].values]

        # 経費の抽出（収集・中間・最終の合計）
        years_cost_row = df.iloc[1, 3:18].values
        years_cost = [convert_year(y) for y in years_cost_row]
        cost_map = {}
        for i, y in enumerate(years_cost):
            if y is None: continue
            cost_sum = 0
            # 行番号: 2=収集運搬, 5=中間処理, 8=最終処分
            for r in [2, 5, 8]:
                val = clean_num(df.iloc[r, 3+i])
                if not pd.isna(val):
                    cost_sum += val
            cost_map[y] = cost_sum

        for i, y in enumerate(years):
            if y is None: continue
            p = pop[i] if i < len(pop) else np.nan
            w = waste[i] if i < len(waste) else np.nan
            c = cost_map.get(y, np.nan)
            records.append({"City": "金沢市", "Year": y, "Population": p, "Waste": w, "Cost": c})
    except Exception as e:
        print(f"[Error] Failed to load Kanazawa data: {e}")
    return records

def load_sakai(path):
    records = []
    try:
        df = pd.read_csv(path, header=None)
        # 排出量データの抽出
        years_waste = []
        waste_list = []
        for i, val in enumerate(df.iloc[1, 1:16].values):
            y = convert_year(val)
            if y: 
                years_waste.append(y)
                waste_list.append(clean_num(df.iloc[2, 1+i]))
        
        waste_map = dict(zip(years_waste, waste_list))

        # 経費データの抽出
        years_cost = []
        cost_list = []
        per_capita_cost = []
        
        # 右表データのスキャン（列19以降）
        for i in range(19, df.shape[1]):
            val = df.iloc[1, i]
            y = convert_year(val)
            if y:
                years_cost.append(y)
                cost_list.append(clean_num(df.iloc[7, i])) # 年間経費
                per_capita_cost.append(clean_num(df.iloc[9, i])) # 1人当たり経費

        cost_map = dict(zip(years_cost, cost_list))
        
        all_years = sorted(list(set(years_waste) | set(years_cost)))
        for y in all_years:
            # 人口の逆算: 総経費(千円) * 1000 / 1人当たり経費(円)
            pop = np.nan
            if y in years_cost:
                idx = years_cost.index(y)
                if idx < len(per_capita_cost) and per_capita_cost[idx] > 0:
                    pop = (cost_list[idx] * 1000) / per_capita_cost[idx]
            
            records.append({
                "City": "堺市",
                "Year": y,
                "Population": pop,
                "Waste": waste_map.get(y, np.nan),
                "Cost": cost_map.get(y, np.nan)
            })
    except Exception as e:
        print(f"[Error] Failed to load Sakai data: {e}")
    return records

def load_toyama(path):
    records = []
    try:
        df = pd.read_csv(path, header=None)
        cost_map = {}
        # 右表: 経費（単位推定: 億円 -> 千円）
        for i in range(3, len(df)):
            row = df.iloc[i]
            if pd.isna(row[7]): continue
            y = convert_year(row[7])
            if y:
                c = clean_num(row[10])
                if not pd.isna(c):
                    cost_map[y] = c * 100000 

        # 左表: 排出量・人口
        for i in range(3, len(df)):
            row = df.iloc[i]
            if pd.isna(row[0]): continue
            y = convert_year(row[0])
            if y:
                w = clean_num(row[4])
                p = clean_num(row[5])
                c = cost_map.get(y, np.nan)
                records.append({"City": "富山市", "Year": y, "Population": p, "Waste": w, "Cost": c})
    except Exception as e:
        print(f"[Error] Failed to load Toyama data: {e}")
    return records

def load_chiba(path):
    records = []
    try:
        df = pd.read_csv(path, header=None)
        # 千葉市の人口データはCSVに含まれていない形式のため、外部定義（2010-2022）
        chiba_pop = {
            2010: 961749, 2011: 962624, 2012: 962130, 2013: 964153, 2014: 966862,
            2015: 971842, 2016: 972861, 2017: 975149, 2018: 977419, 2019: 980637,
            2020: 974951, 2021: 975210, 2022: 975268
        }
        
        # 年度の開始行を検出
        year_rows = []
        for idx, row in df.iterrows():
            val = str(row[0]).strip()
            if val.isdigit() and len(val) == 4 and int(val) > 2000:
                year_rows.append((idx, int(val)))

        for r_idx, year in year_rows:
            target_row = r_idx + 10
            if target_row < len(df):
                cost_val = clean_num(df.iloc[target_row, 6])
                if not pd.isna(cost_val): cost_val /= 1000 # 円 -> 千円
                waste_val = clean_num(df.iloc[target_row, 11])
                
                records.append({
                    "City": "千葉市",
                    "Year": year,
                    "Population": chiba_pop.get(year, np.nan),
                    "Waste": waste_val,
                    "Cost": cost_val
                })
    except Exception as e:
        print(f"[Error] Failed to load Chiba data: {e}")
    return records

# --- メイン処理 ---

def main():
    all_records = []
    
    if os.path.exists(FILES["kanazawa"]): all_records.extend(load_kanazawa(FILES["kanazawa"]))
    if os.path.exists(FILES["sakai"]):    all_records.extend(load_sakai(FILES["sakai"]))
    if os.path.exists(FILES["toyama"]):   all_records.extend(load_toyama(FILES["toyama"]))
    if os.path.exists(FILES["chiba"]):    all_records.extend(load_chiba(FILES["chiba"]))

    if not all_records:
        print("No records loaded. Please check CSV files.")
        return

    df = pd.DataFrame(all_records)
    
    # 指標計算
    # 1. 一人1日当たりごみ排出量 (g/人/日)
    df['Waste_per_Capita_g'] = (df['Waste'] * 1e6) / df['Population'] / 365
    
    # 2. 人口1人当たり年間経費 (円/人/年) = Cost(千円)*1000 / Pop
    df['Cost_per_Capita_Yen'] = (df['Cost'] * 1000) / df['Population']
    
    # 3. ごみ処理単価 (円/t) = Cost(千円)*1000 / Waste(t)
    df['Cost_per_Ton_Yen'] = (df['Cost'] * 1000) / df['Waste']

    # CSV出力
    output_csv = 'waste_analysis_summary.csv'
    df.to_csv(output_csv, index=False, encoding='utf-8-sig')
    print(f"Summary saved to {output_csv}")

    # 可視化
    city_map = {"金沢市": "Kanazawa", "堺市": "Sakai", "富山市": "Toyama", "千葉市": "Chiba"}
    df['City_En'] = df['City'].map(city_map)
    
    fig, axes = plt.subplots(3, 1, figsize=(10, 15))
    
    # Plot 1
    sns.lineplot(data=df, x='Year', y='Waste_per_Capita_g', hue='City_En', marker='o', ax=axes[0])
    axes[0].set_title('Waste Amount per Capita (g/person/day)')
    axes[0].set_ylabel('g / person / day')

    # Plot 2
    sns.lineplot(data=df, x='Year', y='Cost_per_Capita_Yen', hue='City_En', marker='o', ax=axes[1])
    axes[1].set_title('Processing Cost per Capita (Yen/person/year)')
    axes[1].set_ylabel('Yen / person / year')

    # Plot 3
    sns.lineplot(data=df, x='Year', y='Cost_per_Ton_Yen', hue='City_En', marker='o', ax=axes[2])
    axes[2].set_title('Processing Cost per Ton (Yen/t)')
    axes[2].set_ylabel('Yen / t')

    plt.tight_layout()
    output_img = 'waste_analysis_charts.png'
    plt.savefig(output_img)
    print(f"Charts saved to {output_img}")

if __name__ == "__main__":
    main()