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
AI 专属提醒：{{note.DATA}}
{{remark.DATA}}
```

## GitHub Secrets

位置：`Settings -> Secrets and variables -> Actions -> New repository secret`。

| Secret | 必需 | 内容 |
|---|---|---|
| APP_ID | 是 | 微信测试号 AppID |
| APP_SECRET | 是 | 微信测试号 AppSecret |
| TEMPLATE_ID | 是 | 上面这套通用模板 ID |
| USER_IDS | 是 | 用户 key 到 OpenID 的 JSON 对象 |
| RECIPIENTS_JSON | 是 | 家人姓名、城市和角色的 JSON 对象 |
| QWEATHER_API_KEY | 是 | 和风天气 API Key |
| QWEATHER_API_HOST | 是 | 和风天气专属 Host |
| GEMINI_API_KEY | 否 | Gemini API Key |
| GEMINI_MODEL | 否 | Gemini 模型名，默认 `gemini-2.5-flash` |

真实密钥、OpenID 和个人配置只放 Secrets，不写进代码。

## USER_IDS

格式必须是 JSON 对象，key 要与 `RECIPIENTS_JSON` 中的 key 完全一致：

```json
{"parent_1":"OPENID_1","parent_2":"OPENID_2","child_1":"OPENID_3","child_2":"OPENID_4","spouse":"OPENID_5","sibling":"OPENID_6"}
```

OpenID 不是微信号，也不是昵称。家人需要先关注当前测试号。

## RECIPIENTS_JSON

格式：`{"recipients":[...]}`。每个成员必须包含：`key`、`name`、`city_id`、`city_name`、`role`。

支持的角色：

| role | 对象 | AI 重点 |
|---|---|---|
| parent | 父母 | 体感、早晚温差、AQI、紫外线、穿衣和开窗 |
| child | 小孩 | 玩耍、补水、出汗、上下学和道路安全 |
| spouse | 老婆 | 穿衣、防晒、护肤、遮阳伞和甜蜜表达 |
| sibling | 兄弟姐妹 | 通勤、下班降雨、洗车和运动 |

深圳南山区示例城市 ID：`101280604`。其他家人只需更换 `city_id` 和 `city_name`。城市 ID 使用和风天气 LocationList 查询。

## AI 机制

AI 只生成 `note`，不会改写结构化天气字段。模型会收到姓名、角色、地点、温度、体感、湿度、风向、AQI、空气质量、紫外线和未来降雨信息，并按角色生成 80 到 180 字的中文通报。缺失数据不得编造。

## 定时任务

| 北京时间 | UTC cron | 模式 |
|---|---|---|
| 06:30 | `30 22 * * *` | morning |
| 22:00 | `0 14 * * *` | evening |

GitHub Actions 可能延迟几分钟。手动测试：`Actions -> Daily Weather Push -> Run workflow`。

## 本地测试

```powershell
pip install -r requirements.txt
python main.py --mode morning
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
