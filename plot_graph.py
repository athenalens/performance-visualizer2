from flask import Flask, render_template, jsonify
import pandas as pd
import plotly
import plotly.graph_objects as go
import json

app = Flask(__name__)

@app.route('/')
def index():
    try:
        # CSVファイルからデータを読み込む
        df = pd.read_csv('data.csv', header=None)
        
        if df.empty:
            return jsonify({"error": "CSV file is empty"}), 400

        # 括弧を取り除く
        def convert_to_float(x):
            if isinstance(x, str):
                try:
                    return float(x.replace('(', '').replace(')', ''))
                except ValueError:
                    return pd.NA
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
            if pd.isna(y2[i]):
                changes.append(y1[i])
            else:
                changes.append(y2[i])
        changes.append(y1[-1])  # 最終値を追加

        # measureを設定
        measure = []
        for i in range(len(changes)):
            if pd.isna(y2[i]):
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
            increasing = {"marker":{"color":"green"}},  # 緑色
            decreasing = {"marker":{"color":"red"}},  # 赤色
            totals = {"marker":{"color":"blue"}}    
        ))

        # グラフのサイズと背景色を調整
        fig.update_layout(
            autosize=False,
            width=1000,
            height=500,
            title_text="Unit: USD M",
            title_x=0.95,
            paper_bgcolor='rgba(0,0,0,0)',  # 透明な背景
            plot_bgcolor='rgba(0,0,0,0)'  # 透明な背景
        )

        # X軸下部にコメントを表示
        fig.update_xaxes(ticktext=df.iloc[2].tolist(), tickvals=x, tickangle=-45)

        graphJSON = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
        return render_template('index.html', graphJSON=graphJSON)
        
    except FileNotFoundError:
        return jsonify({"error": "CSV file not found"}), 404
    except pd.errors.EmptyDataError:
        return jsonify({"error": "CSV file is empty"}), 400
    except pd.errors.ParserError:
        return jsonify({"error": "Error parsing CSV file"}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True) if 'get_ipython' in globals() else app.run()
