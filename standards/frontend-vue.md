# 前端规范（Vue / 若依前端 / 大屏）

## Vue（plus-ui / ruoyi-ui）

- 组件按业务模块放 views/<模块>/，公共组件抽 components/
- API 调用统一走 `src/api/` 封装，不组件内裸写 axios
- 表单校验用 rules，提交按钮加 loading 防重复提交
- 列表页：查询区 + 工具栏 + 表格 + 分页，沿用项目已有页面模板复制改
- 权限：按钮级 v-hasPermi / v-auth，与后端权限标识一致

## 前后端不分离项目（haishihoutai，Thymeleaf + H+ + jQuery）

- 页面放 templates/，沿用 H+/Bootstrap 组件，不引入新框架
- JS 用已有 jQuery 模式，公共函数抽 app.js 类公共文件

## 大屏（czdaping）

- echarts / ThingJS / 高德地图：控制 rAF 渲染循环，避免持续重绘
- 多 iframe 各跑 echarts/vue 会拉爆 GPU——控制实例数、降帧率、按需销毁
- 定时刷新用可见性判断（页面隐藏时暂停）

## 验证

- `node --check <file>` 语法检查；构建 `npm run build:prod`
- 小程序端改动：提醒需重新构建发布小程序才生效
