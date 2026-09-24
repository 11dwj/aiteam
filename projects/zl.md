# 项目总结：综合执法办案系统（zl）

> 基于 OFBiz（内嵌 Jetty，JDK8）的综合行政执法办案系统（常州经开区综合执法局等）。本总结自包含。

## 一、业务流程

案件受理/立案 → 案件办理（分环节、自研流程引擎流转）→ 文书制作（Word 模板 + 标签填充）→ 文书审批（送审/法制审核）→ 处罚决定 → 结案归档 → **推送省平台**（江苏省综合执法信息化平台）。另有信用监管（评分/预警）、违建管理、网格化工、督查等模块。

## 二、核心架构

- **自研流程引擎** com.cloud.flow（非标准 OFBiz workflow）：ProcessEngine/FlowBean/ActivityBean/RouteBean
- **文书标签系统** com.zsoa.zhzf：模板 + KV 解析器、表单构建（默认值/格式化引擎）、**Spire.Doc 填充 Word 书签**、案件办理核心工具类（3400+ 行）、按状态决定按钮。标签类型 17 种（文本/日期/签名/图片/附件/表格等）
- PC 办案页：左环节 → 中 Tab 文书列表 → 右 iframe 编辑；移动端 H5 同构
- 核心表：案件主表（含 push2province/pushErrorMsg 推送字段、status、nowPunish、立结案日期、处罚决定日期）、案件明细、窗口受理、文书实例/模板、审批流程、送达、时限提醒

## 三、省平台推送（两套独立实现，改前必确认目标）

| | 通用版 | 经开区版 |
|---|---|---|
| 形态 | Java 类手动批量 + 可选自动线程（每天 19 点，当前未启用） | JSP 手动单条 |
| API | 58.213.147.239:8060（HmacSHA1 签名 Token，缓存 5 分钟） | 49.77.204.7（appKey/appSecret 配 global.properties） |
| 失败处理 | 标"推送失败" | 标 null 留在待处理队列可重试 |

- 字段映射：caseguid←infoId、casereason←案由名称等；处罚类型映射（警告01/罚款02/没收03…）；案件分类经映射表转 provinceId
- **可推送判定**：status LIKE '%归档%' AND nowPunish='1' AND 处罚决定日期 IS NOT NULL AND push2province IS NULL

## 四、部署与坑

- 启动：Zulu JDK8，`java -jar ofbiz.jar`，-Dofbiz.admin.port=10345（yz 是 10348，区分实例）
- **代码 GBK 编码**，跨 GBK/UTF-8 编辑易乱码（推送类已有先例）；业务逻辑大量在 JSP + Java 工具类中
- 文书生成的底层是"实体数据 → Word 模板书签填充 → 加水印 → PDFBox 合并转 PDF → 在线预览/打印"方案（同源公共代码 com.cloud，与 yz 共享）

## 五、相关：文档在线预览工具集

OA 系的文件预览基础设施：getPdf.jsp 模式（按命名空间选 Word 模板 → 字段填充 → PDFBox 合并/水印 → 预览归档），依赖 aspose-words/cells/pdf 21.11、Spire.Doc、PDFBox-0.7.2 等。是两个 OFBiz 项目文书输出能力的基础。
