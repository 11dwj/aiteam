# uni-app 小程序规范（RuoYi-App：toupiao、czdaping、ruoyi-warmflow-base 移动端）

- 页面在 `pages/` 注册（pages.json），分包放分包目录
- 请求走统一 `utils/request` 封装，带 token，处理 401 跳登录
- 样式用 rpx；设计令牌按 `standards/ui-mobile.md`（间距 4/8/12/16/20/24/32px、圆角分档、触摸区 ≥32px）
- 按钮位置统一：主操作右上角或底部通栏，同类页面保持一致
- 图片/icon 路径改动注意：路径修正类 SQL 与前端代码同步发布，**需重新构建发布小程序才生效**
- 条件编译区分平台（H5/微信），平台差异 API 用 uni.xxx统一接口
- 列表下拉刷新/上拉加载用 onPullDownRefresh / onReachBottom 标准模式
