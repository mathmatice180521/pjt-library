<template>
  <div class="mypage-container">
    <header class="mypage-header">
      <h1>마이페이지</h1>
      <p class="user-welcome">안녕하세요, <strong>{{ username }}</strong>님!</p>
    </header>

    <nav class="mypage-tabs">
      <button :class="{ active: activeTab === 'feature' }" @click="activeTab = 'feature'">AI 추천 및 4컷 만화</button>
      <button :class="{ active: activeTab === 'bookmarks' }" @click="activeTab = 'bookmarks'">내가 북마크한 책들</button>
      <button :class="{ active: activeTab === 'comments' }" @click="activeTab = 'comments'">내가 쓴 리뷰</button>
    </nav>

    <main class="tab-content">
      
      <div v-if="activeTab === 'feature'" class="ai-section">
        <div v-if="!aiStore.history || aiStore.history.length === 0" class="no-data">
          아직 추천받은 내역이 없습니다.<br/>
          <a @click="openAiChat" class="ai-link" style="cursor: pointer;">AI 도우미에게 추천받으러 가기 👉</a>
        </div>

        <div v-for="(record, idx) in aiStore.history" :key="idx" class="ai-history-card">
          <div class="history-header">
            <span class="ai-badge">AI 큐레이션</span>
            <span class="date">{{ formatDate(record.generated_at) }}의 추천</span>
          </div>

          <div class="history-books">
            <div v-for="book in record.recommended_list" :key="book.book_pk" class="ai-book-item" @click="goToDetail(book.book_pk)">
              
              <div class="cover-wrapper">
                  <img :src="resolveImageUrl(book.cover)" class="mini-cover" @error="handleImgError" />
                  
                  <div v-if="book.comic_image_url" class="comic-badge-container">
                    <div class="comic-preview" @click.stop="downloadImage(book.comic_image_url, book.title)">
                        <img :src="resolveImageUrl(book.comic_image_url)" class="comic-thumb" />
                        <div class="download-overlay"><span>⬇</span></div>
                    </div>
                    <span class="comic-label">4컷만화</span>
                  </div>
              </div>

              <div class="info-area">
                <h3 class="book-title">{{ book.title }}</h3>
                <div class="reason-box">
                  <span class="reason-icon">💬</span>
                  <p class="reason-text">{{ book.reason }}</p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'bookmarks'" class="bookmark-section">
        <div v-if="!bookmarks || bookmarks.length === 0" class="no-data">북마크한 책이 없습니다.</div>
        <div class="bookmark-grid">
          <div v-for="book in bookmarks" :key="book.book_id" class="book-card" @click="goToDetail(book.book_id)">
            <img :src="resolveImageUrl(book.cover_url)" :alt="book.title" @error="handleImgError" />
            <div class="book-info">
              <h3 class="ellipsis">{{ book.title }}</h3>
              <p class="author">{{ book.author }}</p>
            </div>
          </div>
        </div>
      </div>

      <div v-if="activeTab === 'comments'" class="comment-section">
        <div v-if="!comments || comments.length === 0" class="no-data">작성한 댓글이 없습니다.</div>
        <div v-for="comment in comments" :key="comment.comment_id" class="comment-item">
          <div class="comment-target" @click="goToDetail(comment.book_id)">
            <span class="book-tag">도서</span>
            <strong>{{ comment.book_title }}</strong>
          </div>
          <p class="comment-body">{{ comment.content }}</p>
          <div class="comment-footer"><span class="date">{{ formatDate(comment.created_at) }}</span></div>
        </div>
      </div>
    </main>
  </div>
</template>

<script setup>
import { ref, onMounted, computed, watch } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import axios from 'axios';
import { useAccountsStore } from '@/stores/accounts';
import { useAiStore } from '@/stores/airecommend';

const router = useRouter();
const route = useRoute();
const accountsStore = useAccountsStore();
const aiStore = useAiStore();

// 탭 상태 관리
const activeTab = ref(route.query.tab || 'feature'); 
const bookmarks = ref([]);
const comments = ref([]);
const username = computed(() => accountsStore.username || '독자');

// =================================================
// http://www.kpedia.jp/w/7006 여기가 제일 중요합니다.
// =================================================

// 1. API 요청용 주소 (데이터용)
// 예: http://127.0.0.1:8000/api/v1
let API_URL = import.meta.env.VITE_API_URL || 'http://127.0.0.1:8000/api/v1';
// 끝에 슬래시(/)가 있으면 제거
if (API_URL.endsWith('/')) API_URL = API_URL.slice(0, -1);

// 2. 이미지용 서버 도메인 (이미지용)
// API_URL에서 '/api/v1'을 떼어내고 순수 도메인만 남깁니다.
// 예: http://127.0.0.1:8000/api/v1 -> http://127.0.0.1:8000
const SERVER_HOST = API_URL.replace('/api/v1', '');

// 헤더 설정
const config = computed(() => ({ 
    headers: { Authorization: `Bearer ${accountsStore.accessToken}` } 
}));

// [이미지 경로 해결 함수]
const resolveImageUrl = (path) => {
  if (!path) return 'https://placehold.co/150x220?text=No+Image';
  if (path.startsWith('http')) return path; // 이미 완전한 주소면 그대로

  // 경로 앞에 슬래시가 없으면 붙여줌
  const cleanPath = path.startsWith('/') ? path : `/${path}`;
  
  // 도메인 + 경로 조합
  return `${SERVER_HOST}${cleanPath}`;
};

// [API 호출 함수들]
const fetchBookmarks = async () => {
  try {
    const response = await axios.get(`${API_URL}/mypage/bookmarks/`, config.value);
    bookmarks.value = response.data.results || [];
  } catch (error) {
    console.error("북마크 로드 실패:", error);
  }
};

const fetchComments = async () => {
  try {
    const response = await axios.get(`${API_URL}/mypage/comments/`, config.value);
    comments.value = response.data.results || [];
  } catch (error) {
    console.error("댓글 로드 실패:", error);
  }
};

// [다운로드 함수]
const downloadImage = async (url, title) => {
    if (!url) return alert("이미지 주소가 없습니다.");
    
    try {
        const fullUrl = resolveImageUrl(url);
        const response = await axios.get(fullUrl, { responseType: 'blob' });
        
        const blob = new Blob([response.data]);
        const link = document.createElement('a');
        link.href = window.URL.createObjectURL(blob);
        link.download = `${title}_4컷만화.png`;
        document.body.appendChild(link);
        link.click();
        
        document.body.removeChild(link);
        window.URL.revokeObjectURL(link.href);
    } catch (e) {
        console.error("다운로드 실패:", e);
        window.open(resolveImageUrl(url), '_blank');
    }
};

// [기타 유틸]
const goToDetail = (id) => router.push({ name: 'BookDetail', params: { id } });
const formatDate = (date) => new Date(date).toLocaleDateString();
const handleImgError = (e) => { e.target.src = 'https://placehold.co/150x220?text=No+Image'; };
const openAiChat = () => { aiStore.openModal(); };

// [탭 변경 감지]
watch(() => activeTab.value, (newTab) => {
  router.replace({ query: { tab: newTab } });
  loadTabData(newTab);
});

// [데이터 로드 통합]
const loadTabData = (tab) => {
  if (tab === 'feature') aiStore.fetchHistory();
  else if (tab === 'bookmarks') fetchBookmarks();
  else if (tab === 'comments') fetchComments();
};

onMounted(async () => {
  if (!accountsStore.accessToken) { 
      router.push({ name: 'login' }); 
      return; 
  }
  if (!accountsStore.username) await accountsStore.fetchUserInfo();
  
  loadTabData(activeTab.value);
});
</script>

<style scoped>
/* 기존 스타일 그대로 유지 */
.mypage-container { max-width: 1000px; margin: 40px auto; padding: 0 20px; }
.mypage-header h1 { font-size: 28px; margin-bottom: 10px; }
.mypage-tabs { display: flex; gap: 20px; border-bottom: 2px solid #eee; margin-bottom: 40px; }
.mypage-tabs button { padding: 15px 10px; background: none; border: none; font-size: 16px; cursor: pointer; color: #999; }
.mypage-tabs button.active { color: #242424; font-weight: bold; border-bottom: 2px solid #242424; }
.bookmark-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(160px, 1fr)); gap: 30px; }
.book-card { cursor: pointer; }
.book-card img { width: 100%; border-radius: 6px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
.book-info h3 { font-size: 14px; margin-top: 10px; }
.comment-item { padding: 25px; border: 1px solid #f2f2f2; border-radius: 12px; margin-bottom: 20px; }
.book-tag { background: #f9f9f9; padding: 4px 8px; border-radius: 4px; font-size: 12px; margin-right: 8px; color: #888; }
.milli-pagination { display: flex; justify-content: center; align-items: center; margin: 50px 0; gap: 10px; }
.nav-btn { background: none; border: none; font-size: 22px; color: #ccc; cursor: pointer; transition: color 0.2s; }
.nav-btn:hover:not(:disabled) { color: #333; }
.num-group { display: flex; gap: 8px; }
.num-btn { width: 36px; height: 36px; border: none; background: none; border-radius: 50%; cursor: pointer; color: #999; }
.num-btn.active { background: #ffeb00; color: #242424; font-weight: bold; }
.no-data { text-align: center; padding: 100px 0; color: #ccc; }
.ellipsis { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.ai-link { color: #242424; font-weight: bold; text-decoration: none; border-bottom: 1px solid #ffeb00; }
.ai-history-card { background: #fff; border: 1px solid #eee; border-radius: 16px; padding: 25px; margin-bottom: 30px; box-shadow: 0 5px 20px rgba(0,0,0,0.03); }
.history-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; border-bottom: 1px solid #f5f5f5; padding-bottom: 15px; }
.ai-badge { background: #ffeb00; color: #242424; padding: 4px 10px; border-radius: 12px; font-size: 12px; font-weight: 800; }
.date { color: #aaa; font-size: 13px; }
.history-books { display: flex; flex-direction: column; gap: 15px; }
.ai-book-item { display: flex; gap: 15px; cursor: pointer; padding: 10px; border-radius: 8px; transition: background 0.2s; }
.ai-book-item:hover { background: #fafafa; }
.info-area { flex: 1; display: flex; flex-direction: column; justify-content: center; }
.book-title { font-size: 15px; font-weight: bold; margin: 0 0 8px 0; color: #333; }
.reason-box { display: flex; gap: 8px; align-items: flex-start; }
.reason-icon { font-size: 14px; margin-top: 2px; }
.reason-text { font-size: 13px; color: #666; margin: 0; line-height: 1.5; background: #f8f8f8; padding: 10px; border-radius: 0 10px 10px 10px; flex: 1; }
.cover-wrapper { display: flex; gap: 10px; align-items: flex-start; }
.mini-cover { width: 60px; height: 85px; object-fit: cover; border-radius: 4px; box-shadow: 0 2px 5px rgba(0,0,0,0.1); }
.comic-badge-container { display: flex; flex-direction: column; align-items: center; gap: 4px; }
.comic-preview { width: 60px; height: 60px; border-radius: 6px; overflow: hidden; border: 1px solid #ddd; position: relative; cursor: pointer; }
.comic-thumb { width: 100%; height: 100%; object-fit: cover; transition: 0.3s; }
.download-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.2s; color: white; font-size: 20px; font-weight: bold; }
.comic-preview:hover .download-overlay { opacity: 1; }
.comic-preview:hover .comic-thumb { transform: scale(1.1); }
.comic-label { font-size: 10px; color: #888; letter-spacing: -0.5px; }
</style>