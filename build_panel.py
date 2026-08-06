"""4市（千葉・金沢・堺・富山）の一次データCSVを整形パネルにする。
出所: 各市公表資料（Koki-Arai/waste_analysis リポジトリ収録の生CSV）
"""
import re, csv, unicodedata
import pandas as pd, numpy as np

SRC = '/mnt/user-data/uploads/'

def num(x):
    if x is None: return np.nan
    s = unicodedata.normalize('NFKC', str(x)).strip().replace(',', '')
    if s in ('', '-', '—', '―', '－', 'nan', 'None'): return np.nan
    try: return float(s)
    except: return np.nan

def wareki(s):
    s = unicodedata.normalize('NFKC', str(s)).strip()
    if re.fullmatch(r'\d{4}', s): return int(s)
    m = re.match(r'平成\s*(\d+)', s)
    if m: return 1988 + int(m.group(1))
    m = re.match(r'令和\s*(元|\d+)', s)
    if m: return 2018 + (1 if m.group(1) == '元' else int(m.group(1)))
    return None

def rows(path):
    with open(SRC + path, encoding='utf-8-sig', newline='') as f:
        return [r for r in csv.reader(f)]

# ---------------- 千葉市（年度ブロック形式） ----------------
def chiba():
    R = rows('千葉ごみ処理費用.csv')
    out, cur = [], None
    for r in R:
        if not r: continue
        c0 = unicodedata.normalize('NFKC', r[0]).strip()
        if re.fullmatch(r'20\d{2}', c0):
            cur = int(c0); rec = {'fy': cur}; out.append(rec); continue
        if cur is None: continue
        rec = out[-1]
        key = c0.replace(' ', '').replace('※', '')
        if key == '可燃ごみ':
            rec['comb_collect_t']  = num(r[10])   # 収集運搬量（市が収集した可燃ごみ）
            rec['comb_interm_t']   = num(r[11])   # 中間処理投入量（直接搬入=事業系を含む）
            rec['comb_cost_yen']   = num(r[6])
        elif key in ('全種類', '合計'):
            rec['all_collect_t']   = num(r[10])
            rec['all_interm_t']    = num(r[11])
            rec['all_recycle_t']   = num(r[13])
            rec['all_cost_yen']    = num(r[6])
            rec['collect_cost_yen']= num(r[1])
            rec['interm_cost_yen'] = num(r[2])
            rec['final_cost_yen']  = num(r[3])
            rec['admin_cost_yen']  = num(r[5])
    df = pd.DataFrame(out)
    df['city'] = '千葉市'
    return df

# ---------------- 金沢市（横持ち） ----------------
def kanazawa():
    R = rows('金沢ごみ.csv')
    hdr = R[1]
    # 右表（排出量）の年度: col 22 以降 / 左表（経費）: col 3 以降
    yr_w = {i: wareki(hdr[i]) for i in range(22, len(hdr)) if wareki(hdr[i])}
    yr_c = {i: wareki(hdr[i]) for i in range(3, 18) if wareki(hdr[i])}

    def grab(rowidx, label_check=None):
        r = R[rowidx]
        return {yr_w[i]: num(r[i]) for i in yr_w if i < len(r)}

    series = {
        'pop':            grab(2),
        'waste_total_t':  grab(3),
        'household_t':    grab(4),
        'hh_burnable_t':  grab(6),
        'hh_landfill_bulky_t': grab(9),
        'recycle_t':      grab(12),
        'group_collect_t':grab(21),
        'business_t':     grab(29),
        'biz_burnable_t': grab(30),
    }
    cost_rows = {'collect': 2, 'interm': 5, 'final': 8, 'recycle': 11, 'admin': 14, 'total': 17}
    costs = {}
    for name, ri in cost_rows.items():
        r = R[ri]
        costs[name] = {yr_c[i]: num(r[i]) for i in yr_c if i < len(r)}

    yrs = sorted(set(series['waste_total_t']) | set(costs['total']))
    recs = []
    for y in yrs:
        rec = {'fy': y, 'city': '金沢市'}
        for k, d in series.items(): rec[k] = d.get(y, np.nan)
        for k, d in costs.items(): rec['cost_' + k + '_kyen'] = d.get(y, np.nan)
        recs.append(rec)
    return pd.DataFrame(recs)

# ---------------- 堺市 ----------------
def sakai():
    R = rows('堺市ごみ.csv')
    yrs = {i: wareki(R[1][i]) for i in range(1, 17) if wareki(R[1][i])}
    yrs_c = {i: wareki(R[1][i]) for i in range(19, len(R[1])) if wareki(R[1][i])}
    lab = {2: 'waste_total_t', 3: 'household_t', 4: 'hh_daily_t', 7: 'business_t',
           11: 'recycle_t', 16: 'group_collect_t', 19: 'grand_total_t'}
    labc = {2: 'cost_collect_kyen', 4: 'cost_interm_kyen', 6: 'cost_final_kyen',
            7: 'cost_total_kyen', 9: 'cost_per_capita_yen'}
    recs = {}
    for ri, name in lab.items():
        for i, y in yrs.items():
            recs.setdefault(y, {'fy': y, 'city': '堺市'})[name] = num(R[ri][i])
    for ri, name in labc.items():
        for i, y in yrs_c.items():
            recs.setdefault(y, {'fy': y, 'city': '堺市'})[name] = num(R[ri][i])
    return pd.DataFrame(sorted(recs.values(), key=lambda d: d['fy']))

# ---------------- 富山市 ----------------
def toyama():
    R = rows('富山ごみ.csv')
    recs = {}
    for r in R[3:]:
        if len(r) > 5 and wareki(r[0]):
            y = wareki(r[0])
            recs.setdefault(y, {'fy': y, 'city': '富山市'}).update({
                'business_t': num(r[1]), 'household_t': num(r[2]),
                'group_collect_t': num(r[3]), 'waste_total_t': num(r[4]), 'pop': num(r[5])})
        if len(r) > 10 and wareki(r[7]):
            y = wareki(r[7])
            recs.setdefault(y, {'fy': y, 'city': '富山市'})['cost_total_okuyen'] = num(r[10])
    return pd.DataFrame(sorted(recs.values(), key=lambda d: d['fy']))

if __name__ == '__main__':
    pd.set_option('display.width', 200, 'display.max_columns', 50)
    dfs = {'chiba': chiba(), 'kanazawa': kanazawa(), 'sakai': sakai(), 'toyama': toyama()}
    for k, d in dfs.items():
        print('\n' + '=' * 30, k, '=' * 30)
        print(d.to_string(index=False))
        d.to_csv(f'/home/claude/work/panel_{k}.csv', index=False, encoding='utf-8-sig')
