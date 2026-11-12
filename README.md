# dsh-search-pull

让 DeepSeek Harness 的 agent **更愿意先联网再回答**——尤其是开发类问题：现成的开源实现优先复用，而不是凭记忆从头推导。

不换搜索后端、不要第三方 key，只往系统提示里加一条固定规则。

## 做法

一条**静态** prompt section（`systemPrompt.section`）：

- 遇到「怎么做 / 哪个更好 / 有没有现成方案 / 这个报错怎么修 / 库或 API 怎么用 / 现在什么版本」先 `web_search`；
- 若本轮尚未检索，先搜一轮（1-3 次）；纯本地文件操作不必联网；
- 没联网核对过的回答，在开头标「未联网核对」。

另有一个 `tools/execute` 监听，只在开启 `debugFile` 时记一行审计，**不碰 prompt**。

## 为什么是静态的

动态注入（每轮变化的 context，或伪造一条 user 消息）会改动系统提示前缀，导致缓存前缀失效——失效点之后的系统提示和全部历史都要按未命中重新计费。每轮两次翻转就是两次全量重算。

静态文本永不变，首轮之后始终命中缓存，代价只有固定的约 245 个字符。代价是它无法"搜完就消失"，这件事改由措辞承担（"若本轮尚未做任何检索"）——模型看对话就知道自己搜过没有。

> 历史教训：早期版本用 `agent/pre-step` 伪造 user 消息做可见提醒，消息结构不合法，长消息回合直接报错。已废弃。

## 安装 / 卸载

从 GitHub 装（`--profile` 换成你自己的 profile 名，桌面端通常是 `desktop`，命令行版通常是 `web`）：

```bash
dsh plugin --profile web add https://github.com/StudentBuilding-Studio/dsh-search-pull
```

卸载：

```bash
dsh plugin --profile web remove dsh-search-pull
```

（还没发 npm；发了之后可以直接 `add dsh-search-pull`。）

## 配置

在 profile 的 `cordis.patch.yml` 里给这行加 `config:`：

| 键 | 默认 | 说明 |
|---|---|---|
| `mode` | `always` | `off` 则不注册任何 prompt section |
| `order` | `108` | 规则节排序位 |
| `requireUnverifiedLabel` | `true` | 是否要求「未联网核对」标注 |
| `searchTools` | `["web_search"]` | 审计时算作检索的工具名 |
| `sectionText` | `null` | 整段替换规则 |
| `debugFile` | `null` | JSONL 审计文件路径 |

审计文件是唯一能看到它干了什么的地方——它本来就不进对话记录。

## 验证方式

装好后所有回合都带着这条规则，不需要额外确认。想看它有没有真的影响行为，两种办法：

1. 问一个开发类问题（「XX 库现在推荐哪个版本」），看它有没有先调 `web_search`；
2. 开启 `debugFile`，审计文件里会有 `mount` 和每次 `search-observed` 一行。
