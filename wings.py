import streamlit as st
import sqlite3
import pandas as pd
import os
import datetime

icon = 'favicon.ico'
st.set_page_config(
    page_title="Wings TC",
    page_icon=icon,
    layout="centered",
)
# データベースファイル名
DB_FILE = 'event.db'

# データベース接続関数
def get_connection():
    conn = sqlite3.connect(DB_FILE)
    return conn

# データベースとテーブルを初期化する関数
def initialize_database():
    # データベースに接続
    conn = get_connection()
    c = conn.cursor()
    
    # テーブルを作成（テーブルがない場合のみ）
    c.execute( 'CREATE TABLE IF NOT EXISTS list (id INTEGER PRIMARY KEY AUTOINCREMENT,date TEXT NOT NULL UNIQUE, start INTEGER NOT NULL,end INTEGER NOT NULL,place TEXT NOT NULL)' )    
    c.execute( 'CREATE TABLE IF NOT EXISTS action (id INTEGER PRIMARY KEY AUTOINCREMENT,event_id INTEGER NOT NULL,member_name TEXT NOT NULL,status TEXT NOT NULL,comment TEXT )'
	)
    c.execute( 'CREATE TABLE IF NOT EXISTS member (id INTEGER PRIMARY KEY AUTOINCREMENT,name TEXT NOT NULL)'
	)

    # 変更を保存し接続を閉じる
    conn.commit()
    conn.close()
    

# listデータをデータベースに保存する関数
def save_list(date, start, end, place):
    conn = get_connection()
    c = conn.cursor()
    query = f"INSERT INTO list (date, start, end, place) VALUES ('{date}',{start},{end},'{place}')"
    try:
        c.execute( query )
        st.success('スケジュールを追加しました')
    	# そして actionテーブルに人数分の row を作る　(event_id, member_name, status, comment)
        query = f"SELECT * FROM list WHERE date = '{date}'"
        c.execute( query )
        #c.execute('SELECT * FROM list WHERE date = ?',(date,))
        list_tp = c.fetchall()
        event_id = list_tp[0][0]
        #st.write('list_tp[0]= ',list_tp[0],'list_tp[0][0]',list_tp[0][0])
        c.execute(f"SELECT * FROM member")
        data = c.fetchall()
        for d in data:
            query = f"INSERT INTO action (event_id, member_name, status, comment) VALUES ({event_id}, '{d[1]}', '--未定--', '')"
            c.execute( query )
            #c.execute("INSERT INTO action (event_id, member_name, status, comment) VALUES (?, ?, ?, ?)", ( event_id, d[1], '--未定--', ' ' ))

        conn.commit()
        conn.close()
        st.success('action table を追加しました',icon="✅")
    except sqlite3.IntegrityError as e:
        st.exception(e)
# メンバーを追加する
def save_member(namae):
    conn = get_connection()
    c = conn.cursor()
    c.execute(f"INSERT INTO member (name) VALUES ('{namae}')")
    # action データの作成
    today=datetime.datetime.today().date()
    query = f"SELECT id FROM list WHERE date >= '{today}' ORDER BY date"
    c.execute( query )
    data = c.fetchall()    
    for row in data:
        query = f"INSERT INTO action (event_id, member_name, status, comment) VALUES ({row[0]}, '{namae}', '--未定--', '')"
        c.execute( query )

    conn.commit()
    conn.close()
    st.write('追加しました')

# データを取得する関数
def show_list():
	conn = get_connection()
	c = conn.cursor()
	c.execute('SELECT * FROM list')
	data = c.fetchall()
	for d in data:
		st.write(d)
	conn.close()    
def show_action():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM action')
    data = c.fetchall()
    for d in data:
        st.write(d)
    conn.close()
def show_member():
    conn = get_connection()
    c = conn.cursor()
    c.execute('SELECT * FROM member')
    data = c.fetchall()
    for d in data:
        st.write(d)
    conn.close()

#================================================================================
# listデータを取得する関数
def get_list_now():
    conn = get_connection()
    today=datetime.datetime.today().date()
    query = f"SELECT * FROM list WHERE date >= '{today}' ORDER BY date"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

#@st.cache_resource
def get_action_row( event_id ):
    conn = get_connection()
    #query = "SELECT id,member_name,status,comment FROM action WHERE event_id={}".format(event_id)
    query = f"SELECT id, member_name, status, comment FROM action WHERE event_id={event_id}"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def update_action( id, status, comment ):
    conn = get_connection()
    c = conn.cursor()
    query = f"UPDATE action SET status='{status}', comment='{comment}' WHERE id={id}"
    c.execute( query )
    #c.execute("UPDATE action SET status=?, comment=? WHERE id=?", (status, comment, id))
    conn.commit()
    conn.close()
#===============================================================================
def del_member(dname):
    conn = get_connection()
    c = conn.cursor()
    # memberテーブルから削除
    # DELETE FROM テーブル WHERE カラム = 値 ;
    query = f"DELETE FROM member WHERE name = '{dname}'"
    c.execute( query )
    # actionテーブルを削除
    c.execute( f"DELETE FROM action WHERE member_name = '{dname}' " )
    conn.commit()
    conn.close()
    st.write('削除しました')
    st.cache_resource.clear()

def del_list(date):
    conn = get_connection()
    c = conn.cursor()
    query = f"SELECT id FROM list WHERE date='{date}'"
    c.execute( query )
    list_id = c.fetchall()
    event_id = list_id[0][0] # to delete in action table
    # list テーブル   から削除
    c.execute(f"DELETE FROM list WHERE date = '{date}'")
    # action テーブルから削除
    c.execute(f"DELETE FROM action WHERE event_id = {event_id}")
    conn.commit()
    conn.close()
    st.write('削除しました')    

def disp_action(dic_row, df):
	selected_row = dic_row[0]
	event_id = df.iloc[selected_row]['id']
	date = df.iloc[selected_row]['date']
	start = df.iloc[selected_row]['start']
	end = df.iloc[selected_row]['end']
	place = df.iloc[selected_row]['place']

	st.subheader("参加状況")
	this_event = "年月日：{}　　時間：{}  ~ {}　　場所：{}".format(date,start,end,place)
	st.write( this_event )

	df = get_action_row( event_id )
	status = ['🔵', ' ✖️ ', '--未定--']
	config = {
	'member_name' : st.column_config.TextColumn( '名前',  required=True),
	'status' : st.column_config.SelectboxColumn('参加状況', options=status, required=True),
	'comment' : st.column_config.TextColumn( 'コメント', width='large')
	}
	st.session_state["data"] = st.data_editor(df, column_config = config, hide_index=True, height=418, column_order=('member_name','status','comment')) # 11x38 pic?
	ids = st.session_state["data"]['id']
	status = st.session_state["data"]['status']
	comment = st.session_state["data"]['comment']
	# 保存とキャッシュクリア
	if st.button("変更を保存"):
		for i,id in enumerate(ids,0):
			update_action( id, status[i], comment[i] )
		#st.cache_resource.clear()
		#st.rerun()

def del_database():
	conn = get_connection()
	conn.execute('DROP TABLE IF EXISTS list')
	conn.execute('DROP TABLE IF EXISTS action')
	conn.execute('DROP TABLE IF EXISTS member')
	conn.commit()
	st.success('データを削除しました')
# -----------------------( 開始 )--------------------------
# アプリの起動時にデータベースを初期化
initialize_database()

st.header(":green[WINGS テニスクラブ] :tennis:")

# Sidebarの選択肢を定義する
options = ["スケジュール", "管理者用", "DEBUG用"]
choice = st.sidebar.selectbox("Select an option", options)

# Mainコンテンツの表示を変える
if choice == "スケジュール":
	st.subheader("スケジュール")
	# 登録されたistの今日以降を表示
	list_df = get_list_now()
	df = pd.DataFrame(list_df)
	config = {
	'date' : st.column_config.TextColumn( '年月日'),
	'start' : st.column_config.NumberColumn( '開始', width='small'),
	'end' : st.column_config.NumberColumn( '終了', width='small'),
	'place' : st.column_config.TextColumn( '場所', width='medium')
	}
	event = st.dataframe(
   		df,
   		on_select='rerun',
   		selection_mode='single-row',
   		hide_index=True,
   		column_config=config,
   		column_order=('date', 'start', 'end', 'place')
#   		height=418
	)
	st.caption("出欠の表明やメンバーの参加状況を見るには")
	st.markdown("左端の:red[セルをクリック]して下さい")
	st.markdown('''
	---
	'''	
	)
	#####################################
	# そしてここに action table を表示する
	#####################################

	# event.selection['rows'] の返り値は辞書で　{0:0} {0:1} のような形
	if len(event.selection['rows']):
		disp_action( event.selection['rows'], df )
	else:
		try:
			disp_action( {0:0}, df )
		except:
			st.subheader(":red[まだデータがありません] :skull:")
	st.write("参加状況（出欠）を変更したりコメントを記入するには")
	st.write("該当のセルを:red[２度クリック] し　「変更を保存」ボタンを押して下さい")
	
elif choice == "管理者用":
#	emoji = ":tennis:" + " :x:" + " :large_blue_circle:" + " :heavy_multiplication_x:" + " :streamlit:"
#	st.write( emoji )
	st.subheader(":streamlit: 新規スケジュールの入力")
	# スケジュールの追加
	date = st.date_input('年月日')
	start = st.number_input('開始時刻', value=None)
	end = st.number_input('終了時刻', value=None)
	place = st.text_input('場所')
	if st.button('スケジュールを追加します'):
		save_list(date, start, end, place)
	# スケジュールの削除
	st.subheader(":streamlit: スケジュールの削除")
	date_list = st.date_input('削除する年月日')
	if st.button('スケジュールを削除します'):	
		del_list(date_list)

	st.markdown('''
	---
	''')
	st.subheader(":streamlit: メンバーの追加")
	namae = st.text_input('名前')
	if st.button('名前を追加します'):
		save_member(namae)
	st.subheader(":streamlit: メンバーの削除")
	dname = st.text_input('削除する名前')
	if st.button('削除'):
		del_member(dname)
	st.markdown('''
	---
	''')

	st.write(":no_entry_sign: すべてのデータの削除")
	if st.button("すべてのデータの削除"):
	# 確認メッセージを表示する
		if st.warning('本当にデータを削除しますか？この操作は取り消せません。'):
			del_database()
else:
	st.header("DEBUGのためのページ")
	show_list()
	show_action()
	show_member()

