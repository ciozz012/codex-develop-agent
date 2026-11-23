# develop-agent · 用 Codex 分步开发业务 Agent

在 Codex 里开发需要检索资料、调用工具或处理工单的 Agent 时，可以用这个中文 Skill 控制每轮工作的范围。第一次对话拆出能独立验收的功能，下一次只设计其中一个。设计、实现和验收都留下可在新对话接续的记录。

## 安装

**从 GitHub 安装。** 在 GitHub 网页上打开本仓库的 [技能目录](skills/develop-agent)，复制浏览器地址，然后在 Codex 中输入以下请求，并把最后一行替换为刚复制的地址。

```text
使用 $skill-installer，从下面这个 GitHub 目录安装 develop-agent。
粘贴技能目录的网址
```

**下载 ZIP 安装。** 在仓库首页选择 **Code → Download ZIP**，解压后打开 `skills` 文件夹。将里面完整的 `develop-agent` 文件夹复制到下表中的一个位置。目录不存在时先创建它。

| 谁能使用 | 安装后的入口文件 |
|---|---|
| 当前项目 | 项目根目录下的 `.agents/skills/develop-agent/SKILL.md` |
| 当前用户的所有项目（Windows） | `%USERPROFILE%\.agents\skills\develop-agent\SKILL.md` |
| 当前用户的所有项目（macOS / Linux） | `~/.agents/skills/develop-agent/SKILL.md` |

在目标项目打开 Codex，在输入框键入 `$develop-agent` 即可调用。若安装后暂时看不到，重启 Codex。接续指令提取工具和离线回归示例使用 Python 3.7 或更新版本，均只用标准库。[Codex 官方安装与发现说明](https://developers.openai.com/codex/skills/)

## 第一次使用

在自己的项目里，用下面这段话开始拆分功能。

```text
使用 $develop-agent。我要做一个员工服务助手，能回答手册问题，在员工明确要求时起草工单。
这轮只拆功能。每项写清依赖什么输入、能检查什么结果，推荐先做哪一项。
把清单和下一轮接续指令保存到 docs/agent/plan.md，然后停下。
```

新开一次对话，用同一份清单继续设计第一个功能。

```text
使用 $develop-agent，读取 docs/agent/plan.md。只设计清单指定的第一个功能，
写清输入、结果、失败处理和验收条件，交付设计后停下。
```

想先试用现成例子，可以把[员工服务助手示例清单](examples/employee-assistant/docs/agent/plan.md)复制到练习项目的 `docs/agent/plan.md`，再发送第二段请求。清单里的员工、手册和金额均为虚构。

如果清单已经写好了唯一下一步，新对话里说「使用 $develop-agent，接着 docs/agent/plan.md 继续」即可。要看 Codex 将接到哪一步，可以在本仓库根目录运行下面的命令。它只打印示例计划里的接续指令，保留功能范围和停止点。找不到唯一指令时会说明原因，由 Codex 回看清单确定当前项。

```sh
python skills/develop-agent/scripts/read_handoff.py examples/employee-assistant/docs/agent/plan.md
```

示例指令里的 `docs/agent/plan.md` 以练习项目文件夹 `examples/employee-assistant/` 为起点，指的就是传给工具的那份计划。

## 包含的内容

- [主说明](skills/develop-agent/SKILL.md)定义分会话开发的步骤和交接格式，按当前问题选读一份专项参考。
- [专项参考](skills/develop-agent/references)覆盖工具输入输出、身份与权限、写入恢复、知识检索、停止条件、运行记录、回归用例和模型评测。
- [离线回执示例](skills/develop-agent/examples/receipt_regression.py)展示如何用同一组测试检查故障版和修正版。在仓库根目录运行下列命令。故障版预期有两项失败，修正版预期三项全部通过。

```sh
python skills/develop-agent/examples/receipt_regression.py --version faulty
python skills/develop-agent/examples/receipt_regression.py --version fixed
```

Skill 使用当前 Codex 会话已有的文件和命令执行能力。示例可在本地运行。手册数据库、工单接口等业务工具由各项目自行接入。
