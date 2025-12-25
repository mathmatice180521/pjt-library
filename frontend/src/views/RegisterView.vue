<template>
  <div class="auth-page">
    <Transition name="welcome-fade">
      <div v-if="isRegisterSuccess" class="welcome-overlay">
        <div class="welcome-box">
          <div class="confetti">🎉</div>
          <h1>환영합니다!</h1>
          <p>웅성웅성의 새로운 회원이 되셨습니다.</p>
        </div>
      </div>
    </Transition>

    <router-link v-if="!isRegisterSuccess" to="/" class="home-btn">🏠 홈으로</router-link>
    <div v-if="!isRegisterSuccess" class="auth-container">
      <div class="visual-side">
        <div class="visual-content" v-if="randomProverb">
          <span class="proverb-tag">오늘의 영감</span>
          <h2>"{{ randomProverb }}"</h2>
        </div>
        <div class="image-overlay"></div>
        <img src="https://images.unsplash.com/photo-1507842217343-583bb7270b66?q=80&w=1000" alt="Register Visual" />
      </div>

      <div class="form-side">
        <div class="form-wrapper">
          <h1 class="title">회원가입</h1>
          <form @submit.prevent="handleRegister">
            <div class="input-group">
              <label>아이디</label>
              <input v-model="form.username" type="text" placeholder="아이디" required />
            </div>
            <div class="input-group">
              <label>이메일</label>
              <input v-model="form.email" type="email" placeholder="example@mail.com" required />
            </div>
            <div class="input-group">
              <label>비밀번호</label>
              <input v-model="form.password" type="password" placeholder="비밀번호" required />
            </div>
            <div class="input-group">
              <label>비밀번호 확인</label>
              <input v-model="passwordConfirm" type="password" placeholder="비밀번호 재입력" required />
              <p v-if="passwordConfirm && !isMatch" class="error-msg">비밀번호가 일치하지 않습니다.</p>
            </div>
            <button type="submit" class="auth-btn" :disabled="!isMatch || isLoading">
              {{ isLoading ? '가입 중...' : '가입하기' }}
            </button>
          </form>
          <div class="footer-links">
            이미 계정이 있으신가요? <router-link to="/login">로그인</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { reactive, ref, computed, onMounted } from 'vue';
import { useRouter } from 'vue-router';
import { useAccountsStore } from '@/stores/accounts';
import { allProverbs } from '@/assets/proverbs';

const router = useRouter();
const store = useAccountsStore();

const form = reactive({ username: '', email: '', password: '' });
const passwordConfirm = ref('');
const isLoading = ref(false);
const randomProverb = ref("");

// [추가] 가입 성공 상태값
const isRegisterSuccess = ref(false);

const isMatch = computed(() => form.password.length > 0 && form.password === passwordConfirm.value);

onMounted(() => {
  if (allProverbs && allProverbs.length > 0) {
    const idx = Math.floor(Math.random() * allProverbs.length);
    randomProverb.value = allProverbs[idx];
  }
});

const handleRegister = async () => {
  if (!isMatch.value) return;
  isLoading.value = true;
  try {
    await store.register({ ...form });
    // [수정] 바로 이동하지 않고 성공 모션 활성화
    isRegisterSuccess.value = true;
    
    // [추가] 2.5초간 모션을 보여준 뒤 홈으로 이동
    setTimeout(() => {
      router.replace('/');
    }, 2500);
  } catch (err) {
    alert('회원가입 실패: 이미 가입된 아이디거나 형식이 잘못되었습니다.');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
/* 기존 스타일 생략 (이전과 동일) */
.auth-page { width: 100vw; height: 100vh; position: relative; overflow: hidden; }
.home-btn { position: absolute; top: 20px; right: 20px; z-index: 100; text-decoration: none; color: #242424; font-weight: bold; padding: 10px 20px; background: #fff; border-radius: 30px; border: 1px solid #ddd; }
.auth-container { display: flex; height: 100%; }
.visual-side { flex: 3; position: relative; background: #000; }
.visual-side img { width: 100%; height: 100%; object-fit: cover; opacity: 0.6; }
.image-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to top, rgba(0,0,0,0.5), transparent); }
.visual-content { position: absolute; bottom: 12%; left: 10%; z-index: 5; color: #fff; max-width: 80%; }
.proverb-tag { display: inline-block; background: #ffeb00; color: #000; padding: 4px 12px; border-radius: 4px; font-weight: 800; font-size: 12px; margin-bottom: 15px; }
.visual-content h2 { font-size: 2.2rem; font-weight: 800; line-height: 1.4; word-break: keep-all; }
.form-side { flex: 2; display: flex; align-items: center; justify-content: center; background: #fff; padding: 40px; }
.form-wrapper { width: 100%; max-width: 400px; }
.title { font-size: 2.5rem; font-weight: 800; margin-bottom: 40px; }
.input-group { margin-bottom: 25px; text-align: left; }
.input-group label { display: block; font-weight: 700; margin-bottom: 10px; color: #666; }
.input-group input { width: 100%; padding: 15px; border: 1px solid #eee; border-radius: 10px; background: #f9f9f9; box-sizing: border-box; }
.auth-btn { width: 100%; padding: 18px; background: #ffeb00; border: none; border-radius: 10px; font-size: 1.1rem; font-weight: 800; cursor: pointer; margin-top: 10px; }
.auth-btn:disabled { background: #eee; cursor: not-allowed; }
.error-msg { color: #ff4d4f; font-size: 0.8rem; margin-top: 5px; }
.footer-links { margin-top: 30px; color: #888; text-align: center; }
.footer-links a { color: #242424; font-weight: bold; margin-left: 10px; text-decoration: none; border-bottom: 2px solid #ffeb00; }

/* [추가] 가입 성공 웰컴 오버레이 스타일 */
.welcome-overlay {
  position: fixed; top: 0; left: 0; width: 100%; height: 100%;
  background: #ffffff; z-index: 1000; display: flex; justify-content: center; align-items: center;
}
.welcome-box { text-align: center; }
.confetti { font-size: 80px; animation: bounce 1s infinite; }
.welcome-box h1 { font-size: 40px; font-weight: 900; color: #242424; margin: 20px 0 10px; }
.welcome-box p { font-size: 18px; color: #242424; font-weight: 600; }

@keyframes bounce {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-20px); }
}
.welcome-fade-enter-active, .welcome-fade-leave-active { transition: all 0.5s ease; }
.welcome-fade-enter-from { opacity: 0; transform: scale(1.1); }
</style>