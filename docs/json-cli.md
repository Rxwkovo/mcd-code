# CLI JSON 接口 v1

所有已有业务命令都可通过 `--json` 调用。终端模式不变；JSON 模式不播放动画/声音，不输出横幅、提示符或 ANSI。程序不会从人类可读卡片反向解析数据。

```bash
python mcd.py --json --command "/budget 30"
python mcd.py --json "/奶蛙 预算30 --card"
python mcd.py --json
```

前两种每次输出一个 JSON 对象；第三种保持一个进程，从 stdin 接收逐行命令，stdout 每条命令立即返回一行 JSON（JSONL）。命令文件也每条命令一行 JSON。JSON 内字符串里的换行经过转义，不会拆开对象。UTF-8 编码。

## 公共字段

| 字段 | 类型与含义 |
| --- | --- |
| `schema_version` | integer，当前为 1；不兼容变更会升级 |
| `ok` | boolean，该命令是否成功处理；空候选不等于全菜单无解 |
| `mode` | 正式入口固定 `live`；缺少或失效 `MCD_TOKEN` 报认证错误，不返回演示数据 |
| `command` | string，原始命令，Token 已脱敏 |
| `data` | object，各命令业务字段，见下表；未知值为 `null`，列表可为空 |
| `messages` | string array，辅助说明；Agent 不从这些文本提取业务字段 |
| `artifacts` | array，导出物；SVG 含 `type/path/date/width/height/mode/price_cents/character_id/character_name`，path 为本机绝对路径 |
| `confirmation_required` | boolean，当前会话是否有待确认操作 |
| `preview` | object 或 null；含 `operation_id/code/tool/arguments/summary/expires_at`，过期时间为 Unix 秒 |
| `error` | null 或 `{code, message}`；安全脱敏的错误 |
| `running` | boolean，`/exit`、`/quit` 后 false |

状态码：单次/文件全成功退出 0，有业务失败退出 1，启动参数错误退出 2。常驻模式每条结果以 `ok` 为准，可继续查询；EOF/退出会放弃未执行预览。空行返回成功的空 `data`，没有 MCP 调用。没有启动时的隐式状态请求。

稳定错误码：`INVALID_ARGUMENTS`、`DATA_ERROR`、`LOCATION_ERROR`、`AUTH_ERROR`、`RATE_LIMITED`、`TRANSPORT_ERROR`、`MCP_ERROR`、`CONFIRMATION_ERROR`、`IO_ERROR`。未知/非有限数字使用 null，不输出 NaN。`raw` 与原样工具字段仅作为上游信息，不承诺其 Schema 不变。

## 业务字段

已选店时各业务命令额外包含 `data.store` 和 `data.context`，保留接口原字段（如 `storeCode`）。商品列表中 `productCode/quantity` 保持下单参数字段；展示名为 `name`。菜单规范化字段为 `product_code/name/category/kcal`。

| 命令 | 主要 `data` 字段 |
| --- | --- |
| `/help` | `commands` |
| `/status` | `account`、`coupons`、`available_coupon_count`；权限信息取不到为 null |
| `/events`、`/tools` | `events`、`tools` |
| `/location`、`/location 城市 地标` | `location`（city/keyword/source） |
| `/order 搜店 城市 地标`、`/order 得来速 城市 地标`、`/order 外送店` | `stores` |
| `/order 门店 序号` | `store`、`context` |
| `/order 菜单`、`/order 详情 CODE` | `menu`、`detail` |
| `/order 加 CODE 数量`、`/order 用券 序号 券序号`、`/order 清空` | `cart` |
| `/order 算价`、`/pick 序号` | `quote`（items/price_cents/price_source/raw） |
| `/order 地址`、`/order 选地址 序号` | `addresses`、`selected_address` |
| `/order 查单 ID`、`/order 历史` | `order`、`orders` |
| `/coupons 可领`、`/coupons 已有`、`/coupons 门店` | `coupons`、`kind`；已有券含 pages_read/total_pages/total_count |
| `/budget 金额`、`/奶蛙 [预算金额] [--card]` | `recommendations`（报价数组）、`budget_cents/target_cents/delta_cents/quote_count/failure_count`；无目标的目标/差值为 null |
| `/1024 24`、`/1024 102.4` | 同上；`delta_cents` 为实际减目标的有符号整数分 |
| `/1024 热量` | `recommendations`（报价额外含 kcal/delta_kcal/achieved）、`target_kcal/tolerance_kcal` |
| `/1024 积分` | `products/points/target_points/delta_points`；points 未知为 null |
| `/1024` | `modes` |
| `/points`、`/points 详情 SPU_ID` | `products`、`detail` |
| `/成就`、`/achievements` | `achievements`；没有宿主记录时为 null |
| `/偏好`、`/preferences` 及记住/忘掉/暂停/恢复/清空 | `preferences`（schema_version/enabled/notes/order_choices，保存后有 updated_at）；详见 [偏好说明](preferences.md) |
| `/order 下单`、`/order 取消`、`/coupons 领取`、`/points 兑换` | 使用公共 `preview`，`confirmation_required=true`；不执行写操作 |
| `/confirm 当前确认码` | 成功时 `operation/result`；点餐创建且有订单标识时另含 `app_hint`（app/entry/message）、`preference_recorded`（bool），记忆保存失败另含 `preference_warning`；失败用公共 error |
| `/abort`、`/quit`、`/exit` | 无业务字段；预览变 null，退出时 running=false |

## 确认保持同进程

Host 启动 `python mcd.py --json` 后保留 stdin/stdout。用户请求预览时发送对应命令，读取 `preview`；展示该操作和金额，**等待用户对这次操作明确同意之后**，才向同一进程发送 `/confirm <code>`。禁止预先自动确认。

两个独立 `--command` 进程不能共享待确认对象。宿主不能保持进程时只执行只读或预览，并让用户在终端完成确认。没有 `--yes`，不持久化待确认内容，不修改 SQLite 防重网关；过期、改店、改购物车和重复确认的原有检查全部保留。

## 静态日卡

`/奶蛙 --card 预算30` 或 `/奶蛙 预算30 --card` 导出当前第一推荐方案。读取当前门店菜单和成功 `calculate-price` 的同一 Quote；金额不是本地单品相加。图片 1080×1440，内嵌本地 PNG，无脚本、无远程加载，按 UTC+08 日期保存到 `outputs/nawa-YYYY-MM-DD.svg`；正式输出只使用真实菜单与成功官方报价。同日同模式再次导出会原子替换该文件。

只有带券且官方返回明确正优惠额时才标“券后价”；没有选券标“未用券”，选券但优惠情况未知则如实说明。无成功报价/无预算内候选不导出成功卡。导出不改变购物车、不下单，也不确认任何交易。

日卡使用 `assets/characters/` 全部 11 种形象，以日期序数按顺序循环；11 天覆盖一次，每个角色有对应趣味吐槽，同日同角色。角色轮换不改变实际选餐或官方价格。
