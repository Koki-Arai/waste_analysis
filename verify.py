"""一次データによる検証：処理群 vs 対照群の生の比較、DiD、事業系プラセボ。
注意：これは「本文の数値が実データで再現できるか」を確かめるための最小限の検証。
本番推定（対数変換・都市FE・年FE・クラスタSE）は整形パネル確定後に行う。
"""
import pandas as pd, numpy as np
import build_panel as bp

pd.set_option('display.width', 220, 'display.max_columns', 60)

ch, kz, sk, ty = bp.chiba(), bp.kanazawa(), bp.sakai(), bp.toyama()

# 家庭系ごみに相当する系列を揃える
# 千葉：可燃ごみ「収集運搬量」＝市が収集した可燃ごみ（直接搬入＝事業系を含まない）
ch_h = ch.set_index('fy')['comb_collect_t']
ch_b = (ch.set_index('fy')['comb_interm_t'] - ch.set_index('fy')['comb_collect_t'])  # ≒直接搬入（事業系）
kz_h, kz_b = kz.set_index('fy')['household_t'], kz.set_index('fy')['business_t']
sk_h, sk_b = sk.set_index('fy')['household_t'], sk.set_index('fy')['business_t']
ty_h, ty_b = ty.set_index('fy')['household_t'], ty.set_index('fy')['business_t']

def pct(s, base, post):
    return (s.get(post, np.nan) / s.get(base, np.nan) - 1) * 100

print('=' * 88)
print('【1】千葉市：2014年2月有料化 → FY2013は2ヶ月分のみ処理、FY2014が最初の通年')
print('=' * 88)
tab = pd.DataFrame({'千葉_家庭系可燃(収集運搬量)': ch_h, '千葉_事業系≒直接搬入': ch_b,
                    '堺_家庭系': sk_h, '富山_家庭系': ty_h}).loc[2010:2019]
print(tab.to_string())
print(f"\n  千葉 家庭系 FY2013→FY2014 : {pct(ch_h,2013,2014):+.2f}%")
print(f"  堺   家庭系 FY2013→FY2014 : {pct(sk_h,2013,2014):+.2f}%")
print(f"  富山 家庭系 FY2013→FY2014 : {pct(ty_h,2013,2014):+.2f}%")
ctrl = np.mean([pct(sk_h,2013,2014), pct(ty_h,2013,2014)])
print(f"  → 単純DiD（対数近似, %pt）: {pct(ch_h,2013,2014) - ctrl:+.2f} pp")
print(f"  ★事業系プラセボ 千葉 FY2013→FY2014 : {pct(ch_b,2013,2014):+.2f}%  "
      f"（堺 {pct(sk_b,2013,2014):+.2f}%, 富山 {pct(ty_b,2013,2014):+.2f}%）")

print('\n' + '=' * 88)
print('【2】金沢市：2018年2月有料化 → FY2017は2ヶ月分のみ処理、FY2018が最初の通年')
print('=' * 88)
tab = pd.DataFrame({'金沢_家庭系': kz_h, '金沢_家庭系燃やすごみ': kz.set_index('fy')['hh_burnable_t'],
                    '金沢_事業系': kz_b, '堺_家庭系': sk_h, '富山_家庭系': ty_h}).loc[2010:2022]
print(tab.to_string())
print(f"\n  金沢 家庭系 FY2017→FY2018 : {pct(kz_h,2017,2018):+.2f}%")
print(f"  堺   家庭系 FY2017→FY2018 : {pct(sk_h,2017,2018):+.2f}%")
print(f"  富山 家庭系 FY2017→FY2018 : {pct(ty_h,2017,2018):+.2f}%")
ctrl = np.mean([pct(sk_h,2017,2018), pct(ty_h,2017,2018)])
print(f"  → 単純DiD（%pt）: {pct(kz_h,2017,2018) - ctrl:+.2f} pp")
print(f"  ★事業系プラセボ 金沢 FY2017→FY2018 : {pct(kz_b,2017,2018):+.2f}%  "
      f"（堺 {pct(sk_b,2017,2018):+.2f}%, 富山 {pct(ty_b,2017,2018):+.2f}%）")

print('\n' + '=' * 88)
print('【3】代替行動（資源化への振替）は削減を説明するか')
print('=' * 88)
k = kz.set_index('fy')
print(f"  金沢 家庭系ごみ FY2017→FY2018 : {k.household_t[2018]-k.household_t[2017]:+,.0f} t")
print(f"  金沢 資源回収量 FY2017→FY2018 : {k.recycle_t[2018]-k.recycle_t[2017]:+,.0f} t")
print(f"  金沢 集団回収   FY2017→FY2018 : {k.group_collect_t[2018]-k.group_collect_t[2017]:+,.0f} t")
net = (k.household_t[2018]-k.household_t[2017]) + (k.recycle_t[2018]-k.recycle_t[2017]) \
      + (k.group_collect_t[2018]-k.group_collect_t[2017])
print(f"  → 振替を差し引いた正味削減 : {net:+,.0f} t "
      f"（家庭系削減の {net/(k.household_t[2018]-k.household_t[2017])*100:.0f}%）")

print('\n' + '=' * 88)
print('【4】処理経費は減ったか（論文は処理費節約を便益の主柱に置いている）')
print('=' * 88)
print(f"  金沢 経費合計 FY2017 {k.cost_total_kyen[2017]:,.0f}千円 → FY2018 {k.cost_total_kyen[2018]:,.0f}千円 "
      f"({(k.cost_total_kyen[2018]/k.cost_total_kyen[2017]-1)*100:+.1f}%)")
print(f"       うち収集運搬 {k.cost_collect_kyen[2017]:,.0f} → {k.cost_collect_kyen[2018]:,.0f} "
      f"({(k.cost_collect_kyen[2018]/k.cost_collect_kyen[2017]-1)*100:+.1f}%)")
print(f"       うち中間処理 {k.cost_interm_kyen[2017]:,.0f} → {k.cost_interm_kyen[2018]:,.0f} "
      f"({(k.cost_interm_kyen[2018]/k.cost_interm_kyen[2017]-1)*100:+.1f}%)")
c = ch.set_index('fy')
print(f"  千葉 費用合計 FY2013 {c.all_cost_yen[2013]/1e9:,.2f}十億円 → FY2014 {c.all_cost_yen[2014]/1e9:,.2f}十億円 "
      f"({(c.all_cost_yen[2014]/c.all_cost_yen[2013]-1)*100:+.1f}%)")
print(f"       FY2016 {c.all_cost_yen[2016]/1e9:,.2f} / FY2017 {c.all_cost_yen[2017]/1e9:,.2f}十億円")
print(f"  千葉 トンあたり費用 FY2013 {c.all_cost_yen[2013]/c.all_interm_t[2013]:,.0f}円/t "
      f"→ FY2014 {c.all_cost_yen[2014]/c.all_interm_t[2014]:,.0f}円/t")

print('\n' + '=' * 88)
print('【5】本文・表の数値との突き合わせ')
print('=' * 88)
rows = [
    ('千葉 処理前ごみ量', 'Table 1: 258,847t(可燃) / 298,354t(総量)',
     f'可燃中間処理投入量 FY2010-13平均 = {ch.set_index("fy").comb_interm_t.loc[2010:2013].mean():,.0f}t'),
    ('千葉 §4.2.2ベースライン', '179,468t',
     f'可燃収集運搬量 FY2010-13平均 = {ch_h.loc[2010:2013].mean():,.0f}t → ほぼ一致'),
    ('金沢 処理前ごみ量', 'Table 1: 51,243t(可燃) / 63,847t(総量)',
     f'家庭系 FY2015-17平均 = {kz_h.loc[2015:2017].mean():,.0f}t / 家庭系燃やす = {kz.set_index("fy").hh_burnable_t.loc[2015:2017].mean():,.0f}t → 一致しない'),
    ('金沢 §4.2.2ベースライン', '105,375t',
     f'家庭系 FY2015-17平均 = {kz_h.loc[2015:2017].mean():,.0f}t → 近い'),
    ('金沢 DiD推定値', '-14,686t',
     f'家庭系の生の変化 FY2017→18 = {kz_h[2018]-kz_h[2017]:+,.0f}t → 近い（ただし対照群未調整）'),
    ('千葉 DiD推定値', '-16,555t',
     f'可燃収集運搬量の生の変化 FY2013→14 = {ch_h[2014]-ch_h[2013]:+,.0f}t'),
    ('金沢 世帯数', '204,147世帯', '一次データに世帯数なし（人口 466,037人のみ）→ 要出所'),
    ('千葉 世帯数', '430,000世帯', '一次データに人口・世帯数なし → 要出所'),
]
print(pd.DataFrame(rows, columns=['項目', '論文の記載', '一次データによる検証']).to_string(index=False))
