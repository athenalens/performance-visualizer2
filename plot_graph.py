from flask import Flask, render_template, jsonify, request, redirect, url_for
import os
from werkzeug.utils import secure_filename
import pandas as pd
import plotly
import plotly.graph_objects as go
import json
from flask import abort

app = Flask(__name__)

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'csv'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def generate_graph(filepath):
    try:
        df = pd.read_csv(filepath, header=None)
        
        if df.empty:
            abort(400, description="CSV file is empty")

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

        return graphJSON

    except pd.errors.EmptyDataError:
        abort(400, description="CSV file is empty")
    except pd.errors.ParserError:
        abort(400, description="Error parsing CSV file")
    except Exception as e:
        abort(500, description=str(e))

@app.route('/')
def index():
    # ここにホームページのロジックを追加
    return render_template('index.html')

@app.route('/upload', methods=['GET', 'POST'])
def upload_file():
    if request.method == 'POST':
        # ファイルがない、または許可されていない拡張子の場合
        if 'file' not in request.files or not allowed_file(request.files['file'].filename):
            return redirect(request.url)

        file = request.files['file']
        if file.filename == '':
            return redirect(request.url)

        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # ここでplot_graph.pyのロジックを呼び出してグラフを描画
            # 例: graph_data = generate_graph(filepath)
            # return render_template('graph.html', graph_data=graph_data)

        graphJSON = generate_graph(filepath)
        return render_template('index.html', graphJSON=graphJSON)

if __name__ == "__main__":
    app.run(debug=True) if 'get_ipython' in globals() else app.run()
