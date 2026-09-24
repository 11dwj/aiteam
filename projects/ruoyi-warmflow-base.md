# 项目总结：电镀园区运营管理平台（ruoyi-warmflow-base）

> 产业园全业务管理平台，基于 RuoYi-Vue 3.9 + Dromara Warm-Flow 1.8.3 工作流。本总结自包含。

## 一、技术架构

- 后端：Java 8 / Spring Boot 2.5 / MyBatis / Druid / Redis / Quartz / MinIO（可选，@ConditionalOnProperty 开关）
- 前端：Vue 2 + Element UI + ECharts + LogicFlow 流程设计器；小程序 uni-app
- 端口：开发后端 9871 / 前端 9872；Docker 生产前端 7667 / 后端 7668
- 模块：ruoyi-admin（全部 Controller 按业务分包）/ ruoyi-system（190+ 实体）/ ruoyi-flow（Warm-Flow）/ framework / common / ruoyi-ui / app（小程序）/ tools（电力采集 Python 脚本）

## 二、业务模块（十大域）

1. **能源（最大模块）**：能源设备/绑定/读数、激活、告警规则与记录、计费价格（含历史）、日账单（含合并/生成）、月账单（含明细/编辑日志）、缴费、公区能耗点、统计看板；水（water）、气（gas）子模块
2. **电力采集（elec-sync）**：账户/钱包/账单明细（+快照）/抵扣流水/充值/抄表/费率/同步日志。链路：Windows 计划任务驱动 Python 采集器 → 开放接口 /open/elec/sync/** → 同步服务。**成功判定铁律**：sync_type='bill' & sync_status='success' & total>0 & success>0 & fail=0（严禁空同步误判成功）；定时巡检前一日窗口无有效成功则告警
3. **财务**：合同/租金/收费项/账单规则（定时生成应收）/应收/收款（sourceType 区分手动与规则生成，**定金自动抵扣仅限规则生成**）/押金（含审核）/保证金/水电费/催缴
4. **资产**：资产台账/处置/出入库/巡检（计划+任务）/盘点/维修/领用；资产账单/押金/预交；消息提醒
5. **入场/退场/装修**：信息登记（含营业执照附件）、企业、入场审核、企业整改反馈、销户、厂区交接；装修申请/合同/任务/材料/验收/档案（含押金节点）
6. **危化品/危废**：危化品企业/申报/检查/配送（路线+节点）/库存/预警规则 + H5 商城；危废类别/申报/标签/包装/运输
7. **巡查巡检/安全教育**：巡查、每日巡查任务/模板/清单、企业自检；安全宣传/培训主题/学习记录/试题/案例
8. **设备/IoT**：设备与日志、视频通道、Modbus 采集点（X2BACnet 网关）、ICC 门禁/停车（记录+快照）、IoT 告警
9. **生产/运营/工单**：生产作业（参数预设/准备/跟踪）、工单、通知/政策、企业评级
10. **大屏**、企业信用评级、园区合同

## 三、Warm-Flow 集成方式

- 流程分类 flow_category（v3.0：7 大领域 60 节点——入场/生产/退场/财务/资产/安全资讯/OA）
- SpEL 动态审批人 flow_spel；适配器：转办/委派/加签/减签
- CustomGlobalListener 全局监听器下发任务消息（**按 (instance_id, node_code) 关联，不能用 task id——会漂移**）
- 开发约定：流程状态、业务状态、审批任务状态必须一致；生产环境 warm-flow-ui 默认关闭（防公网暴露）

## 四、关键设计约定

- 文件存储 sys_file_storage（storage_source=local|minio），**铁律：业务表不存长 URL/预签名 URL/base64**（曾踩 Data too long 坑）；文件访问一律走后端代理 `/system/file/view/{id}` 做对象级鉴权
- 短信验证码限流**必须用 Redis 原子操作**（禁 hasKey+set 并发绕过），维度含手机号冷却/日限额、IP 分钟/日限额
- SQL 组织：sql/warm 基线 + sql/sqlUpdate/<域>/日期_用途.sql 增量（含 rollback 脚本体系）
- 安全整改 6 条：默认拒绝按需放行、对象级授权（批量操作含无权对象则拒绝）、Swagger/Druid/Actuator/WarmFlow-UI 生产关闭、文件上传统一校验（扩展名黑名单+文件头+拒双扩展）、敏感信息不进日志、开放接口 /open/** 用 API Key

## 五、部署

docker-compose 三服务：redis（不对外）+ backend（多阶段 Dockerfile，挂载 ./data/upload 与 logs，env 注入 MYSQL_URL/REDIS_PASSWORD/TOKEN_SECRET 等）+ frontend（Nginx）；MySQL 外部远程库。传统部署：Ubuntu + JDK8 + 本地覆盖配置（bin/setenv.sh + application-prod.local.yml）。小程序接口 app/api/**，登录白名单 app/permission.js；正式发布需 HTTPS 备案域名。

## 六、踩坑记录（logs 演进沉淀）

- 服务器迁移：旧服务器已废弃，配置/脚本严禁残留旧 IP，需检索清理
- workflow 消息可见性按 task id 漂移 → 改 instance_id+node_code
- 消息按 (type,title,permission) 永久去重导致驳回整改消息只发一次 → 版本号拼 key
- 手动新增应收误触发定金抵扣 → sourceType 区分
- 动态 SQL `!= ''` 导致无法清空字段
- 空/部分失败同步误判成功 → 严格成功判定四条件
- 生产禁 System.out/printStackTrace

## 七、AI 协作体系

Claude Code + Codex 双 AI 协作（CLAUDE.md/AGENTS.md 同构），9 条规则文件 + 12 个项目级 skill（elec-sync-debug、file-storage-check、workflow-change-check、security-vulnerability-remediation 等），logs/ 每日开发日志。

## 八、开发历程与典型工单（2026-07 ~ 08）

**财务/应收（07-13~17）**：商城购物车下单不生成应收——根因是 createTaskFromCart 直接 insertHazOrder 绕过 HazOrderFinanceBridge，修复后可用 backfillHistoryOrders 幂等补齐约 37 笔历史订单。账单规则重复执行不再产生重复应收；水费单价改动按生效区间重算账单。

**消息去重重构（07-21）**：sendBusinessMessageOnce 按 (type,title,permission) 永久去重，导致驳回整改提醒同一用户只能收一条被锁死 → 按 (system,inspectionId,userId) 统计版本号拼进 key。

**小程序图标 + UI 规范统一（07-22~24）**：25 个中文拼音缩写图标放 static/functions/；后端走动态接口，用幂等 SQL 修线上库 icon 严重错配（多模块共用错图标）。static 打包进小程序**必须重新构建发布才生效**，后端路径即时生效。随后按深蓝 v5.0 规范逐页统一 10+ 个 H5 列表页（nav 高度/按钮沉底/空数据图/tab 数字徽章/右下角蓝色 FAB/状态分色）。

**Docker 化（07-28）**：多阶段 Dockerfile + compose 三服务；`application-*.yml` 改环境变量占位；MinIO 关闭走本地存储；离线导出 docker save。

**蒸汽单价迁移（07-29，大金额 SQL 上线范本）**：口径改"元/1000m³"——价格表 9 条×1000、改价历史 20 条×1000、错误日账单删除、223 条快照×1000（amount 不变）→ UI 触发整月重算 → 逐 point_id 核对 → 备回滚脚本。已确认数据不动金额只动快照。

**退场流程管控（08-07，工单 26118 三批实施）**：① 退场前校验 ensureNoPendingBusiness（装修/生产/巡查未完成则拦截）；② 退场完成自动归档企业用户（软删 sys_user + 停用关联，保留审计）；③ 退场中拦截器白名单（资产评估/环境整改/账号注销可用）。

**消息可见性重构（08-12，工单 26208）**：从"按 perms（含隐藏按钮）"改为"按前端可见菜单判定"——复用菜单树 DFS 收集可见 menuIds + 按 perms 批量反查，双保险 OR、异常降级、批量预查防 N+1。效果：园区物业只收生产/巡查/工单类消息。列表为权威源，WebSocket 推送口径留有差异。

**能源账单期初期末口径（08-12）**：月账单期初取 1 日、期末取次月 1 日（半开区间，与 elec-sync 一致）；bad 标记数据不展示不参与计算；禁用点位不参与账单。

**环境/部署问题速查**：PC 端 H5 404"权限不足"假象 = 旧入口前端构建较旧缺新路由；小程序下载模板 zip 失败链路 = H5→原生 file-open 页→浏览器兜底；文件预览统一跳原生 file-open 页；服务器 MySQL 3317/warmflow，域名 www.czjkbmcl.cn（/prod-api 反代），代码内 9871 端口公网不可达。
