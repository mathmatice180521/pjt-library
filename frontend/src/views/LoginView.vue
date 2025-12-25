<template>
  <div class="auth-page">
    <router-link to="/" class="home-btn">🏠 홈으로</router-link>
    <div class="auth-container">
      <div class="visual-side">
        <div class="visual-content" v-if="randomProverb">
          <span class="proverb-tag">오늘의 영감</span>
          <h2>"{{ randomProverb }}"</h2>
        </div>
        <div class="image-overlay"></div>
        <img src="https://images.unsplash.com/photo-1512820790803-83ca734da794?q=80&w=1000" alt="Login Visual" />
      </div>

      <div class="form-side">
        <div class="form-wrapper">
          <h1 class="title">로그인</h1>
          <form @submit.prevent="handleLogin">
            <div class="input-group">
              <label>아이디</label>
              <input v-model="username" type="text" placeholder="아이디 입력" required />
            </div>
            <div class="input-group">
              <label>비밀번호</label>
              <input v-model="password" type="password" placeholder="비밀번호 입력" required />
            </div>
            <button type="submit" class="auth-btn" :disabled="isLoading">로그인</button>
          </form>
          <div class="footer-links">
            아직 회원이 아니신가요? <router-link to="/register">회원가입</router-link>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'; // onMounted 추가
import { useAccountsStore } from '@/stores/accounts';
import { useRouter } from 'vue-router';
import { allProverbs } from '@/assets/proverbs'; // 이름 확인!

const router = useRouter();
const store = useAccountsStore();

const username = ref('');
const password = ref('');
const isLoading = ref(false);

// [수정] 랜덤 명언을 저장할 변수
const randomProverb = ref(null);

// 컴포넌트가 로드될 때 딱 한 번만 실행
onMounted(() => {
  if (allProverbs && allProverbs.length > 0) {
    const idx = Math.floor(Math.random() * allProverbs.length);
    // 현재 데이터가 문자열이므로 randomProverb.value에 문자열이 저장됩니다.
    randomProverb.value = allProverbs[idx];
  }
});

const handleLogin = async () => {
  if (isLoading.value) return;
  isLoading.value = true;
  try {
    await store.login({ 
      username: username.value, 
      password: password.value 
    });
    router.replace('/');
  } catch (err) {
    alert('로그인에 실패했습니다.');
  } finally {
    isLoading.value = false;
  }
};
</script>

<style scoped>
.auth-page { width: 100vw; height: 100vh; position: relative; overflow: hidden; }
.home-btn { position: absolute; top: 20px; right: 20px; z-index: 100; text-decoration: none; color: #242424; font-weight: bold; padding: 10px 20px; background: #fff; border-radius: 30px; border: 1px solid #ddd; }
.auth-container { display: flex; height: 100%; }

.visual-side { flex: 3; position: relative; background: #000; }
.visual-side img { width: 100%; height: 100%; object-fit: cover; opacity: 0.7; }
.image-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: linear-gradient(to top, rgba(0,0,0,0.5), transparent); }
.visual-content { position: absolute; bottom: 10%; left: 10%; z-index: 5; color: #fff; text-align: left; }
.visual-content h2 { font-size: 3rem; font-weight: 800; line-height: 1.3; }

.form-side { flex: 2; display: flex; align-items: center; justify-content: center; background: #fff; padding: 40px; }
.form-wrapper { width: 100%; max-width: 400px; }
.title { font-size: 2.5rem; font-weight: 800; margin-bottom: 40px; }
.input-group { margin-bottom: 25px; text-align: left; }
.input-group label { display: block; font-weight: 700; margin-bottom: 10px; color: #666; }
.input-group input { width: 100%; padding: 15px; border: 1px solid #eee; border-radius: 10px; background: #f9f9f9; box-sizing: border-box; }
.auth-btn { width: 100%; padding: 18px; background: #ffeb00; border: none; border-radius: 10px; font-size: 1.1rem; font-weight: 800; cursor: pointer; margin-top: 10px; }
.footer-links { margin-top: 30px; color: #888; text-align: center; }
.footer-links a { color: #242424; font-weight: bold; margin-left: 10px; text-decoration: none; border-bottom: 2px solid #ffeb00; }
</style>