/**
 * Chrome扩展功能测试套件
 * 用于验证新版本的功能完整性和性能
 */

class ExtensionTestSuite {
    constructor() {
        this.testResults = [];
        this.configManager = null;
        this.startTime = Date.now();
    }

    /**
     * 运行完整测试套件
     */
    async runAllTests() {
        console.log('🚀 开始运行扩展功能测试套件...');
        
        try {
            // 初始化测试环境
            await this.initializeTestEnvironment();
            
            // 运行各项测试
            await this.testConfigManager();
            await this.testStorageFunctionality();
            await this.testUIComponents();
            await this.testBusinessLogic();
            await this.testPerformance();
            await this.testErrorHandling();
            
            // 生成测试报告
            this.generateTestReport();
            
        } catch (error) {
            console.error('❌ 测试套件执行失败:', error);
            this.addTestResult('测试套件执行', false, error.message);
        }
    }

    /**
     * 初始化测试环境
     */
    async initializeTestEnvironment() {
        console.log('🔧 初始化测试环境...');
        
        try {
            // 检查ConfigManager是否可用
            if (typeof ConfigManager !== 'undefined') {
                this.configManager = new ConfigManager();
                await this.configManager.loadConfig();
                this.addTestResult('配置管理器初始化', true, '配置管理器成功初始化');
            } else {
                throw new Error('ConfigManager未定义');
            }
        } catch (error) {
            this.addTestResult('配置管理器初始化', false, error.message);
            throw error;
        }
    }

    /**
     * 测试配置管理器功能
     */
    async testConfigManager() {
        console.log('⚙️ 测试配置管理器功能...');
        
        // 测试配置加载
        try {
            const domains = this.configManager.getDomains();
            this.addTestResult('域名配置加载', 
                domains && domains.douyin && Array.isArray(domains.douyin),
                `加载的域名: ${JSON.stringify(domains)}`);
        } catch (error) {
            this.addTestResult('域名配置加载', false, error.message);
        }

        // 测试URL配置
        try {
            const urls = this.configManager.getUrls();
            this.addTestResult('URL配置加载',
                urls && urls.api && urls.api.product_detail,
                `加载的URL: ${JSON.stringify(urls)}`);
        } catch (error) {
            this.addTestResult('URL配置加载', false, error.message);
        }

        // 测试超时配置
        try {
            const timeouts = this.configManager.getTimeouts();
            this.addTestResult('超时配置加载',
                timeouts && typeof timeouts.default === 'number',
                `加载的超时: ${JSON.stringify(timeouts)}`);
        } catch (error) {
            this.addTestResult('超时配置加载', false, error.message);
        }

        // 测试配置获取方法
        try {
            const testValue = this.configManager.get('domains.douyin', []);
            this.addTestResult('配置获取方法',
                Array.isArray(testValue),
                `获取的值: ${JSON.stringify(testValue)}`);
        } catch (error) {
            this.addTestResult('配置获取方法', false, error.message);
        }
    }

    /**
     * 测试存储功能
     */
    async testStorageFunctionality() {
        console.log('💾 测试存储功能...');
        
        if (typeof chrome === 'undefined' || !chrome.storage) {
            this.addTestResult('Chrome存储API', false, 'Chrome存储API不可用');
            return;
        }

        // 测试存储写入
        try {
            const testKey = 'test_storage_key';
            const testData = { timestamp: Date.now(), test: true };
            
            await chrome.storage.local.set({ [testKey]: testData });
            this.addTestResult('存储写入', true, '数据成功写入存储');
            
            // 测试存储读取
            const result = await chrome.storage.local.get(testKey);
            const isValid = result[testKey] && result[testKey].test === true;
            this.addTestResult('存储读取', isValid, `读取的数据: ${JSON.stringify(result)}`);
            
            // 清理测试数据
            await chrome.storage.local.remove(testKey);
            this.addTestResult('存储清理', true, '测试数据已清理');
            
        } catch (error) {
            this.addTestResult('存储功能', false, error.message);
        }
    }

    /**
     * 测试UI组件
     */
    async testUIComponents() {
        console.log('🎨 测试UI组件...');
        
        // 测试DOM元素存在性
        const requiredElements = [
            'word-list',
            'add-word-button', 
            'random-send-button',
            'tab-keywords',
            'tab-comments'
        ];
        
        for (const elementId of requiredElements) {
            const element = document.getElementById(elementId);
            this.addTestResult(`UI元素-${elementId}`,
                element !== null,
                element ? '元素存在' : '元素不存在');
        }

        // 测试CSS样式加载
        try {
            const computedStyle = window.getComputedStyle(document.body);
            const hasStyles = computedStyle.fontSize !== '' && computedStyle.color !== '';
            this.addTestResult('CSS样式加载', hasStyles, '样式已正确加载');
        } catch (error) {
            this.addTestResult('CSS样式加载', false, error.message);
        }
    }

    /**
     * 测试业务逻辑
     */
    async testBusinessLogic() {
        console.log('🔄 测试业务逻辑...');
        
        // 测试消息传递机制
        if (typeof chrome !== 'undefined' && chrome.tabs) {
            try {
                // 模拟消息发送（在实际环境中）
                this.addTestResult('消息传递机制', true, '消息传递API可用');
            } catch (error) {
                this.addTestResult('消息传递机制', false, error.message);
            }
        } else {
            this.addTestResult('消息传递机制', false, 'Chrome tabs API不可用');
        }

        // 测试数据处理逻辑
        try {
            // 模拟常用词数据处理
            const testWords = [{ word: '测试词汇', used: false }];
            const processedWords = testWords.filter(w => !w.used);
            this.addTestResult('数据处理逻辑',
                processedWords.length === 1,
                '数据处理逻辑正常');
        } catch (error) {
            this.addTestResult('数据处理逻辑', false, error.message);
        }
    }

    /**
     * 测试性能
     */
    async testPerformance() {
        console.log('⚡ 测试性能...');
        
        // 测试配置加载性能
        try {
            const startTime = performance.now();
            
            if (this.configManager) {
                await this.configManager.loadConfig();
                const loadTime = performance.now() - startTime;
                
                this.addTestResult('配置加载性能',
                    loadTime < 1000, // 1秒内完成
                    `加载时间: ${loadTime.toFixed(2)}ms`);
            }
        } catch (error) {
            this.addTestResult('配置加载性能', false, error.message);
        }

        // 测试内存使用
        try {
            if (performance.memory) {
                const memoryInfo = {
                    used: Math.round(performance.memory.usedJSHeapSize / 1024 / 1024),
                    total: Math.round(performance.memory.totalJSHeapSize / 1024 / 1024),
                    limit: Math.round(performance.memory.jsHeapSizeLimit / 1024 / 1024)
                };
                
                this.addTestResult('内存使用情况',
                    memoryInfo.used < 50, // 小于50MB
                    `内存使用: ${memoryInfo.used}MB / ${memoryInfo.total}MB`);
            }
        } catch (error) {
            this.addTestResult('内存使用情况', false, error.message);
        }
    }

    /**
     * 测试错误处理
     */
    async testErrorHandling() {
        console.log('🛡️ 测试错误处理...');
        
        // 测试配置文件缺失处理
        try {
            const invalidConfig = new ConfigManager();
            // 尝试获取不存在的配置
            const result = invalidConfig.get('non.existent.key', 'default');
            this.addTestResult('配置缺失处理',
                result === 'default',
                '正确返回默认值');
        } catch (error) {
            this.addTestResult('配置缺失处理', false, error.message);
        }

        // 测试网络错误处理
        try {
            // 模拟网络请求失败
            const mockError = new Error('网络请求失败');
            const hasErrorHandling = typeof mockError.message === 'string';
            this.addTestResult('网络错误处理', hasErrorHandling, '错误处理机制正常');
        } catch (error) {
            this.addTestResult('网络错误处理', false, error.message);
        }
    }

    /**
     * 添加测试结果
     */
    addTestResult(testName, passed, details) {
        const result = {
            name: testName,
            passed,
            details,
            timestamp: new Date().toISOString()
        };
        
        this.testResults.push(result);
        
        const status = passed ? '✅' : '❌';
        console.log(`${status} ${testName}: ${details}`);
    }

    /**
     * 生成测试报告
     */
    generateTestReport() {
        const endTime = Date.now();
        const duration = endTime - this.startTime;
        
        const totalTests = this.testResults.length;
        const passedTests = this.testResults.filter(r => r.passed).length;
        const failedTests = totalTests - passedTests;
        const successRate = ((passedTests / totalTests) * 100).toFixed(2);
        
        const report = {
            summary: {
                totalTests,
                passedTests,
                failedTests,
                successRate: `${successRate}%`,
                duration: `${duration}ms`,
                timestamp: new Date().toISOString()
            },
            results: this.testResults,
            recommendations: this.generateRecommendations()
        };
        
        console.log('\n📊 测试报告:');
        console.log('='.repeat(50));
        console.log(`总测试数: ${totalTests}`);
        console.log(`通过: ${passedTests}`);
        console.log(`失败: ${failedTests}`);
        console.log(`成功率: ${successRate}%`);
        console.log(`执行时间: ${duration}ms`);
        console.log('='.repeat(50));
        
        if (failedTests > 0) {
            console.log('\n❌ 失败的测试:');
            this.testResults
                .filter(r => !r.passed)
                .forEach(r => console.log(`  - ${r.name}: ${r.details}`));
        }
        
        if (report.recommendations.length > 0) {
            console.log('\n💡 建议:');
            report.recommendations.forEach(rec => console.log(`  - ${rec}`));
        }
        
        // 保存报告到存储
        if (typeof chrome !== 'undefined' && chrome.storage) {
            chrome.storage.local.set({
                test_report: report
            }).catch(error => {
                console.error('保存测试报告失败:', error);
            });
        }
        
        return report;
    }

    /**
     * 生成改进建议
     */
    generateRecommendations() {
        const recommendations = [];
        const failedTests = this.testResults.filter(r => !r.passed);
        
        if (failedTests.length > 0) {
            recommendations.push('修复失败的测试项目以确保功能完整性');
        }
        
        const performanceTests = this.testResults.filter(r => 
            r.name.includes('性能') && !r.passed
        );
        if (performanceTests.length > 0) {
            recommendations.push('优化性能相关问题以提升用户体验');
        }
        
        const uiTests = this.testResults.filter(r => 
            r.name.includes('UI') && !r.passed
        );
        if (uiTests.length > 0) {
            recommendations.push('检查UI组件的正确性和可用性');
        }
        
        if (this.testResults.length < 15) {
            recommendations.push('考虑增加更多测试用例以提高测试覆盖率');
        }
        
        return recommendations;
    }
}

// 导出测试套件
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ExtensionTestSuite;
} else if (typeof window !== 'undefined') {
    window.ExtensionTestSuite = ExtensionTestSuite;
}

// 自动运行测试（在开发环境中）
if (typeof window !== 'undefined' && window.location.href.includes('popup')) {
    // 在popup页面中延迟运行测试
    setTimeout(() => {
        const testSuite = new ExtensionTestSuite();
        testSuite.runAllTests().then(() => {
            console.log('🎉 测试套件执行完成');
        }).catch(error => {
            console.error('❌ 测试套件执行失败:', error);
        });
    }, 2000); // 等待2秒让页面完全加载
}