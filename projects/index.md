# 项目档案索引

每份档案都是**自包含项目总结**（业务、架构、数据模型、业务规则、部署、经验沉淀），不依赖源码可读。涉及具体项目开发时再配合源码位置使用。

| 项目 | 业务 | 技术栈 |
|---|---|---|
| [haishi](haishi.md) | 海事封航解封报告智能体（16 格矩阵 + 多专家 Agent + 风险推演 + 阶梯解封） | 双版本：Python(LangGraph+Chroma+FastAPI) + Java(JDK8 零依赖单 JAR 交付主力, deepseek) |
| [haishihoutai](haishihoutai.md) | 海事业务后台 + 指挥大屏 + 数据同步中枢（信创国产化） | RuoYi 单体 JDK17 + Thymeleaf + 金仓 KingbaseES + JDK8 单 JAR 智能体 |
| [kecu](kecu.md) | 常州经开区招商项目管理 + 绩效考核 | RuoYi-Vue-Plus 5.5.1 + Vue3 + 双数据源 |
| [czdaping](czdaping.md) | 电镀产业园数智园区（投标三端：后台/大屏/小程序） | Flask + Vue3 后台 + Vue2 ECharts 大屏 + uni-app |
| [toupiao](toupiao.md) | 阳光物业投票系统（业主投票/附议/资金公开） | RuoYi-Vue JDK8 + uni-app |
| [ruoyi-warmflow-base](ruoyi-warmflow-base.md) | 电镀园区运营平台（能源/财务/资产/危化/工作流十域） | RuoYi-Vue + Warm-Flow + MinIO + Docker |
| [yz](yz.md) | 智慧印章监管平台 + seal-ai 合规分析服务 | OFBiz + 百度/Paddle OCR + qwen |
| [zl](zl.md) | 综合执法办案系统（文书引擎 + 省平台推送） | OFBiz + 自研流程引擎 + Spire.Doc |

通用资源：Redis 7.4.2 Windows（E:/code/redis）；移动端 UI 规范与能源模块原型（E:/code/guifan/）；对话日志全量存档（E:/code/cclogs、cclogs2）。
