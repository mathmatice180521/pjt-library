import { defineStore } from 'pinia'
import axios from 'axios'

export const useBooksStore = defineStore('books', {
  state: () => ({
    books: [],
    totalPages: 1,
    currentPage: 1,
    isLoading: false
  }),
  actions: {
    async fetchBooks({ q, category, page, per_page } = {}) {
      this.isLoading = true
      try {
        const API_URL = import.meta.env.VITE_API_URL
        const response = await axios.get(`${API_URL}/books/`, {
          params: {
            q: q || undefined,
            category: category || undefined,
            page: page || 1,
            per_page: per_page || 20
          }
        })
        this.books = response.data.results
        this.totalPages = response.data.total_pages || 1
        this.currentPage = parseInt(page) || 1
      } catch (error) {
        console.error('도서 로드 실패:', error)
        this.books = []
        this.totalPages = 1
      } finally {
        this.isLoading = false
      }
    }
  }
})