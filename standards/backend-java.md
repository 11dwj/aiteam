# Java 后端规范（RuoYi 系 / OFBiz）

## RuoYi-Vue / RuoYi-Vue-Plus（kecu、ruoyi-warmflow-base、toupiao）

- 分层：Controller（只做参数校验与转发）→ Service（业务，接口+impl）→ Mapper（MyBatis/PageHelper）→ domain
- Controller 不写业务逻辑；Service 不直接操作 HttpServletRequest
- 新增业务模块放对应 ruoyi-modules/extend 或独立 module，不污染 ruoyi-system
- 权限注解 `@SaCheckPermission` / `@PreAuthorize` 按项目已有体系，新接口必须加权限标识
- 分页用 PageHelper / Plus 的 `Page`，不手写 limit
- 事务：Service 方法加 `@Transactional(rollbackFor = Exception.class)`
- 异常：业务异常抛项目统一异常类，全局处理器兜底，返回统一 Result 结构

## OFBiz 老系统（yz 智慧印章、zl 综合执法）

- 只改 `components/` 下业务组件（entity/minilang/service），**不动 base/ 框架**
- 部署：startoa.bat / ofbiz.jar 内嵌 Jetty 热部署；改 entity 后注意数据库结构同步
- 对外推送（zl 省平台）：区分通用版与经开区版两套实现，改前先确认目标

## 通用

- JDK 版本按项目（haishihoutai 是 JDK17 + Spring Boot 4，kecu 是 Spring Boot 3），不混用依赖版本
- 配置文件区分环境，`config.properties` 等服务器专属配置**不纳入同步**
- 编译验证：`mvn compile -DskipTests` 或项目自带 `build.bat`
- 历史遗留 `_fix/_del` 调试脚本不入库，交付前清理
