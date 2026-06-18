# CheckInCalendarForStream

Let streamers show a check-in calendar for their audience.  
讓實況主能為他們的觀眾展示簽到日曆。

## Download 下載
[Version-1.0.0](https://github.com/LongKey20/CheckInCalendarForStream/releases/tag/Version-1.0.0-Release)

## Installation/How to use 安裝/使用方法
### 安裝方法
1. 在Release中下載TwitchCanlendar-{版本號}.exe的檔案
2. 放到你想要的位置
3. 執行TwitchCanlendar-{版本號}.exe
4. 根據要求輸入你Twitch 頻道的名稱, 通常為你的頻道URL: https://www.twitch.tv/{channel} 的channel部份。設定檔會自動保存在config/目錄下, 如有需要可手動編輯
5. 關閉程式(也可不關閉, 直接使用)
6. 在OBS中新增來源瀏覽器
7. 網址輸入http://127.0.0.1:8000 (預設), 寬高可自由設定, 若使用預設theme, 建議比例為1比1
8. 把新生成的來源移動/調整到你想要的大小即可
完成

### Installation
1. Download the TwitchCanlendar-{version}.exe file in Release.
2. Put it into the folder you like.
3. Double click TwitchCanlendar-{version}.exe
4. Follow the instruction, enter the name of your twitch channel. You may check the URL of your channel: https://www.twitch.tv/{channel} It will be the {channel} parts
5. Close the program (or keep it open)
6. Add the source in OBS
7. Enter http://127.0.0.1:8000 (Default) in Link, you may custom the size of it. If you are using the default theme, ratio 1:1 is recommended.
8. Move the source to the position you like.
Done

### 使用方法
1. 執行TwitchCanlendar-{版本號}.exe
2. 把打開的頁面縮放(不要關閉)
3. 在OBS中開啟直播即可
4. 直播完畢可關閉程式

### How to use
1. Double click TwitchCanlendar-{version}.exe
2. Minimize it(Do not close it).
3. Start the stream by OBS
4. You can close the program when your stream is over.

## Configuration / 設定

設定檔位於 `config/` 目錄，首次執行時會自動建立。

The Configuration file is placed in `config/`. It will be created when you execute the file first time.

### timeZone / 時區

`client_config.json` 的 `timeZone` 欄位使用 IANA time zone 名稱。

The `timeZone` field in `client_config.json` uses an IANA time zone name.

請填入完整的時區名稱，例如：

Enter the full time zone name, for example:

```json
"timeZone": "Asia/Tokyo"
```

常用時區範例 / Common time zones:

| 地區 / Region | timeZone |
| --- | --- |
| 東京 / 日本 / Tokyo / Japan | `Asia/Tokyo` |
| 台灣 / Taiwan | `Asia/Taipei` |
| 中國 / China | `Asia/Shanghai` |
| 香港 / Hong Kong | `Asia/Hong_Kong` |
| 韓國 / South Korea | `Asia/Seoul` |
| 新加坡 / Singapore | `Asia/Singapore` |
| 美國東部 / US Eastern | `America/New_York` |
| 美國西部 / US Pacific | `America/Los_Angeles` |
| 英國 / United Kingdom | `Europe/London` |

更多可用時區可以參考：

For more available time zones, see:

https://en.wikipedia.org/wiki/List_of_tz_database_time_zones

### Theme / 主題

`client_config.json` 的 `style` 欄位指定主題，可更換其他主題。

The `style` field in `client_config.json` can select the theme of the calendar.

### Command / 指令

`command.json` 內可自行設置觸發指令的文字。

You can set the trigger of the command in `command.json`.

1. ShowCalendarCommand:
   顯示月曆
   Show Calendar

## ⚖️ License & Third-Party Assets / 開源授權與第三方素材

### Code License / 程式碼授權
This project is open-source software licensed under the **GNU General Public License v3.0 (GPLv3)**. Please see the [LICENSE](LICENSE) file for the full text.  
本專案原始碼採用 **GNU 通用公共授權條款第三版 (GPLv3)** 開源，完整條款請參閱 [LICENSE](LICENSE) 檔案。

---

### Third-Party Audio Assets Notice / 第三方音效素材聲明

This project includes Pixabay-sourced audio under the **Pixabay Content License**. The same files may appear in more than one place:

* **Source repository**: the `audio/` directory in this Git repository (for development and reference).
* **GitHub Release assets**: the versioned assets zip attached to each release (for example `CheckInCalendar-assets-0.0.3.zip`). On first run, the application may download and extract this zip so that `audio/` exists next to the executable.

Regardless of how you obtained the files, the restrictions below apply to all copies.

本專案的音效素材源自 [Pixabay](https://pixabay.com)，遵循 **Pixabay Content License**。相同檔案可能出現在以下位置：

* **原始碼庫**：本 Git 儲存庫內的 `audio/` 資料夾（供開發與參考）。
* **GitHub Release 資源包**：各版本 Release 所附的 assets 壓縮檔（例如 `CheckInCalendar-assets-0.0.3.zip`）。程式首次執行時可能會下載並解壓，在執行檔旁建立 `audio/`。

無論從上述哪一種方式取得，均適用下列限制。

* **Standalone Distribution Prohibited**: These audio files are bundled strictly for the functional use of this application. In compliance with Pixabay's terms, you are **strictly prohibited** from extracting, redistributing, reselling, or using these audio files standalone for any other purposes.
* **License Separation**: The GPLv3 license of this project applies **ONLY** to the source code and does not extend to the Pixabay audio assets.

* **禁止獨立散佈**：這些音效檔案僅供本應用程式執行功能使用。根據 Pixabay 服務條款，**嚴禁將音效單獨擷取、重新分發、轉售或挪作他用**（不論來自 repo 的 `audio/` 或 Release 資源包）。
* **授權獨立性**：本專案採用的 GPLv3 條款**僅適用於程式碼**，並不包含、也不延伸至 Pixabay 的音效素材。

See also `audio/README.md` in the repository and inside the release assets zip.
另請參閱儲存庫與 Release 資源包內的 `audio/README.md`。

