@echo off
chcp 65001 >nul
echo ===== 环境检查表 =====
echo [Java]
java -version 2>&1 | findstr /i "version"
echo [Maven]
call mvn -v 2>nul | findstr /i "Apache Maven"
echo [Node]
node -v 2>nul
echo [npm]
call npm -v 2>nul
echo [MySQL 服务]
sc query MySQL80 2>nul | findstr /i "STATE"
echo [Redis 本地端口 6379]
powershell -Command "Test-NetConnection -ComputerName 127.0.0.1 -Port 6379 -InformationLevel Quiet" 2>nul
echo ===== 常用启动 =====
echo haishihoutai/kecu: build.bat, start-all.bat / start-dev.bat
echo yz/zl (OFBiz): startoa.bat
echo 前端: npm run dev / npm run build:prod
pause
