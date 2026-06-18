import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: () => import('../views/Upload.vue') },
  { path: '/result/:id', name: 'Result', component: () => import('../views/Result.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
]

const router = createRouter({ history: createWebHistory(), routes })

router.beforeEach((to, from, next) => {
  const publicPages = ['/', '/login'];
  const authRequired = !publicPages.includes(to.path);
  const auth = useAuthStore();

  if (authRequired && !auth.isLoggedIn) {
    next('/login');
  } else {
    next();
  }
});

export default router
