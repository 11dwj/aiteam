# 前端规范（React + HeroUI）

## 组件库强制约定

**凡是 React 生态生成的 UI，必须使用 HeroUI 组件，禁止手搓原生样式/自造组件。**

- 文档：https://heroui.com/en/docs/react/components/select（组件与效果示例）
- 前身 NextUI，基于 React + Tailwind CSS，支持 React 18/19、Next.js/App Router

## 使用要求

1. **优先用 HeroUI 组件覆盖**：按钮、表单（Select/Input/Checkbox 等）、表格、弹窗、Toast、Navbar、卡片等一律查文档选组件，不手写等价物
2. **样式定制走 Tailwind + HeroUI 的 slot/variant 机制**，不覆盖内联样式
3. 若项目已引入其他 React 组件库（antd 等），沿用已有库，不混用
4. 产出 UI 仍需对照 `standards/ui-anti-ai.md` 去 AI 味（HeroUI 默认主题也需按项目设计令牌调整，不直接用默认紫渐变）

## 验证

- `npm run build` 必跑；交互组件需真实运行验证状态（受控/非受控、禁用态）
