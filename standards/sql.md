# SQL 规范（MySQL / 人大金仓 KingbaseES）

## 幂等铁律

- 上线脚本必须可重复执行，不报错、不产生重复数据
- 插入：`INSERT ... SELECT ... WHERE NOT EXISTS` 或 `ON DUPLICATE KEY UPDATE`
- 更新/删除：WHERE 条件带业务唯一键，加存在性判断
- DDL：先查 information_schema 判断列/索引是否存在再执行（金仓用 PG 系统表）

## 上线流程

1. 执行前备份目标表（`CREATE TABLE x_bak_YYYYMMDD AS SELECT ...`）
2. 线上库直连执行前，先在本地/测试库跑一遍验证幂等（跑两遍）
3. 记录：执行的库地址、脚本内容、影响行数，写入当日反馈

## 书写

- 大写关键字，一个条件一行，复杂查询必写注释
- 禁 `SELECT *` 于代码中；统计/修复脚本可用
- 涉及 KingbaseES（haishihoutai）注意 PG 语法差异（如 `||` 拼接、序列）
