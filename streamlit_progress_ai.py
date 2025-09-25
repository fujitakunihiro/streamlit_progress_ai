# streamlit_progress_ai_advanced.py
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import os
import plotly.express as px

CSV_FILE = "tasks_ai.csv"

# --- CSV初期化 ---
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=[
        "Task", "Assignee", "StartDate", "DueDate", "Status",
        "ActualHours", "EstimatedHours", "NumFunctions", "NumTestCases"
    ])
    df_init.to_csv(CSV_FILE, index=False)

# --- CSV読み込み ---
df = pd.read_csv(CSV_FILE)

st.title("高度版 進捗管理＋AI工数予測")

# =========================
# タスク一覧表示＆削除
# =========================
st.subheader("タスク一覧")
if not df.empty:
    header = [
        "タスク名", "担当者", "開始日", "期限日", "ステータス",
        "実績工数（時間）", "見積工数（時間）", "進捗バー", "更新", "削除"
    ]
    # 幅を広めに設定（例: 3や4などに調整）
    col_widths = [4, 3, 3, 3, 3, 3, 3, 4, 2, 2]
    cols = st.columns(col_widths)
    for col, h in zip(cols, header):
        col.markdown(f"**{h}**")
    for i, row in df.iterrows():
        cols = st.columns(col_widths)
        cols[0].write(row["Task"])
        cols[1].write(row["Assignee"])
        cols[2].write(str(row["StartDate"]))
        cols[3].write(str(row["DueDate"]))
        cols[4].write(row["Status"])
        cols[5].write(row["ActualHours"])
        cols[6].write(row["EstimatedHours"])
        est = row["EstimatedHours"]
        actual = row["ActualHours"]
        est_ratio = min(est / 24, 1.0) if est > 0 else 0
        progress = actual / est if est > 0 else 0
        progress = min(progress, 1.0)
        bar_html = f"""
        <div style="position: relative; height: 18px; background: #eee; border-radius: 9px;">
            <div style="position: absolute; left: 0; top: 0; height: 18px; width: {est_ratio*100}%; background: #bbb; border-radius: 9px;"></div>
            <div style="position: absolute; left: 0; top: 0; height: 18px; width: {progress*100}%; background: #4caf50; border-radius: 9px;"></div>
            <div style="position: absolute; left: 6px; top: 0; height: 18px; line-height: 18px; color: #222; font-size: 12px;">
                {actual:.1f}/{est:.1f}h
            </div>
        </div>
        """
        cols[7].markdown(bar_html, unsafe_allow_html=True)
        update_clicked = cols[8].button("更新", key=f"update_{i}")
        del_clicked = cols[9].button("削除", key=f"del_{i}")
        if update_clicked:
            st.session_state["update_task_idx"] = i
            st.session_state["show_update_form"] = True
        if del_clicked:
            df = df.drop(i).reset_index(drop=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("タスクを削除しました！")
            st.rerun()
else:
    st.info("タスクがありません.")

# タスク追加ボタンを一覧の直下に表示
if st.button("タスク追加", key="add_task_main"):
    st.session_state["show_add_form"] = True

# =========================
# タスク追加フォーム（ダイアログ風）
# =========================
if st.session_state.get("show_add_form", False):
    st.subheader("タスク追加")
    with st.form("add_task_form_dialog"):
        task = st.text_input("タスク名")
        assignee = st.text_input("担当者")
        start = st.date_input("開始日")
        due = st.date_input("期限日")
        est_hours = st.number_input("見積工数（時間）", min_value=0.0, step=0.5)
        num_func = st.number_input("関数数", min_value=0, step=1)
        num_test = st.number_input("テストケース数", min_value=0, step=1)
        submitted = st.form_submit_button("タスク追加")
        cancel = st.form_submit_button("キャンセル")
        if submitted:
            df = pd.concat([df, pd.DataFrame([{
                "Task": task,
                "Assignee": assignee,
                "StartDate": start,
                "DueDate": due,
                "Status": "未着手",
                "ActualHours": 0,
                "EstimatedHours": est_hours,
                "NumFunctions": num_func,
                "NumTestCases": num_test
            }])], ignore_index=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("タスクを追加しました！")
            st.session_state["show_add_form"] = False
            st.rerun()
        elif cancel:
            st.session_state["show_add_form"] = False
            st.rerun()

# =========================
# タスク更新フォーム（ダイアログ風）
# =========================
if st.session_state.get("show_update_form", False):
    idx = st.session_state.get("update_task_idx")
    if idx is not None and idx < len(df):
        st.subheader("タスク更新")
        with st.form("update_task_form_dialog"):
            status = st.selectbox("ステータス", ["未着手", "進行中", "完了"], index=0)
            actual_hours = st.number_input("実績工数（時間）", min_value=0.0, step=0.5)
            submitted = st.form_submit_button("更新")
            cancel = st.form_submit_button("キャンセル")
            if submitted:
                df.at[idx, "Status"] = status
                df.at[idx, "ActualHours"] = actual_hours
                df.to_csv(CSV_FILE, index=False)
                st.success("タスクを更新しました！")
                st.session_state["show_update_form"] = False
                st.rerun()
            elif cancel:
                st.session_state["show_update_form"] = False
                st.rerun()

# =========================
# AI工数予測
# =========================
st.subheader("AI工数予測")
completed = df[df["Status"]=="完了"]
if len(completed) < 2:
    st.info("予測には完了したタスクが2件以上必要です。")
else:
    X = completed[["EstimatedHours","NumFunctions","NumTestCases"]]
    y = completed["ActualHours"]
    model = LinearRegression()
    model.fit(X, y)
    
    est_input = st.number_input("見積工数（時間）", min_value=0.0, step=0.5, key="ai_est")
    num_func_input = st.number_input("関数数", min_value=0, step=1, key="ai_func")
    num_test_input = st.number_input("テストケース数", min_value=0, step=1, key="ai_test")
    
    if st.button("AIで実績工数予測"):
        pred = model.predict([[est_input, num_func_input, num_test_input]])
        st.success(f"予測実績工数: {pred[0]:.2f}時間")

# =========================
# 進捗状況グラフ
# =========================
st.subheader("進捗状況グラフ（ステータス別）")
if not df.empty:
    progress_df = df.groupby("Status").size().reset_index(name='Count')
    st.bar_chart(progress_df.set_index("Status"))

st.subheader("実績 vs 見積 工数グラフ")
if not df.empty:
    fig2 = px.scatter(df, x="EstimatedHours", y="ActualHours",
                      color="Assignee", size="NumFunctions",
                      hover_data=["Task", "NumTestCases", "Status"])
    st.plotly_chart(fig2, use_container_width=True)
