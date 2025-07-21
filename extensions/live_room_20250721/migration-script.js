/**
 * Chrome扩展配置外置迁移脚本
 * 用于从旧版本平滑迁移到新版本
 */

class MigrationScript {
    constructor() {
        this.version = '2.0.0';
        this.migrationKey = 'extension_migration_status';
    }

    /**
     * 执行迁移
     */
    async migrate() {
        try {
            console.log('开始执行配置外置迁移...');
            
            // 检查是否已经迁移过
            const migrationStatus = await this.getMigrationStatus();
            if (migrationStatus.completed && migrationStatus.version === this.version) {
                console.log('迁移已完成，跳过迁移过程');
                return { success: true, message: '迁移已完成' };
            }

            // 备份现有数据
            await this.backupExistingData();

            // 验证配置文件
            await this.validateConfiguration();

            // 迁移存储数据格式
            await this.migrateStorageData();

            // 标记迁移完成
            await this.markMigrationComplete();

            console.log('配置外置迁移完成');
            return { success: true, message: '迁移成功完成' };

        } catch (error) {
            console.error('迁移过程中发生错误:', error);
            await this.rollbackMigration();
            return { success: false, message: `迁移失败: ${error.message}` };
        }
    }

    /**
     * 获取迁移状态
     */
    async getMigrationStatus() {
        const result = await chrome.storage.local.get(this.migrationKey);
        return result[this.migrationKey] || { completed: false, version: null };
    }

    /**
     * 备份现有数据
     */
    async backupExistingData() {
        console.log('备份现有数据...');
        
        const allData = await chrome.storage.local.get(null);
        const backupKey = `backup_${Date.now()}`;
        
        await chrome.storage.local.set({
            [backupKey]: {
                timestamp: new Date().toISOString(),
                data: allData,
                version: '1.0.0'
            }
        });
        
        console.log(`数据已备份到: ${backupKey}`);
    }

    /**
     * 验证配置文件
     */
    async validateConfiguration() {
        console.log('验证配置文件...');
        
        try {
            // 尝试加载配置管理器
            if (typeof ConfigManager === 'undefined') {
                throw new Error('ConfigManager未定义，请确保config-manager.js已正确加载');
            }

            const configManager = new ConfigManager();
            await configManager.loadConfig();
            
            // 验证关键配置项
            const requiredConfigs = [
                'domains.douyin',
                'urls.api.product_detail',
                'timeouts.default',
                'storage.keys.frequent_words'
            ];

            for (const configKey of requiredConfigs) {
                const value = configManager.get(configKey);
                if (value === undefined || value === null) {
                    throw new Error(`缺少必需的配置项: ${configKey}`);
                }
            }

            console.log('配置文件验证通过');
        } catch (error) {
            throw new Error(`配置文件验证失败: ${error.message}`);
        }
    }

    /**
     * 迁移存储数据格式
     */
    async migrateStorageData() {
        console.log('迁移存储数据格式...');
        
        // 这里可以添加数据格式转换逻辑
        // 例如：将旧的存储键名转换为新的键名
        
        const allData = await chrome.storage.local.get(null);
        const migratedData = {};
        
        // 迁移常用词数据
        if (allData.frequentWords) {
            migratedData.frequentWords = allData.frequentWords;
        }
        
        // 迁移直播评论规则
        if (allData.liveroom_comments_rule) {
            migratedData.liveroom_comments_rule = allData.liveroom_comments_rule;
        }
        
        // 保存迁移后的数据
        if (Object.keys(migratedData).length > 0) {
            await chrome.storage.local.set(migratedData);
            console.log('存储数据迁移完成');
        }
    }

    /**
     * 标记迁移完成
     */
    async markMigrationComplete() {
        await chrome.storage.local.set({
            [this.migrationKey]: {
                completed: true,
                version: this.version,
                timestamp: new Date().toISOString()
            }
        });
    }

    /**
     * 回滚迁移
     */
    async rollbackMigration() {
        console.log('执行迁移回滚...');
        
        try {
            // 查找最新的备份
            const allData = await chrome.storage.local.get(null);
            const backupKeys = Object.keys(allData).filter(key => key.startsWith('backup_'));
            
            if (backupKeys.length > 0) {
                // 使用最新的备份
                const latestBackupKey = backupKeys.sort().pop();
                const backup = allData[latestBackupKey];
                
                // 清除当前数据
                await chrome.storage.local.clear();
                
                // 恢复备份数据
                await chrome.storage.local.set(backup.data);
                
                console.log(`已从备份 ${latestBackupKey} 恢复数据`);
            }
        } catch (error) {
            console.error('回滚失败:', error);
        }
    }

    /**
     * 清理旧备份
     */
    async cleanupOldBackups(keepCount = 3) {
        console.log('清理旧备份...');
        
        const allData = await chrome.storage.local.get(null);
        const backupKeys = Object.keys(allData)
            .filter(key => key.startsWith('backup_'))
            .sort()
            .reverse(); // 最新的在前
        
        if (backupKeys.length > keepCount) {
            const keysToRemove = backupKeys.slice(keepCount);
            await chrome.storage.local.remove(keysToRemove);
            console.log(`已清理 ${keysToRemove.length} 个旧备份`);
        }
    }

    /**
     * 获取迁移报告
     */
    async getMigrationReport() {
        const migrationStatus = await this.getMigrationStatus();
        const allData = await chrome.storage.local.get(null);
        const backupKeys = Object.keys(allData).filter(key => key.startsWith('backup_'));
        
        return {
            migrationStatus,
            backupCount: backupKeys.length,
            dataKeys: Object.keys(allData).filter(key => !key.startsWith('backup_') && key !== this.migrationKey),
            timestamp: new Date().toISOString()
        };
    }
}

// 导出迁移脚本类
if (typeof module !== 'undefined' && module.exports) {
    module.exports = MigrationScript;
} else if (typeof window !== 'undefined') {
    window.MigrationScript = MigrationScript;
}

// 自动执行迁移（仅在扩展环境中）
if (typeof chrome !== 'undefined' && chrome.storage) {
    const migrationScript = new MigrationScript();
    
    // 在扩展启动时自动执行迁移
    migrationScript.migrate().then(result => {
        console.log('迁移结果:', result);
        
        // 清理旧备份
        migrationScript.cleanupOldBackups();
    }).catch(error => {
        console.error('自动迁移失败:', error);
    });
}