import { defineStore } from 'pinia';
import axios from 'axios';
import { useAccountsStore } from './accounts';

const API_BASE_URL = import.meta.env.VITE_API_URL;

export const useAiStore = defineStore('ai', {
  state: () => ({
    history: [],
    totalPages: 1,
    currentPage: 1,
    isLoading: false,
    
    // [추가] 모달 열림 상태 전역 관리
    isModalOpen: false, 
    
    // [추가] 만화 생성 중 로딩 상태
    isGeneratingComic: false, 
  }),

  actions: {
    // 모달 제어 함수
    openModal() { this.isModalOpen = true; },
    closeModal() { this.isModalOpen = false; },

    async getRecommendation(prompt) {
      this.isLoading = true;
      const accountsStore = useAccountsStore();
      try {
        const response = await axios.post(
          `${API_BASE_URL}/ai/recommend/`,
          { prompt },
          { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } }
        );
        return response.data;
      } catch (error) {
        // 429 에러(하루 1회 제한 등) 처리
        if (error.response && error.response.status === 429) {
          throw new Error(error.response.data.error || '하루 사용량을 초과했습니다.');
        }
        console.error('AI 추천 요청 실패:', error);
        throw error;
      } finally {
        this.isLoading = false;
      }
    },
    
    // [추가] 4컷 만화 생성 요청 액션
    async generateComic(bookId) {
        this.isGeneratingComic = true;
        const accountsStore = useAccountsStore();
        try {
            // views.py의 generate_comic_view 호출
            // URL: /api/v1/ai/books/{book_id}/ai-content/
            const response = await axios.post(
                `${API_BASE_URL}/ai/books/${bookId}/ai-content/`,
                {}, // POST body는 비어있음
                { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } }
            );
            return response.data; // { comic_url: "...", message: "..." } 반환
        } catch (error) {
            console.error('만화 생성 실패:', error);
            throw error;
        } finally {
            this.isGeneratingComic = false;
        }
    },

    async fetchHistory(page = 1) {
      this.isLoading = true;
      const accountsStore = useAccountsStore();
      try {
        const response = await axios.get(`${API_BASE_URL}/ai/recommend/`, {
          params: { page, page_size: 5 },
          headers: { Authorization: `Bearer ${accountsStore.accessToken}` }
        });
        
        this.history = response.data.results;
        this.totalPages = response.data.total_pages || 1;
        this.currentPage = page;
      } catch (error) {
        console.error('AI 히스토리 로드 실패:', error);
      } finally {
        this.isLoading = false;
      }
    }
  }
});