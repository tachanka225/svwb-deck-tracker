import streamlit as st
import pandas as pd
import os
import json

# --- 設定 ---
DATA_FILE = 'deck_data.csv'
PRESETS_FILE = 'presets.json'
MAX_CARD_COPIES = 9
MAX_DECK_SIZE = 99

# カードの種類と対応する背景色
CARD_TYPES = {
    "フォロワー": "#FF9800", # はっきりしたオレンジ
    "スペル": "#81D4FA",     # 水色
    "アミュレット": "#FFF59D"  # 黄色
}

# --- データ読み込み・保存関数 ---
def load_deck():
    if os.path.exists(DATA_FILE):
        df = pd.read_csv(DATA_FILE)
        if 'CardType' not in df.columns:
            df['CardType'] = 'フォロワー'
        return df
    else:
        return pd.DataFrame(columns=['CardName', 'CardType', 'Count'])

def save_deck(df):
    df.to_csv(DATA_FILE, index=False)

def load_presets():
    if os.path.exists(PRESETS_FILE):
        with open(PRESETS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_presets(presets):
    with open(PRESETS_FILE, 'w', encoding='utf-8') as f:
        json.dump(presets, f, ensure_ascii=False, indent=2)

# --- メイン処理 ---
def main():
    st.title("SVWB デッキトラッカー")

    # セッションステートの初期化
    if 'deck_df' not in st.session_state:
        st.session_state.deck_df = load_deck()

    df = st.session_state.deck_df
    current_total = df['Count'].sum() if not df.empty else 0

    # ==========================================
    # サイドバー：デッキプリセット管理
    # ==========================================
    st.sidebar.header("💾 デッキの保存・読込")
    presets = load_presets()

    # デッキ保存フォーム
    with st.sidebar.form("save_preset_form", clear_on_submit=True):
        preset_name = st.text_input("保存するデッキ名")
        submitted = st.form_submit_button("現在のデッキを保存")
        
        if submitted:
            if not preset_name:
                st.error("デッキ名を入力してください。")
            elif len(presets) >= 5 and preset_name not in presets:
                st.error("保存できるデッキは5つまでです。不要なデッキを削除してください。")
            else:
                # 現在のDataFrameを辞書型に変換して保存
                presets[preset_name] = df.to_dict(orient='records')
                save_presets(presets)
                st.success(f"「{preset_name}」を保存しました！")
                st.rerun()

    st.sidebar.divider()
    
    # 保存済みデッキの一覧と操作
    st.sidebar.markdown("**保存済みデッキ一覧**")
    if not presets:
        st.sidebar.caption("保存されたデッキはありません。")
    else:
        for p_name, p_data in presets.items():
            st.sidebar.markdown(f"📦 **{p_name}**")
            col1, col2 = st.sidebar.columns(2)
            with col1:
                if st.button("読込", key=f"load_{p_name}", use_container_width=True):
                    loaded_df = pd.DataFrame(p_data)
                    save_deck(loaded_df)
                    st.session_state.deck_df = loaded_df
                    st.rerun()
            with col2:
                if st.button("削除", key=f"del_p_{p_name}", use_container_width=True):
                    del presets[p_name]
                    save_presets(presets)
                    st.rerun()
            st.sidebar.write("") # 見栄えのための余白

    # ==========================================
    # メイン画面：ヘッダー・特殊処理・追加
    # ==========================================
    st.markdown(f"### 現在のデッキ枚数: **{current_total} / {MAX_DECK_SIZE}**")

    st.header("特殊処理")
    sp_col1, sp_col2 = st.columns(2)
    with sp_col1:
        if st.button("試練の石板を発動", type="primary"):
            if not df.empty:
                df.loc[df['Count'] >= 2, 'Count'] = 1
                save_deck(df)
                st.session_state.deck_df = df
                st.rerun()
    with sp_col2:
        st.caption("※ここに将来的な特殊効果ボタンを追加予定")

    st.divider()

    st.header("カード追加")
    with st.form("add_card_form", clear_on_submit=True):
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            new_card_name = st.text_input("カード名")
        with col2:
            new_card_type = st.selectbox("種類", list(CARD_TYPES.keys()))
        with col3:
            new_card_count = st.number_input("枚数", min_value=1, max_value=MAX_CARD_COPIES, value=1)
        
        submitted = st.form_submit_button("追加")
        
        if submitted and new_card_name:
            if current_total + new_card_count > MAX_DECK_SIZE:
                st.error(f"エラー: デッキの上限({MAX_DECK_SIZE}枚)を超えてしまいます。")
            else:
                if new_card_name in df['CardName'].values:
                    idx = df.index[df['CardName'] == new_card_name][0]
                    if df.at[idx, 'Count'] + new_card_count > MAX_CARD_COPIES:
                        st.error(f"エラー: 「{new_card_name}」が上限の{MAX_CARD_COPIES}枚を超えてしまいます。")
                    else:
                        df.at[idx, 'Count'] += new_card_count
                        df.at[idx, 'CardType'] = new_card_type
                        save_deck(df)
                        st.session_state.deck_df = df
                        st.rerun()
                else:
                    new_row = pd.DataFrame({'CardName': [new_card_name], 'CardType': [new_card_type], 'Count': [new_card_count]})
                    df = pd.concat([df, new_row], ignore_index=True)
                    save_deck(df)
                    st.session_state.deck_df = df
                    st.rerun()

    st.divider()

    # ==========================================
    # デッキ表示・操作エリア
    # ==========================================
    st.header("デッキ情報")
    if not df.empty:
        for c_type, bg_color in CARD_TYPES.items():
            
            # エリアのタイトルを色付きで表示（文字色は白等にして見やすく）
            text_color = "#FFFFFF" if c_type == "フォロワー" else "#333333"
            st.markdown(
                f"<div style='background-color: {bg_color}; padding: 10px; border-radius: 5px; margin-bottom: 15px;'>"
                f"<h4 style='margin: 0; color: {text_color};'>{c_type}</h4>"
                f"</div>",
                unsafe_allow_html=True
            )
            
            type_df = df[df['CardType'] == c_type]
            
            if not type_df.empty:
                cols = st.columns(4)
                for i, (index, row) in enumerate(type_df.iterrows()):
                    col = cols[i % 4]
                    with col:
                        # 各カードをコンテナで囲む
                        with st.container(border=True):
                            count = row['Count']
                            
                            # 色の判定（0なら赤、1なら黄色、それ以外はデフォルト）
                            if count == 0:
                                name_color = "#FF5252" # 赤色
                            elif count == 1:
                                name_color = "#FFC107" # 見やすい黄色（アンバー）
                            else:
                                name_color = "inherit" # デフォルト色
                            
                            # タイトルと×ボタンを横並びにする
                            c_title, c_del = st.columns([4, 1])
                            with c_title:
                                st.markdown(f"<span style='color:{name_color}; font-weight:bold; font-size:1.1em;'>{row['CardName']}</span>", unsafe_allow_html=True)
                            with c_del:
                                # コンテナ右上の削除（×）ボタン
                                if st.button("×", key=f"del_{index}"):
                                    df = df.drop(index).reset_index(drop=True)
                                    save_deck(df)
                                    st.session_state.deck_df = df
                                    st.rerun()

                            st.write(f"残り: **{count}** 枚")
                            
                            # ＋・ーボタン
                            b_col1, b_col2 = st.columns(2)
                            with b_col1:
                                if st.button("＋", key=f"plus_{index}", use_container_width=True):
                                    if count < MAX_CARD_COPIES and current_total < MAX_DECK_SIZE:
                                        df.at[index, 'Count'] += 1
                                        save_deck(df)
                                        st.session_state.deck_df = df
                                        st.rerun()
                            with b_col2:
                                if st.button("ー", key=f"minus_{index}", use_container_width=True):
                                    if count > 0:
                                        df.at[index, 'Count'] -= 1
                                        save_deck(df)
                                        st.session_state.deck_df = df
                                        st.rerun()
            else:
                st.caption(f"登録されている{c_type}はありません。")
                
            st.markdown("<br>", unsafe_allow_html=True) # エリア間の余白
    else:
        st.info("現在デッキにカードが登録されていません。上のフォームから追加してください。")

if __name__ == '__main__':
    main()