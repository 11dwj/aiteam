# 项目总结：智慧印章监管平台（yz）+ seal-ai AI 分析服务

> 基于 OFBiz（内嵌 Jetty，JDK8）的 OA 系统，核心业务是面向村集体（村委会/居委会）等基层组织的**印章/用印监管**。本总结自包含。

## 一、业务全貌

整体链路：智能印章终端（对接"云玺审批平台"）产生用印申请和记录 → 平台同步/入库 → OCR 识别盖章文件与印章 → **seal-ai 服务 AI 合规分析** → 异常预警（重复用印、非工作时间/节假日用印、超时、主体不符等）。

## 二、核心数据模型（OFBiz entity XML 定义，中文标题自动出表单）

- OA 通用：User、Department、Space（多租户）、Flow/FlowData/FlowForm（自研流程引擎）、Announce、Cal、LogInfo 等
- 智慧印章（ExtZhyz 前缀）：**ExtZhyzYyRecord 用印记录（核心表**：aiStatus/aiJsonData/aiWjlxData AI 结果字段、useCount、deviceId、人脸 faceFileUrl、GPS、超时文件等）、公章信息、OCR 结果/文件、人脸管理与验证、核验比对规则、文件类型配置、年度分析报告、**异常报警信息**、节假日与工作时间配置（用于预警）、印章模式（按设备号）
- 人员轨迹表

## 三、关键组件

- 同步：GetYzRecord（同步用印记录，核验相似度阈值 50）、印章管家、用户部门同步
- **异常扫描器**：重复用印/节假日/非工作时间/超时/AI 申请五类扫描 + 发送队列
- OCR：百度 OCR + PaddleOCR 双路、印章比对；消费线程 BlockingQueue（上限 1 万）
- AIUtil 调 seal-ai（默认 `http://localhost:9099/api/seal/analyze`，global.properties 的 aiAnalyzeUrl 可覆盖），结果写回 ExtZhyzYyRecord.aiStatus/aiJsonData

## 四、seal-ai（独立轻量 AI 服务，jar 部署）

**做什么**：接收待盖章文档 OCR 文本（+审批金额/期限/印章 OCR），DashScope qwen-plus（temperature 0.3）语义理解，返回结构化合规结论。三大维度：**主体一致性**（含 20 类村委会"禁开证明"检测）、**条款异常**（以"是否损害村集体利益"为唯一标尺）、**审批完整性**；compliant = 三者全过。支持 6 大类 30+ 子类文档识别。

**架构**：三段式编排——大模型主分析 → 主体不符专项二次判断（proofName 反查防乱判）→ 后端宽松兜底清洗（OCR 噪声、多级流转豁免、自相矛盾清洗等）；模型失败降级规则引擎（置信度 0.80）。**零第三方依赖**（JDK 内置 HttpServer、手写 JSON），`java -jar seal-ai.jar web` 起服务（9099，占用则 9100）。

**持续调优模式（重点经验）**：运维主要是**防误报白名单**——入口硬白名单（如困难/助学类学生资助证明直接判合规），用户贴真实误判文本 → 扩充关键词（"望学校""贵校""给予资助"等）→ 验证命中。曾修：死亡证明被误判为亲属关系证明、协议书预警豁免。

## 四A、调优演进时间线（2026-07-24 ~ 09-10）

**防误报架构反转（核心演进）**：08-18 依《江苏省村（社区）依法协助类工作事项指导目录》（66 项）做前置**白名单**（不在目录就预警）→ 使用几天后预警太多 → 08-25 整体反转为 15 项江苏**转嫁证明黑名单**（食品安全等级评定/危房鉴定/违建认定/排污认定/养老金生存认证等）→ 08-28 黑名单每项加高区分度关键词 + verifyBlacklistHit 反查（原则："村里上报隐患是协助职责，只有出具认定/合格结论才命中"）。

**典型误判修复案例（现象→原因→方案）**：
| 案例 | 原因 | 方案 |
|---|---|---|
| 墓地减免证明 compliant=true 但 detail 喊违规（自相矛盾） | "禁止出具"结论塞在 partyMatch 通道，顶层逻辑没读；定性只抓"兹有…特此证明"套语漏掉主诉求 | prompt 规则 F/G（给付/减免请求优先于关系陈述）+ 后端 sanitizeContradictoryForbiddenDetail 兜底。**修复顺序：先修定性再修裁决汇合，否则把真合规判成违规** |
| 低保困难证明误判"疾病状况证明" | 未区分两种情形 | prompt D2：附经济数据→财产证明（不合规）；仅减免请求→综合情况说明（合规） |
| 身故保险金声明书误判"死亡证明→主体不符" | 真问题是受益人签字栏漏签 | 三层：isInsuranceClaimDeclaration 硬豁免 + prompt 反例 + detectUnsignedConfirmationCheckboxes（"是(否)"占位≥2 处未勾→强制 approvalComplete=false） |
| '227年' 被报条款异常且原因写"OCR识别错误" | OCR 年份噪声 | 正则清洗（非 19xx-20xx 四位/五位以上），命中整条清洗不留提示。踩坑：负向后行断言放"年"前永远不匹配 |
| 12 例回归 4 例漏判 | ①反查词表只有带"证明"的词 ②"AI 成功时完全采信"导致规则引擎没机会跑 | 扩反查词 + supplementForbiddenProofByRules（AI 判无主体不符时再跑一次规则引擎）+ 意图词加"兹有" |
| 改了代码误判依旧 | 只编译到 build/out，运行的是旧 jar | **改完必须重新 build.bat 打包**（反复踩） |

**提示词原则（07-29 定）**：条款异常以"是否损害村集体利益"为唯一标尺（偏向村集体的不算异常）；documentType 用"二级细粒度值 + '综合情况说明基础证明'替代'其他'"（endsWith 天然命中内部值护栏，零逻辑影响）。

## 五、部署与坑

- 启动：`java -Xms1024M -Xmx4096M -Dofbiz.admin.port=10348 -jar ofbiz.jar`（startoa.bat）
- **代码 GBK 编码**，读改中文注释注意乱码；只改 components/ 业务组件不动 base/
- seal-ai 真实 API Key 曾 bake 进 jar，应改环境变量；JSON 解析脆弱、单线程执行器、结果不落库（已知短板）
- 给老 OFBiz 系统加 AI 能力的推荐模式：**独立 HTTP 服务与 OA 解耦**（对齐公司智慧印章 AI 技术路线，haishi 的 Java 交付版也是这个模式）
