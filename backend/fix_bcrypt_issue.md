# 修复 bcrypt 兼容性问题

## 问题描述

登录时出现以下错误：
1. `AttributeError: module 'bcrypt' has no attribute '__about__'` - bcrypt 版本兼容性问题
2. `ValueError: password cannot be longer than 72 bytes` - 密码长度限制

## 解决方案

### 方案1：重新安装兼容的包版本（推荐）

```bash
# 激活您的 conda 环境
conda activate Backup  # 或您的环境名称

# 卸载旧版本
pip uninstall bcrypt passlib -y

# 安装兼容版本
pip install bcrypt==4.0.1
pip install "passlib[bcrypt]>=1.7.4"
```

### 方案2：更新到最新版本

```bash
# 激活您的 conda 环境
conda activate Backup

# 更新所有相关包
pip install --upgrade bcrypt passlib
```

### 方案3：使用修复后的代码（已实现）

我已经更新了 `app/core/security.py`，添加了：
1. 密码长度检查（自动截断超过72字节的密码）
2. 回退机制（如果 passlib 失败，直接使用 bcrypt）
3. 更好的错误处理

## 验证修复

重启后端服务后，尝试登录。如果仍有问题，请运行：

```bash
python -c "import bcrypt; print(bcrypt.__version__)"
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print('passlib OK')"
```

## 注意事项

- bcrypt 有72字节的密码长度限制（这是 bcrypt 算法本身的限制）
- 如果用户密码超过72字节，系统会自动截断
- 建议在前端也添加密码长度限制（如最大64字符）


## 问题描述

登录时出现以下错误：
1. `AttributeError: module 'bcrypt' has no attribute '__about__'` - bcrypt 版本兼容性问题
2. `ValueError: password cannot be longer than 72 bytes` - 密码长度限制

## 解决方案

### 方案1：重新安装兼容的包版本（推荐）

```bash
# 激活您的 conda 环境
conda activate Backup  # 或您的环境名称

# 卸载旧版本
pip uninstall bcrypt passlib -y

# 安装兼容版本
pip install bcrypt==4.0.1
pip install "passlib[bcrypt]>=1.7.4"
```

### 方案2：更新到最新版本

```bash
# 激活您的 conda 环境
conda activate Backup

# 更新所有相关包
pip install --upgrade bcrypt passlib
```

### 方案3：使用修复后的代码（已实现）

我已经更新了 `app/core/security.py`，添加了：
1. 密码长度检查（自动截断超过72字节的密码）
2. 回退机制（如果 passlib 失败，直接使用 bcrypt）
3. 更好的错误处理

## 验证修复

重启后端服务后，尝试登录。如果仍有问题，请运行：

```bash
python -c "import bcrypt; print(bcrypt.__version__)"
python -c "from passlib.context import CryptContext; ctx = CryptContext(schemes=['bcrypt']); print('passlib OK')"
```

## 注意事项

- bcrypt 有72字节的密码长度限制（这是 bcrypt 算法本身的限制）
- 如果用户密码超过72字节，系统会自动截断
- 建议在前端也添加密码长度限制（如最大64字符）

