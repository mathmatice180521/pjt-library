import { defineStore } from 'pinia';
import axios from 'axios';
import router from '@/router';

const API_BASE_URL = import.meta.env.VITE_API_URL;

// [수정] Axios 응답 인터셉터
axios.interceptors.response.use(
  (response) => response,
  async (error) => {
    // 1. 401 에러 (인증 실패/토큰 만료) 발생 시
    if (error.response && error.response.status === 401) {
      const store = useAccountsStore();

      // 2. 현재 로그인 된 상태였다면
      if (store.isAuthenticated) {
        // 로그아웃 요청 자체가 에러난 경우는 제외하고 처리
        if (!error.config.url.includes('logout')) {
          // [요청사항 적용] 알림 메시지 출력
          alert("일정 시간동안 응답이 없어 자동으로 로그아웃 되셨습니다.");
          
          // 로컬 데이터 삭제 (로그아웃 처리)
          store.clearAuthData();
          
          // [요청사항 적용] HomeView(메인 페이지)로 이동
          router.push({ name: 'home' }); 
        }
      }
    }
    return Promise.reject(error);
  }
);

export const useAccountsStore = defineStore('accounts', {
  state: () => ({
    userId: null,
    username: null,
    isAuthenticated: false,
    accessToken: null,
    refreshToken: null,
  }),
  
// stores/accounts.js

actions: {
    // [수정] 앱 시작 시 토큰 유효성 검증 로직 추가
    async initializeAuth() {
      const access = localStorage.getItem('accessToken');
      const refresh = localStorage.getItem('refreshToken');
      const userId = localStorage.getItem('userId');
      const username = localStorage.getItem('username');

      // 1. 토큰이 존재하고, 문자열 'undefined'나 'null'이 아닌지 꼼꼼하게 확인
      if (access && refresh && access !== 'undefined' && access !== 'null') {
        // 일단은 있다고 저장해두지만...
        this.accessToken = access;
        this.refreshToken = refresh;
        this.userId = userId;
        this.username = username;
        this.isAuthenticated = true; // 일단 UI를 로그인 상태로 변경 (깜빡임 방지)

        // 2. [핵심] 진짜 유효한지 서버에 확인 사살 (유저 정보 가져오기 시도)
        try {
            await this.fetchUserInfo(); 
        } catch (error) {
            // 3. 만약 서버가 "누구세요?(401)" 하거나 에러가 나면 -> 즉시 로그아웃 처리
            console.warn("저장된 토큰이 만료되었거나 유효하지 않아 로그아웃 처리합니다.");
            this.clearAuthData();
        }
      } else {
        // 토큰이 없거나 이상하면 바로 클리어
        this.clearAuthData();
      }
    },

    // ... (나머지 fetchUserInfo, login, logout 등은 기존 코드 유지)

    async fetchUserInfo() {
      if (!this.accessToken) return;
      try {
        const response = await axios.get(`${API_BASE_URL}/auth/me/`, {
          headers: { Authorization: `Bearer ${this.accessToken}` }
        });
        this.userId = response.data.id;
        this.username = response.data.username;
        localStorage.setItem('userId', response.data.id);
        localStorage.setItem('username', response.data.username);
      } catch (error) {
        if (error.response && error.response.status !== 401) {
          console.error("유저 정보 로드 실패:", error);
        }
      }
    },

    async register(accountsData) {
      try {
        await axios.post(`${API_BASE_URL}/auth/register/`, accountsData);
        return await this.login({
          username: accountsData.username,
          password: accountsData.password,
        });
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    async login(credentials) {
      try {
        const response = await axios.post(`${API_BASE_URL}/auth/login/`, credentials);
        const { access, refresh } = response.data;
        
        this.accessToken = access;
        this.refreshToken = refresh;
        this.isAuthenticated = true;

        localStorage.setItem('accessToken', access);
        localStorage.setItem('refreshToken', refresh);

        await this.fetchUserInfo();
        return response.data;
      } catch (error) {
        this.clearAuthData();
        throw error.response?.data || error.message;
      }
    },

    async logout() {
      try {
        if (this.accessToken) {
          await axios.post(
            `${API_BASE_URL}/auth/logout/`, 
            { refresh: this.refreshToken }, 
            { headers: { Authorization: `Bearer ${this.accessToken}` } }
          );
        }
      } catch (error) {
        console.error('로그아웃 요청 오류(무시됨):', error);
      } finally {
        this.clearAuthData();
        router.push({ name: 'home' });
      }
    },

    async deleteAccount(password) {
      try {
        await axios.delete(
          `${API_BASE_URL}/auth/delete/`, 
          {
            headers: { Authorization: `Bearer ${this.accessToken}` },
            data: { password },
          }
        );
        this.clearAuthData();
        router.push({ name: 'home' });
      } catch (error) {
        throw error.response?.data || error.message;
      }
    },

    clearAuthData() {
      this.accessToken = null;
      this.refreshToken = null;
      this.userId = null;
      this.username = null;
      this.isAuthenticated = false;
      localStorage.removeItem('accessToken');
      localStorage.removeItem('refreshToken');
      localStorage.removeItem('userId');
      localStorage.removeItem('username');
    }
  },
});