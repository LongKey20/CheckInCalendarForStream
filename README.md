# StreamerTool v2.0.3

StreamerTool 是給實況主使用的 Windows 工具，提供隊列管理與簽到月曆功能。目前支援 Twitch 聊天室，未來可擴充到 YouTube 等平台。

StreamerTool is a Windows tool for streamers. It provides queue management and a check-in calendar. Twitch chat is currently supported, with room for future platform support such as YouTube.

StreamerTool は配信者向けの Windows ツールです。キュー管理とチェックインカレンダー機能を提供します。現在は Twitch チャットに対応しており、将来的には YouTube などのプラットフォームにも拡張できます。

## 下載 / Download / ダウンロード
StreamerTool　V2.0.3　https://github.com/LongKey20/StreamerTool/releases/tag/Version-2.0.3-Release

## 功能 / Features / 機能

### 中文

- 隊列管理：手動加入、刪除、排序、叫號、顯示隊列、重播上次叫號。
- 聊天指令：排隊、顯示隊列、顯示月曆。
- 簽到月曆：同一使用者同一天只會保存一筆紀錄。
- 月曆設定可手動指定人物與月份顯示月曆。
- 黑名單可忽略常見 bot 或指定名稱，避免觸發簽到與指令。
- 啟動時可提示已開啟的 OBS / Streamlabs，方便重新整理 Browser Source。
- CSS 版本檢查會先備份，再盡量不改動原 CSS 的前提下更新必要內容。
- OBS Browser Source 分為叫號、隊列、月曆三個 URL。
- 叫號、隊列、月曆可各自選擇 CSS。
- 叫號/隊列音效與月曆簽到音效可分開設定。
- 介面語言支援中文、English、日本語。

### English

- Queue management: manual add, delete, reorder, call next, show queue, and replay last call.
- Chat commands: join queue, show queue, and show calendar.
- Check-in calendar: one saved row per user per day.
- Calendar settings can manually show a viewer calendar for a selected month.
- The blacklist can ignore common bots or specified names for check-ins and commands.
- Startup notices can detect already-running OBS / Streamlabs and remind users to refresh Browser Sources.
- CSS version checks back up files first, then apply required compatibility updates with minimal changes.
- Separate OBS Browser Source URLs for call, queue, and calendar.
- Call, queue, and calendar can each choose their own CSS.
- Queue/call sound and calendar check-in sound can be configured separately.
- Interface languages: Chinese, English, Japanese.

### 日本語

- キュー管理: 手動追加、削除、並べ替え、呼び出し、キュー表示、前回呼び出しの再表示。
- チャットコマンド: キュー参加、キュー表示、カレンダー表示。
- チェックインカレンダー: 同じユーザーは 1 日 1 件だけ保存されます。
- カレンダー設定から対象名と月を指定して手動表示できます。
- ブラックリストで一般的な bot や指定名のチェックインとコマンドを無視できます。
- 起動時に OBS / Streamlabs の起動を検出し、Browser Source の更新を促せます。
- CSS バージョン確認は先にバックアップし、元の CSS をできるだけ保ったまま必要な互換更新を行います。
- OBS Browser Source 用 URL は呼び出し、キュー、カレンダーで分かれています。
- 呼び出し、キュー、カレンダーはそれぞれ別の CSS を選択できます。
- キュー/呼び出し効果音とカレンダーチェックイン効果音を個別に設定できます。
- UI 言語は中文、English、日本語に対応しています。

## 安裝 / Installation / インストール

### 中文

1. 從 Release 下載：

   ```text
   StreamerTool-v2.0.3.exe
   ```

2. 將 exe 放到你想使用的資料夾。
3. 雙擊執行 `StreamerTool-v2.0.3.exe`。
4. 在「連接和 Log」輸入 Twitch 頻道名稱並連接。

首次啟動時會在 exe 旁建立：

```text
setting/
csv/
css/
audio/
```

### English

1. Download from Release:

   ```text
   StreamerTool-v2.0.3.exe
   ```

2. Put the exe in the folder you want to use.
3. Double-click `StreamerTool-v2.0.3.exe`.
4. Enter the Twitch channel name in Connection & Log and connect.

On first launch, these folders are created beside the exe:

```text
setting/
csv/
css/
audio/
```

### 日本語

1. Release からダウンロードします:

   ```text
   StreamerTool-v2.0.3.exe
   ```

2. exe を使用したいフォルダーに置きます。
3. `StreamerTool-v2.0.3.exe` をダブルクリックします。
4. 「接続とログ」で Twitch チャンネル名を入力して接続します。

初回起動時、exe の横に以下のフォルダーが作成されます:

```text
setting/
csv/
css/
audio/
```

## OBS 設定 / OBS Setup / OBS 設定

### 中文

預設 Host 是 `127.0.0.1`，預設 Port 是 `18080`。

在 OBS 新增 Browser Source，並填入需要的 URL：

```text
叫號: http://127.0.0.1:18080/call
隊列: http://127.0.0.1:18080/queue
月曆: http://127.0.0.1:18080/calendar
```

實際 URL 可在「一般設定」中複製，也可按預覽。

### English

Default host is `127.0.0.1`, and default port is `18080`.

Add Browser Sources in OBS and use the needed URLs:

```text
Call:     http://127.0.0.1:18080/call
Queue:    http://127.0.0.1:18080/queue
Calendar: http://127.0.0.1:18080/calendar
```

The actual URLs can be copied from General Settings, and preview buttons are available.

### 日本語

標準ホストは `127.0.0.1`、標準ポートは `18080` です。

OBS に Browser Source を追加し、必要な URL を入力します:

```text
呼び出し: http://127.0.0.1:18080/call
キュー:   http://127.0.0.1:18080/queue
カレンダー: http://127.0.0.1:18080/calendar
```

実際の URL は「一般設定」からコピーでき、プレビューボタンも使用できます。

## 使用方法 / How to Use / 使い方

### 中文

1. 開啟 StreamerTool。
2. 在「連接和 Log」連接頻道。
3. 在 OBS 加入需要的 Browser Source。
4. 開台期間保持 StreamerTool 開啟。
5. 收台後可關閉 StreamerTool。

### English

1. Open StreamerTool.
2. Connect to the channel in Connection & Log.
3. Add the needed Browser Sources in OBS.
4. Keep StreamerTool open while streaming.
5. Close StreamerTool after the stream ends.

### 日本語

1. StreamerTool を開きます。
2. 「接続とログ」でチャンネルに接続します。
3. OBS に必要な Browser Source を追加します。
4. 配信中は StreamerTool を開いたままにします。
5. 配信終了後、StreamerTool を閉じます。

## 介面分頁 / UI Tabs / UI タブ

### 中文

1. 連接和 Log：平台連接與執行 Log。
2. 隊列管理：手動管理隊列、接受排隊、叫號、顯示隊列。
3. 一般設定：語言、時區、Port、OBS Source URL。
4. 指令設定：排隊指令、顯示隊列指令、顯示月曆指令。
5. 黑名單：新增或刪除要忽略的名稱。
6. 隊列設定：叫號文字、顯示秒數、隊列顯示數量、音效、Call/Queue CSS。
7. 月曆設定：月曆顯示秒數、星期文字、CSV 前綴、Calendar CSS、簽到音效、月曆文字模板、手動顯示月曆。

### English

1. Connection & Log: platform connection and runtime log.
2. Queue: manual queue operations, accept queue toggle, call next, show queue.
3. General Settings: language, timezone, port, and OBS Source URLs.
4. Command Settings: join queue commands, show queue commands, show calendar commands.
5. Blacklist: add or remove names to ignore.
6. Queue Settings: call text, display duration, queue display count, sound, Call/Queue CSS.
7. Calendar Settings: calendar duration, weekday text, CSV prefix, Calendar CSS, check-in sound, calendar text templates, manual calendar display.

### 日本語

1. 接続とログ: プラットフォーム接続と実行ログ。
2. キュー: 手動キュー操作、キュー受付、呼び出し、キュー表示。
3. 一般設定: 言語、タイムゾーン、ポート、OBS Source URL。
4. コマンド設定: キュー参加コマンド、キュー表示コマンド、カレンダー表示コマンド。
5. ブラックリスト: 無視する名前の追加と削除。
6. キュー設定: 呼び出し文、表示秒数、キュー表示数、効果音、Call/Queue CSS。
7. カレンダー設定: カレンダー表示秒数、曜日表示、CSV 接頭辞、Calendar CSS、チェックイン効果音、カレンダーテキスト、手動カレンダー表示。

## 指令 / Commands / コマンド

### 中文

預設指令：

```text
排隊: !排隊, !join, !queue, !参加
顯示隊列: !隊列, !list, !queue-list, !キュー
顯示月曆: !月曆, !calendar, !カレンダー
```

月曆指令可指定月份：

```text
!月曆 2026-07
```

使用任何指令都不會簽到。

### English

Default commands:

```text
Join queue: !排隊, !join, !queue, !参加
Show queue: !隊列, !list, !queue-list, !キュー
Show calendar: !月曆, !calendar, !カレンダー
```

The calendar command can specify a month:

```text
!calendar 2026-07
```

Using any command does not count as calendar check-in.

### 日本語

標準コマンド:

```text
キュー参加: !排隊, !join, !queue, !参加
キュー表示: !隊列, !list, !queue-list, !キュー
カレンダー表示: !月曆, !calendar, !カレンダー
```

カレンダーコマンドでは月を指定できます:

```text
!calendar 2026-07
```

どのコマンドを使ってもチェックインにはなりません。

## 時區 / Timezone / タイムゾーン

### 中文

StreamerTool 使用 UTC 偏移，不使用 IANA timezone。

可使用範例：

```text
UTC+8
UTC+9
+1
-6
+5:30
UTC-4
```

選擇 `Other / Custom` 時，右側會出現 `UTC Offset` 輸入框。

### English

StreamerTool uses UTC offsets instead of IANA timezone names.

Examples:

```text
UTC+8
UTC+9
+1
-6
+5:30
UTC-4
```

When selecting `Other / Custom`, a `UTC Offset` input appears on the right.

### 日本語

StreamerTool は IANA タイムゾーン名ではなく UTC オフセットを使用します。

例:

```text
UTC+8
UTC+9
+1
-6
+5:30
UTC-4
```

`Other / Custom` を選ぶと、右側に `UTC Offset` 入力欄が表示されます。

## 顯示秒數 / Display Duration / 表示秒数

### 中文

叫號、隊列、月曆的顯示秒數都遵循：

```text
0 = 常駐顯示
```

大於 0 時以秒為單位自動隱藏。

### English

Call, queue, and calendar display durations follow this rule:

```text
0 = keep visible
```

Values above 0 auto-hide after that many seconds.

### 日本語

呼び出し、キュー、カレンダーの表示秒数は以下のルールです:

```text
0 = 常時表示
```

0 より大きい値は、その秒数後に自動で非表示になります。

## 月曆 CSV / Calendar CSV / カレンダー CSV

### 中文

CSV 會保存到：

```text
csv/
```

欄位：

```text
date, username, displayName, timestamp, isFirst
```

同一使用者同一天只會保存一筆紀錄。Avatar 不會保存到 CSV，會由 overlay 即時讀取：

```text
https://unavatar.io/twitch/{username}
```

### English

CSV files are saved to:

```text
csv/
```

Columns:

```text
date, username, displayName, timestamp, isFirst
```

Each user is saved at most once per day. Avatar URLs are not saved in CSV and are loaded by the overlay:

```text
https://unavatar.io/twitch/{username}
```

### 日本語

CSV は以下に保存されます:

```text
csv/
```

列:

```text
date, username, displayName, timestamp, isFirst
```

同じユーザーは 1 日 1 件だけ保存されます。アバター URL は CSV に保存されず、overlay が読み込みます:

```text
https://unavatar.io/twitch/{username}
```

## CSS 主題 / CSS Themes / CSS テーマ

### 中文

Runtime CSS 資料夾：

```text
css/call/
css/queue/
css/calendar/
```

叫號、隊列、月曆可各自選擇 CSS。

CSS 會使用版本標記檢查相容性。若目前選用的 CSS 沒有版本標記或版本較舊，程式會詢問是否自動更新。自動更新會先備份到各資料夾的 `backup/`，再盡量不改動原 CSS 的前提下加入必要相容內容。

```text
css/call/backup/
css/queue/backup/
css/calendar/backup/
```

### English

Runtime CSS folders:

```text
css/call/
css/queue/
css/calendar/
```

Call, queue, and calendar can each choose their own CSS.

CSS compatibility is checked with a version marker. If the selected CSS has no marker or an older version, StreamerTool asks whether to update it. Auto update backs up the file into that area's `backup/` folder, then applies only the required compatibility changes while preserving the original CSS as much as possible.

```text
css/call/backup/
css/queue/backup/
css/calendar/backup/
```

### 日本語

実行時 CSS フォルダー:

```text
css/call/
css/queue/
css/calendar/
```

呼び出し、キュー、カレンダーはそれぞれ CSS を選択できます。

CSS はバージョン表記で互換性を確認します。選択中の CSS に表記がない、または古い場合、StreamerTool は更新するか確認します。自動更新では各フォルダーの `backup/` に先にバックアップし、元の CSS をできるだけ保ったまま必要な互換内容だけを追加します。

```text
css/call/backup/
css/queue/backup/
css/calendar/backup/
```

## 音效 / Audio / 効果音

### 中文

Runtime 音效資料夾：

```text
audio/
```

選擇的音效會複製到此資料夾。預設音效是：

```text
audio/default.mp3
```

叫號/隊列音效與月曆簽到音效可分開設定。

### English

Runtime audio folder:

```text
audio/
```

Selected sound files are copied into this folder. The default sound is:

```text
audio/default.mp3
```

Queue/call sound and calendar check-in sound can be configured separately.

### 日本語

実行時音声フォルダー:

```text
audio/
```

選択した効果音はこのフォルダーにコピーされます。標準効果音:

```text
audio/default.mp3
```

キュー/呼び出し効果音とカレンダーチェックイン効果音は別々に設定できます。

## v2.0.3 更新重點 / v2.0.3 Highlights / v2.0.3 更新点

### 中文

- 月曆設定新增手動顯示月曆，可指定人物與月份。
- 改善跨日與長時間閒置後的聊天室連線恢復。
- 啟動時可偵測 OBS / Streamlabs 是否已開啟，並提示重新整理 Browser Source。
- CSS 加入版本檢查；自動更新會先備份，再以最小必要改動補上相容內容。

### English

- Calendar Settings can manually show a calendar for a selected name and month.
- Improved recovery after day changes and long idle chat connections.
- Startup can detect already-running OBS / Streamlabs and remind users to refresh Browser Sources.
- CSS version checks were added. Auto update backs up files first, then applies only the required compatibility changes.

### 日本語

- カレンダー設定で対象名と月を指定して手動表示できるようになりました。
- 日付変更後や長時間アイドル後のチャット接続復帰を改善しました。
- 起動時に OBS / Streamlabs の起動を検出し、Browser Source の更新を促せます。
- CSS バージョン確認を追加しました。自動更新は先にバックアップし、必要な互換更新だけを行います。

## 打包 / Build / ビルド

### 中文

Release 打包前請先關閉正在執行的 StreamerTool。

```powershell
python -m py_compile .\StreamerTool.py
python -m PyInstaller --noconfirm --clean .\StreamerTool.spec
Copy-Item .\dist\StreamerTool.exe .\dist\StreamerTool-v2.0.3.exe -Force
```

### English

Close running StreamerTool processes before building a release.

```powershell
python -m py_compile .\StreamerTool.py
python -m PyInstaller --noconfirm --clean .\StreamerTool.spec
Copy-Item .\dist\StreamerTool.exe .\dist\StreamerTool-v2.0.3.exe -Force
```

### 日本語

Release ビルド前に実行中の StreamerTool を閉じてください。

```powershell
python -m py_compile .\StreamerTool.py
python -m PyInstaller --noconfirm --clean .\StreamerTool.spec
Copy-Item .\dist\StreamerTool.exe .\dist\StreamerTool-v2.0.3.exe -Force
```

## 授權 / License / ライセンス

### 中文

程式碼採用 GPLv3，請參閱 `LICENSE`。

預設音效來源為 Pixabay，音效授權與 GPLv3 程式碼授權分開。不要將內建音效作為獨立音效檔重新散佈、轉售或挪作其他用途。

### English

Source code is licensed under GPLv3. See `LICENSE`.

The default audio is sourced from Pixabay. Audio licensing is separate from the GPLv3 source code license. Do not redistribute, resell, or use the bundled audio as standalone audio files outside StreamerTool.

### 日本語

ソースコードは GPLv3 ライセンスです。`LICENSE` を参照してください。

標準効果音は Pixabay 由来です。音声ライセンスは GPLv3 のソースコードライセンスとは別です。内蔵効果音を StreamerTool 外で単独の音声ファイルとして再配布、販売、使用しないでください。
