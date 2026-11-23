# 设计一个工具的输入输出契约

先用一句话写明工具完成什么业务动作、调用成功的证据，以及调用可能改变什么状态。检查现有工具定义和消费返回值的代码，保留调用方依赖的字段与语义。下面以“保存工单草稿并返回草稿号”为例。项目有现成类型或错误约定时沿用它。

## 请求到达执行层之前

列清每个参数的类型、必填性、取值限制及来源。区分字段缺失、显式传入 null、空白字符串和类型错误。用户身份等受信值由服务端取得。模型只能请求创建草稿，提交工单属于另一个动作。

示例中，用户需要提供有内容的标题，描述可省略。调用方在取不到标题时先追问。若 SDK 或服务端已经收到无效参数，在进入保存逻辑之前校验，并由适配层将校验结果转成调用方能处理的状态。以下是应用层 JSON Schema；接入具体模型服务时，核对其支持的关键字和可选字段规则。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "properties": {
    "title": { "type": "string", "pattern": "\\S" },
    "description": { "type": "string" }
  },
  "required": ["title"],
  "additionalProperties": false
}
```

## 调用方如何解释结果

给每种会改变下一步的结果一个稳定的状态值，规定它必须带的字段、执行到哪一步，以及调用方该做什么。可读提示用于展示，程序根据结构化字段分支。下面是整个调用流程的返回契约，包括参数适配层的提前返回。

| 示例返回 | 何时返回 | 调用方下一步 |
|---|---|---|
| `{"status":"ok","draft_id":"D17"}` | 存储层已确认保存并给出草稿号 | 展示草稿号，可用它打开草稿 |
| `{"status":"needs_input","field":"title"}` | 只缺少标题，尚未调用保存 | 向用户询问标题，再组成完整请求 |
| `{"status":"invalid_input","field":"submit"}` | 有未声明字段、非法类型或空白标题，尚未调用保存 | 指出有问题的字段，修正请求。整个请求被拒绝 |
| `{"status":"failed","code":"write_rejected"}` | 存储层明确拒绝且确认未写入 | 报告保存失败；按业务错误码决定后续处理 |
| `{"status":"unknown","operation_id":"R17"}` | 写请求已发出，回执丢失，暂时无法确认是否写入 | 用操作编号核对结果，向用户说明待确认 |

以下响应 Schema 使各分支互斥。成功必须有草稿号；缺信息、失败、待确认的结果均不能夹带成功凭据。示例中的状态名和字段名可按项目约定替换。

```json
{
  "$schema": "https://json-schema.org/draft/2020-12/schema",
  "type": "object",
  "required": ["status"],
  "oneOf": [
    {
      "properties": { "status": { "const": "ok" }, "draft_id": { "type": "string", "pattern": "\\S" } },
      "required": ["draft_id"]
    },
    {
      "properties": { "status": { "const": "needs_input" }, "field": { "const": "title" } },
      "required": ["field"]
    },
    {
      "properties": { "status": { "const": "invalid_input" }, "field": { "type": "string", "pattern": "\\S" } },
      "required": ["field"]
    },
    {
      "properties": { "status": { "const": "failed" }, "code": { "type": "string", "pattern": "\\S" } },
      "required": ["code"]
    },
    {
      "properties": { "status": { "const": "unknown" }, "operation_id": { "type": "string", "pattern": "\\S" } },
      "required": ["operation_id"]
    }
  ],
  "unevaluatedProperties": false
}
```

设计阶段列出每个分支的样例、预期动作和验收证据。实现阶段从实际入口送入同样的请求，分别核对返回结构和存储状态。例如，传入额外的 `submit: true` 时保存与提交次数均为零；合法请求生成一条可按回执号查询的草稿，正式工单数仍为零。Schema 检查只能验证消息结构，写入结果要从下游核对。

关于字段声明、必填项和额外字段的具体语义，参见 [JSON Schema 对象说明](https://json-schema.org/understanding-json-schema/reference/object)。
