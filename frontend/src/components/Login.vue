<!-- src/components/Login.vue -->
<template>
  <div>
    <h2>Login</h2>
    <form @submit.prevent="handleLogin">
      <input v-model="username" type="text" placeholder="Username" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <button type="submit">Login</button>
    </form>
    <p>Don't have an account? <router-link to="/register">Sign Up</router-link></p>
  </div>
</template>

<script>
import { useAccountsStore } from '../store/accounts';

export default {
  data() {
    return {
      username: '',
      password: '',
    };
  },
  methods: {
    async handleLogin() {
      const accountsStore = useAccountsStore();
      const credentials = { username: this.username, password: this.password };
      try {
        const response = await accountsStore.login(credentials);
        console.log('Login successful:', response);
        this.$router.push({ name: 'home' }); // 로그인 후 홈 화면으로 리다이렉트
      } catch (error) {
        console.error('Login failed:', error);
        alert(error.message || 'Login failed');
      }
    },
  },
};
</script>
