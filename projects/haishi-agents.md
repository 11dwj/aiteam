# 项目总结：海事 AI 智能体集群（ruoyi-agent-image + 独立智能体）

> 海事安全监管平台的 **AI 智能体集合**：图片分析、检查项一致性、风险条目文档解析（五种模式）、扫描件 OCR。
> 两个代码载体：**`haishi2/backend/ruoyi-agent-image`（Maven 模块，随 8080 后端同进程部署，主力交付版，SVN 管理）**
> 和 **`E:\code\图片分析\`（独立 bat 构建版，开发/调试用，各智能体独立目录）**。两版同源同构，HTTP 接口一致。

## 一、智能体清单（4 个能力）

| 智能体 | 接口 | 功能 | 模型 |
|---|---|---|---|
| 图片分析 | `POST /analyze-image`（8100）/ `POST /haishi/image/analyze`（8080） | 1~4 张图 → 人数统计（跨图去重）+ 救生衣判定 → 合规结论 | qwen3.7-plus（视觉） |
| 检查项一致性 | 进程内直调 / `POST /haishi/image/check-item`（8080，支持加密壳） | 检查项名称 + 照片 → 一致/不一致/无法判定 三档 | qwen3.7-plus（视觉） |
| 风险条目解析 | `POST /risk/parse`（8102）/ `POST /haishi/risk/agent/parse`（8080，支持加密壳） | docx/pdf → 五种模式结构化条目 | qwen-plus（文本）+ qwen3.7-plus（OCR） |
| 扫描件 OCR | 内置于风险条目解析（所有模式自动生效） | 无文本层/乱码/JBIG2 PDF → 渲染 → 视觉模型识别 | risk.vision.model |

## 二、风险条目解析——五种模式（POST /risk/parse + mode）

| mode | 用途 | 返回字段 |
|---|---|---|
| `risk` | 风险管控条目（风险库类文档） | area/env/risk(深层)/ent/ms/es/src_file/ref_para |
| `daily` | 每日研判（要素 9 项 + 风险条目） | base(date/warning/flow/leader/attendees/middle/level/weather/tide) + risks |
| `measure` | 措施条目（讲话/文件/公告，企业侧配对） | src/src_name/area/period/side/content/ent |
| `standard` | 重大隐患判定标准（判定标准/清单类） | std/htype/basis/ship/level/check_method/basis_law/src/src_name/ent |
| `summary` | 研判概要（每周/每月，单字段） | summary（200~400 字一段） |

关键口径：std 逐字保留不润色（判定标准是执法依据）；risk 深层分析（表面→根因→后果）；es 强制双侧（单侧缺失按句式补写）；ship 区分适用船舶（内河客船/危货船等）；研判日期三级来源（文档>文件名>留空，确定性代码不猜）。

## 三、模型链降级（2026-10 模型批量下架后加）

三条链（`aliyun.llm.models` / `risk.llm.models` / `risk.vision.models`），逗号分隔依次降级；
仅模型类错误（404/400/model not exist）切下一个，其余走重试。响应 `model` 字段报**实际使用**的模型。

```
视觉链: qwen3.7-plus → qwen3-vl-plus → qwen3.5-omni-plus
文本链: qwen-plus → qwen3.5-plus
```

## 四、扫描件 OCR 链路（三级降级，全模式生效）

```
PDF 文本层（≥100 字且可读率≥50%）
 → 不足/乱码 → ① 内嵌 JPEG 抽图（零依赖）→ ② mutool 渲染（bin/mutool.exe）→ ③ PDFBox（maven 依赖，纯 Java 含 JBIG2）
 → 逐页视觉模型（3 并行，≤30 页）→ CJK 断行合并 → 模式解析 → file.ocr=true
```

可读率检测：隐藏 OCR 层无 ToUnicode 映射 → 提取出 2 万+乱码 → 中文/ASCII 占比 <50% 判坏。

## 五、检查项三档判定 + 是否违规类规则

- 一致：内容可辨认且相关（实物/实景/材料截图/APP 界面截图均可）
- 不一致：内容可辨认且**明显无关**
- 无法判定：拍照质量问题（严重模糊/过暗/遮挡/分辨率低）或关联无法确认
- **是否违规类**（如「是否超过规定时间（夜间）作业」）：只判场景相符，不判违规是否发生——白天作业照=未在禁令时段=一致

## 六、长文档分块容错（防"只出一个领域"事故）

块 4000 字（防输出超 8192 token 截断）、5 路并行、失败块串行补跑一次、**仍失败整体报错不返回残缺**。
截断检测：finish_reason=length 且内容非空也判失败（JSON 括号不配对根因）。

## 七、加密上送（8080 后端）

`HsRiskAgentController`（/haishi/risk/agent/parse）：{encKey, encData} 加密壳 → OpenCryptoUtil 解密（复用
开放接口 RSA+AES 壳和密钥对，GET /open/voyage/pubkey 取公钥）→ 进程内直调智能体。明文 JSON 兼容。

## 八、部署要点

- Maven 版：`mvn clean package -pl ruoyi-agent-image,ruoyi-haishi -am` → 重启后端
- 独立调试（8102）：`java -cp "target/agent-image.jar;target/lib/*" com.risk.ai.web.SimpleHttpServer`
- `bin/mutool.exe`（45MB）随 SVN 检出；PDFBox 由 maven 依赖自动打入 target/lib
- 模型链配置在 `src/main/resources/config.properties`，环境变量同名大写可覆盖

## 九、踩坑记录（重要经验）

1. **模型批量下架**（2026-10-10 qwen-vl-plus/max 全灭）→ 加模型链降级，服务器不再中断
2. **PDF 隐藏乱码层**骗过"≥100 字"检查 → 加可读率检测
3. **python 环境不可控** → 渲染链去 python 化（mutool + PDFBox 纯 Java）
4. **分块输出截断**（8192 token 上限）静默丢块 → 缩块 + 截断检测 + 补跑 + fail-fast
5. **SVN target/ 冲突**频繁 → 建议将 target/ 移出版本库加 ignore（未执行，历史遗留）
6. 提示词写 Java 源码时 `\n` 转义在 Python 补丁脚本中极易变真换行 → 用 Write 工具写补丁脚本文件，不用内联 heredoc

## 十、相关文档

- 接口调用：`ruoyi-agent-image/1/` 下 6 份（图片分析/检查项/风险解析主文档/加密/standard模式/summary模式/OCR实现）
- 设计方案：`E:\code\图片分析\风险研判解析智能体方案.md`（v1.3）
- haishi 项目总结：[haishi.md](haishi.md)
