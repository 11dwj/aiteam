# Skills 源文件夹（随 codeteam 文件夹可移植）

这里是 4 个 skill 的**源文件**，安装后生效的是 `~/.claude/skills/` 下的副本。

| Skill | 用途 |
|---|---|
| start-project | 接客户需求，启动策划→设计→开发→测试→总结全流程 |
| lookup-solution | 遇到问题先查 knowledge/solutions.md 和项目档案 |
| daily-feedback | 生成日终脱敏工作反馈 |
| project-summary | 项目总结并沉淀知识库 |

## 换新电脑

方式一：双击运行 `../scripts/install-skills.bat`（自动复制到 `~/.claude/skills/` 并把 SKILL.md 里的根路径改写为本机实际路径）。

方式二：在 codeteam 目录下对 Claude 说 **"安装 codeteam 的 skills"**，AI 会读本文件夹、复制到 `~/.claude/skills/`、把 `E:/code/codeteam` 改写为本机路径。

## 修改 skill 后

改这里（源），然后重新运行 install-skills.bat 同步到用户目录。
