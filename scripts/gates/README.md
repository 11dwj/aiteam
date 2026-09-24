# 门禁脚本（Gates）

来自 harness 工程的**零依赖** Python 校验脚本（纯 stdlib，Python 3.8+），把"诚实声明"变成机器可判定：编译通过≠业务通过、一次经验≠规则、总结≠使用证据。配合 codeteam 的 S/M/C 工单分级与五态验证体系使用。

## 脚本清单

| 脚本 | 作用 | 何时跑 |
|---|---|---|
| `verification_claim_gate.py` | 校验 S/M/C 验证声明结构：C 级五必填（执行主体/目标入口/命令/断言/证据）、必须含反例断言、静态/编译不得声明业务 PASS | 每个工单收尾时 |
| `quality_gate.py` | 按变更文件路径关键词触发 8 个工程维度证据检查（N+1/事务/幂等/权限/SQL/分页/复用/可观测），含循环内查询正则检测 | 涉及后端改动时 |
| `security_posture_gate.py` | 风险驱动安全基线：NEW+T2/T3 强制威胁模型/授权/密钥/输入校验；按认证模式条件检查；遗留漏洞分"阻断发布"vs"有主债务" | 新功能/涉及安全改动时 |
| `source_hygiene_gate.py` | 扫描本轮变更中的调试残留（breakpoint/debugger/DEBUG print/临时标记/假数据） | 提交前 |
| `knowledge_promotion_gate.py` | 知识入库门槛：NO_CANDIDATE 是正常结果；CANDIDATE→PROMOTED 需触发器（重复出现/跨项目/高严重度）+ 独立来源 + 显式人工批准 | 沉淀 solutions.md 前 |

## 模板

- `verification-claim.template.json` — 验证声明（S/M/C 工单收尾必填，五态 + 业务状态分离 + 日终反馈衔接块）
- `security-posture.template.json` — 安全态势声明（11 控制项 + 已知漏洞清单）
- `quality-rules.template.yaml` — 8 条质量规则的声明式证据清单（每条写明"需要什么证据"）

## 用法

脚本为核心是校验函数（如 `validate_verification_claim(data) -> dict`），返回 `gate_status: PASS/BLOCKED` + 错误码 + 追问问题。使用方式：

```bash
# 让 AI 按模板填好声明 JSON 后，直接调用校验
python -c "import json,verification_claim_gate as g; print(json.dumps(g.validate_verification_claim(json.load(open('claim.json',encoding='utf-8'))),ensure_ascii=False,indent=2))"
```

返回 `gate_status: BLOCKED` 时按 `follow_up_questions` 补证据，直到 PASS。**注意：门禁 PASS 仍 ≠ 业务 PASS**——门禁只保证"声明结构诚实"，业务结论永远来自真实运行验证。
