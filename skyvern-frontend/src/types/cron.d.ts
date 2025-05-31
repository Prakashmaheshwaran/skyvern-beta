declare module 'react' {
  export = React;
}

declare module 'react-hook-form' {
  export const useForm: any;
  export const Controller: any;
  export const useWatch: any;
}

declare module 'lucide-react' {
  export const Clock: any;
  export const Calendar: any;
  export const Check: any;
}

declare module '@/api/workflows' {
  export function setCronSchedule(workflowId: string, cronSchedule: string, enabled: boolean, timezone: string): Promise<any>;
  export function getCronSchedule(workflowId: string): Promise<any>;
}

declare module '@/components/ui/tabs' {
  export const Tabs: React.FC<any>;
  export const TabsList: React.FC<any>;
  export const TabsTrigger: React.FC<any>;
  export const TabsContent: React.FC<any>;
}

declare module '@/components/ui/form' {
  export const Form: any;
  export const FormField: any;
  export const FormItem: any;
  export const FormLabel: any;
  export const FormControl: any;
  export const FormDescription: any;
  export const FormMessage: any;
}

declare module '@/components/ui/input' {
  export const Input: React.FC<any>;
}

declare module '@/components/ui/select' {
  export const Select: React.FC<any>;
  export const SelectTrigger: React.FC<any>;
  export const SelectValue: React.FC<any>;
  export const SelectContent: React.FC<any>;
  export const SelectItem: React.FC<any>;
}

declare module '@/components/ui/switch' {
  export const Switch: React.FC<any>;
}

declare module '@/components/ui/button' {
  export const Button: React.FC<any>;
}

declare module '@/components/ui/card' {
  export const Card: React.FC<any>;
  export const CardHeader: React.FC<any>;
  export const CardTitle: React.FC<any>;
  export const CardDescription: React.FC<any>;
  export const CardContent: React.FC<any>;
  export const CardFooter: React.FC<any>;
}

declare module '@/lib/utils' {
  export function cn(...inputs: any[]): string;
}

declare module '@xyflow/react' {
  export const ReactFlowProvider: React.FC<any>;
}
