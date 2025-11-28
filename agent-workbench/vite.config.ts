import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
// import basicSsl from '@vitejs/plugin-basic-ssl'
import path from 'path'

// https://vite.dev/config/
export default defineConfig({
  plugins: [
    vue(),
    // basicSsl()  // 启用 HTTPS（自签名证书）- 暂时禁用，仅在需要局域网通知时启用
  ],
  server: {
    host: '0.0.0.0', // 允许局域网访问
    port: 5174,
    strictPort: true,
    // https: true,  // 启用 HTTPS - 暂时禁用
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true
      }
    }
  },
  resolve: {
    alias: {
      '@': path.resolve(__dirname, './src')
    }
  }
})
