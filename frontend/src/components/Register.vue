
<template>
  <div>
    <h2>Sign Up</h2>
    <form @submit.prevent="handleregister">
      <input v-model="username" type="text" placeholder="Username" required />
      <input v-model="password" type="password" placeholder="Password" required />
      <input v-model="email" type="email" placeholder="Email" required />
      <button type="submit">Sign Up</button>
    </form>
    <p>Already have an account? <router-link to="/login">Login</router-link></p>
  </div>
</template>

<script>
import { useAccountsStore } from '../store/accounts';

export default {
  data() {
    return {
      username: '',
      password: '',
      email: '',
    };
  },
  methods: {
    async handleregister() {
      const accountsStore = useAccountsStore();
      const accountsData = { username: this.username, password: this.password, email: this.email };
      try {
        const response = await accountsStore.register(accountsData);
        console.log('Sign Up successful:', response);
        this.$router.push({ name: 'login' }); // 회원가입 후 로그인 화면으로 리다이렉트
      } catch (error) {
        console.error('Sign Up failed:', error);
        alert(error.message || 'Sign Up failed');
      }
    },
  },
};
</script>
