---
name: daily-feedback
description: 生成日终脱敏工作反馈（按工单分组：改动文件/验证命令/结果状态），可直接转发负责人。当用户说"日终反馈"、"今天工作总结"、"生成反馈"时使用。
---

# 日终反馈

1. 汇总当日（或本次会话）处理的工单
2. 按模板 `E:/code/codeteam/team/templates/daily-feedback.md` 输出：
   - 每工单：改动文件按 **前端/后端/SQL/配置** 分组、验证命令、结果状态
   - 状态只用：PASS / FAIL / TEST_BLOCKED / NOT_RUN / NEEDS_REVIEW
   - 禁止用"完成"笼统带过
3. 脱敏检查：删除/替换账号、Token、密码、客户敏感数据、内部指标
4. 需发布/需配合事项单独列出（如"小程序需重新构建发布才生效"）
