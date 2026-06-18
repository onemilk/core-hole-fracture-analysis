import { createRouter, createWebHistory } from 'vue-router'
import Home from '../views/Home.vue'

const routes = [
  { path: '/', name: 'Home', component: Home },
  { path: '/upload', name: 'Upload', component: () => import('../views/Upload.vue') },
  { path: '/result/:id', name: 'Result', component: () => import('../views/Result.vue') },
  { path: '/login', name: 'Login', component: () => import('../views/Login.vue') },
]

export default createRouter({ history: createWebHistory(), routes })
