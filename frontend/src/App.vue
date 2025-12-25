<template>
  <div id="app">
    <router-view v-slot="{ Component }">
      <transition name="page-fade" mode="out-in">
        <component :is="Component" />
      </transition>
    </router-view>
  </div>
</template>

<script setup>
// App.vue
import { onMounted } from 'vue';
import { useAccountsStore } from '@/stores/accounts';

const accountsStore = useAccountsStore();

onMounted(async () => {
  // 앱이 켜지자마자 로그인 상태인지 확인
  await accountsStore.initializeAuth();
});
</script>

<style>
/* 전역 스타일 */
body { 
  margin: 0; 
  font-family: 'Pretendard', sans-serif; 
  overflow-x: hidden; 
}

/* [추가] 페이지 전환 애니메이션 효과 (Fade & Slide) */
.page-fade-enter-active,
.page-fade-leave-active {
  transition: opacity 0.3s ease, transform 0.3s ease;
}

.page-fade-enter-from {
  opacity: 0;
  transform: translateY(10px); /* 아래에서 위로 살짝 올라오며 등장 */
}

.page-fade-leave-to {
  opacity: 0;
  transform: translateY(-10px); /* 위로 살짝 올라가며 사라짐 */
}
</style>