import { apiClient } from "./api-client";

// Define the types for cron schedule data
export interface CronScheduleData {
  cron_schedule: string | null;
  cron_enabled: boolean;
  timezone: string;
  next_run_description?: string | null;
}

/**
 * Get the current cron schedule for a workflow
 * @param workflowId ID of the workflow
 * @returns CronScheduleData object
 */
export async function getWorkflowCronSchedule(workflowId: string): Promise<CronScheduleData> {
  const response = await apiClient.get(`/api/workflows/${workflowId}/cron-schedule`);
  return response.data;
}

/**
 * Set a cron schedule for a workflow
 * @param workflowId ID of the workflow
 * @param data CronScheduleData object
 * @returns Updated CronScheduleData object
 */
export async function setWorkflowCronSchedule(workflowId: string, data: CronScheduleData): Promise<CronScheduleData> {
  const response = await apiClient.post(`/api/workflows/${workflowId}/cron-schedule`, data);
  return response.data;
}
