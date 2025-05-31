import React from "react";
import { WorkflowCronSettings } from "@/components/WorkflowCronSettings";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Switch } from "@/components/ui/switch";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProxyLocation } from "@/api/types";
import { WorkflowSettings as WorkflowSettingsType } from "../types/workflowTypes";

interface WorkflowSettingsProps {
  workflowId: string;
  settings: WorkflowSettingsType;
  onSettingsChange: (settings: Partial<WorkflowSettingsType>) => void;
  isLoading?: boolean;
  isGlobalWorkflow?: boolean;
}

export function WorkflowSettings({
  workflowId,
  settings,
  onSettingsChange,
  isLoading = false,
  isGlobalWorkflow = false,
}: WorkflowSettingsProps) {
  return (
    <Tabs defaultValue="general" className="w-full">
      <TabsList>
        <TabsTrigger value="general">General Settings</TabsTrigger>
        <TabsTrigger value="schedule">Scheduling</TabsTrigger>
      </TabsList>
      <TabsContent value="general" className="space-y-4 py-4">
        <Card>
          <CardHeader className="border-b-2">
            <CardTitle className="text-lg">General Settings</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 p-6">
            <div className="flex items-center justify-between">
              <Label htmlFor="persist-browser" className="flex-grow">
                Persist Browser Session
                <p className="text-sm text-muted-foreground">
                  Keep the browser session alive between workflow runs
                </p>
              </Label>
              <Switch
                id="persist-browser"
                disabled={isLoading || isGlobalWorkflow}
                checked={settings.persistBrowserSession}
                onCheckedChange={(checked) => onSettingsChange({ persistBrowserSession: checked })}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="proxy-location">Proxy Location</Label>
              <Select
                disabled={isLoading || isGlobalWorkflow}
                value={settings.proxyLocation || ""}
                onValueChange={(value) => onSettingsChange({ proxyLocation: value as ProxyLocation })}
              >
                <SelectTrigger id="proxy-location">
                  <SelectValue placeholder="Select proxy location" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="us">United States</SelectItem>
                  <SelectItem value="eu">Europe</SelectItem>
                </SelectContent>
              </Select>
            </div>

            <div className="space-y-2">
              <Label htmlFor="webhook-url">Webhook Callback URL</Label>
              <Input
                id="webhook-url"
                disabled={isLoading || isGlobalWorkflow}
                value={settings.webhookCallbackUrl || ""}
                onChange={(e) => onSettingsChange({ webhookCallbackUrl: e.target.value })}
                placeholder="https://your-callback-url.com"
              />
              <p className="text-xs text-muted-foreground">
                Optional URL to receive webhook callbacks when a workflow run completes
              </p>
            </div>
          </CardContent>
        </Card>
      </TabsContent>

      <TabsContent value="schedule" className="py-4">
        <WorkflowCronSettings workflowId={workflowId} />
      </TabsContent>
    </Tabs>
  );
}
