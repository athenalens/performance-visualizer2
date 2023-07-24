from flask import Flask, render_template
import pandas as pd
import plotly
import plotly.graph_objects as go
import numpy as np
import json

app = Flask(__name__)

@app.route('/')
def index():
    # CSVファイルからデータを読み込む
    df = pd.read_csv('data.csv', header=None)

    # 括弧を取り除く
    def convert_to_float(x):
        if isinstance(x, str):
            try:
                return float(x.replace('(', '').replace(')', ''))
            except ValueError:
                return np.nan
        else:
            return x

    # 3行目を除いてconvert_to_float関数を適用
    df.loc[~df.index.isin([2])] = df.loc[~df.index.isin([2])].applymap(convert_to_float)

    # データの準備
    x = df.columns.tolist()
    y1 = df.iloc[0].tolist()
    y2 = df.iloc[1].tolist()

    # 増減を計算
    changes = [y1[0]]  # 初期値を追加
    for i in range(1, len(y1) - 1):  # 2行目の値を使用（最初と最後の値は除く）
        if np.isnan(y2[i]):
            changes.append(y1[i])
        else:
            changes.append(y2[i])
    changes.append(y1[-1])  # 最終値を追加

    # measureを設定
    measure = []
    for i in range(len(changes)):
        if np.isnan(y2[i]):
            measure.append('absolute')
        else:
            measure.append('relative')

    # ウォーターフォールチャートの作成
    fig = go.Figure(go.Waterfall(
        x = x,
        y = changes,
        textposition = "outside",
        text = [str(c) for c in changes],
        measure = measure,
        base = 0,
        increasing = {"marker":{"color":"Green"}},
        decreasing = {"marker":{"color":"Red"}},
        totals = {"marker":{"color":"Blue"}}
    ))

    # グラフのサイズを調整
    fig.update_layout(autosize=False, width=1000, height=500, title_text="Unit: USD M", title_x=0.95)

    # X軸下部にコメントを表示
    fig.update_xaxes(ticktext=df.iloc[2].tolist(), tickvals=x, tickangle=-45)

    graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    return render_template('index.html', graphJSON=graphJSON)

if __name__ == "__main__":
    app.run(debug=True) if 'get_ipython' in globals() else app.run()

