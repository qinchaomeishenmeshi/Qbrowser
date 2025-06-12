// HTTP API 封装
class HttpAPI {
  constructor(baseURL = 'http://localhost:8000') {
    this.baseURL = baseURL;
    this.timeout = 30000;
    this.retryCount = 3;
    this.retryDelay = 1000;
  }

  // 设置基础URL
  setBaseURL(url) {
    this.baseURL = url;
  }

  // 设置超时时间
  setTimeout(timeout) {
    this.timeout = timeout;
  }

  // 构建完整URL
  buildURL(endpoint) {
    if (endpoint.startsWith('http')) {
      return endpoint;
    }
    return `${this.baseURL}${endpoint.startsWith('/') ? endpoint : '/' + endpoint}`;
  }

  // 处理响应
  async handleResponse(response) {
    if (!response.ok) {
      const error = new Error(`HTTP ${response.status}: ${response.statusText}`);
      error.status = response.status;
      error.statusText = response.statusText;
      
      try {
        const errorData = await response.json();
        error.data = errorData;
        error.message = errorData.message || error.message;
      } catch (e) {
        // 忽略JSON解析错误
      }
      
      throw error;
    }

    const contentType = response.headers.get('content-type');
    if (contentType && contentType.includes('application/json')) {
      return await response.json();
    }
    
    return await response.text();
  }

  // 重试机制
  async withRetry(fn, retries = this.retryCount) {
    try {
      return await fn();
    } catch (error) {
      if (retries > 0 && this.shouldRetry(error)) {
        await this.delay(this.retryDelay);
        return this.withRetry(fn, retries - 1);
      }
      throw error;
    }
  }

  // 判断是否应该重试
  shouldRetry(error) {
    // 网络错误或5xx服务器错误才重试
    return !error.status || error.status >= 500;
  }

  // 延迟函数
  delay(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  // GET请求
  async get(endpoint, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        const response = await fetch(url, {
          method: 'GET',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          signal: controller.signal,
          ...options
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // POST请求
  async post(endpoint, data = null, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: data ? JSON.stringify(data) : null,
          signal: controller.signal,
          ...options
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // PUT请求
  async put(endpoint, data = null, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        const response = await fetch(url, {
          method: 'PUT',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: data ? JSON.stringify(data) : null,
          signal: controller.signal,
          ...options
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // DELETE请求
  async delete(endpoint, data = null, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        const response = await fetch(url, {
          method: 'DELETE',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: data ? JSON.stringify(data) : null,
          signal: controller.signal,
          ...options
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // PATCH请求
  async patch(endpoint, data = null, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout);

      try {
        const response = await fetch(url, {
          method: 'PATCH',
          headers: {
            'Content-Type': 'application/json',
            ...options.headers
          },
          body: data ? JSON.stringify(data) : null,
          signal: controller.signal,
          ...options
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // 上传文件
  async upload(endpoint, file, options = {}) {
    return this.withRetry(async () => {
      const url = this.buildURL(endpoint);
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), this.timeout * 3); // 上传超时时间更长

      try {
        const formData = new FormData();
        formData.append('file', file);
        
        // 添加额外的表单数据
        if (options.data) {
          Object.keys(options.data).forEach(key => {
            formData.append(key, options.data[key]);
          });
        }

        const response = await fetch(url, {
          method: 'POST',
          body: formData,
          signal: controller.signal,
          headers: options.headers || {}
        });

        return await this.handleResponse(response);
      } finally {
        clearTimeout(timeoutId);
      }
    });
  }

  // 下载文件
  async download(endpoint, options = {}) {
    const url = this.buildURL(endpoint);
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), this.timeout * 5); // 下载超时时间更长

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: options.headers || {},
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      return response.blob();
    } finally {
      clearTimeout(timeoutId);
    }
  }

  // 流式请求（用于实时数据）
  async stream(endpoint, onData, options = {}) {
    const url = this.buildURL(endpoint);
    const controller = new AbortController();

    try {
      const response = await fetch(url, {
        method: 'GET',
        headers: {
          'Accept': 'text/event-stream',
          'Cache-Control': 'no-cache',
          ...options.headers
        },
        signal: controller.signal
      });

      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder();

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6));
              onData(data);
            } catch (e) {
              console.warn('解析SSE数据失败:', e);
            }
          }
        }
      }
    } catch (error) {
      if (error.name !== 'AbortError') {
        throw error;
      }
    }

    return () => controller.abort();
  }

  // 健康检查
  async health() {
    try {
      const response = await this.get('/api/health');
      return response.status === 'ok';
    } catch (error) {
      return false;
    }
  }

  // 获取API版本
  async version() {
    try {
      const response = await this.get('/api/version');
      return response.version;
    } catch (error) {
      return null;
    }
  }
}

// 创建默认实例
const httpAPI = new HttpAPI();

// 导出API类和默认实例
export { HttpAPI, httpAPI };
export default httpAPI;