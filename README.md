# Family Weather WeChat Push

个人私有项目：使用 GitHub Actions 定时获取和风天气，并通过微信公众号测试号模板消息直接发送给家人。不使用 PushPlus。

## 工作流程

GitHub Actions 定时运行 -> 和风天气 API -> 按角色生成 AI 提醒 -> 微信模板消息逐人发送。

微信只使用一套通用模板。父母、孩子、老婆、兄弟姐妹的差异由 AI 写入 `note` 字段。Gemini 未配置时使用本地备用提醒。

## 外部服务

| 服务 | 用途 | 必需 |
|---|---|---|
| 微信公众号测试号 | AppID、AppSecret、OpenID、模板消息 | 是 |
| 和风天气 | 天气、空气质量和逐小时降雨 | 是 |
| Google Gemini | 角色化 AI 天气通报 | 否 |
| GitHub Actions | 云端定时运行 | 是 |

## 微信模板

创建一套通用模板，字段名必须完全一致：

```text
first
date
name
city
weather
min_temperature
max_temperature
wind_direction
note
travel
child
remark
```

示例内容：

```text
{{first.DATA}}
日期：{{date.DATA}}
收件人：{{name.DATA}}
区域：{{city.DATA}}
天气：{{weather.DATA}}
最低温：{{min_temperature.DATA}}℃
最高温：{{max_temperature.DATA}}℃
风向风力：{{wind_direction.DATA}}
天气建议：{{note.DATA}}
出行提醒：{{travel.DATA}}
孩子提醒：{{child.DATA}}
{{remark.DATA}}
```

## GitHub Secrets

位置：`Settings -> Secrets and variables -> Actions -> New repository secret`。

| Secret | 必需 | 内容 | 示例值（均为占位符） |
|---|---|---|---|
| APP_ID | 是 | 微信测试号 AppID | `wx1234567890abcdef` |
| APP_SECRET | 是 | 微信测试号 AppSecret | `abcdef1234567890abcdef1234567890` |
| TEMPLATE_ID | 是 | 上面这套通用模板 ID | `AbCdEfGhIjKlMnOpQrStUvWxYz0123456789` |
| USER_IDS | 是 | 用户 key 到 OpenID 的 JSON 对象 | `{"parent_1":"oExampleParentOpenId"}` |
| RECIPIENTS_JSON | 是 | 家人姓名、城市和角色的 JSON 对象 | `{"recipients":[{"key":"parent_1",...}]}` |
| QWEATHER_API_KEY | 是 | 和风天气 API Key | `qweather-example-api-key` |
| QWEATHER_API_HOST | 是 | 和风天气专属 Host，不要追加 `/v7` | `https://xxx.qweather.com` |
| QWEATHER_PROJECT_ID | 否* | 和风天气项目 ID，用于签发空气质量 API 的 JWT | `qweather-example-project` |
| QWEATHER_KEY_ID | 否* | 和风天气 JWT Key ID | `qweather-example-key-id` |
| QWEATHER_PRIVATE_KEY | 否* | 和风天气 JWT 私钥，完整 PEM 内容 | `-----BEGIN PRIVATE KEY-----...` |
| GEMINI_API_KEY | 否 | Gemini API Key | `AIzaSyExampleGeminiKey` |
| GEMINI_MODEL | 否 | Gemini 模型名，默认 `gemini-2.5-flash` | `gemini-2.5-flash` |

真实密钥、OpenID 和个人配置只放 Secrets，不写进代码。

* 只有需要空气质量数据时才需要配置这三个 JWT 凭据。`QWEATHER_JWT` 不需要配置，也不能从控制台直接复制；程序会使用 Project ID、Key ID 和私钥动态生成短期 Bearer Token。

## USER_IDS

格式必须是 JSON 对象，key 要与 `RECIPIENTS_JSON` 中的 `key` 完全一致。把下面内容作为 Secret 的完整值粘贴，不要包含代码围栏：

```json
{
  "parent_1": "oExampleParentOpenId",
  "child_1": "oExampleChildOpenId",
  "spouse": "oExampleSpouseOpenId"
}
```

`oExample...` 只是占位符，必须替换成真实 OpenID。OpenID 不是微信号，也不是昵称；家人需要先关注当前测试号。暂时不发送给某人时，可以删除对应成员，或保留 key 但把值留空（程序会跳过该成员）。

## RECIPIENTS_JSON

格式：`{"recipients":[...]}`。把下面内容作为 Secret 的完整值粘贴，不要包含代码围栏；每个成员必须包含：`key`、`name`、`city_id`、`city_name`、`role`。

```json
{
  "recipients": [
    {
      "key": "parent_1",
      "name": "爸爸",
      "city_id": "101280604",
      "city_name": "深圳南山区",
      "role": "parent"
    },
    {
      "key": "child_1",
      "name": "小明",
      "city_id": "101280101",
      "city_name": "广州天河区",
      "role": "child"
    },
    {
      "key": "spouse",
      "name": "爱人",
      "city_id": "101280601",
      "city_name": "深圳福田区",
      "role": "spouse"
    }
  ]
}
```

注意：`USER_IDS` 中的 `parent_1`、`child_1`、`spouse` 必须与这里的 `key` 一一对应；`role` 只能使用 `parent`、`child`、`spouse`、`sibling`。

支持的角色：

| role | 对象 | AI 重点 |
|---|---|---|
| parent | 父母 | 体感、早晚温差、AQI、紫外线、穿衣和开窗 |
| child | 小孩 | 玩耍、补水、出汗、上下学和道路安全 |
| spouse | 老婆 | 穿衣、防晒、护肤、遮阳伞和甜蜜表达 |
| sibling | 兄弟姐妹 | 通勤、下班降雨、洗车和运动 |

深圳南山区示例城市 ID：`101280604`。其他家人只需更换 `city_id` 和 `city_name`。城市 ID 使用和风天气 LocationList 查询。

## 填写检查

1. Secret 名称必须与表格完全一致，名称和值分开填写。
2. 除 `QWEATHER_API_HOST`、`GEMINI_MODEL` 外，示例值都必须替换为你自己的真实值；不要把示例占位符直接保存。
3. `USER_IDS` 和 `RECIPIENTS_JSON` 必须是单个合法 JSON 值，使用英文双引号，最后一项后不要加逗号。
4. JSON 可以换行，但不要加入注释、Markdown 代码围栏或前后多余文字。
5. 保存后到 `Actions -> Daily Weather Push -> Run workflow` 手动运行一次，优先检查 JSON、OpenID 和模板 ID。

## AI 机制

AI 生成的详细建议会同时写入 `note` 和 `travel`，确保新旧微信模板都能显示“出行提醒”。建议会结合角色、未来降雨时段、温度、体感、风力和紫外线等事实；模型不可用时，本地规则也会根据天气生成具体建议。消息日期始终使用 `Asia/Shanghai`（东八区）。

## 定时任务

| 北京时间 | UTC cron | 模式 |
|---|---|---|
| 06:30 | `30 22 * * *` | morning |
| 11:30 | `30 3 * * *` | noon |
| 14:00 | `0 6 * * *` | afternoon |
| 22:00 | `0 14 * * *` | evening |

GitHub Actions 可能延迟几分钟。手动测试：`Actions -> Daily Weather Push -> Run workflow`。

## 本地测试

```powershell
pip install -r requirements.txt
python main.py --mode morning
python main.py --mode noon
python main.py --mode afternoon
python main.py --mode evening
```

本地运行前需要先设置与 GitHub Secrets 同名的环境变量。

## 常见错误

- `配置不完整`：检查 Secret 名称和 JSON 格式。
- `USER_IDS 缺少`：检查两个 JSON 中的 key 是否一致。
- 模板字段错误：检查模板字段名是否与上面的字段完全一致。
- `invalid openid`：检查家人是否关注当前测试号。
- 天气失败：检查天气 Key 和专属 Host。
- Gemini 失败：可暂时不配置 Gemini，程序会使用本地备用提醒。

## 安全

仓库建议设置为 Private。不要提交 `.env`、AppSecret、OpenID、真实 JSON 或真实模板信息。
