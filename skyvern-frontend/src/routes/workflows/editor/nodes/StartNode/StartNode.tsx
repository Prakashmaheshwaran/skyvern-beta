import { getClient } from "@/api/AxiosClient";
import { Handle, NodeProps, Position, useReactFlow } from "@xyflow/react";
import type { StartNode } from "./types";
import {
  Accordion,
  AccordionContent,
  AccordionItem,
  AccordionTrigger,
} from "@/components/ui/accordion";
import { useState } from "react";
import { ProxyLocation } from "@/api/types";
import { useQuery } from "@tanstack/react-query";
import { Label } from "@/components/ui/label";
import { HelpTooltip } from "@/components/HelpTooltip";
import { Input } from "@/components/ui/input";
import { ProxySelector } from "@/components/ProxySelector";
import { useCredentialGetter } from "@/hooks/useCredentialGetter";
import { Switch } from "@/components/ui/switch";
import { Separator } from "@/components/ui/separator";
import { ModelsResponse } from "@/api/types";
import { ModelSelector } from "@/components/ModelSelector";

function isValidCronExpression(value: string): boolean {
  const part = '(?:\\*|\\d+|\\d+-\\d+)(?:/\\d+)?';
  const regex = new RegExp(`^${part}\\s+${part}\\s+${part}\\s+${part}\\s+${part}$`);
  return regex.test(value.trim());
}

function isValidTimezone(tz: string): boolean {
  try {
    Intl.DateTimeFormat(undefined, { timeZone: tz }).format();
    return true;
  } catch {
    return false;
  }
}

function StartNode({ id, data }: NodeProps<StartNode>) {
  const credentialGetter = useCredentialGetter();
  const { updateNodeData } = useReactFlow();

  const { data: availableModels } = useQuery<ModelsResponse>({
    queryKey: ["models"],
    queryFn: async () => {
      const client = await getClient(credentialGetter);

      return client.get("/models").then((res) => res.data);
    },
  });

  const models = availableModels?.models ?? [];

  const [inputs, setInputs] = useState({
    webhookCallbackUrl: data.withWorkflowSettings
      ? data.webhookCallbackUrl
      : "",
    proxyLocation: data.withWorkflowSettings
      ? data.proxyLocation
      : ProxyLocation.Residential,
    persistBrowserSession: data.withWorkflowSettings
      ? data.persistBrowserSession
      : false,
    model: data.withWorkflowSettings ? data.model : { model: models[0] || "" },
    cronSchedule: data.withWorkflowSettings ? data.cronSchedule ?? "" : "",
    cronTimezone: data.withWorkflowSettings ? data.cronTimezone ?? "" : "",
  });

  const [cronError, setCronError] = useState<string | null>(null);
  const [timezoneError, setTimezoneError] = useState<string | null>(null);

  function handleChange(key: string, value: unknown) {
    if (!data.editable) {
      return;
    }
    setInputs({ ...inputs, [key]: value });
    updateNodeData(id, { [key]: value });
    if (key === "cronSchedule") {
      if (value && typeof value === "string" && !isValidCronExpression(value)) {
        setCronError("Invalid cron expression");
      } else {
        setCronError(null);
      }
    }
    if (key === "cronTimezone") {
      if (value && typeof value === "string" && !isValidTimezone(value)) {
        setTimezoneError("Invalid timezone");
      } else {
        setTimezoneError(null);
      }
    }
  }

  if (data.withWorkflowSettings) {
    return (
      <div>
        <Handle
          type="source"
          position={Position.Bottom}
          id="a"
          className="opacity-0"
        />
        <div className="w-[30rem] rounded-lg bg-slate-elevation3 px-6 py-4 text-center">
          <div className="space-y-4">
            <header>Start</header>
            <Separator />
            <Accordion type="single" collapsible>
              <AccordionItem value="settings" className="border-b-0">
                <AccordionTrigger className="py-2">
                  Workflow Settings
                </AccordionTrigger>
                <AccordionContent className="pl-6 pr-1 pt-1">
                  <div className="space-y-4">
                    <div className="space-y-2">
                      <ModelSelector
                        className="nopan w-52 text-xs"
                        value={inputs.model}
                        onChange={(value) => {
                          handleChange("model", value);
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Label>Webhook Callback URL</Label>
                        <HelpTooltip content="The URL of a webhook endpoint to send the workflow results" />
                      </div>
                      <Input
                        value={inputs.webhookCallbackUrl}
                        placeholder="https://"
                        onChange={(event) => {
                          handleChange(
                            "webhookCallbackUrl",
                            event.target.value,
                          );
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Label>Proxy Location</Label>
                        <HelpTooltip content="Route Skyvern through one of our available proxies." />
                      </div>
                      <ProxySelector
                        value={inputs.proxyLocation}
                        onChange={(value) => {
                          handleChange("proxyLocation", value);
                        }}
                      />
                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center gap-2">
                        <Label>Save &amp; Reuse Session</Label>
                        <HelpTooltip content="Persist session information across workflow runs" />
                        <Switch
                          checked={inputs.persistBrowserSession}
                          onCheckedChange={(value) => {
                            handleChange("persistBrowserSession", value);
                          }}
                        />
                      </div>
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Label>Cron Schedule</Label>
                        <HelpTooltip content="CRON expression for scheduling runs" />
                      </div>
                      <Input
                        value={inputs.cronSchedule}
                        placeholder="* * * * *"
                        onChange={(event) => {
                          handleChange("cronSchedule", event.target.value);
                        }}
                        className={cronError ? "border-red-500" : undefined}
                      />
                      {cronError && (
                        <p className="text-xs text-red-500">{cronError}</p>
                      )}
                    </div>
                    <div className="space-y-2">
                      <div className="flex gap-2">
                        <Label>Timezone</Label>
                        <HelpTooltip content="IANA timezone identifier" />
                      </div>
                      <Input
                        value={inputs.cronTimezone}
                        placeholder="UTC"
                        onChange={(event) => {
                          handleChange("cronTimezone", event.target.value);
                        }}
                        className={timezoneError ? "border-red-500" : undefined}
                      />
                      {timezoneError && (
                        <p className="text-xs text-red-500">{timezoneError}</p>
                      )}
                    </div>
                  </div>
                </AccordionContent>
              </AccordionItem>
            </Accordion>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      <Handle
        type="source"
        position={Position.Bottom}
        id="a"
        className="opacity-0"
      />
      <div className="w-[30rem] rounded-lg bg-slate-elevation3 px-6 py-4 text-center">
        Start
      </div>
    </div>
  );
}

export { StartNode };
