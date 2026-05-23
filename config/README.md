# Config README

## timeZone / 時區

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
