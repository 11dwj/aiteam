# 老项目技术栈局限 vs 新技术对比（应答手册）

维护的老项目（yz/zl OFBiz、toupiao JDK8、ruoyi-warmflow-base Spring Boot 2.5 + Vue2）经常被问"为什么不用新的/和最新版差在哪"。本文按**被问场景**组织：先给一句话结论，再给对比表，最后给"为什么还在用"的正当理由（面试/对客户都适用）。

## 1. JDK 8 vs 最新 LTS（17 / 21 / 25）

**一句话**：JDK 8 是 2014 年的版本，语言层面最缺的是记录类、模式匹配和空指针精确定位；新 LTS 在性能（GC）、安全和语法上全面进化，但 JDK 8 生态兼容性最好，老系统换不动主要是依赖牵连。

| 维度 | JDK 8 | JDK 17 | JDK 21 / 25 |
|---|---|---|---|
| 语法 | Lambda / Stream / Optional | + record、sealed、switch 表达式、文本块 | + record 模式匹配、虚拟线程（21） |
| GC | Parallel 为主，G1 不成熟 | G1 成熟默认，ZGC 生产可用 | ZGC/Shenandoah 进一步优化，G1 继续 |
| NPE | 只报行号 | **Helpful NPE** 精确指出哪个变量为 null | 同左 |
| 性能 | 基线 | 同代码综合提升约 5-15% | 虚拟线程让高并发 IO 吞吐大幅提升（替代异步回调） |
| 安全/支持 | 公开更新早已停止（商业付费续命） | LTS | 25 为最新 LTS（2025.09） |
| 生态 | **兼容性最好**，老框架（OFBiz、Spring Boot 2.x、Spire 等老 jar）只认它 | Spring Boot 3 强制基线 | 部分老库仍未适配 |

**为什么还在用 JDK 8**：OFBiz、若依老版、Aspose/Spire 等商业 jar 深度绑定；升级 = 全量依赖重编译回归，客户没有为此付费的意愿。**已有升级实践**：haishihoutai（JDK17 + Spring Boot 4）和 kecu（JDK17 + Spring Boot 3）证明新项目走新栈没问题。

**加分答法**：讲一个实际差异——JDK 8 里 `user.getAddress().getCity()` 报 NPE 只知道哪一行，JDK 14+ 会告诉你 "Cannot invoke getCity() because the return value of getAddress() is null"；以及虚拟线程解决的是什么问题（每请求一线程模型在 IO 密集场景被线程数卡死）。

## 2. Vue 2 vs Vue 3

**一句话**：Vue 2 已于 2023 年 12 月 31 日 **EOL（官方停止维护，不再修 bug 和安全漏洞）**；Vue 3 的核心变化是 Composition API、更好的 TS 支持和 Proxy 响应式，性能与大型项目可维护性明显更好。

| 维度 | Vue 2 | Vue 3 |
|---|---|---|
| 维护状态 | **EOL**（安全风险点，对客户直说） | 当前版本 |
| API | Options API（data/methods 分块） | Composition API（按逻辑组织，逻辑复用用 composables 替代 mixin） |
| 响应式 | Object.defineProperty（**新增属性/数组下标监听不到**，要 $set） | Proxy（全量拦截，无 $set 心智负担） |
| TS | 支持弱 | 源码 TS 重写，类型推导一流 |
| 性能 | — | 静态提升/patch 优化，打包更小、渲染更快；Fragment 多根节点 |
| 生态 | Element UI、uView（老项目在用） | Element Plus、Vite 工具链 |
| 迁移 | — | 小项目可渐进迁移（@vue/compat），但 UI 库要整套换 |

**为什么还在用 Vue 2**：toupiao / czdaping 小程序 / ruoyi-warmflow-base 的 ruoyi-ui 都是 Vue2 + Element UI / uView，业务页面多，整套换 UI 库等于重写前端；投标类项目按交付验收，不为技术更新买单。

**混用教训**（czdaping 项目自带总结）：AI 辅助开发时必须强制声明技术栈清单，否则会 Vue2/Vue3、ElementUI/Element Plus、Less/SCSS 混用直接报错。

## 3. Spring Boot 2.x vs 3.x+

**一句话**：Spring Boot 3 把基线抬到 JDK 17 并切换到 Jakarta EE 9 命名空间（javax.* → jakarta.*），这是最大的破坏性变化；新项目直接上 3，老项目升级成本主要在依赖链。

| 维度 | Spring Boot 2.5（warmflow-base 在用） | Spring Boot 3.x（kecu 3.5 / haishihoutai 4.0） |
|---|---|---|
| JDK 基线 | 8+ | **17+** |
| 命名空间 | javax.* | **jakarta.***（所有 import 要改，拦截器/校验/上传全部受影响） |
| 安全 | Spring Security 5 | Security 6（写法变化大） |
| 可观测 | 老_actuator | Micrometer Tracing 原生集成 |
| AI 集成 | 需自己封装 | 生态有 Spring AI 等 |

**实践差异已踩过**：haishihoutai 用的是 Shiro 而非 Spring Security（若依单体版传统），kecu 用 Sa-Token——若依系两代框架的安全方案本身就不同，面试可展开。

## 4. OFBiz vs 现代框架（yz / zl）

**一句话**：OFBiz 是 2000 年代的企业应用框架，服务定义用 XML、实体用 XML、页面大量 JSP，启动慢、人才少、文档老；但它的"entity XML 定义自动出表单/列表 + 内嵌 Jetty 热部署"在当年效率极高，老系统稳定运行多年，重写成本远高于维护成本。

| 维度 | OFBiz（yz/zl） | 现代等价物 |
|---|---|---|
| 实体层 | entitydef XML 定义，中文字段名自动出 CRUD | MyBatis-Plus / JPA + 代码生成器 |
| 服务层 | minilang / services.xml | Spring Service |
| 视图 | JSP 内嵌大量业务逻辑 | Vue 前后端分离 |
| 流程 | 自研 Flow 引擎（com.cloud.flow） | Warm-Flow / Flowable / Camunda |
| 编码 | **GBK**（跨文件编辑易乱码，实际踩过） | UTF-8 |
| 部署 | java -jar ofbiz.jar 内嵌 Jetty，JDK8 | Docker + 独立容器 |
| 文书 | Spire.Doc 书签填充 + PDFBox | poi-tl / pandoc 等 |

**给老系统加新能力的模式**（seal-ai / haishi 交付版验证过）：不动 OFBiz，**旁边挂独立轻量 HTTP 服务**（零依赖 JDK8 单 JAR），OA 通过 HTTP 调用——这是"老系统 + AI"的推荐架构，也是可以对外讲的设计决策。

## 5. RuoYi 生态两代对比

| | RuoYi-Vue（toupiao / warmflow-base） | RuoYi-Vue-Plus（kecu 5.5.1） |
|---|---|---|
| JDK | 8 | 17 + Spring Boot 3 |
| 前端 | Vue2 + Element UI | Vue3 + TS + Element Plus + UnoCSS |
| ORM | MyBatis + PageHelper | MyBatis-Plus |
| 安全 | Spring Security + JWT | **Sa-Token** |
| 权限 | RBAC + 数据权限 | + 多租户 |
| 工作流 | 需自集成（warmflow-base 集成 Warm-Flow） | 内置 Warm-Flow + SnailJob |

## 6. 通用应答框架（被问任何"老 vs 新"时）

1. **先承认事实**：老 = 停止维护/缺新特性/安全风险（Vue2 EOL、JDK8 无公开更新），不遮掩
2. **再讲约束**：生态绑定（商业 jar / UI 库 / 客户环境）、升级 = 全量回归、客户不为重构买单
3. **再讲收益**：老系统稳定运行多年；维护中沉淀的功力（读老代码、定位线上问题）比追新更有价值
4. **最后证明跟得上**：新项目已经用新栈（JDK17 + Spring Boot 3/4 + Vue3 + uni-app + LLM），并且能把老系统的领域知识平移过去
