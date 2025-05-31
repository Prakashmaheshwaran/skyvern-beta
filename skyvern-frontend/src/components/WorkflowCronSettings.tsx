import React, { useState, useEffect } from "react";
import { useForm } from "react-hook-form";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "./ui/card";
import { Label } from "./ui/label";
import { Input } from "./ui/input";
import { Button } from "./ui/button";
import { Switch } from "./ui/switch";
import { Popover, PopoverContent, PopoverTrigger } from "./ui/popover";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "./ui/select";
import { toast } from "./ui/use-toast";
import { HelpCircle } from "lucide-react";
import { getWorkflowCronSchedule, setWorkflowCronSchedule } from "@/api/workflows";

type CronScheduleFormData = {
  cron_schedule: string;
  cron_enabled: boolean;
  timezone: string;
};

const COMMON_CRON_PRESETS = [
  { label: "Every day at midnight", value: "0 0 * * *" },
  { label: "Every hour", value: "0 * * * *" },
  { label: "Every 15 minutes", value: "*/15 * * * *" },
  { label: "Every Monday at 9 AM", value: "0 9 * * MON" },
  { label: "Every weekday at 9 AM", value: "0 9 * * MON-FRI" },
  { label: "First day of every month", value: "0 0 1 * *" },
];

const COMMON_TIMEZONES = [
  "UTC",
  "America/New_York",
  "America/Chicago", 
  "America/Denver",
  "America/Los_Angeles",
  "Europe/London",
  "Europe/Paris",
  "Asia/Tokyo",
  "Asia/Shanghai",
  "Australia/Sydney",
];

interface WorkflowCronSettingsProps {
  workflowId: string;
}

export function WorkflowCronSettings({ workflowId }: WorkflowCronSettingsProps) {
  const {
    register,
    handleSubmit,
    setValue,
    watch,
    formState: { errors, isDirty, isSubmitting },
  } = useForm<CronScheduleFormData>({
    defaultValues: {
      cron_schedule: "",
      cron_enabled: false,
      timezone: "UTC",
    },
  });

  const [isLoading, setIsLoading] = useState(true);
  const [nextRunDescription, setNextRunDescription] = useState<string | null>(null);
  const cronEnabled = watch("cron_enabled");
  const selectedCron = watch("cron_schedule");

  // Fetch existing cron schedule when component loads
  useEffect(() => {
    const fetchCronSchedule = async () => {
      try {
        setIsLoading(true);
        const response = await getWorkflowCronSchedule(workflowId);
        setValue("cron_schedule", response.cron_schedule || "");
        setValue("cron_enabled", response.cron_enabled);
        setValue("timezone", response.timezone || "UTC");
        setNextRunDescription(response.next_run_description || null);
      } catch (error) {
        console.error("Failed to fetch cron schedule:", error);
        toast({
          title: "Error",
          description: "Failed to load cron schedule settings",
          variant: "destructive",
        });
      } finally {
        setIsLoading(false);
      }
    };

    if (workflowId) {
      fetchCronSchedule();
    }
  }, [workflowId, setValue]);

  const onSubmit = async (data: CronScheduleFormData) => {
    try {
      const response = await setWorkflowCronSchedule(workflowId, data);
      setNextRunDescription(response.next_run_description || null);
      toast({
        title: "Success",
        description: "Cron schedule updated successfully",
      });
    } catch (error) {
      console.error("Failed to update cron schedule:", error);
      toast({
        title: "Error",
        description: "Failed to update cron schedule",
        variant: "destructive",
      });
    }
  };

  const handlePresetSelect = (preset: string) => {
    setValue("cron_schedule", preset, { shouldDirty: true });
  };

  return (
    <Card>
      <CardHeader className="border-b-2">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">Schedule</CardTitle>
          <div className="flex items-center space-x-2">
            <Label htmlFor="cron-enabled">Enable Scheduling</Label>
            <Switch
              id="cron-enabled"
              checked={cronEnabled}
              onCheckedChange={(checked) => setValue("cron_enabled", checked, { shouldDirty: true })}
              disabled={isLoading}
            />
          </div>
        </div>
        <CardDescription>
          Configure automated execution of this workflow on a schedule
        </CardDescription>
      </CardHeader>
      <CardContent className="p-6">
        {isLoading ? (
          <div className="flex justify-center py-4">Loading...</div>
        ) : (
          <form onSubmit={handleSubmit(onSubmit)} className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between">
                <Label htmlFor="cron-expression" className="mb-1">
                  Cron Expression
                </Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button variant="ghost" size="sm">
                      <HelpCircle className="h-4 w-4" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-80 p-4">
                    <div className="space-y-2">
                      <h4 className="font-medium">Cron Expression Format</h4>
                      <p className="text-sm text-muted-foreground">
                        Format: minute hour day-of-month month day-of-week
                      </p>
                      <p className="text-sm text-muted-foreground">
                        Example: "0 9 * * MON-FRI" (weekdays at 9 AM)
                      </p>
                      <a 
                        href="https://crontab.guru/" 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="text-sm text-blue-600 hover:underline"
                      >
                        Learn more at crontab.guru
                      </a>
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              <div className="flex space-x-2">
                <Input
                  id="cron-expression"
                  className="flex-grow"
                  placeholder="e.g. 0 9 * * MON-FRI"
                  disabled={!cronEnabled || isLoading}
                  {...register("cron_schedule", { 
                    required: cronEnabled ? "Cron expression is required" : false,
                  })}
                />
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      type="button"
                      variant="outline"
                      disabled={!cronEnabled || isLoading}
                    >
                      Presets
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-72 p-2">
                    <div className="space-y-1">
                      {COMMON_CRON_PRESETS.map((preset) => (
                        <Button
                          key={preset.value}
                          type="button"
                          variant={selectedCron === preset.value ? "secondary" : "ghost"}
                          className="w-full justify-start text-left"
                          onClick={() => handlePresetSelect(preset.value)}
                        >
                          <span className="truncate">{preset.label}</span>
                        </Button>
                      ))}
                    </div>
                  </PopoverContent>
                </Popover>
              </div>
              {errors.cron_schedule && (
                <p className="text-sm text-red-500">{errors.cron_schedule.message}</p>
              )}
            </div>

            <div className="space-y-2">
              <Label htmlFor="timezone">Timezone</Label>
              <Select
                disabled={!cronEnabled || isLoading}
                value={watch("timezone")}
                onValueChange={(value) => setValue("timezone", value, { shouldDirty: true })}
              >
                <SelectTrigger>
                  <SelectValue placeholder="Select timezone" />
                </SelectTrigger>
                <SelectContent>
                  {COMMON_TIMEZONES.map((tz) => (
                    <SelectItem key={tz} value={tz}>
                      {tz}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {nextRunDescription && cronEnabled && (
              <div className="rounded-md bg-muted p-3 text-sm">
                <p className="text-muted-foreground">{nextRunDescription}</p>
              </div>
            )}

            <div className="pt-4 flex justify-end">
              <Button 
                type="submit" 
                disabled={!isDirty || isSubmitting || isLoading}
              >
                {isSubmitting ? "Saving..." : "Save Schedule"}
              </Button>
            </div>
          </form>
        )}
      </CardContent>
    </Card>
  );
}
