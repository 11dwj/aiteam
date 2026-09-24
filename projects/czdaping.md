# 项目总结：常州经开区表面处理（电镀）循环产业园数智园区项目（cztoubiao）

> 投标与交付项目，三端一体：PC 管理后台 + 数据可视化大屏 + 微信小程序（企业侧）。本总结自包含。

## 一、业务主线

企业微信小程序提交入场登记 → 管理后台审核发证 → 企业申请生产作业计划 → 审批 → 作业准备/巡检巡查/整改验收 → 资产扫码盘点 → 第三方报警自动生成工单 → 分派处置闭环；全过程数据汇聚到大屏（用电、进退场、入驻统计）。

## 二、三端架构

**1) PC 管理后台**
- 前端：Vue 3 + Element Plus + Vite（:7668），仅管理员登录，LocalStorage 会话 + 路由守卫
- 后端：Python Flask + PyMySQL + JWT（Gunicorn 4 worker，:7666），模块：auth/admin/work_order/job_plan/company/info/file_attachment/factory
- 页面：工作台、入场登记、作业计划审批、作业准备、巡查报告、盘点任务、资产工单
- 核心表：ZHSQ_CTWING_EVENT（工单/事件，对接电信 CTWing 报警）、ZHSQ_CTWING_DEVICE、DeviceType、ActionLog、InfoRegistration、JobPlanApplication、JobNode、LoginAccount、FileAttachment
- 特色：第三方报警自动生成工单（`/api/work_order/auto_create` 零参数全自动）

**2) 大屏**
- Vue 2 + ECharts + ElementUI + Less，原生 HTML+JS 模块化（每模块独立目录 + Cmp.js），无打包工具，http-server :9872
- 模块：主体特色、智慧安全、综合调度、智慧防汛、智慧环保、智慧能源、智慧运营、园区总量、三维场景（Cesium 3dtiles）、弹窗图层
- 功能：企业用电排行、园区用电统计、入驻企业统计、进退场管理、3 个月轮播、Pie3D
- 对接后台 getToken.jsp 换 token；三维底图 cdz3dtiles/tileset.json

**3) 小程序（企业侧）**
- uni-app + Vue 2 + uView UI + Vuex
- 页面组：首页、管理端、企业端、登录、园区简介、个人中心
- 业务页：入场登记（申请/我的/详情）、生产作业（计划申请/填写/详情/作业准备/任务/处置确认）、企业整改、巡检巡查（详情/表单/整改验收）、资产盘点（扫码/已盘点）、工单详情

## 三、经验沉淀（项目自带 AI 辅助开发总结，很有价值）

1. **AI 初次理解项目必须强制完整读取技术栈文件并建立清单**，否则会 Vue2/Vue3 混用、ElementUI/Element Plus 混用、Less/SCSS 混用
2. 布局强制 Grid/Flex 三层结构（容器-行-列），禁止 div 平铺；CSS 防选择器重叠冗余
3. 小程序 UI 必须给模板/组件参考，让 AI 自由发挥会得到"一眼 AI"的 emoji 界面；局部动效交给 AI 效果很好
4. 数据库应一开始让 AI 参与设计，避免开发中反复加字段加表
5. AI 修不动 bug 时：切 ask 模式先定位、多轮追问多方案、有正确示例一定给参考
6. 大屏复用既有架构（模块目录 + Cmp.js 命名 + Less）是快速交付投标大屏的有效路径
7. 大屏 GPU 坑：高德 WebGL 持续 rAF + 多 iframe 各跑 echarts 导致占用高 → 降帧率/控制渲染循环

## 四、部署

PC 后端 Gunicorn；大屏静态文件 http-server/Nginx（有《生产环境部署配置清单》《认证问题修复说明》）；小程序走微信 code 换 session 自动登录。

## 五、性能优化实战（2026-08-05~06，两个经典案例）

**大屏 GPU 占用高 → PowerSaver 节能调度器**：真凶是①高德 WebGL 常驻 rAF + ThingJS 3D；②28 个子模块各自 iframe 各跑 echarts+vue；③CSS 无限脉冲动画。方案（已实施 33 文件）：index.html 调度器（页面不可见或空闲 3 分钟触发）→ 主页面加 .powersave（全局 animation-play-state:paused）→ postMessage 广播 iframe 暂停 CSS 动画和 ≥1s 数据刷新定时器，一动即恢复。

**大屏加载慢（实测推翻直觉）**：scene 文件仅 1.7MB 下载 0.24s，真凶是 `Cache-Control: no-store` + HTTP/1.1 下 74 请求×6 并发排队（最坏≈18s）；thing/uearth 两个 min.js 合计 9.65MB 完全没压缩。方案：nginx 开 http2 + gzip（省 75%，brotli 可选）+ .min.js 30 天 immutable 缓存 + 贴图 7 天 + access_log off。

**404 假象案例**：publicResource（16MB 库文件）整个目录没上传到服务器；且改配置的 nginx 服务器与大屏实际运行的是两台机器——**改配置前先确认目标机器**。
