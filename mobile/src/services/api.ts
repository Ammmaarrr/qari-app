/**
 * API Service for Qari App (React Native)
 * Handles all communication with the backend
 */
import AsyncStorage from '@react-native-async-storage/async-storage';

// API Configuration
const API_BASE_URL = __DEV__ 
  ? 'http://10.0.2.2:8000'  // Android emulator localhost
  : 'https://api.qari-app.com';

// Token storage keys
const TOKEN_KEY = '@qari_auth_token';
const USER_KEY = '@qari_user';

// Types
export interface User {
  id: string;
  email: string;
  name: string;
}

export interface AuthToken {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AnalysisResult {
  request_id?: string;
  matched_ayah: {
    surah: number;
    ayah: number;
    confidence: number;
    text?: string;
  };
  errors: TajweedError[];
  overall_score: number;
  recommendation: string;
  processing_time_seconds?: number;
}

export interface TajweedError {
  type: string;
  letter?: string;
  expected?: string;
  detected?: string;
  start_time: number;
  end_time: number;
  confidence: number;
  suggestion: string;
  correction_audio_url: string;
  word_index?: number;
  severity?: string;
}

export interface UserStats {
  total_sessions: number;
  total_practice_time: number;
  average_score: number;
  best_score: number;
  total_errors_fixed: number;
  streak_days: number;
  last_practice: string | null;
}

export interface SessionSummary {
  session_id: string;
  surah: number;
  ayah: number;
  score: number;
  error_count: number;
  timestamp: string;
}

export interface PracticeItem {
  item_id: string;
  surah: number;
  ayah: number;
  error_type: string;
  next_review: string;
  interval: number;
  repetitions: number;
}

// API Error class
class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = 'ApiError';
  }
}

// Auth token management
let authToken: string | null = null;

async function getAuthToken(): Promise<string | null> {
  if (authToken) return authToken;
  authToken = await AsyncStorage.getItem(TOKEN_KEY);
  return authToken;
}

async function setAuthToken(token: string): Promise<void> {
  authToken = token;
  await AsyncStorage.setItem(TOKEN_KEY, token);
}

async function clearAuthToken(): Promise<void> {
  authToken = null;
  await AsyncStorage.removeItem(TOKEN_KEY);
  await AsyncStorage.removeItem(USER_KEY);
}

// Request helper
async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const token = await getAuthToken();
  
  const headers: HeadersInit = {
    'Accept': 'application/json',
    ...options.headers,
  };
  
  if (token) {
    (headers as Record<string, string>)['Authorization'] = `Bearer ${token}`;
  }
  
  if (!(options.body instanceof FormData)) {
    (headers as Record<string, string>)['Content-Type'] = 'application/json';
  }
  
  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    headers,
  });
  
  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}));
    throw new ApiError(response.status, errorData.detail || 'Request failed');
  }
  
  return response.json();
}

// Auth API
export const authApi = {
  async register(email: string, password: string, name: string): Promise<User> {
    const response = await request<User>('/api/v1/auth/register', {
      method: 'POST',
      body: JSON.stringify({ email, password, name }),
    });
    return response;
  },
  
  async login(email: string, password: string): Promise<AuthToken> {
    const response = await request<AuthToken>('/api/v1/auth/login', {
      method: 'POST',
      body: JSON.stringify({ email, password }),
    });
    await setAuthToken(response.access_token);
    return response;
  },
  
  async logout(): Promise<void> {
    await clearAuthToken();
  },
  
  async getMe(): Promise<User> {
    return request<User>('/api/v1/auth/me');
  },
  
  async isLoggedIn(): Promise<boolean> {
    const token = await getAuthToken();
    return !!token;
  },
};

// Analysis API
export const analysisApi = {
  async analyzeRecording(
    audioUri: string,
    surah: number,
    ayah: number
  ): Promise<AnalysisResult> {
    const formData = new FormData();
    
    // Add audio file
    formData.append('audio', {
      uri: audioUri,
      type: 'audio/m4a',
      name: 'recording.m4a',
    } as any);
    
    formData.append('surah', surah.toString());
    formData.append('ayah', ayah.toString());
    
    return request<AnalysisResult>('/api/v1/recordings/analyze', {
      method: 'POST',
      body: formData,
    });
  },
};

// Progress API
export const progressApi = {
  async getStats(): Promise<UserStats> {
    return request<UserStats>('/api/v1/progress/stats');
  },
  
  async getSessionHistory(limit = 20, offset = 0): Promise<SessionSummary[]> {
    return request<SessionSummary[]>(
      `/api/v1/progress/sessions?limit=${limit}&offset=${offset}`
    );
  },
  
  async getErrorProgress(): Promise<any[]> {
    return request<any[]>('/api/v1/progress/errors');
  },
  
  async getDailyProgress(days = 7): Promise<any[]> {
    return request<any[]>(`/api/v1/progress/daily?days=${days}`);
  },
  
  async getSurahProgress(): Promise<any[]> {
    return request<any[]>('/api/v1/progress/surah');
  },
};

// Practice API (Spaced Repetition)
export const practiceApi = {
  async getDueItems(limit = 10): Promise<PracticeItem[]> {
    return request<PracticeItem[]>(`/api/v1/practice/due?limit=${limit}`);
  },
  
  async submitReview(itemId: string, quality: number): Promise<any> {
    return request<any>('/api/v1/practice/review', {
      method: 'POST',
      body: JSON.stringify({ item_id: itemId, quality }),
    });
  },
  
  async getStats(): Promise<any> {
    return request<any>('/api/v1/practice/stats');
  },
  
  async getRecommended(): Promise<any> {
    return request<any>('/api/v1/practice/recommended');
  },
};

// Corrections API
export const correctionsApi = {
  async getCorrections(): Promise<any[]> {
    return request<any[]>('/api/v1/corrections');
  },
  
  async getCorrection(errorType: string): Promise<any> {
    return request<any>(`/api/v1/corrections/${errorType}`);
  },
};

// Feedback API
export const feedbackApi = {
  async submitFeedback(
    sessionId: string,
    errorId: string,
    feedbackType: 'helpful' | 'not_helpful' | 'incorrect',
    comment?: string
  ): Promise<any> {
    return request<any>('/api/v1/feedback', {
      method: 'POST',
      body: JSON.stringify({
        session_id: sessionId,
        error_id: errorId,
        feedback_type: feedbackType,
        comment,
      }),
    });
  },
};

// Health check
export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE_URL}/health`);
    return response.ok;
  } catch {
    return false;
  }
}

// Export base URL for other uses
export { API_BASE_URL };
