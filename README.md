# Family Weather WeChat Push

个人私有项目：使用 GitHub Actions 定时获取和风天气，并直接通过微信公众号测试号模板消息发送给家人。不使用 PushPlus 等第三方推送中转服务。

## 功能

- 北京时间每天 06:30 早安推送、22:00 晚安推送
- 微信直连：AppID、AppSecret、模板消息接口
- 角色模板：父母、孩子、老婆、兄弟姐妹
- 每位家人独立配置 OpenID、姓名、城市和角色
- 同一城市只请求一次天气
- Gemini 可选；未配置时使用内置提醒

## 配置原则

所有个人信息和密钥都通过环境变量提供，不写入代码：

- `APP_ID`、`APP_SECRET`：微信测试号凭据
- `TEMPLATE_ID_PARENT`、`TEMPLATE_ID_CHILD`、`TEMPLATE_ID_SPOUSE`、`TEMPLATE_ID_SIBLING`：四套模板 ID
- `USER_IDS`：用户 key 到 OpenID 的 JSON 对象
- `RECIPIENTS_JSON`：姓名、城市、角色的 JSON 对象
- `QWEATHER_API_KEY`、`QWEATHER_API_HOST`：天气服务配置
- `GEMINI_API_KEY`、`GEMINI_MODEL`：可选 AI 提醒配置

`USER_IDS` 和 `RECIPIENTS_JSON` 不要提交到仓库。GitHub 私有仓库中建议将它们作为 Repository Secrets。变量格式见 `.env.example`。

## 收件人配置

`RECIPIENTS_JSON` 示例：

```json
{"recipients":[{"key":"parent_1","name":"父亲","city_id":"101280604","city_name":"深圳南山区","role":"parent"},{"key":"parent_2","name":"母亲","city_id":"101280604","city_name":"深圳南山区","role":"parent"},{"key":"child_1","name":"孩子1","city_id":"101280604","city_name":"深圳南山区","role":"child"},{"key":"child_2","name":"孩子2","city_id":"101280604","city_name":"深圳南山区","role":"child"},{"key":"spouse","name":"老婆","city_id":"101280604","city_name":"深圳南山区","role":"spouse"},{"key":"sibling","name":"兄弟姐妹","city_id":"101280604","city_name":"深圳南山区","role":"sibling"}]}
```

`USER_IDS` 示例：

```json
{"parent_1":"OPENID_1","parent_2":"OPENID_2","child_1":"OPENID_3","child_2":"OPENID_4","spouse":"OPENID_5","sibling":"OPENID_6"}
```

## 微信模板字段

四套模板建议使用相同字段键：

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

## 本地运行

```powershell
pip install -r requirements.txt
$env:APP_ID = "..."
$env:APP_SECRET = "..."
$env:USER_IDS = "{...}"
$env:RECIPIENTS_JSON = "{...}"
python main.py --mode morning
```

## GitHub Actions

Workflow 文件为 `.github/workflows/schedule.yml`。在私有仓库 `Settings -> Secrets and variables -> Actions` 配置 `.env.example` 中的变量。

- `22:30 UTC` 对应北京时间 `06:30`
- `14:00 UTC` 对应北京时间 `22:00`
- cron 可能延迟数分钟
- 可在 Actions 页面手动运行测试

## 安全

不要提交 `.env`、微信密钥、OpenID、个人 JSON 配置或真实模板 ID。
