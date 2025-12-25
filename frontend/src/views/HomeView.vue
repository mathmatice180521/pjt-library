<template>
  <div class="home-container">
    <section class="hero-section" :style="{ backgroundImage: `url(${randomBgImage})` }">
      <div class="hero-overlay"></div>
      <div class="hero-content" :class="{ 'visible': isQuoteVisible }">
        <span class="today-tag">오늘의 문장</span>
        <h1 class="quote-text">“{{ todayQuote?.text || '...' }}”</h1>
        <p class="quote-author">— {{ todayQuote?.author || 'Unknown' }}</p>
      </div>
    </section>

    <section class="quick-menu-container">
      <div class="quick-menu-inner">
        <div class="menu-item" @click="handleTodayRecommendation">
          <div class="icon-circle"><span>📚</span></div>
          <span class="menu-label">오늘의 추천</span>
        </div>
        <div class="menu-item" @click="handleProtectedNav('bookmarks')">
          <div class="icon-circle"><span>❤️</span></div>
          <span class="menu-label">내 서재</span>
        </div>
        <div class="menu-item" @click="handleProtectedNav('comments')">
          <div class="icon-circle"><span>✍️</span></div>
          <span class="menu-label">리뷰 관리</span>
        </div>
        
        <div class="menu-item" @click="handleAiClick">
          <div class="icon-circle"><span>🤖</span></div>
          <span class="menu-label">AI 웅성이</span>
        </div>
      </div>
    </section>

    <section class="recommend-section">
      <div class="section-header">
        <div class="header-titles">
          <h2>이런 책은 어때요?</h2>
          <p>웅성웅성 회원들이 추천하는 베스트 도서</p>
        </div>
        <router-link to="/booklist" class="view-all">전체보기</router-link>
      </div>

      <div class="slider-wrapper">
        <button class="slide-btn prev" @click="moveSlide(-1)" v-show="currentIndex > 0">
          <span class="arrow"></span>
        </button>

        <div class="slider-container">
          <div class="book-track" :style="{ transform: `translateX(-${currentIndex * 20}%)` }">
            <div v-for="book in recommendedBooks" :key="book.id" class="book-card-item">
              <router-link :to="`/books/${book.id}`" class="book-link">
                <div class="cover-container">
                  <img :src="book.cover_url || 'https://placehold.co/150x220'" class="book-img" />
                  <div class="hover-overlay">상세보기</div>
                </div>
                <div class="book-meta">
                  <strong class="title">{{ book.title }}</strong>
                  <span class="author">{{ book.author }}</span>
                </div>
              </router-link>
            </div>
          </div>
        </div>

        <button class="slide-btn next" @click="moveSlide(1)" v-show="currentIndex < maxIndex">
          <span class="arrow right"></span>
        </button>
      </div>
    </section>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, watch } from 'vue';
import { useBooksStore } from '@/stores/books';
import { useAccountsStore } from '@/stores/accounts';
import { useAiStore } from '@/stores/airecommend'; // [추가]
import { useRouter } from 'vue-router';
import { allQuotes } from '@/assets/quotes';

const store = useBooksStore();
const accountsStore = useAccountsStore();
const aiStore = useAiStore(); // [추가]
const router = useRouter();

const recommendedBooks = ref([]);
const currentIndex = ref(0);
const itemsPerView = 5;
const todayQuote = ref(null);
const isQuoteVisible = ref(false);

const maxIndex = computed(() => Math.max(0, (recommendedBooks.value?.length || 0) - itemsPerView));

// [추가] AI 버튼 클릭 핸들러
const handleAiClick = () => {
  if (!accountsStore.isAuthenticated) {
    if(confirm('로그인이 필요한 서비스입니다.\n로그인 페이지로 이동하시겠습니까?')) {
      router.push('/login');
    }
    return;
  }
  aiStore.openModal(); // 전역 모달 열기
};

// ... (기존 슬라이더, 쿼트 로직 유지) ...
const moveSlide = (step) => {
  const target = currentIndex.value + step;
  if (target >= 0 && target <= maxIndex.value) currentIndex.value = target;
};

const shuffleArray = (array) => {
  const shuffled = [...array];
  for (let i = shuffled.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [shuffled[i], shuffled[j]] = [shuffled[j], shuffled[i]];
  }
  return shuffled;
};

watch(() => store.books, (newBooks) => {
    if (newBooks && newBooks.length > 0) recommendedBooks.value = shuffleArray(newBooks);
}, { immediate: true });

const bgImages = [
  'https://images.unsplash.com/photo-1512820790803-83ca734da794?q=80&w=1600',
  'https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?q=80&w=1600',
  'https://images.unsplash.com/photo-1456513080510-7bf3a84b82f8?q=80&w=1600',
  'https://images.unsplash.com/photo-1481627834876-b7833e8f5570?q=80&w=1600'
];
const randomBgImage = ref(bgImages[Math.floor(Math.random() * bgImages.length)]);

const handleTodayRecommendation = () => {
  if (store.books?.length > 0) {
    const randomIndex = Math.floor(Math.random() * store.books.length);
    router.push(`/books/${store.books[randomIndex].id}`);
  } else {
    alert('도서 목록을 불러오는 중입니다.');
  }
};

const handleProtectedNav = (tab) => {
  if (!accountsStore.isAuthenticated) return router.push('/login');
  router.push({ name: 'mypage', query: { tab } });
};

onMounted(() => {
  store.fetchBooks();
  if (allQuotes && allQuotes.length > 0) todayQuote.value = allQuotes[Math.floor(Math.random() * allQuotes.length)];
  setTimeout(() => { isQuoteVisible.value = true; }, 100);
});
</script>

<style scoped>
/* (기존 스타일 전체 유지) */
.home-container { padding-bottom: 60px; }
.hero-section { position: relative; height: 480px; background-size: cover; background-position: center; display: flex; align-items: center; justify-content: center; }
.hero-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(135deg, rgba(0,0,0,0.6), rgba(0,0,0,0.2)); }
.hero-content { position: relative; z-index: 5; text-align: center; color: white; padding: 0 20px; }
.hero-content .today-tag, .hero-content .quote-text, .hero-content .quote-author { opacity: 0; transform: translateY(20px); transition: opacity 0.8s ease-out, transform 0.8s ease-out; }
.hero-content.visible .today-tag, .hero-content.visible .quote-text, .hero-content.visible .quote-author { opacity: 1; transform: translateY(0); }
.today-tag { font-size: 14px; background: #ffeb00; color: #242424; padding: 6px 18px; border-radius: 30px; font-weight: 900; margin-bottom: 25px; display: inline-block; }
.quote-text { font-size: 34px; font-weight: 800; line-height: 1.4; margin-bottom: 15px; text-shadow: 0 4px 12px rgba(0,0,0,0.4); }
.quote-author { font-size: 18px; font-weight: 300; opacity: 0.9; }

/* 퀵 메뉴 */
.quick-menu-container { background: white; padding: 40px 0; border-bottom: 10px solid #f8f8f8; }
.quick-menu-inner { display: flex; justify-content: center; gap: 60px; max-width: 1200px; margin: 0 auto; }
.menu-item { display: flex; flex-direction: column; align-items: center; cursor: pointer; transition: 0.3s; }
.icon-circle { width: 68px; height: 68px; background: #fff; border: 1.5px solid #eee; border-radius: 22px; display: flex; align-items: center; justify-content: center; font-size: 28px; box-shadow: 0 8px 15px rgba(0,0,0,0.05); margin-bottom: 12px; transition: 0.3s; }
.menu-label { font-size: 14px; font-weight: 700; color: #444; }
.menu-item:hover .icon-circle { transform: translateY(-8px); border-color: #ffeb00; box-shadow: 0 12px 25px rgba(255, 235, 0, 0.3); }

/* 추천 섹션 */
.recommend-section { max-width: 1200px; margin: 0 auto; padding: 60px 20px; }
.section-header { display: flex; justify-content: space-between; align-items: flex-end; margin-bottom: 40px; }
.header-titles h2 { font-size: 24px; font-weight: 900; margin-bottom: 6px; }
.header-titles p { color: #888; font-size: 14px; }
.view-all { font-weight: 700; color: #888; text-decoration: none; border-bottom: 2px solid #eee; padding-bottom: 2px; font-size: 14px; }
.slider-wrapper { position: relative; }
.slider-container { overflow: hidden; width: 100%; }
.book-track { display: flex; transition: transform 0.6s cubic-bezier(0.23, 1, 0.32, 1); }
.book-card-item { flex: 0 0 20%; padding: 0 10px; box-sizing: border-box; }
.cover-container { position: relative; aspect-ratio: 1/1.45; border-radius: 8px; overflow: hidden; box-shadow: 10px 15px 30px rgba(0,0,0,0.12); transition: 0.4s ease; }
.book-img { width: 100%; height: 100%; object-fit: cover; }
.hover-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.6); color: #fff; display: flex; align-items: center; justify-content: center; opacity: 0; transition: 0.3s; font-weight: 700; }
.book-card-item:hover .cover-container { transform: translateY(-10px); }
.book-card-item:hover .hover-overlay { opacity: 1; }
.book-meta { padding: 15px 0; }
.book-meta .title { display: block; font-size: 15px; font-weight: 800; color: #242424; margin-bottom: 4px; line-height: 1.4; height: 2.8em; overflow: hidden; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; }
.book-meta .author { font-size: 13px; color: #999; }
.slide-btn { position: absolute; top: 40%; transform: translateY(-50%); width: 44px; height: 44px; background: #fff; border: none; border-radius: 50%; box-shadow: 0 5px 15px rgba(0,0,0,0.15); cursor: pointer; z-index: 100; display: flex; align-items: center; justify-content: center; }
.slide-btn.prev { left: -22px; }
.slide-btn.next { right: -22px; }
.arrow { width: 10px; height: 10px; border-left: 2px solid #333; border-bottom: 2px solid #333; transform: rotate(45deg); margin-left: 4px; }
.arrow.right { transform: rotate(-135deg); margin-left: -4px; }
@media (max-width: 900px) { .book-card-item { flex: 0 0 33.33%; } }
</style>