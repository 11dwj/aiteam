# 项目总结：IPAS_JK 常州经开区招商项目管理平台（kecu）

> 为常州经开区科技和投资促进局开发的政务系统，核心是"招商项目全生命周期管理 + 招商人员绩效考核"。本总结自包含。

## 一、业务全貌

组织结构为七个招商处室（综合/外资/高端装备/材料电子/生命健康/服务业/科技人才）。功能模块：

1. **招商项目管理**：新增/返投/增资项目录入（类型 1/2/3），产业类型（制造业/服务业/人才类），项目详情与状态流转
2. **绩效考核**（对应《2025 年招商人员绩效考核实施办法》）：新增有效信息审核、落地项目质量审核（6 维度评分）、中天园区质量审核、产业研究质量审核、到账外资质量审核、个人/团队/部门绩效汇总
3. **到账外资管理**：到账记录、审核、合作项目关联
4. **产业研究管理**、**接待差旅管理**（公务接待/差旅申请审核）
5. **工作流审批**：Warm-Flow 流程设计器
6. 系统管理：RBAC、菜单、部门数据权限

## 二、技术架构

- 后端：RuoYi-Vue-Plus 5.5.1 / JDK 17 / Spring Boot 3.5 / MyBatis-Plus / Sa-Token / Warm-Flow / SnailJob / Redisson
- 前端：plus-ui（Vue 3 + TS + Vite + Element Plus + Pinia + UnoCSS + ECharts）
- **双数据源**（最大架构特点）：master（ruoyi_ipas 系统库）+ ipas_jk（业务库），Service 层 `@DS("ipas_jk")` 切换——漏注解会查错库

## 三、核心数据表

project/project_detail、info（新增有效信息）、land（落地质量）、middle_park、personal/team/department_assessment、assessment_result、account（到账外资）、account_cooperation、research、reception、travel + 若依系统表。

## 四、关键业务规则（评分引擎）

- InfoScoreCalculator / LandScoreCalculator 独立成 util，评分规则与 CRUD 解耦
- 项目创建/更新时 state<4 自动重算；**state≥4 后评分冻结**（进入深度审核，已审核数据不被覆盖）
- 返投项目得分 = 原得分 × 0.7；多选字段逗号分隔（如 '1,2'）

## 五、部署

开发 `start-all.bat`（自动起 MySQL/Redis/前后端），后端 8080、前端 80；生产 `mvn clean package` 出 jar + 前端 `npm run build:prod` + Nginx 反代；生产库 192.168.0.20:3317；有 Docker 配置。

## 六、经验沉淀

- 双数据源 + @DS 模式：业务库独立备份迁移方便，但必须规范"业务 Service 一律加 @DS"
- "评分冻结"状态机机制保证审核数据稳定
- 代码生成器 + Bo/Vo 分层让政务 CRUD 效率极高
- DB 变更强制提交 SQL 脚本到 sql/功能实现部分/（交接文档四类目录：设计/实现/使用/测试）——值得推广
- 坑：部分前端页面处室下拉是硬编码静态数据，组织调整需改代码

## 七、开发历程（2026-07-29 接手）

**07-29 接手第一天**：环境排查——系统 JAVA_HOME 指向 JDK8 但项目需 17+，用户要保留系统 JDK8 → 在 start-dev.bat 内 `set JAVA_HOME` 指向 JDK25（脚本级隔离不改系统变量）；Maven 多模块首次必须根目录 `mvn clean install -DskipTests` 否则找不到内部模块。

**07-30 数据本地化**：mysqldump 从远程 192.168.0.20:3317 备份双库到本地（ruoyi_ipas 62 表 + ipas_jk 74 表）；application-dev.yml 采用"本地生效 + 远程注释保留"双份结构随时切回。发现架构问题：业务表不继承 BaseEntity（无审计字段）、部分绩效接口 @SaCheckPermission 被注释放开、全局 RSA+AES API 加密。

**08-04 改部门名称影响评估**（未执行，识别风险）：① 高危——PersonalAssessmentServiceImpl 等硬编码处室名按 dept_name 实时匹配，改名即考核分组失效；② 中危——几乎所有业务表冗余存 department_name 快照不级联更新。安全改名三步：先改代码常量 → 按 department_id 批量刷冗余名 → 最后改 sys_dept。

**08-10 2026 版考核办法与代码对齐**：先校对文档本身（错别字/附件编号错乱/权重矛盾），再列 7 步同步计划——团队权重差异（中天园区 10%+产业研究 10% → 重点区域拜访 10%+泛法语区招引 5%+产业研究 5%）、岗位月薪与"年薪×65%÷12"对不上、代码用 `post.contains("总监")` 字符串匹配岗位很脆弱。

**09-04 网络安全专项治理**：解读区党群工作部红头通知，生成两份可填写报送材料（网络日志留存自查表：通用日志≥6个月/政务应用≥1年，19 项指标；政务信息系统网络安全责任书：建设/集成/运维/安全服务四方责任）。拉取 dev 分支 +8827 行新功能。

**生产环境**（运维手册）：向日葵→堡垒机→两台龙蜥 7.9 服务器（64: WEB+Nginx，配置 czjxkh.conf；65: 数据库）。前端更新 = dist.zip 解压 + nginx -s reload；后端 = target.zip + systemctl restart czjxkhbackend.service。

**环境问题速查**：Navicat 报 2059 caching_sha2_password（旧客户端，可改 mysql_native_password）；yml 改了"不生效"是 target/classes 缓存（mvn clean）；admin 密码 BCrypt 无法反推只能重置；192.168.0.20 是共享库改动需确认。
