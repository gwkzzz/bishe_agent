import { createRouter, createWebHistory } from "vue-router";

import CaseDetailView from "@/views/CaseDetailView.vue";
import CaseOverviewView from "@/views/CaseOverviewView.vue";
import ConsultationView from "@/views/ConsultationView.vue";
import DocumentView from "@/views/DocumentView.vue";
import EvidenceManagerView from "@/views/EvidenceManagerView.vue";
import LoginView from "@/views/LoginView.vue";
import PersonalCenterView from "@/views/PersonalCenterView.vue";
import RegisterView from "@/views/RegisterView.vue";

export const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/", redirect: "/login" },
    { path: "/login", name: "login", component: LoginView, meta: { publicOnly: true } },
    { path: "/register", name: "register", component: RegisterView, meta: { publicOnly: true } },
    {
      path: "/consultation",
      name: "consultation",
      component: ConsultationView,
      meta: { requiresAuth: true }
    },
    {
      path: "/cases",
      name: "cases",
      component: CaseOverviewView,
      meta: { requiresAuth: true }
    },
    {
      path: "/cases/:caseId",
      name: "case-detail",
      component: CaseDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: "/evidence",
      name: "evidence",
      component: EvidenceManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: "/cases/:caseId/evidence",
      name: "case-evidence",
      component: EvidenceManagerView,
      meta: { requiresAuth: true }
    },
    {
      path: "/documents",
      name: "documents",
      component: DocumentView,
      meta: { requiresAuth: true }
    },
    {
      path: "/documents/:documentId",
      name: "document",
      component: DocumentView,
      meta: { requiresAuth: true }
    },
    {
      path: "/profile",
      name: "profile",
      component: PersonalCenterView,
      meta: { requiresAuth: true }
    }
  ]
});

router.beforeEach((to) => {
  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);
  const token = localStorage.getItem("auth_token");

  if (requiresAuth && !token) {
    return {
      name: "login",
      query: {
        redirect: to.fullPath,
        reason: "login-required"
      }
    };
  }

  return true;
});
