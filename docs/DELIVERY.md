# 麦门 Code · 交付说明

交付候选版日期：2026-10-15（北京时间）。

**奶蛙会记住你的口味，越点越懂你。** 本项目是通过真实麦当劳 MCP 点餐的 Skill，附带零第三方 Python 依赖的终端入口。项目仓库为 [Rxwkovo/mcd-code](https://github.com/Rxwkovo/mcd-code)，报名尚未提交。

## 收到源码后

解压源码包，进入包含 `mcd.py` 的 `mcd-code` 目录，使用 Python 3.10+：

```powershell
python scripts/release_check.py --official
python mcd.py --json --command "/help"
```

上面两条只检查文件或帮助，不执行点餐。正式使用按 [README.md](../README.md) 安全输入 `MCD_TOKEN`；Skill 加载 [SKILL.md](../SKILL.md)，先取得用户本次位置，再选附近营业门店。Agent 使用同一个 `python mcd.py --json` 进程完成多步点餐。

## 本次交付内容

- 真实门店、菜单、优惠券、官方算价、预算推荐、1024 挑战、点餐预览与确认、查单。
- 奶蛙字符动画与笑声、11 种角色轮换的静态 SVG 日卡；素材标注网络来源，出处见 [素材说明](../assets/SOURCES.md)。
- 本机偏好记忆：主动口味与后续真实订单选择，支持查看、纠正、忘记、暂停和清空；个性化选餐由 Skill 宿主理解，不设固定偏好分数。
- 玩家次数与趣味称号，由宿主根据真实事实灵活维护。
- 创建订单成功后，提醒用户到麦当劳 App「我的订单」查看或进入待支付订单付款。
- 官方原样声明、MCP 集成说明、环境变量占位符配置、实际工具 Schema、验证清单和四行报名草稿。

源码包不包含 `.local/`、`outputs/`、Token、私有订单响应、操作数据库、本机偏好或开发测试归档。首次安装没有预置口味或用户位置。

## 验收边界

已有真实门店、菜单、券、算价、预算/目标挑战与日卡记录；一笔真实点餐经用户确认创建，并在当时查单核实为待支付，未执行支付。偏好存取、独立进程读取、去重、忘记和暂停等本机检查已通过。完整记录见 [VERIFICATION.md](VERIFICATION.md)。

宿主跨会话个性化体验、最近新增的订单后偏好保存与 App 提醒分支，尚未通过再次真实下单验收；取消、真实领券、真实积分兑换、支付/取餐和外送端到端也未验收。不能将这些项目对外表述为已实测。为交付检查不重复创建订单。

## 由你完成的报名步骤

1. 核对 [公开仓库](https://github.com/Rxwkovo/mcd-code) 默认分支，确保 README.md、CONTEST_DECLARATION.md、MCP_INTEGRATION.md 和 mcp-config.example.json 直接位于根目录；包含 `.github/`、`.gitignore`、`.gitattributes`。
2. [报名草稿](registration-issue.md) 已填入真实仓库地址，退出登录后检查仓库可读，并查看 GitHub Actions 结果。
3. 标题使用 `【参赛申请】麦门 Code（mcd-code）`，正文复制草稿全部四行，到 [官方 Issue 页面](https://github.com/M-China/mcd-developer-innovation-challenge/issues/new) 由本人提交。字段与内容同一行，项目地址使用纯 URL。
4. 等待官方在 Issue 下回复成功通知；提交 Issue 不等于报名成功。[报名准备清单](SUBMISSION.md) 列出发布和资格核对项。

根据 [官方活动规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)，报名截止为 **2026-10-25 23:59（北京时间）**。保持仓库公开可访问；不改官方声明，不把代码 MIT 许可套用于第三方素材。
