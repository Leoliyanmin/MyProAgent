# Deployment Instruction

## Requirements

```shell
pip install -r requirements.txt
```

## Configuration（MacOS）

### Database

```shell
export SUSTECH_ASSISTANT_DATABASE_URL="postgresql://<username>:<password>@<host>:<port>/<database>"

#example: export SUSTECH_ASSISTANT_DATABASE_URL="postgresql://assistant:123456@localhost:5432/sustechdata"
```

### Security

Generate the secret key for JWT with

```shell
openssl rand -hex 32
```

Then set the environment variable

```shell
export SUSTECH_ASSISTANT_SECRETE_KEY=<SECRET KEY>
```

## System Initialization

```shell
cd backend/app
python main.py
```





## Configuration（Windows）

### Database

首先打开DataGrip

```sql
CREATE ROLE assistant WITH LOGIN PASSWORD '123456';
-- 在 DataGrip 的 postgres 超级用户连接里执行
CREATE DATABASE sustechdata
    OWNER assistant
    TEMPLATE template0
    ENCODING 'UTF8'
    LC_COLLATE 'C'
    LC_CTYPE 'C';

GRANT ALL PRIVILEGES ON DATABASE sustechdata TO assistant;
```

```powershell
setx SUSTECH_ASSISTANT_DATABASE_URL "postgresql://assistant:123456@localhost:5432/sustechdata"
```

然后关闭当前terminal，开一个新的。

### Security

### 2.1 生成密钥

在 Windows 用 Python：

```
python -c "import secrets; print(secrets.token_hex(32))"
```

输出类似：

```
5ce14153f40b5111a1a4715a68424edf288aeb72e492b0a8829a6092bb39cbc7
```

### 2.2 设置环境变量

永久设置：

```
setx SUSTECH_ASSISTANT_SECRET_KEY "161a4b82d083a4b614a8a269839948621ca376bea7249cda3e821aff6e8f521e"
```
### 2.3 设置Email本地加密密钥
```
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```
输出类似：
```
TNAW8-Ybgvzh9Y5tfgX9Mj30kd5k0ZjQv_rMeZN9jXA=
```
永久设置：在backend/app/core/.env中设置
```
EMAIL_CREDENTIAL_SECRET_KEY=TNAW8-Ybgvzh9Y5tfgX9Mj30kd5k0ZjQv_rMeZN9jXA=
```
## 3. 系统初始化 & 启动项目

进入后端目录并运行：

```powershell
cd D:\25Autumn\OOAD\CS309_OOAD_Project\backend\app
python main.py
```
