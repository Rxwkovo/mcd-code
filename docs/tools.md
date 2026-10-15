# MCP 真实工具目录

- tools/list 捕获时间：`2026-10-15T11:19:52.8156059+08:00`。
- 实际连接端点：`https://mcp.mcd.cn`。
- 服务端：`mcd-mcp`，版本 `1.0.0`。
- 实际返回 **35 个工具**；本文件读取到 **13 个工具的本地响应结构**。
- 完整工具描述、输入及输出 Schema：[原始 tools/list 捕获](tool-schemas.json)。

本文件的工具列表表示服务器可用能力，不表示 CLI 已实现或已真实执行每个工具。实际命令接入情况见 [MCP_INTEGRATION.md](../MCP_INTEGRATION.md)。

**证据区分：**输入及输出声明表来自 tools/list 的 Schema；“实际观察字段”只来自另行保存的本地探测响应。声明字段不等于调用成功，未探测工具不冒充已验证。观察仅记录路径与类型，不包含 Token、用户标识值、地址、手机号、订单、支付链接或响应示例值。

**结构展示限制：**单个 Schema 最多展示 240 行、12 层，完整字段以原始捕获为准；响应观察每个数组最多抽样 64 个元素、共 240 条字段路径。空数组或 null 只能证明此次响应形态；未出现的字段不能推定不存在。动态映射键及未知字段名统一写成 `{key}`，避免把标识值误写为字段名。

## 与旧资料的差异

- 活动门店日期、场次的真实名称为 `query-party-store-date`、`query-party-store-session`，使用实际清单名称。
- 当前清单还包含 `query-meal-assistance`、`query-promotions`、`query-survey-coupon`；不根据旧文章推断工具是否存在。
- 响应中实际观察到 `success`、`datetime` 等封装字段；部分工具的 outputSchema 未完整声明这些公共封装字段。
- `list-nutrition-foods` 的 `data` 声明为 string，实测也是字符串，内部采用 `[n]{字段名,...}:` 加 CSV 行的 TOON 形式。不能直接当作 JSON 餐品数组。热量等字段缺失或无法精确对应餐品规格时显示“未知”。
- 工具的描述文字可能列出业务必需条件，而 inputSchema.required 较少；执行时必须同时遵守业务条件，不能只看 required 表。

## 实际工具名

1. [`auto-bind-coupons`](#auto-bind-coupons)
2. [`available-coupons`](#available-coupons)
3. [`calculate-price`](#calculate-price)
4. [`campaign-calendar`](#campaign-calendar)
5. [`cancel-order`](#cancel-order)
6. [`create-order`](#create-order)
7. [`delivery-create-address`](#delivery-create-address)
8. [`delivery-query-addresses`](#delivery-query-addresses)
9. [`delivery-query-stores`](#delivery-query-stores)
10. [`draw-lottery`](#draw-lottery)
11. [`list-nutrition-foods`](#list-nutrition-foods)
12. [`mall-create-order`](#mall-create-order)
13. [`mall-order-detail`](#mall-order-detail)
14. [`mall-order-list`](#mall-order-list)
15. [`mall-points-products`](#mall-points-products)
16. [`mall-product-detail`](#mall-product-detail)
17. [`now-time-info`](#now-time-info)
18. [`order-list`](#order-list)
19. [`party-order-create`](#party-order-create)
20. [`query-lottery-info`](#query-lottery-info)
21. [`query-meal-assistance`](#query-meal-assistance)
22. [`query-meal-detail`](#query-meal-detail)
23. [`query-meals`](#query-meals)
24. [`query-my-account`](#query-my-account)
25. [`query-my-coupons`](#query-my-coupons)
26. [`query-my-prizes`](#query-my-prizes)
27. [`query-nearby-stores`](#query-nearby-stores)
28. [`query-order`](#query-order)
29. [`query-party-city`](#query-party-city)
30. [`query-party-store`](#query-party-store)
31. [`query-party-store-date`](#query-party-store-date)
32. [`query-party-store-session`](#query-party-store-session)
33. [`query-promotions`](#query-promotions)
34. [`query-store-coupons`](#query-store-coupons)
35. [`query-survey-coupon`](#query-survey-coupon)

## auto-bind-coupons

自动领取麦麦省所有当前可用的麦当劳优惠券。无需指定具体的优惠券和couponId，系统会自动领取用户可领的所有券。当用户说"帮我领券"、"自动领取优惠券"、"一键领券"时使用此工具。

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 自动领券结果响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object（隐式） | 否 | 领券结果数据 |
| $.data.failedCount | integer | 否 | 领取失败数量 |
| $.data.failedCoupons | array | 否 | 领取失败的优惠券列表 |
| $.data.failedCoupons[] | object | — |  |
| $.data.failedCoupons[].couponId | string | 是 | 优惠券ID |
| $.data.failedCoupons[].couponName | string | 是 | 优惠券名称 |
| $.data.failedCoupons[].reason | string | 否 | 失败原因 |
| $.data.successCount | integer | 否 | 成功领取数量 |
| $.data.successCoupons | array | 否 | 成功领取的优惠券列表 |
| $.data.successCoupons[] | object | — |  |
| $.data.successCoupons[].couponCode | string | 否 | 优惠券码 |
| $.data.successCoupons[].couponId | string | 是 | 优惠券ID |
| $.data.successCoupons[].couponImage | string | 否 | 优惠券图片URL |
| $.data.successCoupons[].couponName | string | 是 | 优惠券名称 |
| $.data.totalCount | integer | 否 | 优惠券总数 |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## available-coupons

查询用户当前可领取的麦麦省的优惠券列表。返回券名称、图片、状态和促销标签。当用户询问有什么优惠、可以领什么券时使用此工具。

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 优惠券列表响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | array | 是 | 优惠券列表 |
| $.data[] | object | — |  |
| $.data[].couponImage | string | 否 | 优惠券图片URL |
| $.data[].couponName | string | 是 | 优惠券名称 |
| $.data[].couponStatus | string | 是 | 优惠券状态 |
| $.data[].label | string | 是 | 状态标签文本 |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | array |
| $.data[] | object |
| $.data[].couponName | string |
| $.data[].couponImage | string |
| $.data[].couponStatus | string |
| $.data[].label | string |

## calculate-price

Description: 计算商品的价格（含优惠），支持到店自提(orderType=1)和外送(orderType=2)两种场景 When： - 用户问"这些商品多少钱" - 用户问"总价是多少" Input: - reservationDate: 预约场景必传，非预约场景不传。格式: yyyy-MM-dd HH:mm - storeCode: 门店编码 - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取） - items: 商品列表（数组） - productCode: 商品编码，必填 - quantity: 商品数量，必填，大于等于1 - couponId: 优惠券ID，选填（如果用户要使用优惠券） - couponCode: 优惠券编码，选填（如果用户要使用优惠券） - mod…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，从query-nearby-stores或delivery-query-stores返回结果中获取。得来速(beType=5)/外送(orderType=2)/团餐场景必传，到店自取(beType=1)场景不传 |
| $.beType | integer | 是 | 1-到店取餐，2-麦乐送到家，5-得来速(DT)，6-企业团餐；枚举 [1,2,5,6] |
| $.gmServiceCode | string | 否 | 团餐-助餐服务码 |
| $.items | array | 否 | 待价格计算的商品列表 |
| $.items[] | object | — |  |
| $.items[].couponCode | string | 否 | 优惠券code |
| $.items[].couponId | string | 否 | 优惠券Id |
| $.items[].modification | object | 否 | 商品特制选项 |
| $.items[].modification.values | array | 否 | 特制选项列表 |
| $.items[].modification.values[] | object | — |  |
| $.items[].modification.values[].code | string | 否 | 特制code |
| $.items[].modification.values[].key | string | 否 | 特制key |
| $.items[].modification.values[].quantity | integer | 否 | 特制数量 |
| $.items[].productCode | string | 否 | 商品code |
| $.items[].quantity | integer | 否 | 数量，必填，不能为空，且大于等于1 |
| $.items[].roundList | array | 否 | 套餐子项 |
| $.items[].roundList[] | object | — |  |
| $.items[].roundList[].comboItemList | array | 否 | 套餐套餐round下商品 |
| $.items[].roundList[].comboItemList[] | object | — |  |
| $.items[].roundList[].comboItemList[].code | string | 否 | 商品编码 |
| $.items[].roundList[].comboItemList[].modification | object | 否 | 商品特制选项 |
| $.items[].roundList[].comboItemList[].modification.values | array | 否 | 特制选项列表 |
| $.items[].roundList[].comboItemList[].modification.values[] | object | — |  |
| $.items[].roundList[].comboItemList[].modification.values[].code | string | 否 | 特制code |
| $.items[].roundList[].comboItemList[].modification.values[].key | string | 否 | 特制key |
| $.items[].roundList[].comboItemList[].modification.values[].quantity | integer | 否 | 特制数量 |
| $.items[].roundList[].comboItemList[].quantity | integer | 否 | 商品数量 |
| $.items[].roundList[].round | string | 否 | 套餐round |
| $.needTableware | boolean | 否 | 是否需要餐具，true需要，false不需要 |
| $.orderType | integer | 是 | 订单类型，1-到店（含到店自取+得来速车道取餐），2-外送（含麦乐送+企业团餐）；枚举 [1,2] |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式:yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |
| $.withOrder | object | 否 | 随单购商品 |
| $.withOrder.cardId | string | 否 | 随单购卡id |
| $.withOrder.cardType | integer | 否 | 随单购卡类型 |
| $.withOrder.membershipCode | string | 否 | 随单购会员code |
| $.withOrder.membershipSpecId | string | 否 | 随单购规格id |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.deliveryOriginalPrice | integer | 否 | 运费原价 单位分 |
| $.data.deliveryPrice | integer | 否 | 运费现价 单位分 |
| $.data.discount | integer | 否 | 优惠金额 单位分 |
| $.data.enjoyable | object | 否 | 可享受的优惠 |
| $.data.enjoyable.amountType | string | 否 | 1 特价 2 折扣 3 立减 |
| $.data.enjoyable.balance | integer | 否 | 门槛差额(可享受的优惠时才有值)，单位分 |
| $.data.enjoyable.realDiscount | number | 否 | 实际优惠值  特价(ex:18)  折扣（ex:7.5） 立减(ex:5)  金额单位是元 与discount区别计算了tender |
| $.data.enjoyed | object | 否 | 已享受的优惠 |
| $.data.enjoyed.amountType | string | 否 | 1 特价 2 折扣 3 立减 |
| $.data.enjoyed.balance | integer | 否 | 门槛差额(可享受的优惠时才有值)，单位分 |
| $.data.enjoyed.realDiscount | number | 否 | 实际优惠值  特价(ex:18)  折扣（ex:7.5） 立减(ex:5)  金额单位是元 与discount区别计算了tender |
| $.data.mealAssistanceList | array | 否 | 可选的助餐服务列表 |
| $.data.mealAssistanceList[] | object | — |  |
| $.data.mealAssistanceList[].code | string | 否 | 助餐服务编码 |
| $.data.mealAssistanceList[].name | string | 否 | 助餐服务名称 |
| $.data.originalPrice | integer | 否 | 原价 单位分 |
| $.data.packingOriginalPrice | integer | 否 | 打包费原价 单位分 |
| $.data.packingPrice | integer | 否 | 打包费现价 单位分 |
| $.data.price | integer | 否 | 现价 单位分 |
| $.data.productList | array | 否 | 商品列表 |
| $.data.productList[] | object | — |  |
| $.data.productList[].originalSubtotal | integer | 否 | 商品原小计 单位分 |
| $.data.productList[].productCode | string | 否 | 商品编码 |
| $.data.productList[].productName | string | 否 | 商品名称 |
| $.data.productList[].quantity | integer | 否 | 数量 |
| $.data.productList[].subtotal | integer | 否 | 商品小计 单位分 |
| $.data.productOriginalPrice | integer | 否 | 商品原价 单位分 |
| $.data.productPrice | integer | 否 | 商品现价 单位分 |
| $.data.tablewarePrice | integer | 否 | 餐具费现价 单位分 |
| $.data.takeWayList | array | 否 | 可选的取餐方式选项列表 |
| $.data.takeWayList[] | object | — |  |
| $.data.takeWayList[].code | string | 否 | 取餐方式code，到店下单时需要携带 |
| $.data.takeWayList[].subtitle | string | 否 | 取餐方式副标题 |
| $.data.takeWayList[].title | string | 否 | 取餐方式标题 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

已观察到响应字段结构，但该结构本身不能证明业务成功；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.data | object |
| $.data.productOriginalPrice | integer |
| $.data.productPrice | integer |
| $.data.originalPrice | integer |
| $.data.discount | integer |
| $.data.price | integer |
| $.data.productList | array |
| $.data.productList[] | object |
| $.data.productList[].productCode | string |
| $.data.productList[].productName | string |
| $.data.productList[].quantity | integer |
| $.data.productList[].originalSubtotal | integer |
| $.data.productList[].subtotal | integer |
| $.data.takeWayList | array |
| $.data.takeWayList[] | object |
| $.data.takeWayList[].code | string |
| $.data.takeWayList[].title | string |
| $.data.takeWayList[].subtitle | string |

## campaign-calendar

查询麦当劳中国当月的营销活动日历，返回进行中、往期和未来日期的活动。适用于查看用户进行中和即将到来的可参与活动，还可查询用户对活动的订阅状态。 When： - 用户问"最近有什么活动"、"这个月有什么优惠活动"、"有什么可以参加的" - 用户想查看品鉴会、主题派对等活动信息

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.specifiedDate | string | 否 | 可选的查询基准日期（格式：yyyy-MM-dd）；若传入，则以该日为锚点，返回当天及时间线上与其最邻近的前后各一个有活动的日子（共三天）；若不填，默认返回当前月所有活动 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 活动日历响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object | 是 | 活动日历数据 |
| $.data.currentTime | string | 否 | 当前时间 |
| $.data.dailyList | array | 否 | 每日活动列表 |
| $.data.dailyList[] | object | — |  |
| $.data.dailyList[].date | string | 否 | 日期 (yyyy-MM-dd) |
| $.data.dailyList[].dateText | string | 否 | 日期文案 |
| $.data.dailyList[].events | array | 否 | 事件列表 |
| $.data.dailyList[].events[] | object | — |  |
| $.data.dailyList[].events[].activityBgImg | string | 否 | 活动事件背景图 |
| $.data.dailyList[].events[].activitySubTitle | string | 否 | 活动副标题 |
| $.data.dailyList[].events[].activityTitle | string | 否 | 活动事件标题 |
| $.data.dailyList[].events[].articleDto | object | 否 | 文章信息 |
| $.data.dailyList[].events[].articleDto.content | string | 否 | 内容 |
| $.data.dailyList[].events[].articleDto.imgList | array | 否 | 图片列表 |
| $.data.dailyList[].events[].articleDto.imgList[] | string | — |  |
| $.data.dailyList[].events[].articleDto.title | string | 否 | 标题 |
| $.data.dailyList[].events[].couponImage | string | 否 | 优惠券图片 |
| $.data.dailyList[].events[].couponInfo | object | 否 | 优惠券信息 |
| $.data.dailyList[].events[].couponInfo.couponCode | string | 否 | 券Code |
| $.data.dailyList[].events[].couponInfo.couponId | string | 否 | 券ID |
| $.data.dailyList[].events[].couponInfo.isAllTradeTime | integer | 否 | 是否全天可用: 0-否, 1-是 |
| $.data.dailyList[].events[].couponInfo.tradeEndDate | string | 否 | 核销结束日期 |
| $.data.dailyList[].events[].couponInfo.tradeStartDate | string | 否 | 核销开始日期 |
| $.data.dailyList[].events[].couponInfo.tradeTimePeriods | array | 否 | 核销时间段 |
| $.data.dailyList[].events[].couponInfo.tradeTimePeriods[] | object | — |  |
| $.data.dailyList[].events[].couponInfo.tradeTimePeriods[].endTime | string | 否 | 结束时间 |
| $.data.dailyList[].events[].couponInfo.tradeTimePeriods[].startTime | string | 否 | 开始时间 |
| $.data.dailyList[].events[].couponInfo.weekdays | array | 否 | 核销日周几限制 (1-周日, 2-周一, ..., 7-周六) |
| $.data.dailyList[].events[].couponInfo.weekdays[] | integer | — |  |
| $.data.dailyList[].events[].eventType | integer | 否 | 事件类型: 0-活动, 1-神秘期活动, 2-优惠券, 3-品鉴会, 4-CMS文章, 5-麦麦省, 6-派对 |
| $.data.dailyList[].events[].price | string | 否 | 价格 |
| $.data.dailyList[].today | boolean | 否 | 是否是当天 |
| $.data.subscribedEvents | array | 否 | 已订阅的活动列表 |
| $.data.subscribedEvents[] | object | — |  |
| $.data.subscribedEvents[].activityBgImg | string | 否 | 活动事件背景图 |
| $.data.subscribedEvents[].activitySubTitle | string | 否 | 活动副标题 |
| $.data.subscribedEvents[].activityTitle | string | 否 | 活动事件标题 |
| $.data.subscribedEvents[].articleDto | object | 否 | 文章信息 |
| $.data.subscribedEvents[].couponImage | string | 否 | 优惠券图片 |
| $.data.subscribedEvents[].couponInfo | object | 否 | 优惠券信息 |
| $.data.subscribedEvents[].eventType | integer | 否 | 事件类型: 2-优惠券, 3-品鉴会, 6-派对 |
| $.data.subscribedEvents[].price | string | 否 | 价格 |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.currentTime | string |
| $.data.dailyList | array |
| $.data.dailyList[] | object |
| $.data.dailyList[].date | string |
| $.data.dailyList[].dateText | string |
| $.data.dailyList[].events | array |
| $.data.dailyList[].events[] | object |
| $.data.dailyList[].events[].activityCode | string |
| $.data.dailyList[].events[].{key} | integer / object / string |
| $.data.dailyList[].events[].eventType | integer |
| $.data.dailyList[].events[].activityTitle | string |
| $.data.dailyList[].events[].price | string |
| $.data.dailyList[].events[].activitySubTitle | string |
| $.data.dailyList[].events[].{key}.status | integer |
| $.data.dailyList[].events[].{key}.text | string |
| $.data.dailyList[].events[].{key}.{key} | integer / string |
| $.data.dailyList[].events[].articleDto | object |
| $.data.dailyList[].events[].articleDto.title | string |
| $.data.dailyList[].events[].articleDto.content | string |
| $.data.dailyList[].events[].articleDto.imgList | array |
| $.data.dailyList[].events[].articleDto.imgList[] | string |
| $.data.dailyList[].events[].articleDto.{key} | integer / string |
| $.data.dailyList[].today | boolean |
| $.data.subscribedEvents | array |

## cancel-order

Description: 取消订单，非商城订单 When： - 用户说"取消订单"、"我要取消" - 用户说"帮我取消一下订单" Input: - cancelReasonCode: 取消原因code，必填，可选值：1=改主意了, 2=重复下单, 3=点错了/点多了/点少了, 4=地址/电话填错了, 5=送达时间选错了, -1=其它原因 Next： - 提示用户"订单已取消"

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.cancelReasonCode | string | 是 | 取消原因code，默认为1 |
| $.orderId | string | 是 | 订单号 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.cancelResult | boolean | 否 | 取消结果 |
| $.data.orderId | string | 否 | 订单号 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## create-order

Description: 创建麦当劳订单，支持到店(orderType=1)和外送(orderType=2)两种场景下单, 必须先确定订单类型，必填 (1：到店，2外送) When： - 用户说"我要下单" - 用户说"创建订单" Input: - addressId: 配送地址ID， orderType=2时必填 - storeCode: 必填 - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取） - takeWayCode: orderType=1时必传，取值来自 calculate-price 返回的 data.takeWayList[].code - reservationDate: 预约场景必传，非预约场景不传。格式: yyyy-MM-dd HH:mm - items: 商品…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.addressId | string | 否 | 配送地址id，外送or团餐的地址 |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，从query-nearby-stores或delivery-query-stores返回结果中获取。得来速(beType=5)/外送(orderType=2)/团餐场景必传，到店自取(beType=1)场景不传 |
| $.beType | integer | 是 | 1-到店取餐，2-麦乐送到家，5-得来速(DT)，6-企业团餐；枚举 [1,2,5,6] |
| $.gmServiceCode | string | 否 | 企业团餐场景(beType=6)下，必传，参数来自query-meal-assistance |
| $.items | array | 否 | 待价格计算的商品列表 |
| $.items[] | object | — |  |
| $.items[].couponCode | string | 否 | 优惠券code |
| $.items[].couponId | string | 否 | 优惠券Id |
| $.items[].modification | object | 否 | 商品特制选项 |
| $.items[].modification.values | array | 否 | 特制选项列表 |
| $.items[].modification.values[] | object | — |  |
| $.items[].modification.values[].code | string | 否 | 特制code |
| $.items[].modification.values[].key | string | 否 | 特制key |
| $.items[].modification.values[].quantity | integer | 否 | 特制数量 |
| $.items[].productCode | string | 否 | 商品code |
| $.items[].quantity | integer | 否 | 数量 |
| $.items[].roundList | array | 否 | 套餐子项 |
| $.items[].roundList[] | object | — |  |
| $.items[].roundList[].comboItemList | array | 否 | 套餐套餐round下商品 |
| $.items[].roundList[].comboItemList[] | object | — |  |
| $.items[].roundList[].comboItemList[].code | string | 否 | 商品编码 |
| $.items[].roundList[].comboItemList[].modification | object | 否 | 商品特制选项 |
| $.items[].roundList[].comboItemList[].modification.values | array | 否 | 特制选项列表 |
| $.items[].roundList[].comboItemList[].modification.values[] | object | — |  |
| $.items[].roundList[].comboItemList[].modification.values[].code | string | 否 | 特制code |
| $.items[].roundList[].comboItemList[].modification.values[].key | string | 否 | 特制key |
| $.items[].roundList[].comboItemList[].modification.values[].quantity | integer | 否 | 特制数量 |
| $.items[].roundList[].comboItemList[].quantity | integer | 否 | 商品数量 |
| $.items[].roundList[].round | string | 否 | 套餐round |
| $.needTableware | boolean | 否 | 是否需要餐具，true需要，false不需要 |
| $.orderType | integer | 是 | 订单类型，1-到店（含到店自取+得来速车道取餐），2-外送（含麦乐送+企业团餐）；枚举 [1,2] |
| $.remark | string | 否 | 订单备注（选填，最多50字），如"无接触配送"，仅orderType=2场景下需要引导用户填写 |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式:yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |
| $.takeWayCode | string | 否 | 到店/得来速场景(orderType=1)必传，外送/团餐场景(orderType=2)不传。值从 calculate-price 返回的takeWayList[].code 中选取 |
| $.withOrder | object | 否 | 随单购商品 |
| $.withOrder.cardId | string | 否 | 随单购卡id |
| $.withOrder.cardType | integer | 否 | 随单购卡类型 |
| $.withOrder.membershipCode | string | 否 | 随单购OMM code |
| $.withOrder.membershipSpecId | string | 否 | 随单购OMM 规格id |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.orderDetail | object | 否 | 订单详情 |
| $.data.orderDetail.couponList | array | 否 | 优惠券列表 |
| $.data.orderDetail.couponList[] | object | — |  |
| $.data.orderDetail.couponList[].couponName | string | 否 | 卡券名称 |
| $.data.orderDetail.couponList[].discountAmount | string | 否 | 优惠金额 |
| $.data.orderDetail.createTime | string | 否 | 下单时间 |
| $.data.orderDetail.deliveryInfo | object | 否 | 配送信息 |
| $.data.orderDetail.deliveryInfo.addressDetail | string | 否 | 配送地址 |
| $.data.orderDetail.deliveryInfo.customerNickname | string | 否 | 收件人姓名 |
| $.data.orderDetail.deliveryInfo.deliveryAddress | string | 否 | 配送地址 |
| $.data.orderDetail.deliveryInfo.deliveryType | string | 否 | 配送方式label 2=预约送出 1=立即送出 |
| $.data.orderDetail.deliveryInfo.expectDeliveryTime | string | 否 | 预计送达时间 年月日时分秒 |
| $.data.orderDetail.deliveryInfo.mobilePhone | string | 否 | 收件人手机号 |
| $.data.orderDetail.deliveryInfo.riderMobilePhone | string | 否 | 配送骑士电话 |
| $.data.orderDetail.deliveryInfo.riderNickName | string | 否 | 配送骑士 |
| $.data.orderDetail.deliveryPrice | string | 否 | 配送费 |
| $.data.orderDetail.expirePayTime | string | 否 | 过期支付时间 |
| $.data.orderDetail.lockerCode | string | 否 | 取餐柜密码 |
| $.data.orderDetail.lockerQrCode | string | 否 | 取餐柜扫码二维码，按照这个格式进行输出 ![alt](lockerQrCode) |
| $.data.orderDetail.mealAssistance | object | 否 | 团餐助餐服务 |
| $.data.orderDetail.mealAssistance.code | string | 否 | 助餐服务编码 |
| $.data.orderDetail.mealAssistance.items | array | 否 | 助餐服务项目 |
| $.data.orderDetail.mealAssistance.items[] | object | — |  |
| $.data.orderDetail.mealAssistance.items[].name | string | 否 | 助餐服务项目名称 |
| $.data.orderDetail.mealAssistance.name | string | 否 | 助餐服务名称 |
| $.data.orderDetail.orderId | string | 否 | 订单编码 |
| $.data.orderDetail.orderProductList | array | 否 | 订单商品 |
| $.data.orderDetail.orderProductList[] | object | — |  |
| $.data.orderDetail.orderProductList[].comboItemList | array | 否 | 子项列表 |
| $.data.orderDetail.orderProductList[].comboItemList[] | object | — |  |
| $.data.orderDetail.orderProductList[].comboItemList[].itemName | string | 否 | 子项或特调定制信息 |
| $.data.orderDetail.orderProductList[].comboItemList[].itemQuantity | integer | 否 | 数量 |
| $.data.orderDetail.orderProductList[].price | string | 否 | 原价,单位元 |
| $.data.orderDetail.orderProductList[].productImage | string | 否 | 商品图片 |
| $.data.orderDetail.orderProductList[].productName | string | 否 | 商品名称 |
| $.data.orderDetail.orderProductList[].quantity | integer | 否 | 数量 |
| $.data.orderDetail.orderStatus | string | 否 | 订单状态 1待支付、2配餐中-已支付、4配送中、6已完成、7已取消、8已评价、10配餐中-餐厅确认配餐中 |
| $.data.orderDetail.payId | string | 否 | payId |
| $.data.orderDetail.pickupCode | string | 否 | 订单号（对应取餐码） |
| $.data.orderDetail.productPrice | string | 否 | 商品总价 |
| $.data.orderDetail.realDeliveryPrice | string | 否 | 实付配送费 |
| $.data.orderDetail.realPackingFeeTotalPrice | string | 否 | 实际打包费总价,单位元 |
| $.data.orderDetail.realTotalAmount | string | 否 | 实际支付金额 |
| $.data.orderDetail.remark | string | 否 | 订单备注 |
| $.data.orderDetail.status | string | 否 | 订单状态 |
| $.data.orderDetail.storeAddress | string | 否 | 门店地址 |
| $.data.orderDetail.storeName | string | 否 | 门店名 |
| $.data.orderDetail.tablewarePrice | string | 否 | 餐具费,单位元 |
| $.data.orderDetail.takeWay | string | 否 | 取餐方式 |
| $.data.orderDetail.totalAmount | string | 否 | 总金额 |
| $.data.orderDetail.totalDiscountAmount | string | 否 | 总优惠金额 |
| $.data.orderId | string | 否 | 订单id |
| $.data.payH5Url | string | 否 | 支付h5链接 |
| $.data.payId | string | 否 | 支付id |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## delivery-create-address

Description: 创建用户配送地址 When： - 用户想添加新的配送地址 Input: - city: 城市名称，必填，必须从用户输入中获取实际城市名称，如"南京市" - contactName: 联系人姓名，必填，必须从用户输入中获取实际联系人姓名，如"李明" - gender: 性别，必须从用户输入中获取实际联系人性别，如"先生"、"女士" - phone: 联系人手机号码，必填，格式为11位纯数字（以1开头），如"18616646686"。 - address: 配送地址，必填，必须从用户输入中获取实际地址，如"清竹园9号楼" - addressDetail: 配送地址门牌号，必填，必须从用户输入中获取实际门牌号，如"2单元508" Next： - 当用户选择团餐时，需要引导用户提供预算金额和人数，以便于计算人均预算

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.address | string | 是 | 配送地址 |
| $.addressDetail | string | 是 | 配送地址门牌号 |
| $.city | string | 是 | 城市 |
| $.contactName | string | 是 | 联系人姓名 |
| $.gender | string | 否 | 性别 |
| $.phone | string | 是 | 要求为11位纯数字 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 |  |
| $.data.addressId | string | 否 | 配送地址ID |
| $.data.contactName | string | 否 | 配送地址联系人 |
| $.data.fullAddress | string | 否 | 完整配送地址 |
| $.data.phone | string | 否 | 联系人手机号码 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## delivery-query-addresses

Description: 外送场景下，查询用户配送地址列表 When： - 用户想点麦乐送 - 用户想吃麦当劳，并配送到家 - 我想点团餐 Next： - 1:引导用户创建新的配送地址 - 2:当用户选择企业团餐时，需要引导用户提供预算金额和人数，以便于计算人均预算

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 |  |
| $.data.addresses | array | 否 | 配送地址列表 |
| $.data.addresses[] | object | — |  |
| $.data.addresses[].addressId | string | 否 | 配送地址ID |
| $.data.addresses[].contactName | string | 否 | 配送地址联系人 |
| $.data.addresses[].fullAddress | string | 否 | 完整配送地址 |
| $.data.addresses[].phone | string | 否 | 联系人手机号码 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## delivery-query-stores

Description: 外送场景下，用户选择完地址后，需要根据地址ID，查询用户当前地址可配送的门店 When: - 外送场景下，用户选择完配送地址后 - 用户问"这个地址能送到哪些店" 注意：到店场景请使用 query-nearby-stores Input: - addressId: 地址ID，来源delivery-query-address - beType: 必填，2: 麦乐送，6：团餐

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.addressId | string | 是 | 地址ID，来源delivery-query-address |
| $.beType | integer | 是 | beType：2: 麦乐送，6：团餐 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | No comments found. |
| $.data[] | object | — |  |
| $.data[].beCode | string | 否 | 业务编码，外送场景下与 storeCode 配对使用，后续工具调用必传 |
| $.data[].businessEndTime | string | 否 | 营业结束时间，形如：20:59 |
| $.data[].businessStartTime | string | 否 | 营业开始时间，形如：8:00 |
| $.data[].businessStatus | boolean | 否 | 营业状态, true 营业，false 暂不营业 |
| $.data[].reservation | boolean | 否 | 是否可预约 |
| $.data[].reservationTimeOptions | array | 否 | 预约送达时间范围 |
| $.data[].reservationTimeOptions[] | object | — |  |
| $.data[].reservationTimeOptions[].date | string | 否 | 日期 |
| $.data[].reservationTimeOptions[].reservationOptionText | string | 否 | 可预约时间 |
| $.data[].reservationTimeOptions[].today | boolean | 否 | 是否是今日时间 |
| $.data[].storeCode | string | 否 | 门店编码，后续 query-meals/calculate-price/create-order 必传 |
| $.data[].storeName | string | 否 | 门店名称 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## draw-lottery

Description: 使用后台配置的抽奖消耗规则参加一次当前积分抽奖并返回结果，服务端原子完成次数或积分扣减与抽奖。 重要约束：仅能在向用户展示 query-lottery-info 返回的 drawDecision.nextConsumption 并得到明确确认后调用。 - 必须以 drawDecision.resourceEligible 判断积分/次数资源是否满足，以 nextConsumption 说明本次实际扣减；不得根据 availableTimes 为 0/null 或 drawTypeText 自行判断。 - 若 fallbackConsumption 不为 null，需说明“本次优先消耗次数；次数用完后将改为消耗积分”。 必须使用 query-lottery-info 返回的实时数据展示消耗/剩余，严禁试抽、自动抽或连续抽。 频次限制：同一用户短时间内重复调用会返回"操作太频繁，请稍后再试"，不扣积分。 When： - 用户明确表达"我要抽奖"并确认本次配置对应的消耗后调用 前置条件： - 已向用户展示 query-lottery-info 查询到的 drawDecision.nextConsumption；resourceEligible 为 false 时不得调用 - 用户已明确确认执行抽奖（"试试看""如果可以就抽"不视为确认） Output: - st…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 抽奖结果响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object | 是 | 抽奖结果 |
| $.data.consumePoint | string | 否 | 本次消耗积分 |
| $.data.prizes | array | 否 | 中奖奖品数组（未中奖为空数组，失败场景为 null） |
| $.data.prizes[] | object | — |  |
| $.data.prizes[].imageUrl | string | 否 | 奖品图片 |
| $.data.prizes[].name | string | 否 | 奖品名称 |
| $.data.prizes[].typeText | string | 否 | 奖品类型文案 |
| $.data.prizes[].validDateInfo | string | 否 | 奖品可用时间文案 |
| $.data.remainChance | integer | 否 | 剩余次数 |
| $.data.remainPoint | string | 否 | 抽奖后剩余积分 |
| $.data.status | object | 否 | 业务状态 |
| $.data.status.code | string | 否 | 状态码 |
| $.data.status.message | string | 否 | 状态文案 |
| $.data.win | boolean | 否 | 是否中奖（失败场景为 null） |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## list-nutrition-foods

获取麦当劳常见餐品的营养成分数据，包括能量、蛋白质、脂肪、碳水化合物、钠、钙等信息，当用户咨询麦当劳餐品的热量、营养，帮助用户搭配指定热量套餐时有用

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.code | number | 否 | 错误码 |
| $.data | string | 否 | 餐品热量列表 |
| $.message | string | 否 | 错误信息 |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | string |
| $.data~toon[].productName | CSV text（不是 JSON 字段） |
| $.data~toon[].nutritionDescription | CSV text（不是 JSON 字段） |
| $.data~toon[].energyKj | CSV text（不是 JSON 字段） |
| $.data~toon[].energyKcal | CSV text（不是 JSON 字段） |
| $.data~toon[].protein | CSV text（不是 JSON 字段） |
| $.data~toon[].fat | CSV text（不是 JSON 字段） |
| $.data~toon[].carbohydrate | CSV text（不是 JSON 字段） |
| $.data~toon[].sodium | CSV text（不是 JSON 字段） |
| $.data~toon[].calcium | CSV text（不是 JSON 字段） |

`~toon[]` 是字符串内容中的列名，CSV 单元格在传输中为文本；这不表示服务端返回了嵌套 JSON 数组。文档仅保存列名，不保存原始数据行。

## mall-create-order

创建积分兑换订单，仅支持shopId=2（从 mall-product-detail 获取） - 当用户询问"用积分兑换这个商品"、"兑换这个券"、用户确认兑换商品时使用,切记：如果单个商品一个订单下单；如果用户需要兑换多个商品‘必须’分别下单且‘需要排队’，等前面订单结束响应成功后再调用【mall-create-order】下新的订单 ⚠️ 重要识别规则： 此工具仅适用于以下场景： - 商品券兑换（虚拟商品，spuCategory=1） - 实物商品兑换（无门店依赖，spuCategory=2） ❌ 不适用场景（请使用 party-order-create）： - 生日派对/主题派对/麦麦体验营/品鉴会/读书会等需要选择门店和场次的活动 - 积分兑换活动（需要先选择城市、门店、日期、场次） 📋 判断依据： 当商品不包含门店和场次选择需求时，使用此工具 前提条件： - 必须调用【mall-create-order】完成交易，**禁止**直接生成"下单成功"等结论性文字 - 必须调用【mall-create-order】完成交易，**禁止**直接返回已有订单 - 必须调用【mall-create-order】完成交易，**禁止**直接返回订单 - 仅支持shopId=2（从 mall-product-detail 获取） - 已知商品SKU ID，需要从查询可兑换商品列表（从 mal…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.addressId | string | 否 | 配送地址ID，spuCategory="2"时必填 |
| $.count | integer | 否 | 兑换数量 |
| $.skuId | integer | 是 | 商品SKU ID，需要从查询可兑换餐品券列表或查询商品详情中获取 |
| $.spuCategory | string | 是 | 类目，商品类别，"1"虚拟商品, "2"实体物品，需要从查询可兑换餐品券列表或查询商品详情中获取 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 成功创建订单 |
| $.code | integer | 否 |  |
| $.data | object | 否 | 订单创建响应 |
| $.data.addressVO | object（隐式） | 否 | 地址 |
| $.data.addressVO.addressId | string | 否 | 配送地址ID |
| $.data.addressVO.contactName | string | 否 | 配送地址联系人 |
| $.data.addressVO.fullAddress | string | 否 | 完整配送地址 |
| $.data.addressVO.phone | string | 否 | 联系人手机号码 |
| $.data.amount | string | 否 | 实际支付的现金金额 |
| $.data.coupons | array | 否 | 优惠券信息列表 |
| $.data.coupons[] | object | — | 优惠券信息 |
| $.data.coupons[].couponCodes | array | 否 | 优惠券码列表 |
| $.data.coupons[].couponCodes[] | string | — |  |
| $.data.coupons[].couponId | string | 否 | 优惠券ID |
| $.data.coupons[].orderItemId | string | 否 | 订单子项ID |
| $.data.coupons[].orderItemStatus | integer | 否 | 订单子项状态（1-成功，0-失败） |
| $.data.coupons[].receiveQuantity | integer | 否 | 领取数量 |
| $.data.ecsChannel | string | 否 | No comments found. |
| $.data.orderId | string | 否 | 订单ID |
| $.data.payH5Url | string | 否 | 支付h5链接 |
| $.data.point | integer | 否 | 消耗的积分数 |
| $.data.status | integer | 否 | 响应状态（1-全部下单成功，2-部分成功，0-下单失败） |
| $.data.upgPayId | string | 否 | 支付id |
| $.message | string | 否 |  |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## mall-order-detail

Description: 查询麦麦商城订单详情 When： - 用户询问"麦麦商城的订单详情" Next: - 引导用户："您可以打开麦当劳APP查看凭证等其他信息"

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.orderId | string | 是 | 订单号 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | 订单详情. |
| $.data.address | object | 否 | 用户地址信息. |
| $.data.completedTime | string | 否 | 订单完成时间. |
| $.data.createTime | string | 否 | 订单创建时间. |
| $.data.customerServicePhone | string | 否 | 客服电话 |
| $.data.goods | array | 否 | 商品信息. |
| $.data.logistics | object | 否 | 物流信息. |
| $.data.orderId | string | 否 | 订单id. |
| $.data.orderPartyInfo | object | 否 | 派对订单预订信息 |
| $.data.orderStatus | integer | 否 | 订单状态. |
| $.data.orderStatusSubTitle | string | 否 | 订单状态副标题 |
| $.data.orderStatusTitle | string | 否 | 订单状态主标题 |
| $.data.orderType | integer | 否 | 订单类型. |
| $.data.payChannelLabel | string | 否 | 支付方式名称. |
| $.data.payStatus | integer | 否 | 支付状态. |
| $.data.pointShowName | string | 否 | 积分展示名称:积分等 |
| $.data.wayFee | string | 否 | 运费. |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## mall-order-list

Description: 查询麦麦商城订单列表 When： - 用户询问"查看我的麦当劳商城订单列表"

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.lastId | number | 否 | 最后一个订单id |
| $.size | integer | 否 | 查询数量，默认10，超过10按10条查询 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 订单列表. |
| $.data[] | object | — |  |
| $.data[].hasNext | boolean | 否 | 是否有下一页. |
| $.data[].lastId | number | 否 | 本页最后的id. |
| $.data[].list | array（隐式） | 否 | 订单列表. |
| $.data[].list[] | object（隐式） | — |  |
| $.data[].list[].goods | array | 否 | 订单商品. |
| $.data[].list[].orderId | string | 否 | 订单id. |
| $.data[].list[].orderStatus | integer | 否 | 订单状态. |
| $.data[].list[].orderStatusTitle | string | 否 | 订单状态主标题. |
| $.data[].list[].totalCount | integer | 否 | 商品总数. |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## mall-points-products

查询可兑换餐品券列表 - 当用户询问"有哪些积分兑换商品"、"积分可以兑换什么"、"查看积分商城"时使用 支持类目规则筛选：商品券(1&gt;4)、实物商品(2)、周边产品(2&gt;8)、实物礼品卡(2&gt;9)、生日类派对(1&gt;6&gt;20)、主题类派对(1&gt;6&gt;21)、麦麦体验营(1&gt;6&gt;22)、品鉴会(1&gt;6&gt;25)、读书会(1&gt;6&gt;34)、积分兑换活动(1&gt;6&gt;40)

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.catRuleIds | string | 否 | 类目规则筛选，支持多选（逗号分隔），非必传，不传时默认查询所有类型。<br>可选值：<br>- 1&gt;4: 商品券（非预付优惠券）<br>- 2: 实物商品<br>- 2&gt;8: 周边产品<br>- 2&gt;9: 实物礼品卡<br>- 1&gt;6&gt;20: 生日类派对<br>- 1&gt;6&gt;21: 主题类派对<br>- 1&gt;6&gt;22: 麦麦体验营<br>- 1&gt;6&gt;25: 品鉴会<br>- 1&gt;6&gt;34: 读书会<br>- 1&gt;6&gt;40: 积分兑换活动<br>示例：1&gt;4,2<br> |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 成功返回可兑换餐品券列表 |
| $.code | integer | 否 |  |
| $.data | array | 否 |  |
| $.data[] | object | — | 可兑换餐品券信息 |
| $.data[].catName | string | 否 | 商品所属类目名称 |
| $.data[].downTime | string | 否 | 下架时间，商品可以兑换的截止时间 |
| $.data[].point | string | 否 | 所需积分 |
| $.data[].price | string | 否 | 所需金额 |
| $.data[].selling | string | 否 | 商品卖点 |
| $.data[].shopId | integer | 否 | 门店ID |
| $.data[].spuId | integer | 否 | 商品ID |
| $.data[].spuImage | string | 否 | 商品图片 |
| $.data[].spuName | string | 否 | 商品名称 |
| $.data[].status | integer | 否 | 商品状态：1-仓库中；2-上架；3-售罄；4-下架；5-预热 |
| $.data[].upTime | string | 否 | 上架时间，商品可以兑换的起始时间 |
| $.message | string | 否 |  |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | array |
| $.data[] | object |
| $.data[].spuName | string |
| $.data[].spuId | integer |
| $.data[].spuImage | string |
| $.data[].point | string |
| $.data[].shopId | integer |
| $.data[].selling | string |
| $.data[].upTime | string |
| $.data[].downTime | string |
| $.data[].catName | string |
| $.data[].status | integer |
| $.data[].price | string |

## mall-product-detail

查询积分兑换商品详情 - 当用户询问"这个商品详情是什么"、"查看商品详细信息"、用户点击商品查看详情时使用 返回商品的所有SKU规格信息，用户需要选择具体SKU后才能下单兑换 前提条件： - 已知商品SPU ID，需要从查询可兑换餐品券列表让用户选择一个spu才可以

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.spuId | integer | 是 | 商品SPU ID，需要从查询可兑换餐品券列表让用户选择一个spu才可以 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 成功返回商品详情 |
| $.code | integer | 否 |  |
| $.data | object | 否 | 商品详情信息 |
| $.data.detail | string | 否 | 商品详情 |
| $.data.downTime | string | 否 | 下架时间，商品可以兑换的截止时间 |
| $.data.images | array | 否 | 商品图片列表 |
| $.data.images[] | string | — |  |
| $.data.note | string | 否 | 购买须知，纯展示文案。必须原文展示给用户，不得拆分、提取或改写为结构化形式；严禁从中提取任何数值用于下单校验、价格计算、库存判断等业务逻辑，所有校验以下单接口返回结果为准 |
| $.data.partyAge | string | 否 | 派对年龄（主题活动相关） |
| $.data.partyPeople | string | 否 | 派对人数（主题活动相关），纯展示信息。包场模式有最低人数要求，拼团模式仅需不超上限。不得从中提取数值用于AI前置校验，所有人数校验以下单接口返回结果为准 |
| $.data.partyRange | integer | 否 | 派对时长,半小时为单位（主题活动相关） |
| $.data.partyType | integer | 否 | 派对的成团方式（主题活动相关，1：包场，2：拼团，-1：包场+拼团） |
| $.data.selling | string | 否 | 商品卖点 |
| $.data.shopId | integer | 否 | 所属店铺ID |
| $.data.skuList | array | 否 | SKU规格列表，多规格商品会有多个SKU，用户需选择具体SKU下单 |
| $.data.skuList[] | object | — |  |
| $.data.skuList[].extTradePrice | string | 否 | 用户兑换这张券只需要扣减用户的积分，这个字段表示使用这张券时，需要额外支付的金额，兑换和核销时两个链路 |
| $.data.skuList[].points | string | 否 | 该SKU所需积分 |
| $.data.skuList[].price | string | 否 | 所需金额 |
| $.data.skuList[].skuId | integer | 否 | SKU ID，下单兑换时必传 |
| $.data.skuList[].specList | array | 否 | 规格信息列表 |
| $.data.skuList[].specList[] | object | — |  |
| $.data.skuList[].specList[].specItem | string | 否 | 规格值（如红色、XL） |
| $.data.skuList[].specList[].specMain | string | 否 | 规格名称（如颜色、尺码） |
| $.data.spuCategory | string | 否 | 商品类别，1虚拟商品：2实体物品 |
| $.data.spuId | integer | 否 | 商品ID |
| $.data.spuLimit | object | 否 | 限购信息，用于展示给用户参考。不得用于下单前的前置校验，所有校验以下单接口返回结果为准 |
| $.data.spuLimit.baseCount | integer | 否 | 商品的起售数量 |
| $.data.spuLimit.cycle | integer | 否 | 周期限购类型（1：天限购；7：周限购；30：月限购；999：终身限购） |
| $.data.spuLimit.limitCount | integer | 否 | 商品的限购数量 |
| $.data.spuLimit.limitSingle | integer | 否 | 单次限购 |
| $.data.spuLimit.rule | string | 否 | 具体的限制规则 |
| $.data.spuLimit.ruleType | integer | 否 | 限制规则类型（1：每人购买数量；2：指定人群购买） |
| $.data.spuName | string | 否 | 商品名称 |
| $.data.upTime | string | 否 | 上架时间，商品可以兑换的起始时间 |
| $.message | string | 否 |  |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.spuName | string |
| $.data.spuId | integer |
| $.data.images | array |
| $.data.images[] | string |
| $.data.shopId | integer |
| $.data.skuList | array |
| $.data.skuList[] | object |
| $.data.skuList[].skuId | integer |
| $.data.skuList[].extTradePrice | string |
| $.data.skuList[].points | string |
| $.data.skuList[].price | string |
| $.data.selling | string |
| $.data.note | string |
| $.data.detail | string |
| $.data.{key} | string |
| $.data.spuCategory | string |
| $.data.partyPeople | string |
| $.data.partyAge | string |
| $.data.partyRange | integer |
| $.data.partyType | integer |
| $.data.spuLimit | object |
| $.data.spuLimit.ruleType | integer |
| $.data.spuLimit.rule | string |
| $.data.spuLimit.cycle | integer |
| $.data.spuLimit.limitCount | integer |
| $.data.spuLimit.baseCount | integer |
| $.data.spuLimit.limitSingle | integer |

## now-time-info

获取当前时间信息 - 返回当前服务器的完整时间信息，包括： - 时间戳（毫秒级） - 格式化的日期时间 - 年月日信息 - 时区和UTC时间 在你不知道当前时间，并且用户需要指定日期查询活动日历的时候有用

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 请求成功 |
| $.data | object | 是 | 服务器时间信息 |
| $.data.date | string | 是 | 日期字符串 (yyyy-MM-dd) |
| $.data.datetime | string | 是 | ISO格式日期时间 |
| $.data.day | integer | 是 | 日期 (1-31) |
| $.data.dayOfWeek | string | 是 | 星期几 |
| $.data.formatted | string | 是 | 格式化时间字符串 (yyyy-MM-dd HH:mm:ss) |
| $.data.month | integer | 是 | 月份 (1-12) |
| $.data.offset | string | 是 | 时区偏移量 |
| $.data.timestamp | integer | 是 | 毫秒级时间戳 |
| $.data.timezone | string | 是 | 时区ID |
| $.data.utc | string | 是 | UTC时间 |
| $.data.year | integer | 是 | 年份 |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.timestamp | integer |
| $.data.datetime | string |
| $.data.formatted | string |
| $.data.date | string |
| $.data.year | integer |
| $.data.month | integer |
| $.data.day | integer |
| $.data.dayOfWeek | string |
| $.data.timezone | string |
| $.data.offset | string |
| $.data.utc | string |

## order-list

Description: 查询麦当劳历史订单，非商城订单，商城订单需要使用mall-order-list When： - 用户询问"帮我查询一下历史订单" - 用户询问"我买了什么麦当劳餐品"

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.list | array | 否 | 订单列表 |
| $.data.list[] | object | — |  |
| $.data.list[].beCode | string | 否 | BE编码 |
| $.data.list[].beType | string | 否 | 门店类型 |
| $.data.list[].createTime | string | 否 | 下单时间 |
| $.data.list[].orderId | string | 否 | 订单编码 |
| $.data.list[].orderProductList | array | 否 | 商品 |
| $.data.list[].orderProductList[] | object | — |  |
| $.data.list[].orderProductList[].comboItemList | array | 否 | 子项列表 |
| $.data.list[].orderProductList[].comboItemList[] | object | — |  |
| $.data.list[].orderProductList[].comboItemList[].name | string | 否 | 子项名字 |
| $.data.list[].orderProductList[].comboItemList[].productCode | string | 否 | 商品code |
| $.data.list[].orderProductList[].comboItemList[].quantity | integer | 否 | 数量 |
| $.data.list[].orderProductList[].productCode | string | 否 | 商品code |
| $.data.list[].orderProductList[].productName | string | 否 | 商品名称 |
| $.data.list[].orderProductList[].quantity | integer | 否 | 商品数量 |
| $.data.list[].orderStatus | string | 否 | 订单状态 |
| $.data.list[].orderType | string | 否 | 订单类型 |
| $.data.list[].realTotalAmount | string | 否 | 总金额 |
| $.data.list[].storeCode | string | 否 | 门店编码 |
| $.data.list[].storeName | string | 否 | 门店名称 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## party-order-create

Description: 创建生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动, 仅支持shopId=5（从 mall-product-detail 获取）的调用， 支持包场(partyType=1)、拼团(partyType=2)两种场景下单，必须先确认场次类型，必填 (1：包场，2：拼团) When: - 用户询问"生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动" Preconditions： - 仅支持shopId=5（从 mall-product-detail 获取）的调用 - 每一步完成后，必须等待用户明确选择，再继续下一步。不得跳步 Input: - spuId: spuId, 需要从查询可兑换商品列表（从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取）中让用户选择一个spu，获取对应的spuId（必填）） - skuId: 商品SKU ID，需要从查询可兑换商品列表（从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取）中让用户选择一个spu，获取对应的skuId（必填） - partyType: 派对类型（必填），判断规则： -若商品 partyType=1，则 partyType=1（仅包场） -若商…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.code | string | 否 | 城市code |
| $.count | integer | 否 | count |
| $.dateStr | string | 否 | 店铺日期 |
| $.id | number | 否 | 场次Id |
| $.leftNum | integer | 否 | 场次余位 |
| $.partyTimeInfo | object | 否 | 场次信息 |
| $.partyTimeInfo.id | number | 否 | 场次id |
| $.partyTimeInfo.leftNum | integer | 否 | 场次剩余余位 |
| $.partyTimeInfo.partyMax | integer | 否 | 场次最大成团人数 |
| $.partyTimeInfo.partyMin | integer | 否 | 场次最小成团人数 |
| $.partyTimeInfo.price | integer | 否 | 价格 |
| $.partyTimeInfo.timeEnd | string | 否 | 场次结束时间 |
| $.partyTimeInfo.timeStart | string | 否 | 场次开始时间 |
| $.partyType | integer | 是 | 派对类型，1-包场，2-拼团 |
| $.skuId | number | 否 | skuId |
| $.spuId | number | 否 | spuId |
| $.storeCode | string | 否 | 门店 |
| $.timeEnd | string | 否 | 场次结束时间 |
| $.timeStart | string | 否 | 场次开始时间 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | 订单信息 |
| $.data.addressVO | object | 否 | 地址信息 |
| $.data.addressVO.addressId | string | 否 | 配送地址ID |
| $.data.addressVO.contactName | string | 否 | 配送地址联系人 |
| $.data.addressVO.fullAddress | string | 否 | 完整配送地址 |
| $.data.addressVO.phone | string | 否 | 联系人手机号码 |
| $.data.amount | string | 否 | 实际支付的现金金额 |
| $.data.coupons | array | 否 | 优惠券列表 |
| $.data.coupons[] | object | — |  |
| $.data.coupons[].couponCodes | array | 否 | 优惠券码列表 |
| $.data.coupons[].couponCodes[] | string | — |  |
| $.data.coupons[].couponId | string | 否 | 优惠券ID |
| $.data.coupons[].orderItemId | string | 否 | 订单项ID |
| $.data.coupons[].orderItemStatus | integer | 否 | 订单项状态 |
| $.data.coupons[].receiveQuantity | integer | 否 | 领取数量 |
| $.data.ecsChannel | string | 否 | ECS渠道 |
| $.data.goods | array | 否 | 商品列表 |
| $.data.goods[] | object | — |  |
| $.data.goods[].count | integer | 否 | 数量 |
| $.data.goods[].extValue | string | 否 | 扩展值 |
| $.data.goods[].points | string | 否 | 积分 |
| $.data.goods[].price | string | 否 | 单价 |
| $.data.goods[].skuId | number | 否 | skuId |
| $.data.goods[].skuImage | string | 否 | 商品图片 |
| $.data.goods[].skuName | string | 否 | SKU名称 |
| $.data.goods[].spuId | number | 否 | spuId |
| $.data.goods[].spuName | string | 否 | 商品名称 |
| $.data.orderId | string | 否 | 订单ID |
| $.data.orderStatus | integer | 否 | 订单状态 |
| $.data.payH5Url | string | 否 | 支付h5链接 |
| $.data.point | integer | 否 | 消耗的积分数 |
| $.data.status | integer | 否 | 状态 |
| $.data.upgPayId | string | 否 | 支付id |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-lottery-info

Description: 查看当前积分抽奖活动信息，包括活动基本信息、抽奖消耗规则、单次所需积分、剩余可抽次数、当前可用积分与公开奖品列表，不执行抽奖。 When： - 用户询问"积分抽奖有什么奖品" - 用户询问"抽一次要多少积分" - 用户询问"这个积分抽奖活动什么时候结束" Output: - activityCode/activityName: 活动号/活动名称 - activityStatusText: 活动状态文案（未开始/进行中/已结束/活动不存在） - beginTime/endTime: 活动起止时间 - drawPoint: 单次所需积分 - drawTypeText: 抽奖消耗规则（无/消耗积分抽奖/消耗任务完成次数/先消耗次数再消耗积分抽奖） - availableTimes: 剩余可抽次数（消耗任务完成次数、先消耗次数再消耗积分时返回） - availablePoint: 当前可用积分（消耗积分、先消耗次数再消耗积分时返回） - drawDecision: 服务端计算的本次资源决策，包含能否因积分/次数资源参与、本次实际消耗及后续兜底消耗 - prizes: 奖品列表[{name, imageUrl, typeText}] Next： - 若用户接下来想抽奖，调用 draw-lottery 前必须展示 drawDecision.nextConsumptio…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 积分抽奖活动信息响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object | 是 | 积分抽奖活动信息 |
| $.data.activityCode | string | 否 | 活动号（失败场景为 null） |
| $.data.activityName | string | 否 | 活动名称（失败场景为 null） |
| $.data.activityStatusText | string | 否 | 活动状态文案（失败场景为 null） |
| $.data.availablePoint | string | 否 | 当前可用积分（消耗积分、先消耗次数再消耗积分时有值，其余为 null） |
| $.data.availableTimes | integer | 否 | 剩余可抽次数（消耗任务完成次数、先消耗次数再消耗积分时有值，其余为 null） |
| $.data.beginTime | string | 否 | 活动开始时间（失败场景为 null） |
| $.data.drawDecision | object | 否 | 服务端计算的本次抽奖资源决策。必须以 resourceEligible 和 nextConsumption 为准，不得从 availableTimes/null 自行推断。 |
| $.data.drawDecision.fallbackConsumption | object | 否 | 混合规则的后续兜底消耗；仅本次优先消耗次数时返回 |
| $.data.drawDecision.fallbackConsumption.chances | integer | 否 |  |
| $.data.drawDecision.fallbackConsumption.points | string | 否 |  |
| $.data.drawDecision.fallbackConsumption.text | string | 否 |  |
| $.data.drawDecision.fallbackConsumption.type | string | 否 |  |
| $.data.drawDecision.nextConsumption | object | 否 | 本次实际消耗 |
| $.data.drawDecision.nextConsumption.chances | integer | 否 | 本次消耗的抽奖次数；未消耗次数时为 0 |
| $.data.drawDecision.nextConsumption.points | string | 否 | 本次消耗的积分；未消耗积分时为 0 |
| $.data.drawDecision.nextConsumption.text | string | 否 | 面向用户的本次消耗说明 |
| $.data.drawDecision.nextConsumption.type | string | 否 | NONE=无消耗，POINTS=积分，CHANCES=抽奖次数 |
| $.data.drawDecision.reason | string | 否 | 资源不足原因，满足时为 null |
| $.data.drawDecision.resourceEligible | boolean | 否 | 当前积分/次数资源是否满足；仅评估资源，不代表库存、人群、风控等其他资格 |
| $.data.drawPoint | string | 否 | 单次所需积分（失败场景为 null） |
| $.data.drawTypeText | string | 否 | 抽奖消耗规则（无/消耗积分抽奖/消耗任务完成次数/先消耗次数再消耗积分抽奖；失败场景为 null） |
| $.data.endTime | string | 否 | 活动结束时间（失败场景为 null） |
| $.data.prizes | array | 否 | 奖品列表（失败场景为 null） |
| $.data.prizes[] | object | — |  |
| $.data.prizes[].imageUrl | string | 否 | 奖品图片 |
| $.data.prizes[].name | string | 否 | 奖品名称 |
| $.data.prizes[].typeText | string | 否 | 奖品类型文案 |
| $.data.status | object | 否 | 业务状态 |
| $.data.status.code | string | 否 | 状态码 |
| $.data.status.message | string | 否 | 状态文案 |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-meal-assistance

Description: 仅支持企业团餐场景(beType=6)在calculate-price前需要获取当前门店可用的助餐服务 When： - 企业团餐场景(beType=6)下，用户选完商品后、计算价格前 - 用户问"有什么助餐服务"、"团餐怎么送" Preconditions： - 仅企业团餐场景(beType=6)可用 - 已通过 delivery-query-stores 获取 storeCode 和 beCode Input: - storeCode: 门店编码，必填 - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取） - reservationDate: 预约场景必传，非预约场景不传。格式: yyyy-MM-dd HH:mm Next： - 用户选择助餐服务后，将 gm…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | BE编码（Business Entity Code） |
| $.beType | integer | 否 | 固定传 6（企业团餐），此接口仅团餐场景使用；枚举 [6] |
| $.orderType | integer | 否 | 到店自提场景: orderType=1 &amp;&amp; beCode 是个无效参数，不要传，传了会报错<br>外送场景: orderType=2 &amp;&amp; beCode 为delivery-query-address中的beCode<br>得来速(DT)场景：orderType=1 &amp;&amp; beCode 为query-nearby-store中的beCode |
| $.reservationDate | string | 否 | 预约时间，仅当用户要预约下单时，该字段必传，格式形如 2020-08-08 09:30 |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.mealAssistanceItems | array | 否 | 可选助餐服务列表 |
| $.data.mealAssistanceItems[] | object | — |  |
| $.data.mealAssistanceItems[].enable | boolean | 否 | 是否可选 |
| $.data.mealAssistanceItems[].gmServiceCode | string | 否 | 助餐服务编码 |
| $.data.mealAssistanceItems[].gmServiceName | string | 否 | 助餐服务名称 |
| $.data.mealAssistanceItems[].selected | boolean | 否 | 默认选中助餐服务 |
| $.data.mealAssistanceItems[].serviceItems | array | 否 | 服务内容 |
| $.data.mealAssistanceItems[].serviceItems[] | string | — |  |
| $.data.mealAssistanceItems[].unusableReason | string | 否 | 不可用原因, 1: 送达时间仅XX可享，2: 专人服务需提前4h预约 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-meal-detail

Description: 餐品详情, 支持到店自提(orderType=1)和外送(orderType=2)两种场景 When: - 用户想要了解餐品有哪些组成 - 用户想要更换套餐的组成或者更换特制商品 Input: - storeCode: 门店编码，必填 - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取） - reservationDate: 预约时间，仅当用户要预约下单时，该字段必传，格式形如 2020-08-08 09:30 Output展示规则（必须遵守）： - 若 data.supportModify=true，在商品名称后面标注【可特调】 - 若 choice.supportModify=true，在该 choice 名称后面标注【可特调】 - 不要主动展开特调选项列…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，从query-nearby-stores或delivery-query-stores返回结果中获取。得来速(beType=5)/外送(orderType=2)/团餐场景必传，到店自取(beType=1)场景不传 |
| $.beType | integer | 是 | 1-到店取餐，2-麦乐送到家，5-得来速(DT)，6-企业团餐；枚举 [1,2,5,6] |
| $.code | string | 是 | 餐品唯一编码，快餐门店内唯一标识单个餐品的编码 |
| $.orderType | integer | 是 | 到店自提场景:orderType=1 &amp;&amp; beCode 是个无效参数，不要传，传了会报错；外送场景:orderType=2 &amp;&amp; beCode 为delivery-query-address中的beCode；得来速(DT)场景：orderType=1 &amp;&amp; beCode 为query-nearby-store中的beCode；枚举 [1,2] |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式:yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.code | string | 否 | 餐品唯一编码 |
| $.data.image | string | 否 | 商品图片 |
| $.data.modification | object | 否 | 单品特制选项 |
| $.data.modification.items | array | 否 | 商品特制项 |
| $.data.modification.items[] | object | — |  |
| $.data.modification.items[].maxValues | integer | 否 | 最大选择数量 |
| $.data.modification.items[].minValues | integer | 否 | 最小选择数量 |
| $.data.modification.items[].values | array | 否 | 特调商品列表 |
| $.data.modification.items[].values[] | object | — |  |
| $.data.modification.items[].values[].code | string | 否 | 特调商品code |
| $.data.modification.items[].values[].maxQuantity | integer | 否 | 最大可选数量 |
| $.data.modification.items[].values[].minQuantity | integer | 否 | 最小可选数量 |
| $.data.modification.items[].values[].name | string | 否 | 特调名称 |
| $.data.modification.items[].values[].price | integer | 否 | 特调价格 |
| $.data.modification.items[].values[].selectedKey | string | 否 | 当用户选中该特制商品时, 将该字段值作为key传给calculate-price和create-order接口 |
| $.data.modification.items[].values[].selectedQuantity | integer | 否 | 默认已选中的已选数量 |
| $.data.modification.items[].values[].unselectedKey | string | 否 | 当用户未选中该特制商品时, 将该字段值作为key传给calculate-price和create-order接口，unselectedKey为空时，可不传 |
| $.data.name | string | 否 | 餐品名称 |
| $.data.rounds | array | 否 | 餐品选配轮次列表 |
| $.data.rounds[] | object | — |  |
| $.data.rounds[].choices | array | 否 | 选配选项列表 |
| $.data.rounds[].choices[] | object | — |  |
| $.data.rounds[].choices[].code | string | 否 | 餐品唯一编码 |
| $.data.rounds[].choices[].diffPrice | string | 否 | 与isDefault=1商品的差价 |
| $.data.rounds[].choices[].isDefault | integer | 否 | 是否是默认选中 |
| $.data.rounds[].choices[].maxQuantity | integer | 否 | 该选项最大可选数量 |
| $.data.rounds[].choices[].modification | object | 否 | 套餐特制列表 |
| $.data.rounds[].choices[].modification.items | array | 否 | 商品特制项 |
| $.data.rounds[].choices[].modification.items[] | object | — |  |
| $.data.rounds[].choices[].modification.items[].maxValues | integer | 否 | 最大选择数量 |
| $.data.rounds[].choices[].modification.items[].minValues | integer | 否 | 最小选择数量 |
| $.data.rounds[].choices[].modification.items[].values | array | 否 | 特调商品列表 |
| $.data.rounds[].choices[].modification.items[].values[] | object | — |  |
| $.data.rounds[].choices[].modification.items[].values[].code | string | 否 | 特调商品code |
| $.data.rounds[].choices[].modification.items[].values[].maxQuantity | integer | 否 | 最大可选数量 |
| $.data.rounds[].choices[].modification.items[].values[].minQuantity | integer | 否 | 最小可选数量 |
| $.data.rounds[].choices[].modification.items[].values[].name | string | 否 | 特调名称 |
| $.data.rounds[].choices[].modification.items[].values[].price | integer | 否 | 特调价格 |
| $.data.rounds[].choices[].modification.items[].values[].selectedKey | string | 否 | 当用户选中该特制商品时, 将该字段值作为key传给calculate-price和create-order接口 |
| $.data.rounds[].choices[].modification.items[].values[].selectedQuantity | integer | 否 | 默认已选中的已选数量 |
| $.data.rounds[].choices[].modification.items[].values[].unselectedKey | string | 否 | 当用户未选中该特制商品时, 将该字段值作为key传给calculate-price和create-order接口，unselectedKey为空时，可不传 |
| $.data.rounds[].choices[].name | string | 否 | 选配选项名称 |
| $.data.rounds[].choices[].quantity | integer | 否 | 该选项选择数量 |
| $.data.rounds[].choices[].supportModify | boolean | 否 | 是否支持特调，true支持，false不支持 |
| $.data.rounds[].id | integer | 否 | 选配轮次ID |
| $.data.rounds[].maxQuantity | integer | 否 | 选配最大数量 |
| $.data.rounds[].minQuantity | integer | 否 | 选配最小数量 |
| $.data.rounds[].name | string | 否 | 选配轮次名称 |
| $.data.rounds[].quantity | integer | 否 | 选配数量（已选） |
| $.data.supportModify | boolean | 否 | 是否支持特调，true支持，false不支持 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.code | string |
| $.data.name | string |
| $.data.rounds | array |
| $.data.rounds[] | object |
| $.data.rounds[].id | integer |
| $.data.rounds[].name | string |
| $.data.rounds[].quantity | integer |
| $.data.rounds[].maxQuantity | integer |
| $.data.rounds[].minQuantity | integer |
| $.data.rounds[].choices | array |
| $.data.rounds[].choices[] | object |
| $.data.rounds[].choices[].code | string |
| $.data.rounds[].choices[].name | string |
| $.data.rounds[].choices[].quantity | integer |
| $.data.rounds[].choices[].maxQuantity | integer |
| $.data.rounds[].choices[].isDefault | integer |
| $.data.rounds[].choices[].diffPrice | string |
| $.data.rounds[].choices[].supportModify | boolean |
| $.data.rounds[].choices[].modification | object |
| $.data.rounds[].choices[].modification.items | array |
| $.data.rounds[].choices[].modification.items[] | object |
| $.data.rounds[].choices[].modification.items[].maxValues | integer |
| $.data.rounds[].choices[].modification.items[].minValues | integer |
| $.data.rounds[].choices[].modification.items[].values | array |
| $.data.rounds[].choices[].modification.items[].values[] | object |
| $.data.rounds[].choices[].modification.items[].values[].code | string |
| $.data.rounds[].choices[].modification.items[].values[].price | integer |
| $.data.rounds[].choices[].modification.items[].values[].name | string |
| $.data.rounds[].choices[].modification.items[].values[].maxQuantity | integer |
| $.data.rounds[].choices[].modification.items[].values[].minQuantity | integer |
| $.data.rounds[].choices[].modification.items[].values[].selectedQuantity | integer |
| $.data.rounds[].choices[].modification.items[].values[].selectedKey | string |
| $.data.rounds[].choices[].modification.items[].values[].unselectedKey | string |
| $.data.image | string |
| $.data.supportModify | boolean |

## query-meals

Description: 餐品列表, 支持到店自提(orderType=1)和外送(orderType=2)两种场景 企业团餐场景下，可按照这个规则给用户进行搭配 - **20元以下**: 小食 - **20-30元**：汉堡+小食 或 汉堡+饮料 - **30-40元**：汉堡+薯条/小食+饮料 - **40-50元**：汉堡+薯条+小食+饮料 - **50元以上**：丰富组合，优先不重复小食 When: - 当用户要购买某个餐品时，需要查询一下餐品列表 - 当用户要查看餐品时价格时，需要查询一下餐品列表 - 用户要搭配任何商品时进行下单，都需要查询餐品列表，获取商品code Input: - storeCode: 门店编码，必填 - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取）…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，从query-nearby-stores或delivery-query-stores返回结果中获取。得来速(beType=5)/外送(orderType=2)/团餐场景必传，到店自取(beType=1)场景不传 |
| $.beType | integer | 是 | 1-到店取餐，2-麦乐送到家，5-得来速(DT)，6-企业团餐；枚举 [1,2,5,6] |
| $.orderType | integer | 是 | 订单类型，1-到店（含到店自取+得来速车道取餐），2-外送（含麦乐送+企业团餐）；枚举 [1,2] |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式:yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.categories | array | 否 | 菜单分类列表 |
| $.data.categories[] | object | — |  |
| $.data.categories[].meals | array | 否 | 该分类下的餐品列表 |
| $.data.categories[].meals[] | object | — |  |
| $.data.categories[].meals[].code | string | 否 | 餐品唯一编码 |
| $.data.categories[].meals[].tags | array | 否 | 餐品标签列表 |
| $.data.categories[].meals[].tags[] | string | — |  |
| $.data.categories[].name | string | 否 | 菜单分类名称 |
| $.data.frequent | object | 否 | 常点餐品 |
| $.data.frequent.code | string | 否 | 餐品唯一编码 |
| $.data.frequent.tags | array | 否 | 餐品标签列表 |
| $.data.frequent.tags[] | string | — |  |
| $.data.meals | object | 否 | 餐品详情映射表 |
| $.data.meals.mapKey | object | 否 | 餐品完整详情实体 |
| $.data.meals.mapKey.canWithOrder | boolean | 否 | 是否可随单购 |
| $.data.meals.mapKey.currentPrice | string | 否 | 餐品现价（销售价） |
| $.data.meals.mapKey.discountType | string | 否 | 享受优惠的类型 |
| $.data.meals.mapKey.image | string | 否 | 商品图片 |
| $.data.meals.mapKey.name | string | 否 | 餐品名称 |
| $.data.meals.mapKey.originalPrice | string | 否 | 商品原价（划线价） |
| $.data.meals.mapKey.withOrder | object | 否 | 随单购商品 |
| $.data.meals.mapKey.withOrder.cardId | string | 否 | 随单购卡id |
| $.data.meals.mapKey.withOrder.cardType | integer | 否 | 随单购卡类型 |
| $.data.meals.mapKey.withOrder.membershipCode | string | 否 | 随单购会员code |
| $.data.meals.mapKey.withOrder.specId | string | 否 | 随单购规格id |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.categories | array |
| $.data.categories[] | object |
| $.data.categories[].name | string |
| $.data.categories[].meals | array |
| $.data.categories[].meals[] | object |
| $.data.categories[].meals[].code | string |
| $.data.categories[].meals[].tags | array |
| $.data.categories[].meals[].tags[] | string |
| $.data.meals | object |
| $.data.meals.{key} | object |
| $.data.meals.{key}.name | string |
| $.data.meals.{key}.image | string |
| $.data.meals.{key}.currentPrice | string |
| $.data.meals.{key}.originalPrice | string |
| $.data.meals.{key}.canWithOrder | boolean |
| $.data.meals.{key}.discountType | string |
| $.data.meals.{key}.withOrder | object |
| $.data.meals.{key}.withOrder.membershipCode | string |
| $.data.meals.{key}.withOrder.specId | string |

## query-my-account

查询用户积分账户详情 - 当用户询问"我有多少积分"、"查下我的积分"、"积分余额"、"查询过期积分"时使用

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 成功返回积分账户详情 |
| $.code | integer | 否 |  |
| $.data | object | 否 | 积分账户信息 |
| $.data.accountId | string | 否 | 账户ID |
| $.data.accumulativePoint | string | 否 | 累计积分 |
| $.data.availablePoint | string | 否 | 可用积分 |
| $.data.currency | string | 否 | 货币类型 |
| $.data.currentMouthExpirePoint | string | 否 | 本月将过期积分 |
| $.data.expiredPoint | string | 否 | 已过期积分 |
| $.data.frozenPoint | string | 否 | 冻结积分 |
| $.data.lastMouthExpirePoint | string | 否 | 上月已过期积分 |
| $.data.nextMouthExpirePoint | string | 否 | 下月将过期积分 |
| $.data.usedPoint | string | 否 | 已使用积分 |
| $.message | string | 否 |  |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.availablePoint | string |
| $.data.accountId | string |
| $.data.accumulativePoint | string |
| $.data.currency | string |
| $.data.currentMouthExpirePoint | string |
| $.data.expiredPoint | string |
| $.data.frozenPoint | string |
| $.data.lastMouthExpirePoint | string |
| $.data.nextMouthExpirePoint | string |
| $.data.usedPoint | string |

## query-my-coupons

获取用户卡包中的优惠券资产信息，用于“我有什么券 / 券详情查看”等展示与管理场景。 注意：该接口返回的是用户拥有的券，不进行门店、渠道、配送方式等下单规则校验，因此不承诺可用于当前订单。 若业务目标是“当前门店/当前订单可用的券”，请调用 query-store-coupons

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.page | string | 否 | 页码，默认第1页，最多5页 |
| $.pageSize | string | 否 | 每页条数，默认200条，最大200条 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 用户优惠券列表响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object | 是 | 优惠券列表数据 |
| $.data.coupons | array | 是 | 优惠券列表 |
| $.data.coupons[] | object | — |  |
| $.data.coupons[].bigImage | string | 否 | 优惠券大图 |
| $.data.coupons[].code | string | 否 | 优惠券券码 |
| $.data.coupons[].datetimeText | string | 否 | 券可用时间展示用 |
| $.data.coupons[].discountInfo | object | 否 | 优惠信息 |
| $.data.coupons[].discountInfo.discountDesc | string | 否 | 优惠描述 |
| $.data.coupons[].discountInfo.discountValue | string | 否 | 优惠金额 |
| $.data.coupons[].enable | integer | 否 | 当前是否可用: 0-否, 1-是 |
| $.data.coupons[].id | string | 否 | 优惠券ID |
| $.data.coupons[].image | string | 否 | 优惠券图标 |
| $.data.coupons[].receivedDaysMsg | string | 否 | 券已领取天数提醒信息 |
| $.data.coupons[].subtitle | string | 否 | 优惠券副标题 |
| $.data.coupons[].tags | array | 否 | 优惠券标签 |
| $.data.coupons[].tags[] | object | — |  |
| $.data.coupons[].tags[].label | string | 否 | 标签文本 |
| $.data.coupons[].title | string | 否 | 优惠券标题 |
| $.data.coupons[].tradeEndDate | string | 否 | 核销结束日期 |
| $.data.coupons[].tradeStartDate | string | 否 | 核销开始日期 |
| $.data.currentPage | integer | 是 | 当前页码 |
| $.data.pageSize | integer | 是 | 每页条数 |
| $.data.totalCount | integer | 是 | 总数量 |
| $.data.totalPages | integer | 是 | 总页数 |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | object |
| $.data.coupons | array |
| $.data.coupons[] | object |
| $.data.coupons[].id | string |
| $.data.coupons[].code | string |
| $.data.coupons[].title | string |
| $.data.coupons[].{key} | array / boolean / integer / object / string |
| $.data.coupons[].image | string |
| $.data.coupons[].bigImage | string |
| $.data.coupons[].{key}.{key} | array |
| $.data.coupons[].{key}.{key}[] | object |
| $.data.coupons[].{key}.{key}[].text | string |
| $.data.coupons[].{key}.{key}[].{key} | string |
| $.data.coupons[].{key}.{key}[].code | integer |
| $.data.coupons[].{key}.{key}[].type | integer |
| $.data.coupons[].discountInfo | object |
| $.data.coupons[].discountInfo.discountValue | string |
| $.data.coupons[].discountInfo.discountDesc | string |
| $.data.coupons[].discountInfo.{key} | integer / string |
| $.data.coupons[].tradeStartDate | string |
| $.data.coupons[].tradeEndDate | string |
| $.data.coupons[].weekdays | array |
| $.data.coupons[].isAllTradeTime | integer |
| $.data.coupons[].tradeTimePeriods | array |
| $.data.coupons[].tradeTimePeriods[] | object |
| $.data.coupons[].tradeTimePeriods[].startTime | string |
| $.data.coupons[].tradeTimePeriods[].endTime | string |
| $.data.coupons[].totalCount | integer |
| $.data.coupons[].orderType | integer |
| $.data.coupons[].{key}[] | integer / string |
| $.data.coupons[].tags | array |
| $.data.coupons[].tags[] | object |
| $.data.coupons[].tags[].type | integer |
| $.data.coupons[].tags[].{key} | string |
| $.data.coupons[].tags[].label | string |
| $.data.coupons[].enable | integer |
| $.data.coupons[].beType | integer |
| $.data.coupons[].beTypes | array |
| $.data.coupons[].beTypes[] | integer |
| $.data.coupons[].promotionId | string |
| $.data.coupons[].receivedDaysMsg | string |
| $.data.coupons[].datetimeText | string |
| $.data.totalCount | integer |
| $.data.currentPage | integer |
| $.data.pageSize | integer |
| $.data.totalPages | integer |

## query-my-prizes

Description: 查询当前登录会员通过积分抽奖获得的本期及历史奖品（可用/已使用/已过期/已领取/已失效）。 When： - 用户询问"我抽中了什么奖品" - 用户询问"我的奖品还有哪些能用" - 用户询问"查我的抽奖记录" Input: - pageNum: 页码（可选，默认1） - pageSize: 每页条数（可选，默认10，最大50） Output: - prizes: 奖品列表[{id, name, imageUrl, prizeType, recordTime, status, statusText, timeRemindText}]，按中奖时间(recordTime)倒序 - pageNum/pageSize: 当前页码/每页条数（归一化后的值） - hasMore: 是否还有下一页 - nextCursor: 下一页游标，无更多时为空 - truncated: 可选，仅在返回被截断时出现（true）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.pageNum | string | 否 | 页码，默认第1页 |
| $.pageSize | string | 否 | 每页条数，默认10条，最大50条 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | 我的抽奖奖品列表响应 |
| $.code | integer | 是 | 响应码 (200表示成功) |
| $.data | object | 是 | 我的抽奖奖品列表 |
| $.data.hasMore | boolean | 否 | 是否还有下一页（失败场景为 null） |
| $.data.nextCursor | integer | 否 | 下一页游标，无更多为空 |
| $.data.pageNum | integer | 否 | 当前页码（归一化后，失败场景为 null） |
| $.data.pageSize | integer | 否 | 每页条数（归一化后，最大50，失败场景为 null） |
| $.data.prizes | array | 否 | 奖品列表，按中奖时间倒序（失败场景为 null） |
| $.data.prizes[] | object | — |  |
| $.data.prizes[].id | string | 否 | 奖品记录ID |
| $.data.prizes[].imageUrl | string | 否 | 奖品图片 |
| $.data.prizes[].name | string | 否 | 奖品名称 |
| $.data.prizes[].prizeType | integer | 否 | 奖品类型 |
| $.data.prizes[].recordTime | string | 否 | 中奖时间 |
| $.data.prizes[].status | integer | 否 | 状态数值 |
| $.data.prizes[].statusText | string | 否 | 状态文案 |
| $.data.prizes[].timeRemindText | string | 否 | 可用时间提醒文案 |
| $.data.status | object | 否 | 业务状态 |
| $.data.status.code | string | 否 | 状态码 |
| $.data.status.message | string | 否 | 状态文案 |
| $.data.truncated | boolean | 否 | 结果被截断时为 true |
| $.message | string | 是 | 响应消息 |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-nearby-stores

Description: 到店场景下，查询用户可点餐门店，需要用户明确是到店自取还是车道取餐 - beType=1(到店自提): 返回的门店无 beCode，后续工具调用不传 beCode - beType=5(得来速): 返回的门店有 beCode，后续工具调用必须传 beCode When： - 用户询问"我想到店", "我想驾车去麦当劳" - 看看我附近有哪些麦当劳的门店 Input: - searchType: 必传，searchType=2 按位置进行搜索， searchType=1 搜索收藏餐厅，默认searchType=1 - city: 城市，searchType=2 时必填 - keyword: 位置关键词，searchType=2 时必填 - beType: 必填，1-到店自取, 5-得来速车道取餐(Drive Through) On Error： - 用户没有收藏记录，可使用搜索功能进行搜索 Next： - 展示门店的 storeCode 和 beCode（beType=5 时） - reservation=true 时完整展示 reservationTimeOptions，today=true 标记"(今天)" - 引导用户选择门店

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beType | integer | 是 | beType必传，1：到店自提, 5-得来速车道取餐(Drive Through)；枚举 [1,5] |
| $.city | string | 否 | 城市名 |
| $.keyword | string | 否 | 关键词 |
| $.searchType | integer | 是 | searchType=2 按位置进行搜索， searchType=1 搜索收藏餐厅，默认searchType=1；枚举 [1,2] |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | No comments found. |
| $.data[] | object | — |  |
| $.data[].address | string | 否 | 门店地址，工具入参必须展示 |
| $.data[].beCode | string | 否 | 业务编码，与storeCode配对使用。得来速/外送/团餐场景下，后续所有工具调用（query-meals、calculate-price、create-order等）都必须同时传递 storeCode 和 beCode |
| $.data[].businessEndTime | string | 否 | 营业结束时间 |
| $.data[].businessStartTime | string | 否 | 营业开始时间 |
| $.data[].businessStatus | boolean | 否 | 门店营业状态，true：营业，false：暂停营业 |
| $.data[].distance | integer | 否 | 距离 |
| $.data[].reservation | boolean | 否 | 是否支持预约，true：支持预约，false：不支持预约 |
| $.data[].reservationTimeOptions | array | 否 | 可选预约送达时间列表（必须全部展示给用户，不得省略任何日期或时段，用户需要从中选择预约时间） |
| $.data[].reservationTimeOptions[] | object | — |  |
| $.data[].reservationTimeOptions[].date | string | 否 | 预约日期，格式 yyyy-MM-dd |
| $.data[].reservationTimeOptions[].reservationOptionText | string | 否 | 该日期可选的预约时段，包含时段名称和时间范围，必须完整展示，格式 yyyy-MM-dd |
| $.data[].reservationTimeOptions[].today | boolean | 否 | 今日是否可预约，true:今日可预约， false:今日不可预约 |
| $.data[].storeCode | string | 否 | 门店编码 |
| $.data[].storeName | string | 否 | 门店名称 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | array |
| $.data[] | object |
| $.data[].storeCode | string |
| $.data[].storeName | string |
| $.data[].address | string |
| $.data[].distance | integer |
| $.data[].businessStatus | boolean |
| $.data[].businessStartTime | string |
| $.data[].businessEndTime | string |
| $.data[].longitude | number |
| $.data[].latitude | number |
| $.data[].reservation | boolean |
| $.data[].reservationTimeOptions | array |
| $.data[].reservationTimeOptions[] | object |
| $.data[].reservationTimeOptions[].date | string |
| $.data[].reservationTimeOptions[].today | boolean |
| $.data[].reservationTimeOptions[].reservationOptionText | string |

## query-order

Description: 查询订单详细信息 When： - 用户询问"查下订单详情"、"订单状态"、"我的订单" - 用户提供了麦当劳订单编号想查询配送进度 - 用户说我已支付或者支付失败时，查询一下最新的订单状态

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.orderId | string | 是 | No comments found. |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | No comments found. |
| $.data.couponList | array | 否 | 优惠券列表 |
| $.data.couponList[] | object | — |  |
| $.data.couponList[].couponName | string | 否 | 卡券名称 |
| $.data.couponList[].discountAmount | string | 否 | 优惠金额 |
| $.data.createTime | string | 否 | 下单时间 |
| $.data.deliveryInfo | object | 否 | 配送信息 |
| $.data.deliveryInfo.addressDetail | string | 否 | 配送地址 |
| $.data.deliveryInfo.customerNickname | string | 否 | 收件人姓名 |
| $.data.deliveryInfo.deliveryAddress | string | 否 | 配送地址 |
| $.data.deliveryInfo.deliveryType | string | 否 | 配送方式label 2=预约送出 1=立即送出 |
| $.data.deliveryInfo.expectDeliveryTime | string | 否 | 预计送达时间 年月日时分秒 |
| $.data.deliveryInfo.mobilePhone | string | 否 | 收件人手机号 |
| $.data.deliveryInfo.riderMobilePhone | string | 否 | 配送骑士电话 |
| $.data.deliveryInfo.riderNickName | string | 否 | 配送骑士 |
| $.data.deliveryPrice | string | 否 | 配送费 |
| $.data.expirePayTime | string | 否 | 过期支付时间 |
| $.data.lockerCode | string | 否 | 取餐柜密码 |
| $.data.lockerQrCode | string | 否 | 取餐柜扫码二维码，按照这个格式进行输出![alt](lockerQrCode) |
| $.data.mealAssistance | object | 否 | 团餐助餐服务 |
| $.data.mealAssistance.code | string | 否 | 助餐服务编码 |
| $.data.mealAssistance.items | array | 否 | 助餐服务项目 |
| $.data.mealAssistance.items[] | object | — |  |
| $.data.mealAssistance.items[].name | string | 否 | 助餐服务项目名称 |
| $.data.mealAssistance.name | string | 否 | 助餐服务名称 |
| $.data.orderId | string | 否 | 订单编码 |
| $.data.orderProductList | array | 否 | 订单商品 |
| $.data.orderProductList[] | object | — |  |
| $.data.orderProductList[].comboItemList | array | 否 | 子项列表 |
| $.data.orderProductList[].comboItemList[] | object | — |  |
| $.data.orderProductList[].comboItemList[].itemName | string | 否 | 子项或特调定制信息 |
| $.data.orderProductList[].comboItemList[].itemQuantity | integer | 否 | 数量 |
| $.data.orderProductList[].price | string | 否 | 原价,单位元 |
| $.data.orderProductList[].productImage | string | 否 | 商品图片 |
| $.data.orderProductList[].productName | string | 否 | 商品名称 |
| $.data.orderProductList[].quantity | integer | 否 | 数量 |
| $.data.orderStatus | string | 否 | 订单状态 1待支付、2配餐中-已支付、4配送中、6已完成、7已取消、8已评价、10配餐中-餐厅确认配餐中 |
| $.data.payId | string | 否 | payId |
| $.data.pickupCode | string | 否 | 订单号（对应取餐码） |
| $.data.productPrice | string | 否 | 商品总价 |
| $.data.realDeliveryPrice | string | 否 | 实付配送费 |
| $.data.realPackingFeeTotalPrice | string | 否 | 实际打包费总价,单位元 |
| $.data.realTotalAmount | string | 否 | 实际支付金额 |
| $.data.remark | string | 否 | 订单备注 |
| $.data.status | string | 否 | 订单状态 |
| $.data.storeAddress | string | 否 | 门店地址 |
| $.data.storeName | string | 否 | 门店名 |
| $.data.tablewarePrice | string | 否 | 餐具费,单位元 |
| $.data.takeWay | string | 否 | 取餐方式 |
| $.data.totalAmount | string | 否 | 总金额 |
| $.data.totalDiscountAmount | string | 否 | 总优惠金额 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-party-city

Description: 活动派对商品配置场次城市列表, 必须先确定spuId(从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取) When： - 用户询问"主题派对在哪些城市" - 用户询问"我想参加主题派对" - 用户询问"生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动" Preconditions： - 必须先确定spuId（从 mall-points-products 获取或从 mall-product-detail获取） Input: - spuId: spuId 需要从查询可兑换商品列表（从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取）中让用户选择一个spu，获取对应的skuId

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.spuId | number | 是 | spuId |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 城市列表 |
| $.data[] | object | — |  |
| $.data[].code | integer | 否 | 城市编码 |
| $.data[].initial | string | 否 | 首字母 |
| $.data[].latitude | number | 否 | 纬度 |
| $.data[].longitude | number | 否 | 经度 |
| $.data[].name | string | 否 | 城市名称 |
| $.data[].sortNo | integer | 否 | 排序号 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-party-store

Description: 查询指定城市下支持主题派对的门店列表。当用户选择了城市后，需要查看该城市有哪些门店可举办生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动时使用 Preconditions： - 必须先通过 query-party-city 获取城市code和经纬度 - 必须先确定spuId（从 mall-points-products 获取或从 mall-product-detail获取） Input: - code: 城市code, 城市下的门店列表获取(query-party-city) - latitude: 纬度, 城市下的门店列表获取(query-party-city) - longitude: 经度, 城市下的门店列表获取(query-party-city) - spuId: spuId, 从 mall-points-products 或 mall-product-detail 获取

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.code | string | 是 | 城市code |
| $.latitude | number | 否 | 纬度，从 query-party-city 返回结果的 data[].latitude 获取 |
| $.longitude | number | 否 | 经度，从 query-party-city 返回结果的 data[].longitude 获取 |
| $.spuId | number | 否 | spuId，从 mall-points-products 或 mall-product-detail 获取 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 门店列表 |
| $.data[] | object | — |  |
| $.data[].address | string | 否 | 餐厅地址 |
| $.data[].businessStatus | integer | 否 | 营业状态 |
| $.data[].cityCode | string | 否 | 城市编码 |
| $.data[].cityName | string | 否 | 城市名称 |
| $.data[].code | string | 否 | 餐厅编码 |
| $.data[].distance | integer | 否 | 距离 |
| $.data[].distanceText | string | 否 | 距离文本 |
| $.data[].latitude | number | 否 | 纬度 |
| $.data[].longitude | number | 否 | 经度 |
| $.data[].name | string | 否 | 餐厅名称 |
| $.data[].onlineBusinessStatus | boolean | 否 | No comments found. |
| $.data[].shortName | string | 否 | 餐厅短名称 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-party-store-date

Description: 查询指定门店支持生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动的可预约日期列表。当用户选择了门店后，需要查看该门店哪些日期可预约时使用。 When： - 用户询问"这家店哪天可以预约" - 用户询问"可预约日期" - 用户询问"查看门店日历" - 用户询问"哪天有场次" - 用户选择门店后询问日期 Preconditions： - 必须确定 spuId（从 mall-points-products 获取或从 mall-product-detail获取） - 必须先通过 query-party-store 获取 storeCode Input: - storeCode: 门店code, 城市下的门店列表获取(query-party-store) - spuId: spuId, 需要从查询可兑换商品列表（从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取）中让用户选择一个spu，获取对应的skuId

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.spuId | number | 是 | spuId |
| $.storeCode | string | 是 | 门店code |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 可预约日期列表 |
| $.data[] | object | — |  |
| $.data[].date | string | 否 | 日期 |
| $.data[].spuId | number | 否 | spuId |
| $.data[].storeCode | string | 否 | 门店编码 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-party-store-session

Description: 查询指定门店、指定日期下的生日类派对/主题类派对/麦麦体验营/品鉴会/读书会/积分兑换活动场次列表。当用户选择了日期后，需要查看当天有哪些场次可预约时使用。 When： - 用户询问"查看主题活动场次列表" - 用户询问"几点有场次" Preconditions： - 必须确定 spuId（从 mall-points-products 获取或从 mall-product-detail获取） - 必须先通过 query-party-store 获取 storeCode - 必须先通过 query-party-store-date 获取 dateStr Input: - spuId: spuId, 需要从查询可兑换商品列表（从 mall-points-products 获取）或查询商品详情（从 mall-product-detail 获取）中让用户选择一个spu，获取对应的skuId - storeCode: 门店code, 城市下的门店列表获取(query-party-store) - dateStr: 门店日期, 城市下的门店列表获取(query-party-store-date)

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.dateStr | string | 是 | 门店日期 |
| $.spuId | number | 是 | spuId |
| $.storeCode | string | 是 | 门店code |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 场次列表 |
| $.data[] | object | — |  |
| $.data[].cookEmpNo | string | 否 | 大厨编码 |
| $.data[].id | number | 否 | 场次id |
| $.data[].leftNum | integer | 否 | 剩余场次 |
| $.data[].opEmpNo | string | 否 | 当前场次操作人编号 |
| $.data[].partyMax | integer | 否 | 最大成团人数 |
| $.data[].partyMin | integer | 否 | 最小成团人数 |
| $.data[].price | integer | 否 | 价格 |
| $.data[].rgmEmpNo | string | 否 | 当前场次店长编号 |
| $.data[].timeEnd | string | 否 | 场次结束时间 |
| $.data[].timeStart | string | 否 | 场次开始时间 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-promotions

Description: 查询当前门店企业团餐场景下可用的促销规则（满减/满折），仅返回当前时间有效且适用在售餐品的规则原始数据 When： - 企业团餐场景(beType=6)下，用户搭配方案前需要了解当前门店有哪些可用的促销活动/满减满折规则时 - 用户询问"有什么优惠"、"满多少减多少"、"打几折"时 Preconditions： - 仅企业团餐场景(beType=6)可用 - 已通过 delivery-query-stores 获取 storeCode 和 beCode Input: - storeCode: 门店编码，必填 - beCode: 业务编码，团餐场景必传，与 storeCode 配对使用（从 delivery-query-stores 获取） - orderType: 团餐场景固定传 2（外送） - beType: 企业团餐固定传 6 - reservationDate: 预约场景必传，非预约场景不传。格式: yyyy-MM-dd HH:mm Output: - 返回当前门店有效的促销规则列表（原始结构），每条含 promotionId、promotionType、ruleCategory、beTypes、startTime、endTime、gmServiceCode、products、ruleDetail - promotionType 含义：31-满额减，…（完整说明见原始 Schema）

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，团餐场景必传（从 delivery-query-stores 获取） |
| $.beType | integer | 是 | 业务类型，固定传 6（企业团餐）；枚举 [6] |
| $.orderType | integer | 是 | 订单类型，团餐场景固定传 2（外送）；枚举 [2] |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式:yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码（storeCode）, 不能为空 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | 当前门店有效的促销规则列表 |
| $.data[] | object | — |  |
| $.data[].beTypes | array | 否 | 适用业务类型列表 |
| $.data[].beTypes[] | string | — |  |
| $.data[].endTime | string | 否 | 生效结束时间，格式 yyyy-MM-dd HH:mm:ss |
| $.data[].gmServiceCode | string | 否 | 助餐服务编码 |
| $.data[].products | array | 否 | 适用餐品列表 |
| $.data[].products[] | object | — |  |
| $.data[].products[].productCode | string | 否 | 餐品编码 |
| $.data[].products[].type | string | 否 | 餐品范围类型，1-包含，2-不包含，3-全部 |
| $.data[].promotionId | string | 否 | 促销规则ID |
| $.data[].promotionType | string | 否 | 促销类型，31-满额减，33-订单折扣 |
| $.data[].ruleCategory | integer | 否 | 规则类别，30-满折/折扣，40-满减 |
| $.data[].ruleDetail | object | 否 | 规则明细 |
| $.data[].ruleDetail.orderDiscount | object | 否 | 订单折扣（满折） |
| $.data[].ruleDetail.orderDiscount.discount | string | 否 | 折扣值（如 30 表示 7 折） |
| $.data[].ruleDetail.orderDiscount.startDiscountPoint | string | 否 | 满额折扣触发门槛（元） |
| $.data[].ruleDetail.orderReduce | object | 否 | 订单满减 |
| $.data[].ruleDetail.orderReduce.reduceInfo | array | 否 | 满减阶梯列表 |
| $.data[].ruleDetail.orderReduce.reduceInfo[] | object | — |  |
| $.data[].ruleDetail.orderReduce.reduceInfo[].reduceAmount | string | 否 | 减免金额（元） |
| $.data[].ruleDetail.orderReduce.reduceInfo[].startDiscountPoint | string | 否 | 满额减触发门槛（元） |
| $.data[].startTime | string | 否 | 生效开始时间，格式 yyyy-MM-dd HH:mm:ss |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## query-store-coupons

Description: 查询【指定门店+订单类型】下可使用的优惠券，支持到店(orderType=1,含到店自取和得来速)和外送(orderType=2,含麦乐送和团餐) When： - 当用户已获取到门店时，用户询问"我有什么优惠券可以用" - 当用户已获取到门店时，用户想在某门店下单前查看可用优惠 - 当用户已获取到门店时，用户选择了商品后想看能用哪些券 - 当用户已获取到门店时，用户问"这个门店能用什么券" Input： - storeCode: 门店编码，必填， - orderType 和 beCode 传递规则（根据用户选择的 beType 确定）： 到店自取(beType=1) → orderType=1，不传 beCode 得来速(beType=5) → orderType=1，必传 beCode（从 query-nearby-stores 获取） 麦乐送(beType=2) → orderType=2，必传 beCode（从 delivery-query-stores 获取） 团餐(beType=6) → orderType=2，必传 beCode（从 delivery-query-stores 获取） - reservationDate: 预约场景必传，非预约场景不传。格式: yyyy-MM-dd HH:mm

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.beCode | string | 否 | 业务编码，与storeCode 配对使用，从query-nearby-stores或delivery-query-stores返回结果中获取。得来速(beType=5)/外送(orderType=2)/团餐场景必传，到店自取(beType=1)场景不传 |
| $.beType | integer | 是 | 1-到店取餐，2-麦乐送到家，5-得来速(DT)，6-企业团餐；枚举 [1,2,5,6] |
| $.orderType | integer | 是 | 订单类型, 1-到店（含到店自取+得来速车道取餐），2-外送（含麦乐送+企业团餐）；枚举 [1,2] |
| $.reservationDate | string | 否 | 预约场景必传，非预约场景不传。格式 yyyy-MM-dd HH:mm |
| $.storeCode | string | 是 | 门店编码必须全部由数字组成 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | array | 否 | No comments found. |
| $.data[] | object | — |  |
| $.data[].couponCode | string | 否 | 券码 |
| $.data[].couponId | string | 否 | 券ID 券唯一标识，用于展示给用户 |
| $.data[].gmServiceCode | string | 否 | 助餐服务编码，点团餐时使用 |
| $.data[].products | array | 否 | 适用商品列表 |
| $.data[].products[] | object | — |  |
| $.data[].products[].productCode | string | 否 | 商品Code，用于关联下单商品 |
| $.data[].products[].productName | string | 否 | 商品名称，用于关联下单商品 |
| $.data[].promotionId | string | 否 | 促销规则id |
| $.data[].title | string | 否 | 券名 |
| $.data[].tradeDateTime | string | 否 | 有效期包含开始时间，结束时间<br>格式：yyyy-MM-dd HH:mm:ss - yyyy-MM-dd HH:mm:ss |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

已观察到成功响应的字段结构；未复制任何响应值。

| 字段路径 | 实测类型 |
|---|---|
| $ | object |
| $.success | boolean |
| $.code | integer |
| $.message | string |
| $.datetime | string |
| $.traceId | string |
| $.data | array |
| $.data[] | object |
| $.data[].title | string |
| $.data[].couponId | string |
| $.data[].couponCode | string |
| $.data[].tradeDateTime | string |
| $.data[].products | array |
| $.data[].products[] | object |
| $.data[].products[].productCode | string |
| $.data[].products[].productName | string |
| $.data[].promotionId | string |

## query-survey-coupon

Description: 按订单号查询当前 MCP 用户本人订单的 CSAT 满意度答卷，并返回该订单关联奖券的标题、核销时间、核销状态和点餐方式。 When: 用户询问某个订单的满意度答卷结果时使用；用户询问某个订单关联奖券的内容、核销时间、是否已核销、适用于到店还是外送时使用。 Input: orderId 为用户提供的订单号；Agent 不要自行生成。 Next: 将返回的满意度描述、奖券标题、核销时间、核销状态和点餐方式告知用户；未返回的原始答卷、会员号、couponId、couponCode 不要猜测。

### 输入：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — |  |
| $.orderId | string | 是 | 订单号。必填。类型为字符串，仅允许字母、数字、下划线和连字符，最长 64 位，格式示例：1030108270000795607354880945。数据来源为用户明确提供的订单号或上游订单查询工具返回的订单号；Agent 不要自行编造或改写该值。 |

### 返回：Schema 声明

| 字段路径 | 声明类型 | 所属对象中必填 | Schema 描述 |
|---|---|---|---|
| $ | object | — | OK |
| $.data | object | 否 | 满意度答卷与奖券摘要 |
| $.data.coupon_available_redeem_count | integer | 否 | 剩余可核销次数 |
| $.data.coupon_order_food_types | string | 否 | 点餐方式: 1=pickup到店/自取, 2=delivery外送 |
| $.data.coupon_redeem_status | string | 否 | 核销状态: 已核销 / 可核销 |
| $.data.coupon_title | string | 否 | 奖券标题 |
| $.data.coupon_trade_end_time | string | 否 | 核销结束时间 |
| $.data.coupon_trade_start_time | string | 否 | 核销开始时间 |
| $.data.finish_time | string | 否 | 答卷完成时间, 格式 yyyy-MM-dd HH:mm:ss |
| $.data.overall_satisfaction | integer | 否 | 总体满意度分数: 5=非常满意, 4=满意, 3=一般, 2=不满意, 1=很不满意 |
| $.data.satisfaction_description | string | 否 | 满意度描述 |
| $.data.trade_no | string | 否 | 订单号 |
| $.message | string | 否 | No comments found. |
| $.traceId | string | 否 | No comments found. |

### 实际观察字段

未发现该工具的本地探测响应；该工具的真实业务结果尚未通过本文件验证。

## 更新本文件

从项目根目录运行（只读已有捕获和本地探测文件；不连接网络）：

```sh
python scripts/document_tools.py --schemas docs/tool-schemas.json --output docs/tools.md --observations .local
```

不传 `--observations` 时只生成 Schema 声明，不读取本地私有探测。请勿提交 `.local` 文件夹。
