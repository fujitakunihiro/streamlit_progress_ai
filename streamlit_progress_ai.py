# streamlit_progress_ai_advanced.py
import streamlit as st
import pandas as pd
from sklearn.linear_model import LinearRegression
import os
import plotly.express as px
import json
import math

CSV_FILE = "tasks_ai.csv"

# --- CSV初期化 ---
if not os.path.exists(CSV_FILE):
    df_init = pd.DataFrame(columns=[
        "Task", "Assignee", "StartDate", "DueDate", "Status",
        "ActualHours", "EstimatedHours", "NumFunctions", "NumTestCases", "SubTasks"
    ])
    df_init.to_csv(CSV_FILE, index=False)

# --- CSV読み込み ---
df = pd.read_csv(CSV_FILE)

st.title("高度版 進捗管理＋AI工数予測")

st.markdown(
    '<link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css" rel="stylesheet">',
    unsafe_allow_html=True
)

# =========================
# タスク一覧表示＆削除＆サブタスク追加
# =========================
st.subheader("タスク一覧")
if not df.empty:
    header = [
        "タスク名", "担当者", "開始日", "期限日", "ステータス",
        "実績工数（時間）", "見積工数（時間）", "進捗バー", "更新", "削除"
    ]
    col_widths = [4, 3, 3, 3, 3, 3, 3, 4, 2, 2]
    cols = st.columns(col_widths)
    for col, h in zip(cols, header):
        col.markdown(f"**{h}**")
    for i, row in df.iterrows():
        # --- 親タスクとサブタスク表示（カード枠→区切り線へ変更） ---
        st.markdown(
            """
            <hr style="border: none; border-top: 3px solid #bcd; margin: 32px 0 18px 0;">
            """,
            unsafe_allow_html=True
        )

        # --- 親タスク（表形式） ---
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
        update_clicked = cols[8].button("✏️", key=f"update_{i}")
        del_clicked = cols[9].button("🗑️", key=f"del_{i}")
        if update_clicked:
            st.session_state["update_task_idx"] = i
            st.session_state["show_update_form"] = True
        if del_clicked:
            df = df.drop(i).reset_index(drop=True)
            df.to_csv(CSV_FILE, index=False)
            st.success("タスクを削除しました！")
            st.rerun()

        # --- サブタスク追加ボタン ---
        st.markdown('<div style="margin:8px 0;"></div>', unsafe_allow_html=True)
        subtask_btn = st.button("＋ サブタスク追加", key=f"subtask_add_btn_{i}")
        if subtask_btn:
            st.session_state[f"show_subtask_form_{i}"] = True

        # --- サブタスク追加フォーム ---
        if st.session_state.get(f"show_subtask_form_{i}", False):
            with st.form(f"subtask_form_{i}"):
                sub_name = st.text_input("サブタスク名", key=f"subtask_name_{i}")
                sub_assignee = st.text_input("担当者", key=f"subtask_assignee_{i}")
                sub_start = st.date_input("開始日", key=f"subtask_start_{i}")
                sub_due = st.date_input("期限日", key=f"subtask_due_{i}")
                sub_status = st.selectbox("ステータス", ["未着手", "進行中", "完了"], key=f"subtask_status_{i}")
                sub_actual_hours = st.number_input("実績工数（時間）", min_value=0.0, step=0.5, key=f"subtask_actual_{i}")
                sub_est_hours = st.number_input("見積工数（時間）", min_value=0.0, step=0.5, key=f"subtask_est_{i}")
                submitted = st.form_submit_button("登録")
                cancel = st.form_submit_button("キャンセル")
                if submitted and sub_name:
                    sub_tasks_raw = row.get("SubTasks", "[]")
                    if isinstance(sub_tasks_raw, float) and math.isnan(sub_tasks_raw):
                        sub_tasks_raw = "[]"
                    sub_tasks = json.loads(sub_tasks_raw)
                    sub_tasks.append({
                        "name": sub_name,
                        "assignee": sub_assignee,
                        "start": str(sub_start),
                        "due": str(sub_due),
                        "status": sub_status,
                        "actual_hours": sub_actual_hours,
                        "est_hours": sub_est_hours,
                        "done": sub_status == "完了"
                    })
                    df.at[i, "SubTasks"] = json.dumps(sub_tasks)
                    df.to_csv(CSV_FILE, index=False)
                    st.success("サブタスクを追加しました！")
                    st.session_state[f"show_subtask_form_{i}"] = False
                    st.rerun()
                elif cancel:
                    st.session_state[f"show_subtask_form_{i}"] = False
                    st.rerun()

        # --- サブタスク表（親タスクの下にインデント表示） ---
        sub_tasks_raw = row.get("SubTasks", "[]")
        if isinstance(sub_tasks_raw, float) and math.isnan(sub_tasks_raw):
            sub_tasks_raw = "[]"
        sub_tasks = json.loads(sub_tasks_raw)
        if sub_tasks:
            st.markdown(
                """
                <div style="background:#f7fbff;border-radius:14px;padding:18px 18px 10px 32px;margin:18px 0 0 0;">
                """,
                unsafe_allow_html=True
            )
            sub_header = [
                "サブタスク名", "担当者", "開始日", "期限日", "ステータス",
                "実績工数（時間）", "見積工数（時間）", "進捗バー", "更新", "削除"
            ]
            sub_col_widths = [4, 3, 3, 3, 3, 3, 3, 4, 2, 2]
            sub_cols = st.columns(sub_col_widths)
            for col, h in zip(sub_cols, sub_header):
                col.markdown(f"<span style='font-size:13px'>{h}</span>", unsafe_allow_html=True)
            for j, sub in enumerate(sub_tasks):
                sub_cols = st.columns(sub_col_widths)
                sub_cols[0].markdown(f"<span style='margin-left:16px'>{sub.get('name', '')}</span>", unsafe_allow_html=True)
                sub_cols[1].write(sub.get("assignee", ""))
                sub_cols[2].write(sub.get("start", ""))
                sub_cols[3].write(sub.get("due", ""))
                sub_cols[4].write(sub.get("status", ""))
                sub_cols[5].write(sub.get("actual_hours", ""))
                sub_cols[6].write(sub.get("est_hours", ""))
                # 進捗バー
                est = sub.get("est_hours", 0)
                actual = sub.get("actual_hours", 0)
                try:
                    est = float(est)
                    actual = float(actual)
                except:
                    est = 0
                    actual = 0
                progress = actual / est if est > 0 else 0
                progress = min(progress, 1.0)
                bar_html = f"""
                <div style="position: relative; height: 14px; background: #eee; border-radius: 7px;">
                    <div style="position: absolute; left: 0; top: 0; height: 14px; width: {progress*100}%; background: #4caf50; border-radius: 7px;"></div>
                    <div style="position: absolute; left: 6px; top: 0; height: 14px; line-height: 14px; color: #222; font-size: 11px;">
                        {actual:.1f}/{est:.1f}h
                    </div>
                </div>
                """
                sub_cols[7].markdown(bar_html, unsafe_allow_html=True)
                # 更新ボタン
                update_clicked = sub_cols[8].button("✏️", key=f"sub_update_{i}_{j}")
                if update_clicked:
                    st.session_state[f"show_sub_update_form_{i}_{j}"] = True
                # 削除ボタン
                if sub_cols[9].button("🗑️", key=f"sub_del_btn_{i}_{j}"):
                    sub_tasks.pop(j)
                    df.at[i, "SubTasks"] = json.dumps(sub_tasks)
                    df.to_csv(CSV_FILE, index=False)
                    st.rerun()

                # --- サブタスク更新フォーム ---
                if st.session_state.get(f"show_sub_update_form_{i}_{j}", False):
                    with st.form(f"sub_update_form_{i}_{j}"):
                        sub_name = st.text_input("サブタスク名", value=sub.get("name", ""), key=f"sub_update_name_{i}_{j}")
                        sub_assignee = st.text_input("担当者", value=sub.get("assignee", ""), key=f"sub_update_assignee_{i}_{j}")
                        sub_start = st.date_input("開始日", value=pd.to_datetime(sub.get("start", "")), key=f"sub_update_start_{i}_{j}")
                        sub_due = st.date_input("期限日", value=pd.to_datetime(sub.get("due", "")), key=f"sub_update_due_{i}_{j}")
                        sub_status = st.selectbox("ステータス", ["未着手", "進行中", "完了"], index=["未着手", "進行中", "完了"].index(sub.get("status", "未着手")), key=f"sub_update_status_{i}_{j}")
                        sub_actual_hours = st.number_input("実績工数（時間）", min_value=0.0, step=0.5, value=float(sub.get("actual_hours", 0)), key=f"sub_update_actual_{i}_{j}")
                        sub_est_hours = st.number_input("見積工数（時間）", min_value=0.0, step=0.5, value=float(sub.get("est_hours", 0)), key=f"sub_update_est_{i}_{j}")
                        submitted = st.form_submit_button("更新")
                        cancel = st.form_submit_button("キャンセル")
                        if submitted:
                            sub_tasks[j] = {
                                "name": sub_name,
                                "assignee": sub_assignee,
                                "start": str(sub_start),
                                "due": str(sub_due),
                                "status": sub_status,
                                "actual_hours": sub_actual_hours,
                                "est_hours": sub_est_hours,
                                "done": sub_status == "完了"
                            }
                            df.at[i, "SubTasks"] = json.dumps(sub_tasks)
                            df.to_csv(CSV_FILE, index=False)
                            st.success("サブタスクを更新しました！")
                            st.session_state[f"show_sub_update_form_{i}_{j}"] = False
                            st.rerun()
                        elif cancel:
                            st.session_state[f"show_sub_update_form_{i}_{j}"] = False
                            st.rerun()
            st.markdown("</div>", unsafe_allow_html=True)  # サブタスク表枠閉じ

else:
    st.info("タスクがありません.")

# タスク追加ボタンを一覧の直下に表示
if st.button("タスク追加", key="add_task_main"):
    st.session_state["show_add_form"] = True

# =========================
# タスク追加フォーム（フォーム表示）
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
        submitted = st.form_submit_button("追加")
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
# タスク更新フォーム（ダイアログ風・全項目編集）
# =========================
if st.session_state.get("show_update_form", False):
    idx = st.session_state.get("update_task_idx")
    if idx is not None and idx < len(df):
        st.subheader("タスク更新")
        with st.form("update_task_form_dialog"):
            task = st.text_input("タスク名", value=df.at[idx, "Task"])
            assignee = st.text_input("担当者", value=df.at[idx, "Assignee"])
            start = st.date_input("開始日", value=pd.to_datetime(df.at[idx, "StartDate"]))
            due = st.date_input("期限日", value=pd.to_datetime(df.at[idx, "DueDate"]))
            status = st.selectbox("ステータス", ["未着手", "進行中", "完了"], index=["未着手", "進行中", "完了"].index(df.at[idx, "Status"]))
            actual_hours = st.number_input("実績工数（時間）", min_value=0.0, step=0.5, value=float(df.at[idx, "ActualHours"]))
            est_hours = st.number_input("見積工数（時間）", min_value=0.0, step=0.5, value=float(df.at[idx, "EstimatedHours"]))
            num_func = st.number_input("関数数", min_value=0, step=1, value=int(df.at[idx, "NumFunctions"]))
            num_test = st.number_input("テストケース数", min_value=0, step=1, value=int(df.at[idx, "NumTestCases"]))
            submitted = st.form_submit_button("更新")
            cancel = st.form_submit_button("キャンセル")
            if submitted:
                df.at[idx, "Task"] = task
                df.at[idx, "Assignee"] = assignee
                df.at[idx, "StartDate"] = start
                df.at[idx, "DueDate"] = due
                df.at[idx, "Status"] = status
                df.at[idx, "ActualHours"] = actual_hours
                df.at[idx, "EstimatedHours"] = est_hours
                df.at[idx, "NumFunctions"] = num_func
                df.at[idx, "NumTestCases"] = num_test
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

# =========================
# 進捗状況グラフ
# =========================
