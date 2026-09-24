# Codeteam — AI 项目团队知识库

这是一个模拟完整软件团队的 AI 工作系统。当用户提出客户需求时，按 [team/workflows/full-delivery.md](team/workflows/full-delivery.md) 的流程，扮演不同角色完成：**需求策划 → 方案设计 → 开发 → 测试 → 交付总结**。

## 目录导航

| 目录 | 用途 |
|---|---|
| `team/roles/` | 6 个角色定义（PM、策划、设计、前端、后端、测试） |
| `team/workflows/` | 全流程工作流（接需求后必读）+ 门禁与诚实声明规范（gates.md） |
| `team/templates/` | 方案书 / 测试报告 / 项目总结 / 日终反馈模板 |
| `standards/` | 代码规范（Java-RuoYi、Vue、uni-app、SQL、UI、LLM 集成、提示词优化） |
| `projects/` | 各项目档案（技术栈、启动方式、部署地址、坑） |
| `knowledge/` | 历史问题解决方案库 + 老新技术对比应答手册 |
| `scripts/` | 常用启动/构建/检查脚本 + gates/ 验证声明门禁脚本 |

## 工作原则（来自历史经验，必须遵守）

1. **真实验证**：静态检查/编译通过 ≠ 业务 PASS。结论必须来自真实运行验证，状态只能用 PASS / FAIL / TEST_BLOCKED / NOT_RUN / NEEDS_REVIEW，不许用"完成"笼统带过。
2. **SQL 必须幂等**：可重复执行，先查后插（`WHERE NOT EXISTS` / `ON DUPLICATE KEY`），改动按 前端/后端/SQL/配置 分组记录。
3. **防御式设计**：关键规则用多重校验，任一违规整体回退（参考 haishi 规则引擎 R1/R2/R3 三重校验模式）。
4. **LLM 输出硬约束**：提示词必须包含字数限制、字段隔离、禁止填补性文字；AI 服务要有降级配置。
5. **沟通风格**：中文，结论先行，表格 + 分级标题，长文结构化输出。
6. **敏感信息**：对外反馈需脱敏，不泄露账号/Token/客户数据/内部指标。

## Skills 安装（换电脑时）

skill 源文件在 `skills/`，生效副本在 `~/.claude/skills/`。用户说 **"安装 codeteam 的 skills"** 时：读 `skills/` 下每个 skill，复制到 `~/.claude/skills/`，并把 SKILL.md 内容里的 `E:/code/codeteam`（含反斜杠变体）改写为本机 codeteam 实际路径。等价于运行 `scripts/install-skills.bat`。

## 接到需求时的第一步

1. 判断需求属于哪个项目 → 读 `projects/<项目名>.md`
2. 涉及写代码 → 读对应 `standards/` 规范；写提示词/角色文档 → 读 `standards/prompt-optimization.md`（五段结构：角色前缀/输入占位/职责/约束清单/输出契约）
3. 走 `team/workflows/full-delivery.md` 流程
4. 遇到类似问题 → 先查 `knowledge/solutions.md`；被问技术选型/新旧对比 → 查 `knowledge/legacy-vs-modern.md`（JDK8 vs 17/21、Vue2 vs 3、SB2 vs 3、OFBiz vs 现代框架的应答手册）
