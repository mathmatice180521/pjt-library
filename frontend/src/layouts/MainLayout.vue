<template>
  <div class="main-layout">
    <Transition name="fade">
      <div v-if="isDeleteSuccess" class="event-overlay">
        <div class="event-content">
          <div class="event-icon">🌿</div>
          <h2>그동안 웅성웅성과 함께해주셔서 감사합니다.</h2>
          <p>사용자님의 소중한 기록을 안전하게 정리했습니다.</p>
        </div>
      </div>
    </Transition>

    <Transition name="fade">
      <div v-if="isLogoutSuccess" class="event-overlay">
        <div class="event-content">
          <div class="event-icon">👋</div>
          <h2>로그아웃 되었습니다.</h2>
          <p>오늘도 웅성웅성과 함께해 주셔서 감사합니다.<br/>다음에 또 만나요!</p>
        </div>
      </div>
    </Transition>

    <nav class="millie-nav" v-if="!isDeleteSuccess && !isLogoutSuccess">
      <div class="nav-container">
        <div class="nav-left">
          <router-link to="/" class="logo">
            <span class="logo-text">웅성웅성</span>
          </router-link>
          <div class="search-box">
            <input v-model="searchQuery" type="text" placeholder="어떤 책을 찾으시나요?" @keyup.enter="goToBookList" />
            <button @click="goToBookList" class="search-icon">🔍</button>
          </div>
        </div>

        <ul class="nav-right">
          <li><router-link to="/" class="nav-link">홈</router-link></li>
          <template v-if="!isAuthenticated">
            <li><router-link to="/login" class="nav-link">로그인</router-link></li>
            <li><router-link to="/register" class="nav-link register-btn">회원가입</router-link></li>
          </template>
          <template v-else>
            <li><router-link to="/mypage" class="nav-link">마이 페이지</router-link></li>
            <li><a @click="requestLogout" class="nav-link logout-link">로그아웃</a></li>
            <li>
              <button @click="confirmDelete" class="delete-auth-btn">서비스 탈퇴</button>
            </li>
          </template>
        </ul>
      </div>
    </nav>

    <main class="content-view" v-if="!isDeleteSuccess && !isLogoutSuccess">
      <router-view></router-view>
    </main>

    <AiChatModal :isVisible="aiStore.isModalOpen" @close="aiStore.closeModal" />

    <Transition name="modal-fade">
      <div v-if="showLogoutModal" class="modal-overlay" @click.self="showLogoutModal = false">
        <div class="modal-window">
          <div class="modal-icon">🚪</div>
          <h2 class="modal-title">로그아웃 하시겠습니까?</h2>
          <p class="modal-desc">언제든지 다시 돌아오실 수 있어요.</p>
          <div class="modal-action-group">
            <button @click="showLogoutModal = false" class="btn-cancel-round">취소</button>
            <button @click="handleLogout" class="btn-confirm-delete" style="background: #ffeb00; color: #242424;">로그아웃</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="modal-fade">
      <div v-if="showDeleteStep1" class="modal-overlay" @click.self="showDeleteStep1 = false">
        <div class="modal-window">
          <div class="modal-icon">😢</div>
          <h2 class="modal-title">웅성웅성을 떠나시나요?</h2>
          <p class="modal-desc">탈퇴하시면 서재에 담긴 책들과<br/>리뷰들이 모두 삭제됩니다.</p>
          <div class="modal-action-vertical">
            <button @click="showDeleteStep1 = false" class="btn-keep">계속 이용하기</button>
            <button @click="showDeleteStep2 = true; showDeleteStep1 = false" class="btn-leave-link">그래도 탈퇴할래요</button>
          </div>
        </div>
      </div>
    </Transition>

    <Transition name="modal-fade">
      <div v-if="showDeleteStep2" class="modal-overlay" @click.self="showDeleteStep2 = false">
        <div class="modal-window">
          <h2 class="modal-title">본인 확인</h2>
          <p class="modal-desc">비밀번호를 입력해주세요.</p>
          <div class="input-container">
            <input v-model="deletePassword" type="password" class="modal-password-input" @keyup.enter="handleDeleteAccount" />
          </div>
          <div class="modal-action-group">
            <button @click="showDeleteStep2 = false" class="btn-cancel-round">취소</button>
            <button @click="handleDeleteAccount" class="btn-confirm-delete">탈퇴 완료</button>
          </div>
        </div>
      </div>
    </Transition>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue';
import { useRouter, useRoute } from 'vue-router';
import { useAccountsStore } from '@/stores/accounts';
import { useAiStore } from '@/stores/airecommend'; // [추가]
import AiChatModal from '@/components/AiChatModal.vue'; // [추가]

const store = useAccountsStore();
const aiStore = useAiStore(); // [추가]
const router = useRouter();
const route = useRoute();

const searchQuery = ref(route.query.q || '');
const isAuthenticated = computed(() => store.isAuthenticated);

// 회원탈퇴 상태
const showDeleteStep1 = ref(false);
const showDeleteStep2 = ref(false);
const deletePassword = ref('');
const isDeleteSuccess = ref(false);

// 로그아웃 상태
const showLogoutModal = ref(false);
const isLogoutSuccess = ref(false);

// [추가] AI 모달 열기 (로그인 체크 포함)
const openAiChat = () => {
  if (!store.isAuthenticated) {
    if(confirm('로그인이 필요한 서비스입니다.\n로그인 하시겠습니까?')) router.push('/login');
    return;
  }
  aiStore.openModal();
};

const goToBookList = () => router.push({ path: '/booklist', query: { q: searchQuery.value || undefined } });

const requestLogout = () => { showLogoutModal.value = true; };

const handleLogout = () => {
  showLogoutModal.value = false;
  isLogoutSuccess.value = true;
  setTimeout(() => {
    store.logout(); 
    router.push('/');
    isLogoutSuccess.value = false;
  }, 2000);
};

const confirmDelete = () => { showDeleteStep1.value = true; };

const handleDeleteAccount = async () => {
  if (!deletePassword.value) return;
  try {
    await store.deleteAccount(deletePassword.value);
    showDeleteStep2.value = false;
    isDeleteSuccess.value = true;
    setTimeout(() => {
      store.logout();
      router.push('/');
      isDeleteSuccess.value = false;
    }, 3000);
  } catch (err) {
    alert('비밀번호가 일치하지 않습니다.');
  }
};
</script>

<style scoped>
.main-layout { min-height: 100vh; background-color: #fff; }
.millie-nav { position: sticky; top: 0; z-index: 1000; height: 64px; background: rgba(255, 255, 255, 0.98); backdrop-filter: blur(10px); border-bottom: 1px solid #eee; display: flex; align-items: center; }
.nav-container { width: 100%; max-width: 1200px; margin: 0 auto; padding: 0 20px; display: flex; justify-content: space-between; align-items: center; gap: 40px; }
.nav-left { display: flex; align-items: center; gap: 40px; flex: 1; }
.logo-text { font-size: 24px; font-weight: 900; color: #242424; text-decoration: none; }
.search-box { display: flex; align-items: center; background: #f3f3f3; border-radius: 25px; padding: 0 22px; height: 44px; flex: 1; max-width: 550px; }
.search-box input { border: none; background: transparent; outline: none; flex: 1; }
.search-icon { border: none; background: transparent; cursor: pointer; }
.nav-right { display: flex; align-items: center; list-style: none; gap: 25px; margin: 0; padding: 0; }
.nav-link { text-decoration: none; color: #444; font-size: 15px; font-weight: 700; cursor: pointer; }
.register-btn { background: #ffeb00; padding: 8px 18px; border-radius: 20px; color: #242424 !important; }
.delete-auth-btn { background: #fff; border: 1.2px solid #eee; padding: 6px 14px; border-radius: 15px; color: #999; font-size: 13px; font-weight: 600; cursor: pointer; }

/* [추가] AI 버튼 스타일 */
.ai-nav-btn { color: #6a1b9a !important; font-weight: 800; }

/* 애니메이션 오버레이 */
.event-overlay { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: #fff; z-index: 9999; display: flex; justify-content: center; align-items: center; }
.event-content { text-align: center; animation: fadeInUp 0.8s ease; }
.event-icon { font-size: 60px; margin-bottom: 20px; }
.event-content h2 { font-size: 24px; font-weight: 800; color: #242424; margin-bottom: 10px; }
.event-content p { color: #888; font-size: 16px; line-height: 1.5; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(20px); }
  to { opacity: 1; transform: translateY(0); }
}

/* Transitions */
.fade-enter-active, .fade-leave-active { transition: opacity 0.5s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
.modal-fade-enter-active, .modal-fade-leave-active { transition: opacity 0.3s; }
.modal-fade-enter-from, .modal-fade-leave-to { opacity: 0; }

/* 모달 스타일 */
.modal-overlay { position: fixed; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0, 0, 0, 0.6); backdrop-filter: blur(4px); display: flex; justify-content: center; align-items: center; z-index: 2000; }
.modal-window { background: #fff; width: 360px; padding: 40px 30px; border-radius: 24px; text-align: center; box-shadow: 0 10px 40px rgba(0,0,0,0.2); }
.modal-icon { font-size: 44px; margin-bottom: 20px; }
.modal-title { font-size: 22px; font-weight: 800; margin-bottom: 12px; color: #242424; }
.modal-desc { font-size: 15px; color: #777; line-height: 1.6; margin-bottom: 30px; }
.btn-keep { background: #ffeb00; color: #242424; border: none; height: 54px; width: 100%; border-radius: 14px; font-weight: 800; cursor: pointer; }
.btn-leave-link { background: none; border: none; color: #bbb; text-decoration: underline; cursor: pointer; padding: 10px; }
.modal-password-input { width: 100%; padding: 15px; border: 1.5px solid #eee; border-radius: 12px; margin-bottom: 20px; box-sizing: border-box; font-size: 16px; }
.btn-cancel-round { flex: 1; height: 50px; background: #f5f5f5; border: none; border-radius: 12px; color: #888; cursor: pointer; font-weight: 700; transition: background 0.2s; }
.btn-cancel-round:hover { background: #eee; }
.btn-confirm-delete { flex: 1; height: 50px; background: #242424; border: none; border-radius: 12px; color: #fff; cursor: pointer; font-weight: 700; transition: background 0.2s; }
.btn-confirm-delete:hover { opacity: 0.9; }
.modal-action-group { display: flex; gap: 10px; }
.modal-action-vertical { display: flex; flex-direction: column; gap: 10px; }
</style>