---
name: start-project
description: 接到客户需求后启动完整交付流程（策划→设计→开发→测试→总结）。当用户描述一个新需求、客户反馈、要加功能或修 bug 且希望走完整流程时使用。
---

# 启动项目交付流程

1. 读 `E:/code/codeteam/team/workflows/full-delivery.md`，按阶段 0-5 执行
2. 定位项目：读 `E:/code/codeteam/projects/index.md` 找到对应项目卡片；未匹配则询问用户
3. PM 角色先做需求复述 + 工单分级（S/M/C），向用户确认后再继续
4. M/C 级输出方案书到目标项目 `docs/` 目录（模板：`E:/code/codeteam/team/templates/requirement-plan.md`）
5. 开发前读对应规范（standards/ 下 backend-java / frontend-vue / miniapp-uniapp / sql / ai-llm）
6. 测试报告 + 日终反馈 + 项目总结按模板产出
7. 全程遵守 `E:/code/codeteam/CLAUDE.md` 的工作原则（真实验证、SQL 幂等、防御式设计、脱敏）

若目标项目有自己的 CLAUDE.md / .claude/ 规则（如 haishihoutai、ruoyi-warmflow-base），项目规则优先。
