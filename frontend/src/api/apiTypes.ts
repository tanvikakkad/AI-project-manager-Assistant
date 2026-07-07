/** Mirrors backend `core/responses.py` — every endpoint responds in this shape. */
export interface ApiResponse<T> {
  data: T;
}

export interface ApiErrorDetail {
  code: string;
  message: string;
  details?: Record<string, unknown> | null;
}

export interface ApiErrorResponse {
  error: ApiErrorDetail;
}
