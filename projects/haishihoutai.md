# 项目总结：jyhsxt 海事业务后台（haishihoutai）

> 海事解封业务的管理后台 + 指挥大屏 + 数据同步/推演中枢，与解封智能体（[haishi](haishi.md)）通过 HTTP 对接。对外文档统一称"业务系统"，信创国产化交付，以"可演示里程碑"驱动（M0 环境基线 ✅ → M1 业务骨架 → M2 业务闭环 → M3 交付准备）。本总结自包含。

## 一、技术架构（信创硬约束）

RuoYi 4.8.3 单体版二开：**JDK 17 + Spring Boot 4.0.6 + Shiro（非 Spring Security）+ MyBatis/PageHelper + Thymeleaf 前后端不分离（H+/jQuery/Bootstrap，禁引 Vue/React）**。

- 数据库**人大金仓 KingbaseES**（PG 模式，端口 54321，kingbase8 JDBC 手动 install 本地 Maven）
- 金仓适配要点：禁 MySQL 语法（`find_in_set`→`position`、`auto_increment`→`IDENTITY`、`blob`→`bytea`、`char(1)` 比较带引号）；SQL 头部必须 `SET client_encoding TO 'UTF8'`（否则 Windows ksql 报错）；Druid wall filter `db-type: postgresql` 三项配置不能删（否则 `SELECT *` 被误拦）；PageHelper 方言 postgresql
- 版本控制 **SVN**：提交前先 update、一次提交一件事、5 类前缀（feat/fix/refactor/chore/docs）
- 未来目标：麒麟 OS + 东方通 + 国产 JDK，禁绑定厂商特性

## 二、业务模块

- **biz 包**：案例库（BizCase/Strategy/Risk）、事件、阈值、区域、推演日志、智能体调用日志、大屏系列控制器（AIS 回放/区域/案例/事件/网格/台风/气象）+ 案例匹配（旧版等权打分保留给大屏 + 新版加权规则）
- **jyhs.closure（封航事件）**：6 个同步 job 从外部"数据服务管控系统"**单向定时同步**（上游 permitAll 未加固，不做反向推送）
- **jyhs.ais**：对接外部 AIS 接口，事件船舶快照 + 历史 + 同步审计
- **jyhs.suggestion**：解封建议引擎——按网格饱和度红→黄→绿、"先外围后核心"生成建议，输入=匹配案例+气象预警+台风+粒子流，自动生成+人工确认
- **jyhs.report**：报告/回填，含 Word 渲染；weather 气象日报；typhoon 台风路径；grid 网格分钟级统计
- **ai/java（交付版智能体）**：Python 版的**零依赖 JDK8 单 JAR 移植**（~740KB）——RuleEngine（16 格矩阵/核查/排程/兜底）、StrategyAiService（3 套并行 AI 生成+归一化+校验+单套兜底）、RagService（**60 条预计算向量打进 JSON，运行时只 embed 查询词、内存余弦，无向量库**）、公文模板不调 LLM、SimpleHttpServer（4 路由，与 Python 版接口一致）

## 三、与智能体对接（HTTP，智能体 :8000）

1. `POST /generate-report`：事件+气象+船清单+预报+可选风险案例 → 判定+核查+3 套策略+风险推演（AI ~25s / 纯规则 ~200ms）
2. `POST /generate-plan`：选定策略 → 公文 HTML（<50ms）
3. `POST /export-plan`：→ .doc，docUrl 落库
4. `POST /predict-risk`：历史案例风险点 → 本次风险点位概率时间窗

约定：能见度单位米、风为蒲福风级；核心气象项缺失=核查不过，次要项（水深/流速）缺失=降"人工确认"不阻断。

## 四、数据模型（biz_ 前缀，IDENTITY 主键 + 若依审计字段）

- v1 六张核心：biz_event（封航事件主表，后被取代）、biz_region 辖区、biz_threshold 阈值、biz_case 案例、biz_inference_log 推演日志、biz_case_strategy
- v3 多分局改造：biz_closure_event（带 org_code）、事件-分局配置、协作分局、组织/区域字典、同步审计
- 其他：biz_ais_event_ship(_history)、biz_match_rule 匹配打分规则、biz_screen_case、biz_case_risk_summary/point、biz_release_* 解封建议、biz_grid_* 网格、biz_typhoon、biz_weather_forecast、biz_backfill
- **关系链**：封航事件 → AIS 船舶快照 → 网格饱和度统计 → 案例匹配（match_rule 打分）→ 解封建议 → 调智能体生成报告 → 推演日志/公文 docUrl 回挂事件

## 五、关键业务决策

多分局同时使用：不做用户体系对接，用"大屏弹窗选择未完成封航事件"做事件级隔离（演示级强度）；数据口径=有事件维度的按 eventId 过滤、无维度按归属分局 org_code 反查、纯全局（台风/阈值/打分规则）共享；AI 服务无状态不需分局逻辑。

## 六、部署

金仓 createdb → ksql 导入若依+quartz 脚本 → mvn clean install -DskipTests → 运行 RuoYiApplication（:80，admin/admin123）；智能体独立进程 `java -jar haishi-ai.jar`（:8000）。

## 七、经验沉淀

- **若依→金仓信创迁移完整 checklist**（方言映射、client_encoding、Druid、PageHelper、代码生成器按 pg_class 适配）可直接复用
- **CLAUDE.md 作为"项目宪法"** 的实践：技术栈"是什么/不是什么"表、SVN 提交铁律、AI 协作偏好（探索性问题先给建议不动手、修 bug 不顺手重构）
- **Python 原型 → JDK8 零依赖单 JAR 交付**双轨模式：数据资产 JSON 化共用，三场景判定结果一致性验收
- "预计算向量打包进 JAR + 运行时只 embed 查询"是小样本 RAG 去向量库依赖的轻量做法
- 单向定时同步规避上游接口未加固的风险

## 八、开发历程与踩坑（2026-08-13 ~ 09-22）

**对接决策（08-17/18）**：智能体对接方式二选一——HTTP 独立进程（零侵入、可独立升级、挂了后台走规则降级）vs 9 个类拷进单进程（耦合），选前者。字段映射约定：`BizEvent.startTime→t0、eventType→reason、severity→level`；`weatherDesc` 是文字不能用于阈值判定，数值必须走 weather 字段；超时 90s（后调 180s）；`hold=true` 不是错误。

**关键 bug 案例表**：

| 现象 | 原因 | 方案 |
|---|---|---|
| 别人点"生成大屏案例"，弹窗弹在你页面 | biz_ais_history_task 全局共享无用户隔离 | sessionStorage 发起者标记（方案已定，暂缓） |
| SVN 拉 10 个冲突 | 同事提交 build/ 编译产物 | svn resolve --accept working + 建议 build/ 加 svn:ignore |
| 案例库 biz_case 是空架子 | 归档闭环未实现 | 向量库方案确认为正解而非临时方案 |
| 页面 404"权限不足"假象 | PC 访问的旧入口前端构建较旧缺新路由 | 重新 build:prod 部署或统一入口 |

**演进要点**：
- 辖区口径是"航段/分局段位"（南京/镇江/扬州/泰州/常州/江阴/靖江/张家港/南通/常熟/太仓共 11 段），风险预测按"辖区×时间窗"聚合段级 hotspots
- 大屏协作边界（09-11 明确）：时间轴/地图相机/台风路径线/海图渲染归 GIS 大屏项目组；台风实时/预警解除接口归后台；智能体只保证数据就绪
- 数据红线：**AIS 数据不直传外部模型**；外部"数据服务管控系统"单向定时同步（6 个 sync job），不做反向推送
- LLM 配置：开发机 dashscope qwen-plus，服务器内网中转 198.17.x（deepseek，仅部署机可达 IP 白名单）——`config.properties` 两边不同，**不纳入双服务器同步**
