# Command-Maker
コマンドの作成、実行、保存ができる、PythonのGUIアプリケーションです。  
何度も同じコマンドを実行する際や、引数のファイルパスをいちいち入力するのが面倒な場合を想定して作成しました。 
全画面非対応(実行可能ですがサイズ調整等は行われません)

## 基本画面
![image](https://github.com/gengithub17/Command-Maker/assets/25129056/f8c47794-caa2-4ec9-92a2-f68657bb8269)
- Name : コマンドを保存する際の名前
- pwd  : コマンドを実行するパス(フォルダ選択可能)
- Command : 実行するコマンド名(実行ファイル選択可能)
- Arg : コマンドの引数(フラグ)
- Arg Value : 引数(フラグ)に値を設定する場合に追加(ファイル選択可能)

### 各種操作
一部操作には、ショートカットキーが割り当てられています。 
保存データは、名前の重複不可。
- Save As(⌘/Ctrl + Shift + S) : 新規保存
- Save(⌘/Ctrl + S) : 上書き保存
- Open(⌘/Ctrl + O) : 保存したデータを開く
- Clear(⌘/Ctrl + R) : データのクリア
- Execute(⌘/Ctrl + Enter/Return) : コマンドの実行
- Copy(⌘/Ctrl + C) : コマンドをクリップボードにコピー
- Rel Path : pwdから見た相対パスに変換(存在するファイルに対してのみ適用されます。)
- extend : アプリ内コンソールを開きます。

## 保存データ管理画面
![image](https://github.com/gengithub17/Command-Maker/assets/25129056/dbb4871e-a8bb-4486-ac21-8f00f0dd2922)
- Back : 基本画面に戻ります。
- Edit : コマンド名編集画面に移ります。
- Delete : 選択されたコマンドデータを削除します。
- Copy : 選択されたコマンドデータを複製します。
- Select All : 現在表示中のコマンド全てを選択します。
画面右上のボタンにより、表示するコマンドを変更できます。

### コマンド名編集画面
![image](https://github.com/gengithub17/Command-Maker/assets/25129056/82c92f95-0856-4339-8970-2a1e8aa521c6)
保存されているコマンドデータの保存名を変更できます。  
OKボタンを押すことにより変更が保存されます。
