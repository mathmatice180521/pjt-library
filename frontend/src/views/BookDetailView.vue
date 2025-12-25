<template>
  <div v-if="book" class="detail-container">
    <section class="detail-header">
      <div class="header-content">
        <img :src="book.cover_url || 'https://placehold.co/200x300?text=No+Cover'" class="main-cover" />
        <div class="book-info-area">
          <p class="category">{{ book.category?.name || '미분류' }}</p>
          <h1 class="title">{{ book.title }}</h1>
          
          <div class="meta-info">
            <div class="rating-box">
              <span class="stars">⭐ {{ book.customer_review_rank || '0.0' }}</span>
              <span class="rank-text">점</span>
            </div>
            <div class="info-row">
              <span class="label">저자</span>
              <span class="value">{{ book.author }}</span>
            </div>
            <div class="info-row">
              <span class="label">출판사</span>
              <span class="value">{{ book.publisher }}</span>
            </div>
          </div>

          <button @click="toggleBookmark" :class="['btn-save', { active: book.is_bookmarked }]">
            {{ book.is_bookmarked ? '❤️ 저장됨' : '🤍 내 서재 담기' }}
          </button>
        </div>
      </div>
    </section>

    <section class="description-section">
      <h3>도서 소개</h3>
      <p class="description-text">{{ book.description || '도서 소개 정보가 없습니다.' }}</p>
    </section>

    <section class="detail-body">
      <div class="review-header">
        <h3>리뷰 ({{ book.comment_count || 0 }})</h3>
        <button v-if="isAuthenticated" @click="goToCreateComment" class="btn-write">리뷰 쓰기</button>
      </div>

      <div v-if="book.comments && book.comments.length > 0">
        <div v-for="comment in book.comments" :key="comment.comment_id" class="comment-card">
          <div class="comment-user">
            <span class="username">{{ comment.username }}</span>
            <span class="date">{{ formatDate(comment.created_at) }}</span>
          </div>
          <p class="comment-content">{{ comment.content }}</p>
          
          <div v-if="isMyComment(comment)" class="comment-actions">
            <button @click="goToUpdateComment(comment)">수정</button>
            <button @click="handleDeleteComment(comment.comment_id)" class="delete">삭제</button>
          </div>
        </div>
      </div>

      <div v-else class="empty-comments">
        첫 번째 리뷰를 남겨보세요! ✍️
      </div>
    </section>
  </div>
  
  <div v-else class="loading">정보를 불러오는 중...</div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import axios from 'axios';
import { useAccountsStore } from '@/stores/accounts';
import { useCommentsStore } from '@/stores/comments';

const route = useRoute();
const router = useRouter();
const accountsStore = useAccountsStore();
const commentStore = useCommentsStore();

const book = ref(null);
const isAuthenticated = computed(() => accountsStore.isAuthenticated);

const isMyComment = (c) => isAuthenticated.value && String(accountsStore.userId) === String(c.user_id);

const fetchBookDetail = async () => {
  const id = route.params.id;
  if (!id || id === 'undefined') return;

  const url = `${import.meta.env.VITE_API_URL}/books/${id}/`;
  try {
    const config = isAuthenticated.value ? { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } } : {};
    const res = await axios.get(url, config);
    book.value = res.data;
  } catch (err) {
    if (err.response?.status === 401) {
      // 토큰 만료 시 비로그인 모드로 한 번 더 시도
      const res = await axios.get(url);
      book.value = res.data;
    }
  }
};

const toggleBookmark = async () => {
  if (!isAuthenticated.value) return router.push({ name: 'login' });
  const url = `${import.meta.env.VITE_API_URL}/books/${book.value.id}/bookmark/`;
  const config = { headers: { Authorization: `Bearer ${accountsStore.accessToken}` } };
  try {
    if (book.value.is_bookmarked) { await axios.delete(url, config); book.value.is_bookmarked = false; }
    else { await axios.post(url, {}, config); book.value.is_bookmarked = true; }
  } catch (err) { if (err.response?.status === 401) router.push({ name: 'login' }); }
};

const handleDeleteComment = async (id) => {
  if (confirm("삭제하시겠습니까?")) { await commentStore.deleteComment(id); fetchBookDetail(); }
};

const goToCreateComment = () => router.push({ name: 'commentcreate', params: { bookId: book.value.id } });
const goToUpdateComment = (c) => router.push({ name: 'commentupdate', params: { commentId: c.comment_id }, query: { content: c.content } });
const formatDate = (d) => new Date(d).toLocaleDateString();

// 상세 페이지 내에서 다른 책으로 이동 시 감시
watch(() => route.params.id, (newId) => { if (newId) fetchBookDetail(); });
onMounted(fetchBookDetail);
</script>

<style scoped>
/* 1. 전체 컨테이너 및 기본 레이아웃 */
.detail-container { 
  max-width: 900px; 
  margin: 40px auto; 
  padding: 20px; 
  color: #242424;
}

/* 2. 헤더 섹션 (커버 이미지 + 주요 정보) */
.detail-header { 
  margin-bottom: 50px; 
}

.header-content { 
  display: flex; 
  gap: 50px; 
  align-items: flex-start; 
}

.main-cover { 
  width: 240px; 
  border-radius: 8px; 
  box-shadow: 0 10px 30px rgba(0,0,0,0.1); 
  flex-shrink: 0;
}

.book-info-area { 
  flex: 1; 
}

.category { 
  color: #888; 
  font-size: 0.95rem; 
  margin-bottom: 10px; 
}

.title { 
  font-size: 2.4rem; 
  font-weight: 800;
  margin: 0 0 20px 0; 
  line-height: 1.2; 
}

/* 3. [신규 추가] 메타 정보 섹션 (별점, 저자, 출판사) */
.meta-info {
  margin-bottom: 30px;
  padding: 20px 0;
  border-top: 1px solid #f0f0f0;
  border-bottom: 1px solid #f0f0f0;
}

.rating-box {
  margin-bottom: 15px;
  display: flex;
  align-items: center;
}

.stars {
  font-size: 1.5rem;
  font-weight: 800;
  color: #242424;
  margin-right: 5px;
}

.rank-text {
  font-size: 0.9rem;
  color: #999;
  margin-top: 4px;
}

.info-row {
  display: flex;
  margin-bottom: 8px;
  font-size: 1.05rem;
}

.info-row .label {
  width: 70px;
  color: #999;
  flex-shrink: 0;
}

.info-row .value {
  color: #444;
  font-weight: 500;
}

/* 4. 버튼 스타일 */
.btn-save { 
  padding: 14px 32px; 
  border-radius: 30px; 
  border: 1px solid #ddd;
  background: white; 
  cursor: pointer; 
  font-weight: bold; 
  transition: all 0.2s;
  font-size: 1rem;
}

.btn-save:hover {
  background-color: #f9f9f9;
}

.btn-save.active { 
  background-color: #fff0f0; 
  border-color: #ff4d4f; 
  color: #ff4d4f; 
}

/* 5. [신규 추가] 도서 소개 섹션 */
.description-section {
  padding: 50px 0;
  border-bottom: 1px solid #eee;
}

.description-section h3 {
  font-size: 1.4rem;
  font-weight: 700;
  margin-bottom: 25px;
}

.description-text {
  line-height: 1.9;
  color: #4a4a4a;
  font-size: 1.1rem;
  white-space: pre-wrap; /* 서버에서 온 줄바꿈 데이터 유지 */
  word-break: break-all;
}

/* 6. 리뷰/댓글 섹션 */
.detail-body { 
  padding-top: 40px; 
}

.review-header { 
  display: flex; 
  justify-content: space-between; 
  align-items: center; 
  margin-bottom: 30px; 
}

.review-header h3 {
  font-size: 1.4rem;
}

.btn-write { 
  background: #ffeb00; 
  border: none; 
  padding: 12px 24px; 
  border-radius: 25px; 
  font-weight: bold; 
  cursor: pointer; 
  transition: background 0.2s;
}

.btn-write:hover {
  background: #f7e300;
}

.comment-card { 
  padding: 30px 0; 
  border-bottom: 1px solid #f5f5f5; 
}

.comment-user { 
  margin-bottom: 12px; 
}

.username { 
  font-weight: bold; 
  margin-right: 15px; 
  font-size: 1.1rem; 
}

.date { 
  color: #bbb; 
  font-size: 0.9rem; 
}

.comment-actions { 
  margin-top: 15px; 
  display: flex; 
  gap: 20px; 
}

.comment-actions button { 
  background: none; 
  border: none; 
  color: #999; 
  cursor: pointer; 
  font-size: 0.9rem; 
  padding: 0;
  text-decoration: underline; 
}

.comment-actions button.delete { 
  color: #ff4d4f; 
}

/* 7. 로딩 상태 */
.loading { 
  text-align: center; 
  padding: 100px 0; 
  font-size: 1.2rem; 
  color: #bbb; 
}

/* 반응형 처리 (모바일 대응) */
@media (max-width: 768px) {
  .header-content {
    flex-direction: column;
    align-items: center;
    text-align: center;
    gap: 30px;
  }
  
  .info-row {
    justify-content: center;
  }
  
  .info-row .label {
    width: 60px;
  }
}
</style>