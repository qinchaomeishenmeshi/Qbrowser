# Chrome扩展配置外置版本部署指南

## 概述

本指南详细说明如何将Chrome扩展从旧版本（硬编码配置）迁移到新版本（配置外置）。新版本提供了更好的可维护性、灵活性和扩展性。

## 版本对比

| 特性 | 旧版本 (v1.0) | 新版本 (v2.0) |
|------|---------------|---------------|
| 配置管理 | 硬编码 | 外置JSON配置 |
| 可维护性 | 低 | 高 |
| 配置验证 | 无 | 完整验证 |
| 错误处理 | 基础 | 增强 |
| 向后兼容 | N/A | 完全兼容 |
| 性能优化 | 无 | 配置缓存 |

## 文件结构对比

### 旧版本文件
```
live_room/
├── manifest.json          # 旧版本清单
├── background.js          # 旧版本后台脚本
├── content.js            # 旧版本内容脚本
├── popup.html            # 旧版本弹窗
├── popup.js              # 旧版本弹窗脚本
└── utils/
    ├── request.js        # 旧版本请求工具
    └── setting.js        # 旧版本设置
```

### 新版本文件
```
live_room/
├── manifest-v2.json           # 新版本清单
├── background-refactored.js   # 重构后台脚本
├── content-refactored.js      # 重构内容脚本
├── popup-v2.html             # 新版本弹窗
├── popup-refactored.js       # 重构弹窗脚本
├── config/
│   └── app-config.json       # 配置文件
├── utils/
│   ├── config-manager.js     # 配置管理器
│   ├── request-refactored.js # 重构请求工具
│   └── setting-refactored.js # 重构设置
├── config-validator.js       # 配置验证器
├── migration-script.js       # 迁移脚本
└── 文档文件...
```

## 部署步骤

### 步骤1: 备份现有扩展

1. **导出现有扩展数据**
   ```bash
   # 备份扩展目录
   cp -r live_room live_room_backup_$(date +%Y%m%d)
   ```

2. **导出Chrome存储数据**
   - 打开Chrome扩展管理页面
   - 点击"开发者模式"
   - 使用"检查视图"导出storage数据

### 步骤2: 验证新版本文件

1. **检查必需文件**
   ```bash
   # 确保以下文件存在
   ls -la live_room/config/app-config.json
   ls -la live_room/utils/config-manager.js
   ls -la live_room/manifest-v2.json
   ls -la live_room/*-refactored.js
   ```

2. **验证配置文件**
   ```javascript
   // 在浏览器控制台中运行
   fetch('chrome-extension://YOUR_EXTENSION_ID/config/app-config.json')
     .then(response => response.json())
     .then(config => console.log('配置文件有效:', config))
     .catch(error => console.error('配置文件错误:', error));
   ```

### 步骤3: 部署新版本

#### 方案A: 直接替换（推荐用于开发环境）

1. **停用旧扩展**
   - 在Chrome扩展管理页面停用现有扩展

2. **替换文件**
   ```bash
   # 重命名旧文件
   mv manifest.json manifest-v1.json
   mv background.js background-v1.js
   mv content.js content-v1.js
   mv popup.html popup-v1.html
   mv popup.js popup-v1.js
   
   # 启用新文件
   mv manifest-v2.json manifest.json
   mv background-refactored.js background.js
   mv content-refactored.js content.js
   mv popup-v2.html popup.html
   mv popup-refactored.js popup.js
   ```

3. **重新加载扩展**
   - 在Chrome扩展管理页面点击"重新加载"

#### 方案B: 并行部署（推荐用于生产环境）

1. **创建新扩展目录**
   ```bash
   cp -r live_room live_room_v2
   cd live_room_v2
   ```

2. **配置新版本**
   ```bash
   # 使用新版本文件
   cp manifest-v2.json manifest.json
   cp background-refactored.js background.js
   cp content-refactored.js content.js
   cp popup-v2.html popup.html
   cp popup-refactored.js popup.js
   ```

3. **安装新扩展**
   - 在Chrome扩展管理页面加载新目录
   - 测试功能正常后停用旧扩展

### 步骤4: 执行数据迁移

1. **自动迁移**
   - 新版本会自动执行迁移脚本
   - 检查控制台输出确认迁移状态

2. **手动迁移**（如果自动迁移失败）
   ```javascript
   // 在扩展的background页面控制台中运行
   const migrationScript = new MigrationScript();
   migrationScript.migrate().then(result => {
     console.log('迁移结果:', result);
   });
   ```

### 步骤5: 验证部署

1. **功能测试**
   - [ ] 扩展图标正常显示
   - [ ] 弹窗界面正常打开
   - [ ] 常用词功能正常
   - [ ] 直播评论功能正常
   - [ ] 配置保存和加载正常

2. **配置测试**
   ```javascript
   // 在content script控制台中运行
   if (typeof configManager !== 'undefined') {
     console.log('配置管理器可用');
     console.log('域名配置:', configManager.getDomains());
     console.log('URL配置:', configManager.getUrls());
   } else {
     console.error('配置管理器不可用');
   }
   ```

3. **性能测试**
   - 检查内存使用情况
   - 验证配置加载时间
   - 确认无内存泄漏

## 回滚方案

如果新版本出现问题，可以快速回滚到旧版本：

### 自动回滚
```javascript
// 在扩展控制台中运行
const migrationScript = new MigrationScript();
migrationScript.rollbackMigration();
```

### 手动回滚
1. 停用新版本扩展
2. 恢复备份的旧版本文件
3. 重新加载旧版本扩展
4. 从备份恢复存储数据

## 配置自定义

### 修改配置文件

编辑 `config/app-config.json`：

```json
{
  "domains": {
    "douyin": ["douyin.com", "your-custom-domain.com"]
  },
  "urls": {
    "api": {
      "product_detail": "https://your-api.com/product/detail/"
    }
  },
  "timeouts": {
    "default": 30000,
    "api_request": 15000
  }
}
```

### 验证自定义配置

```javascript
// 使用配置验证器
const validator = new ConfigValidator();
validator.validateConfig().then(result => {
  if (result.isValid) {
    console.log('配置验证通过');
  } else {
    console.error('配置验证失败:', result.errors);
  }
});
```

## 故障排除

### 常见问题

1. **配置文件加载失败**
   - 检查文件路径和权限
   - 验证JSON格式
   - 确认web_accessible_resources配置

2. **迁移脚本执行失败**
   - 检查控制台错误信息
   - 验证存储权限
   - 手动执行迁移步骤

3. **功能异常**
   - 清除扩展数据重新测试
   - 检查配置项是否完整
   - 验证API接口可用性

### 调试工具

1. **配置诊断**
   ```javascript
   // 获取配置诊断信息
   configManager.getDiagnostics().then(info => {
     console.log('配置诊断:', info);
   });
   ```

2. **迁移报告**
   ```javascript
   // 获取迁移报告
   const migrationScript = new MigrationScript();
   migrationScript.getMigrationReport().then(report => {
     console.log('迁移报告:', report);
   });
   ```

## 维护建议

1. **定期备份**
   - 定期备份配置文件和扩展数据
   - 保留多个版本的备份

2. **配置管理**
   - 使用版本控制管理配置文件
   - 建立配置变更审核流程

3. **监控告警**
   - 监控扩展错误日志
   - 设置配置验证失败告警

4. **性能优化**
   - 定期清理旧备份数据
   - 优化配置文件大小
   - 监控内存使用情况

## 联系支持

如果在部署过程中遇到问题，请：

1. 查看控制台错误信息
2. 收集迁移报告和配置诊断信息
3. 提供详细的错误描述和复现步骤
4. 联系技术支持团队

---

**注意**: 在生产环境部署前，请务必在测试环境中完整验证所有功能。