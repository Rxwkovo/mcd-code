# 报名准备清单

核对日期：2026-10-15，UTC+08:00。

交付入口：[DELIVERY.md](DELIVERY.md)。项目仓库为 [Rxwkovo/mcd-code](https://github.com/Rxwkovo/mcd-code)，报名草稿已填写该地址；报名尚未提交。

官方依据：[活动 README](https://github.com/M-China/mcd-developer-innovation-challenge)、[完整规则](https://github.com/M-China/mcd-developer-innovation-challenge/blob/main/activityGuidelines.md)。报名及排名截止为 **2026-10-25 23:59，北京时间**。以官方后续发布为准。

## 已整理的材料

| 官方要求或展示项 | 本项目文件 | 状态 |
| --- | --- | --- |
| 项目介绍、安装、示例和目标用户 | README.md | 已具备 |
| 官方参赛声明，文件名和内容不变 | CONTEST_DECLARATION.md | 已具备，交付检查联网逐字节核对 |
| 实际 MCP Server、Tool、流程和价值 | MCP_INTEGRATION.md | 已具备 |
| 脱敏 MCP 配置，仅环境变量占位符 | mcp-config.example.json | 已具备，Authorization 为 Bearer ${MCD_TOKEN} |
| 源代码、可运行内容与 Skill | mcd.py、mcdcode/、SKILL.md、scripts/ | 已具备，正式路径仅使用真实接口 |
| 真实调用与交易证据 | docs/VERIFICATION.md、两个真实验收 JSON | 已具备；订单创建后查单核实待支付，未支付 |
| 动画、笑声与 11 种日卡形象 | assets/ | 已纳入公开包，来源与条款单独说明 |
| WorkBuddy 专项材料 | workbuddy.md | 当前未使用 WorkBuddy，不伪造对话；不按该条件申报专项奖励 |
| 报名正文 | docs/registration-issue.md | 四行格式已整理，项目 URL 已填写 |

## 发布前仍需确认

1. **核对公开仓库及必需文件。** 仓库为 https://github.com/Rxwkovo/mcd-code；检查默认分支根目录、公开访问和 Actions 结果。代码上传不等于报名成功。
2. **第三方素材的授权依据。** 官方声明要求原创或合法授权；BigNaiWa README 目前仅写“仅供学习娱乐使用”，原视频及角色也保留各自权利。现有材料有来源说明，但没有提供可核对的原权利人授权证明。不能把开源代码、网络搜集或二创致敬视为素材授权已齐备。
3. 参赛人的身份、年龄及活动资格由本人核实；不要在公开仓库上传身份证、手机号或兑奖信息。

上述材料检查通过不等于官方资格审核通过；尤其不替参赛者作素材权利或身份声明。

## 操作顺序

1. 本机执行 `python scripts/release_check.py --official`，确认交付检查通过。
2. 使用 `python scripts/package_source.py` 生成源码包。解压后，上传 **mcd-code 目录内部文件**，保证仓库根目录直接看到 README.md 等必需文件；不要多包一层目录。
3. 在 GitHub 将仓库设为 Public，并在退出登录或无痕窗口确认可以读取必需文件。不要上传 `.local/`、`outputs/`、凭据、订单、支付链接或操作状态库。
4. `docs/registration-issue.md` 已填入 https://github.com/Rxwkovo/mcd-code，提交前再核对仓库地址。
5. 打开 [官方新建 Issue 页面](https://github.com/M-China/mcd-developer-innovation-challenge/issues/new)，使用下方标题，粘贴草稿正文后由本人提交。
6. 查看官方系统在 Issue 下的成功或失败通知；创建 Issue 本身不等于报名成功。发布后检查本仓库的 GitHub Actions 结果。

建议 Issue 标题：**【参赛申请】麦门 Code（mcd-code）**

正文保留四行标准格式，字段标签和内容写在同一行，项目地址使用纯 URL，不使用 Markdown 链接。草稿之外的说明不粘贴进报名正文。

## 正式使用前

配置 Python 3.10+ 和当前进程 MCD_TOKEN，加载 Skill 后先提供本次城市/地标或附近门店。独立终端运行 `python mcd.py`；Agent 使用 `python mcd.py --json` 保持同一会话。下单、取消、领券、兑换仍逐笔确认，不能为了报名重复创建订单。
