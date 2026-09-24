# 项目总结：阳光窑观（剑苑小区）阳光物业投票系统（toupiao）

> 面向住宅小区的"阳光物业管理平台"，核心是业主投票表决系统 + 物业资金阳光公开。本总结自包含。

## 一、业务全貌与投票流程

物业/管理端发起投票（选小区、关联事项）→ 后台审批（通过/驳回）→ 业主小程序实名认证（业主认证）→ 按房屋确权投票/附议 → 达到附议门槛进入执行 → 结果用于动用维修资金/公共收益的项目（方案审批 → 项目完成/归档），全程资金流水公开可查（阳光监管）。

## 二、功能模块

1. **投票管理**：发起、列表、附议（VoteSecondment）、联合署名（VoteCosigner）、投票记录、审批
2. **基础信息**：小区/楼栋/房屋（Excel 批量导入）/业主（认证）/物业公司
3. **资金管理**：资金账户、维修资金使用、公共收益收入/支出、缴费记录
4. **项目管理**：方案管理、项目（完成/取消/归档）、项目档案
5. 统计报表导出、小区资金画像、通知公告、短信验证码登录（翼企云 SMS 网关）

## 三、技术架构

- PC 管理端：RuoYi-Vue（Java 8 + Spring Boot + MyBatis + Vue2 Element UI + MySQL utf8mb4 + Redis），@PreAuthorize + v-hasPermi 按钮权限
- 业主端：uni-app 小程序——登录/注册、业主认证、选小区、投票列表（维修资金/公共收益子页）、法律法规、公告、个人中心
- 核心表：t_vote / t_vote_record / t_vote_secondment / t_vote_cosigner、t_community / t_building / t_house / t_owner / t_property_company、t_fund_account / t_maintenance_fund_usage / t_public_revenue_income/expense / t_payment_record、t_project / t_project_plan / t_project_archive + sys_* 系统表

## 四、部署

deploy/ 一键脚本：打包后端/打包前端/启动服务/更新并重启 .bat + nginx.conf 示例；另有生产安全加固脚本（deploy-prod-security.bat、nginx-security-config-example.conf）。

## 五、经验沉淀

1. **ClaudeCode "AI 员工"工作体系**：CLAUDE.md + 规范文档自动加载、按 5 大任务类型（功能开发/BUG 修复/数据处理/权限配置/界面优化）走标准流程、Todo 清单、对话记录归档按日期——完整的 AI 协作工程化实践
2. analysis/detailed_analysis.py 用脚本统计 AI 工作记录（任务分类/模块分布/质量指标），把 AI 工作量可量化
3. 菜单/权限全走**增量 SQL 脚本**并配执行说明文档；权限标识 `模块:功能:操作` 三段式
4. 质量红线：BigDecimal/Integer 空值检查、全部接口 @PreAuthorize、事务 @Transactional、SQL 用 #{} 防注入
5. 历史数据迁移（房屋 Excel 花名册）独立成 Python 脚本，不进业务代码

## 六、核心业务细节（07-30 文档化时确认）

物业→小区→楼栋→房屋四级；业主认证按产权面积占比；**电子投票双指标计票（人数+面积，普通事项过半、重大事项 2/3）**；状态机：待附议→审核→发布→投票→结束→出结果，联署附议机制；公共收益阳光公示、维修资金缴存/使用/分摊、工程项目闭环。

**环境搭建三个实际故障（07-29）**：① application.yml 上传路径写死旧机器 D:/pythonProject7 → 改本机路径否则附件上传报错；② MySQL80 端口被改成 1111、root 密码不符 → my.ini 改回 3306 + --init-file 重置（注意影响其他连 1111 的程序）；③ Navicat 2059 认证插件 → 改 mysql_native_password。
