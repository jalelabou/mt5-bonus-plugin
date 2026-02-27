import api from "./client";
import type {
  Bonus,
  BonusDetail,
  Campaign,
  CampaignListItem,
  PaginatedResponse,
  TokenResponse,
  AuditLogEntry,
  User,
} from "../types";

// Auth
export const login = (email: string, password: string) =>
  api.post<TokenResponse>("/auth/login", { email, password });

export const getMe = () => api.get<User>("/auth/me");

// Campaigns
export const getCampaigns = (params?: Record<string, unknown>) =>
  api.get<PaginatedResponse<CampaignListItem>>("/campaigns", { params });

export const getCampaign = (id: number) =>
  api.get<Campaign>(`/campaigns/${id}`);

export const createCampaign = (data: Partial<Campaign>) =>
  api.post<Campaign>("/campaigns", data);

export const updateCampaign = (id: number, data: Partial<Campaign>) =>
  api.put<Campaign>(`/campaigns/${id}`, data);

export const duplicateCampaign = (id: number) =>
  api.post<Campaign>(`/campaigns/${id}/duplicate`);

export const updateCampaignStatus = (id: number, status: string) =>
  api.patch<Campaign>(`/campaigns/${id}/status`, { status });

// Bonuses
export const getBonuses = (params?: Record<string, unknown>) =>
  api.get<PaginatedResponse<Bonus>>("/bonuses", { params });

export const getBonus = (id: number) =>
  api.get<BonusDetail>(`/bonuses/${id}`);

export const assignBonus = (data: { campaign_id: number; mt5_login: string; deposit_amount?: number }) =>
  api.post<Bonus>("/bonuses/assign", data);

export const cancelBonus = (id: number, reason: string) =>
  api.post<Bonus>(`/bonuses/${id}/cancel`, { reason });

export const forceConvert = (id: number) =>
  api.post<Bonus>(`/bonuses/${id}/force-convert`);

export const overrideLeverage = (id: number, newLeverage: number) =>
  api.post<Bonus>(`/bonuses/${id}/override-leverage`, { new_leverage: newLeverage });

// Accounts
export const getAccount = (login: string) =>
  api.get(`/accounts/${login}`);

// Reports
export const getReportSummary = (params?: Record<string, unknown>) =>
  api.get("/reports/summary", { params });

export const getReportConversions = (params?: Record<string, unknown>) =>
  api.get("/reports/conversions", { params });

export const getReportCancellations = (params?: Record<string, unknown>) =>
  api.get("/reports/cancellations", { params });

export const getReportLeverage = () =>
  api.get("/reports/leverage");

export const exportReport = (reportType: string, format: string, params?: Record<string, unknown>) =>
  api.get("/reports/export", { params: { report_type: reportType, format, ...params }, responseType: "blob" });

// Audit
export const getAuditLogs = (params?: Record<string, unknown>) =>
  api.get<PaginatedResponse<AuditLogEntry>>("/audit", { params });

// Triggers
export const triggerDeposit = (mt5_login: string, deposit_amount: number, agent_code?: string) =>
  api.post("/triggers/deposit", { mt5_login, deposit_amount, agent_code });

export const triggerRegistration = (mt5_login: string) =>
  api.post("/triggers/registration", { mt5_login });

export const triggerPromoCode = (mt5_login: string, promo_code: string, deposit_amount?: number) =>
  api.post("/triggers/promo-code", { mt5_login, promo_code, deposit_amount });

// Health
export const getHealth = () => api.get<{ status: string; scheduler_running: boolean }>("/health");

// Gateway
export const getMockAccounts = () => api.get("/gateway/accounts");
