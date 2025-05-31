import { getClient } from './AxiosClient';

// Export the API client for use in other modules
export const apiClient = getClient(null, 'v1');
