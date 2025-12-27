# Japanese City Waste Management Analysis
(日本国内主要都市における一般廃棄物処理データの比較分析)

## Overview
This repository contains a Python script to analyze and visualize waste management data from four Japanese cities: **Kanazawa**, **Sakai**, **Toyama**, and **Chiba**. 

The script processes raw CSV data provided by local municipalities, cleans format irregularities, and calculates key performance indicators (KPIs) to compare efficiency and waste reduction progress.

## Key Indicators Calculated
1. **Waste Amount per Capita (g/person/day)**: 1人1日当たりごみ排出量
2. **Processing Cost per Capita (Yen/person/year)**: 人口1人当たりごみ処理経費
3. **Processing Cost per Ton (Yen/t)**: ごみ処理単価（トン当たり）

## Prerequisites
The following CSV files (raw data) are required in the root directory:
* `金沢ごみ.csv` (Kanazawa)
* `堺市ごみ.csv` (Sakai)
* `富山ごみ.csv` (Toyama)
* `千葉ごみ処理費用.csv` (Chiba)

*Note: Since the raw data formats differ significantly between cities (e.g., year representations in Japanese Era name "Heisei/Reiwa", irregular header positions), the script includes specific parsing logic for each file.*

## Installation & Usage

### 1. Install Dependencies
```bash
pip install -r requirements.txt