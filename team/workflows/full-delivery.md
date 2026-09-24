# 全流程交付工作流

客户需求进来后，按以下阶段依次推进。每个阶段有对应角色和产出物，产出物写入项目的 `docs/` 目录。

## 阶段 0：需求受理（PM）

0. 需求模糊时先做**元提示词改写**（见 `standards/prompt-optimization.md` 第五节）：把一句话模糊需求改写成结构化提示词（变量显式化、约束按维度表补齐、输出契约明确），向用户确认后再继续
1. 判断需求来源（现场反馈 / 红头文件 / 领导口头），还原完整需求原文
2. 定位所属项目，读 `projects/<项目>.md` 了解技术栈与约束
3. 工单分级：**S**（简单，单点修改）/ **M**（一般，需方案）/ **C**（复杂，需方案+评审+反例验证）
4. S 级直接进入开发；M/C 级先输出方案书（模板：`team/templates/requirement-plan.md`）

## 阶段 1：策划（策划师）

- 可行性研究：列出现有条件（数据样本、接口、配置、权限）是否满足
- 涉及 AI 功能：参考 haishi 模式——历史样本 → 规则矩阵 → LLM 生成 → 人工校准
- 输出：需求方案书（含改动范围：前端/后端/SQL/配置 四组清单）

## 阶段 2：设计（设计师）

- 移动端 → 读 `standards/ui-mobile.md`（设计令牌体系）+ `standards/ui-anti-ai.md`（去 AI 味）
- 管理后台 → 参照若依 H+/element 风格，不另起炉灶
- 输出：页面原型（HTML 静态稿优先，参考 guifan/能源/ 的原型做法）

## 阶段 3：开发（前端 + 后端并行）

- 后端：读 `standards/backend-java.md`；AI 服务读 `standards/ai-llm.md`
- 前端 PC：读 `standards/frontend-vue.md`；小程序：读 `standards/miniapp-uniapp.md`
- SQL：读 `standards/sql.md`，必须幂等
- 每完成一组改动即编译验证（`mvn compile -DskipTests` / `node --check` / `npm run build:prod`）

## 阶段 3.5：工单门禁（所有角色）

按 `team/workflows/gates.md` 执行：开工前入口确认双证 + 改动契约；复杂 bug 假设驱动调查（两轮无新事实即停）；收尾跑 `scripts/gates/` 校验脚本（验证声明 / 质量 / 安全 / 调试残留）。

## 阶段 4：测试（测试工程师）

- 按 `team/templates/test-report.md` 输出测试报告
- C 级工单必须含**反例/失败路径**验证（比如规则引擎：构造违规数据确认整体拒收）
- 验证状态只用：PASS / FAIL / TEST_BLOCKED / NOT_RUN / NEEDS_REVIEW

## 阶段 5：交付与总结（PM）

1. 日终反馈：按 `team/templates/daily-feedback.md` 生成可转发负责人的脱敏反馈
2. 项目总结：按 `team/templates/project-summary.md`，沉淀到 `knowledge/`
3. 遇到新问题+解决方案 → 追加到 `knowledge/solutions.md`
4. 上线后 badcase 回流：误判样本 → 补豁免规则 → 回归测试（形成闭环）
