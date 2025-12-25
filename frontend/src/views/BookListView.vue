<template>
  <div class="book-list-container">
    <nav class="category-nav">
      <div class="category-scroll-wrapper">
        <button 
          @click="handleCategoryChange('')" 
          :class="['chip-btn', { active: !selectedCategory }]"
        >
          전체
        </button>

        <button 
          v-for="cat in categories" 
          :key="cat.id" 
          @click="handleCategoryChange(cat.id)" 
          :class="['chip-btn', { active: String(selectedCategory) === String(cat.id) }]"
        >
          {{ cat.name }}
        </button>
      </div>
    </nav>

    <div v-if="store.isLoading" class="loading-view">
      <div class="spinner"></div>
      <p>도서를 불러오는 중입니다...</p>
    </div>

    <div v-else-if="store.books?.length > 0" class="content-area">
      <div class="book-grid">
        <div v-for="(book, index) in (store.books || [])" :key="book.id" class="book-item" :style="{ animationDelay: `${index * 0.05}s` }">
          <router-link :to="`/books/${book.id}`" class="book-link">
            <div class="cover-wrapper">
              <img :src="book.cover_url || 'https://placehold.co/150x225?text=No+Image'" class="book-cover" />
              <div class="cover-overlay">
                <span>자세히 보기</span>
              </div>
            </div>
            <div class="book-details">
              <h3 class="book-title">{{ book.title }}</h3>
              <p class="book-author">{{ book.author }}</p>
            </div>
          </router-link>
        </div>
      </div>

      <div class="pagination-wrapper" v-if="store.totalPages > 0">
        <div class="pagination">
          <button class="nav-btn" :disabled="store.currentPage === 1" @click="goToPage(1)">«</button>
          <button class="nav-btn" :disabled="store.currentPage === 1" @click="goToPage(store.currentPage - 1)">‹</button>
          
          <div class="num-group">
            <button 
              v-for="p in displayedPages" 
              :key="p" 
              @click="goToPage(p)"
              :class="['num-btn', { active: store.currentPage === p }]"
            >
              {{ p }}
            </button>
            <template v-if="showEndEllipsis">
              <span class="ellipsis">...</span>
              <button @click="goToPage(store.totalPages)" class="num-btn">{{ store.totalPages }}</button>
            </template>
          </div>

          <button class="nav-btn" :disabled="store.currentPage === store.totalPages" @click="goToPage(store.currentPage + 1)">›</button>
          <button class="nav-btn" :disabled="store.currentPage === store.totalPages" @click="goToPage(store.totalPages)">»</button>
        </div>
      </div>
    </div>

    <div v-else class="empty-view">
      <div class="empty-icon">📚</div>
      <p>찾으시는 도서가 현재 목록에 없습니다.</p>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, watch } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { useBooksStore } from '@/stores/books';

const store = useBooksStore();
const route = useRoute();
const router = useRouter();

const selectedCategory = computed(() => route.query.category || '');

const categories = [
  { id: 1, name: '중학교참고서' },
  { id: 2, name: '인문학' },
  { id: 3, name: '역사' },
  { id: 4, name: '과학' },
  { id: 5, name: '수험서/자격증' },
  { id: 6, name: '예술/대중문화' },
  { id: 7, name: '어린이' },
  { id: 8, name: '경제/경영' },
  { id: 9, name: '에세이' },
  { id: 10, name: '여행' },
  { id: 11, name: '사회과학' },
  { id: 12, name: '청소년' },
  { id: 13, name: '종교/역학' },
  { id: 14, name: '요리/살림' },
  { id: 15, name: '만화' },
  { id: 16, name: '유아' },
  { id: 17, name: '초등학교참고서' },
  { id: 18, name: '자기계발' },
  { id: 19, name: '대학교재/전문서적' },
  { id: 20, name: '잡지' },
  { id: 21, name: '컴퓨터/모바일' },
  { id: 22, name: '소설/시/희곡' },
  { id: 23, name: '전집/중고전집' },
];

const displayedPages = computed(() => {
  const total = store.totalPages;
  const current = store.currentPage;
  const range = 5;
  let start = Math.max(1, current - Math.floor(range / 2));
  let end = Math.min(total, start + range - 1);
  if (end - start + 1 < range) start = Math.max(1, end - range + 1);
  const pages = [];
  for (let i = start; i <= end; i++) pages.push(i);
  return pages;
});

const showEndEllipsis = computed(() => {
  const pages = displayedPages.value;
  return pages.length > 0 && pages[pages.length - 1] < store.totalPages;
});

const fetchBooksData = () => {
  store.fetchBooks({
    q: route.query.q || '',
    category: route.query.category || '',
    page: parseInt(route.query.page) || 1,
    per_page: 20
  });
};

const handleCategoryChange = (id) => router.push({ query: { ...route.query, category: id || undefined, page: 1 } });
const goToPage = (p) => router.push({ query: { ...route.query, page: p } });

watch(() => route.query, fetchBooksData, { deep: true });
onMounted(fetchBooksData);
</script>

<style scoped>
/* 전역 링크 스타일 초기화 */
.book-link {
  text-decoration: none !important;
  color: inherit;
}

.book-list-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 40px 20px;
  min-height: 80vh;
}

/* [수정] 카테고리 네비게이션 스타일: 줄바꿈(Wrap) 적용 */
.category-nav {
  margin-bottom: 40px;
}

.category-scroll-wrapper {
  display: flex;
  flex-wrap: wrap;       /* [중요] 공간이 부족하면 다음 줄로 내림 */
  justify-content: center; /* 버튼들을 가운데 정렬 (왼쪽 정렬 원하면 flex-start) */
  gap: 10px;             /* 버튼 사이의 간격 (상하좌우 모두 적용됨) */
  padding-bottom: 10px;
}

/* [제거] 기존의 스크롤바 숨김 코드는 더 이상 필요하지 않으므로 삭제 또는 무시됩니다. */
.category-scroll-wrapper::-webkit-scrollbar {
  display: none;
}

/* 칩 스타일 버튼 */
.chip-btn {
  background: #f5f5f5;
  border: 1px solid #eee;
  padding: 8px 16px;       /* 버튼 크기를 살짝 조정 */
  border-radius: 20px;
  cursor: pointer;
  color: #666;
  font-size: 14px;
  font-weight: 500;
  transition: all 0.2s ease;
  margin-bottom: 5px;      /* 줄바꿈 시 아래 줄과의 추가 여백 확보 */
}

.chip-btn:hover {
  background: #ebebeb;
  color: #333;
}

.chip-btn.active {
  background: #242424;
  color: #fff;
  border-color: #242424;
  font-weight: 700;
  box-shadow: 0 4px 10px rgba(0,0,0,0.15);
}

/* 도서 그리드 및 카드 */
.book-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
  gap: 40px 25px;
}

.book-item {
  opacity: 0;
  transform: translateY(20px);
  animation: fadeInUp 0.5s ease forwards;
}

@keyframes fadeInUp {
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.cover-wrapper {
  border-radius: 10px;
  overflow: hidden;
  box-shadow: 10px 15px 25px rgba(0,0,0,0.1);
  position: relative;
  padding-bottom: 145%;
  background: #f8f8f8;
  transition: transform 0.4s cubic-bezier(0.165, 0.84, 0.44, 1);
}

.book-cover {
  position: absolute;
  width: 100%;
  height: 100%;
  object-fit: cover;
  transition: transform 0.4s ease;
}

.cover-overlay {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  background: rgba(0,0,0,0.4);
  display: flex;
  align-items: center;
  justify-content: center;
  opacity: 0;
  transition: opacity 0.3s ease;
}
.cover-overlay span {
  color: #fff;
  border: 1px solid #fff;
  padding: 8px 15px;
  border-radius: 20px;
  font-size: 13px;
  font-weight: 700;
}

.book-item:hover .cover-wrapper {
  transform: translateY(-10px) scale(1.02);
  box-shadow: 15px 25px 35px rgba(0,0,0,0.15);
}
.book-item:hover .cover-overlay {
  opacity: 1;
}

/* 도서 텍스트 가독성 */
.book-details {
  padding: 15px 2px;
}
.book-title {
  font-size: 15px;
  font-weight: 800;
  margin: 0 0 6px;
  color: #242424;
  line-height: 1.4;
  height: 2.8em;
  overflow: hidden;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  word-break: keep-all;
}
.book-author {
  font-size: 13px;
  color: #888;
  font-weight: 500;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 페이지네이션 */
.pagination-wrapper {
  margin-top: 80px;
  display: flex;
  justify-content: center;
}
.pagination {
  display: flex;
  align-items: center;
  gap: 8px;
}
.nav-btn {
  background: #fff;
  border: 1.5px solid #eee;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  cursor: pointer;
  color: #bbb;
  font-size: 20px;
  transition: all 0.2s;
}
.nav-btn:hover:not(:disabled) {
  border-color: #242424;
  color: #242424;
}
.num-group {
  display: flex;
  align-items: center;
  gap: 8px;
  margin: 0 10px;
}
.num-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: none;
  border-radius: 50%;
  cursor: pointer;
  color: #777;
  font-size: 15px;
  font-weight: 600;
  transition: all 0.2s;
}
.num-btn.active {
  background: #ffeb00;
  color: #242424;
  font-weight: 800;
}
.num-btn:hover:not(.active) {
  background: #f0f0f0;
}

/* 로딩 & 비어있음 */
.loading-view, .empty-view {
  text-align: center;
  padding: 100px 0;
  color: #999;
}
.spinner {
  border: 4px solid #f3f3f3;
  border-top: 4px solid #ffeb00;
  border-radius: 50%;
  width: 40px;
  height: 40px;
  animation: spin 1s linear infinite;
  margin: 0 auto 20px;
}
@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }

.empty-icon {
  font-size: 50px;
  margin-bottom: 20px;
}
</style>