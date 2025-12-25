import { createApp } from 'vue';
import App from './App.vue';
import router from './router';
import { createPinia } from 'pinia';
import axios from 'axios';
import { useAccountsStore } from '@/stores/accounts';

const app = createApp(App);
const pinia = createPinia();

app.use(pinia); // Pinia를 먼저 등록
app.use(router);

// Axios 인터셉터 설정
axios.interceptors.response.use(
  (response) => response,
  (error) => {
    const originalRequest = error.config;
    
    // URL 존재 여부 확인 후 체크 (안전장치)
    const isLoginRequest = originalRequest.url && originalRequest.url.includes('/auth/login/');

    if (error.response && error.response.status === 401) {
      if (isLoginRequest) {
        // 로그인 요청에서 401이 나면 여기서 차단하지 않고 
        // LoginView.vue의 catch 블록으로 바로 넘깁니다.
        return Promise.reject(error);
      }
      
      // 일반 API 요청 시 401인 경우
      alert('로그인 세션이 만료되었습니다. 다시 로그인해주세요.');
      const accountsStore = useAccountsStore();
      accountsStore.logout(); 
    }
    return Promise.reject(error);
  }
);

app.mount('#app');