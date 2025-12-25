import { defineStore } from 'pinia';
import axios from 'axios';
import { useAccountsStore } from './accounts';

// 배포된 서버 주소로 변경
const API_BASE_URL = import.meta.env.VITE_API_URL;

export const useCommentsStore = defineStore('comments', {
  state: () => ({
    isLoading: false,
  }),
  actions: {
    // 댓글 작성
    async createComment(bookId, content) {
      this.isLoading = true;
      try {
        const accountsStore = useAccountsStore();
        const response = await axios.post(
          `${API_BASE_URL}/books/${bookId}/comments/`, // 주소 수정
          { content },
          { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } }
        );
        return response.data;
      } finally {
        this.isLoading = false;
      }
    },
    // 댓글 수정
    async updateComment(commentId, content) {
      this.isLoading = true;
      try {
        const accountsStore = useAccountsStore();
        await axios.put(
          `${API_BASE_URL}/comments/${commentId}/`, // 주소 수정
          { content },
          { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } }
        );
      } finally {
        this.isLoading = false;
      }
    },
    // 댓글 삭제
    async deleteComment(commentId) {
      try {
        const accountsStore = useAccountsStore();
        await axios.delete(
          `${API_BASE_URL}/comments/${commentId}/`, // 주소 수정
          { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } }
        );
      } catch (error) {
        console.error('삭제 실패:', error);
        throw error;
      }
    }
  }
});