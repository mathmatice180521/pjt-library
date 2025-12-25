<!-- src/components/Home.vue -->
<template>
  <div>
    <h2>Welcome, {{ user.username }}!</h2>
    <button @click="logout">Logout</button>
  </div>
</template>

<script>
import { useUserStore } from '../store/userStore';

export default {
  computed: {
    user() {
      const userStore = useUserStore();
      return userStore.user;
    },
  },
  methods: {
    async logout() {
      const userStore = useUserStore();
      try {
        await userStore.logout();
        console.log('로그아웃 완료');
        this.$router.push({ name: 'login' });  // 로그아웃 후 로그인 화면으로 리다이렉트
      } catch (error) {
        console.error('로그아웃 실패:', error);
      }
    },
  },
};
</script>
