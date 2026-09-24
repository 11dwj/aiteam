# 去"AI 味"UI 规范

来源：`E:/code/避免AI味的UI规范-impeccable-style.md`（impeccable.style，64 种反模式 / 59 条检测规则）。可用 `npx impeccable detect` 自动检测。

## 核心原则

避免"生成器默认值"——每个设计决定都应是有意的，不是框架/模型随手给的。

## 高频红线

- ❌ 紫蓝渐变、紫色系"AI 签名色"、奶油色背景、暗底彩色发光
- ❌ Inter / Geist / Space Grotesk 等被滥用字体
- ❌ 字号无步进（步进应 ≥1.25 倍）、正文 <14px、行宽 >80 字符（max-width 65–75ch）
- ❌ 均质三卡片布局、无意义大圆角、装饰性 emoji 图标
- ✅ 对比度正文 ≥4.5:1；行高 1.5–1.7；层级靠字号字重而非颜色堆砌

## 使用方式

产出 UI 前对照检查；交付前可跑 `npx impeccable detect` 或让 AI 按上述规则自查一遍。
