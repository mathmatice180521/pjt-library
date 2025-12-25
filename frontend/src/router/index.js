import { createRouter, createWebHistory } from 'vue-router';
import { useAccountsStore } from '@/stores/accounts';

// 레이아웃 및 뷰 Import
import MainLayout from '@/layouts/MainLayout.vue'; // 새로 만든 레이아웃
import HomeView from '@/views/HomeView.vue';
import BookListView from '@/views/BookListView.vue';
import BookDetailView from '@/views/BookDetailView.vue';
import MyPageView from '@/views/MyPageView.vue';
import CommentCreateView from '@/views/CommentCreateView.vue';
import CommentUpdateView from '@/views/CommentUpdateView.vue';
import LoginView from '@/views/LoginView.vue';
import RegisterView from '@/views/RegisterView.vue';

const routes = [
  // [그룹 1] 네비바와 배너가 포함된 메인 레이아웃 적용 페이지들
  {
    path: '/',
    component: MainLayout,
    children: [
      {
        path: '',
        name: 'home',
        component: HomeView,
        meta: { requiresAuth: false },
      },
      {
        path: 'booklist',
        name: 'booklist',
        component: BookListView,
        meta: { requiresAuth: false },
      },
      {
        path: 'books/:id',
        name: 'BookDetail',
        component: BookDetailView,
        props: true,
        meta: { requiresAuth: false },
      },
      {
        path: 'books/:bookId/comment/create',
        name: 'commentcreate',
        component: CommentCreateView,
        props: true,
        meta: { requiresAuth: true }
      },
      {
        path: 'comments/:commentId/update',
        name: 'commentupdate',
        component: CommentUpdateView,
        props: true,
        meta: { requiresAuth: true }
      },
      {
        path: 'mypage',
        name: 'mypage',
        component: MyPageView,
        meta: { requiresAuth: true },
      },
    ]
  },

  // [그룹 2] 네비바가 없는 완전 독립 페이지들
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false },
  },
  {
    path: '/register',
    name: 'register',
    component: RegisterView,
    meta: { requiresAuth: false },
  },
];

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior() {
    return { top: 0 };
  }
});

// 네비게이션 가드 (보내주신 로직 그대로 유지)
router.beforeEach((to, from, next) => {
  const accountsStore = useAccountsStore();
  if (to.meta.requiresAuth && !accountsStore.isAuthenticated) {
    next({ name: 'login' });
  } else if (
    (to.name === 'login' || to.name === 'register') &&
    accountsStore.isAuthenticated
  ) {
    next({ name: 'home' });
  } else {
    next();
  }
});

export default router;