# calmana 評価用プログラム

## Summary
+ 本システムは [calmana](https://github.com/nakazono0424/calmana) の評価用プログラムである．
+ ユーザによる修正を考慮した予測結果と考慮しない予測結果をそれぞれ実際に予定が行われた実施日と比較し，その差分を累積したグラフを表示する．

## Requirements
+ Python 3.X
+ heron-Rust
  + https://github.com/nakazono0424/heron-Rust

## Install heron-Rust
1. `$ git clone git@github.com:nakazono0424/heron-Rust.git`
1. `$ cd heron-Rust`
1. `$ cargo build --release`

## Install calmana_eval
### Install using venv(recommend)
```
$ git clone git@github.com:nakazono0424/calmana_env.git
$ cd calmana_env
$ python3 -m venv .venv
$ source .venv/bin/activate
(.venv) $ pip install -r requirements.txt
```

## Settings
+ google calendar の予定に extended properties としてリカーレンスを付与
+ コード中の `heron_path` に heron のパスを記述
  + `Settings.yml`に書いて読み込むようにする．

## Run
```
$ python calmana_env.py -c [calendar ID] -y [forecast year] -r [recurrence name]
```
### オプション引数
```
-h, --help            show this help message and exit
-c, --calendar        Google Calendar ID
-y, --year            get event year
-r, --recurrence      recurrence name
```