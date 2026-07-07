import axios from "axios";
import type { ApiErrorResponse } from "./apiTypes";

const DEFAULT_ERROR_MESSAGE = "Something went wrong. Please try again.";

/** Extracts the backend's structured error message, falling back to a generic one. */
export function getApiErrorMessage(error: unknown): string {
  if (axios.isAxiosError<ApiErrorResponse>(error)) {
    return error.response?.data?.error?.message ?? DEFAULT_ERROR_MESSAGE;
  }
  return DEFAULT_ERROR_MESSAGE;
}
