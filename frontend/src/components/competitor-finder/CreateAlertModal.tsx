"use client";

import { useEffect, useState } from "react";
import { useTranslations } from "@/hooks/use-translations";
import { useCreateAlert, useUpdateAlert } from "@/modules/competitors/hooks";
import type { CompetitorAlert, AlertType } from "@/modules/competitors/hooks";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from "@/components/ui/dialog";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  TrendingDown,
  DollarSign,
  UserPlus,
  Star,
  ThumbsDown,
  BarChart3,
  BookOpen,
} from "lucide-react";

// ---------------------------------------------------------------------------
// Alert type options
// ---------------------------------------------------------------------------

const ALERT_TYPE_OPTIONS: {
  value: AlertType;
  icon: React.ElementType;
  tKey: string;
}[] = [
  { value: "bsr_drop", icon: TrendingDown, tKey: "alerts.bsrDrop" },
  { value: "price_change", icon: DollarSign, tKey: "alerts.priceChange" },
  { value: "new_book", icon: UserPlus, tKey: "alerts.newCompetitor" },
  { value: "review_spike", icon: Star, tKey: "alerts.reviewSpike" },
  { value: "new_negative_theme", icon: ThumbsDown, tKey: "alerts.newNegativeTheme" },
  { value: "rank_change", icon: BarChart3, tKey: "alerts.rankChange" },
  { value: "new_book_by_author", icon: BookOpen, tKey: "alerts.newBookByAuthor" },
];

const FREQUENCY_OPTIONS = ["instant", "daily", "weekly"] as const;

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

interface CreateAlertModalProps {
  open: boolean;
  onClose: () => void;
  editAlert?: CompetitorAlert | null;
}

export function CreateAlertModal({
  open,
  onClose,
  editAlert,
}: CreateAlertModalProps) {
  const t = useTranslations("competitors");
  const createMutation = useCreateAlert();
  const updateMutation = useUpdateAlert();

  // ---- form state ----
  const [alertType, setAlertType] = useState<AlertType>("bsr_drop");
  const [alertName, setAlertName] = useState("");
  const [threshold, setThreshold] = useState("");
  const [percentChange, setPercentChange] = useState("");
  const [deliveryChannels, setDeliveryChannels] = useState<string[]>(["in-app"]);
  const [checkFrequency, setCheckFrequency] = useState<string>("daily");

  // ---- pre-fill when editing ----
  useEffect(() => {
    if (editAlert) {
      setAlertType(editAlert.alert_type);
      setAlertName(editAlert.name ?? editAlert.title ?? "");
      setThreshold(String(editAlert.config?.threshold ?? ""));
      setPercentChange(String(editAlert.config?.percent_change ?? ""));
      setDeliveryChannels(editAlert.delivery_channels ?? ["in-app"]);
      setCheckFrequency(editAlert.check_frequency ?? "daily");
    } else {
      resetForm();
    }
  }, [editAlert, open]);

  function resetForm() {
    setAlertType("bsr_drop");
    setAlertName("");
    setThreshold("");
    setPercentChange("");
    setDeliveryChannels(["in-app"]);
    setCheckFrequency("daily");
  }

  // ---- channel toggle ----
  function toggleChannel(channel: string) {
    setDeliveryChannels((prev) =>
      prev.includes(channel)
        ? prev.filter((c) => c !== channel)
        : [...prev, channel],
    );
  }

  // ---- submit ----
  function handleSubmit() {
    const config: Record<string, unknown> = {};
    if (threshold) config.threshold = Number(threshold);
    if (percentChange) config.percent_change = Number(percentChange);

    const payload = {
      alert_type: alertType,
      name: alertName,
      config,
      delivery_channels: deliveryChannels,
      check_frequency: checkFrequency,
      active: true,
    };

    if (editAlert) {
      updateMutation.mutate(
        { id: editAlert.id, updates: payload },
        { onSuccess: () => onClose() },
      );
    } else {
      createMutation.mutate(payload, { onSuccess: () => onClose() });
    }
  }

  const isPending = createMutation.isPending || updateMutation.isPending;

  // ---- determine which config fields to show ----
  const showThreshold = ["bsr_drop", "review_spike", "rank_change"].includes(alertType);
  const showPercent = ["price_change", "bsr_drop"].includes(alertType);

  return (
    <Dialog open={open} onOpenChange={(v) => !v && onClose()}>
      <DialogContent className="max-w-xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>
            {editAlert
              ? t("alerts.modal.editTitle")
              : t("alerts.modal.title")}
          </DialogTitle>
          <DialogDescription className="sr-only">
            {editAlert
              ? t("alerts.modal.editTitle")
              : t("alerts.modal.title")}
          </DialogDescription>
        </DialogHeader>

        <div className="space-y-6 py-2">
          {/* ---- Alert Type ---- */}
          <div className="space-y-2">
            <Label>{t("alerts.modal.alertType")}</Label>
            <div className="grid grid-cols-2 gap-2 sm:grid-cols-3">
              {ALERT_TYPE_OPTIONS.map(({ value, icon: Icon, tKey }) => (
                <button
                  key={value}
                  type="button"
                  onClick={() => setAlertType(value)}
                  className={`flex items-center gap-2 rounded-lg border p-3 text-left text-sm transition-colors ${
                    alertType === value
                      ? "border-primary bg-primary/5 ring-1 ring-primary"
                      : "border-border hover:border-primary/40"
                  }`}
                >
                  <Icon className="h-4 w-4 flex-shrink-0" />
                  <span className="leading-snug">{t(tKey)}</span>
                </button>
              ))}
            </div>
          </div>

          {/* ---- Alert Name ---- */}
          <div className="space-y-2">
            <Label htmlFor="alert-name">{t("alerts.modal.alertName")}</Label>
            <Input
              id="alert-name"
              value={alertName}
              onChange={(e) => setAlertName(e.target.value)}
              placeholder={t("alerts.modal.namePlaceholder")}
            />
          </div>

          {/* ---- Configuration ---- */}
          {(showThreshold || showPercent) && (
            <div className="space-y-2">
              <Label>{t("alerts.modal.configuration")}</Label>
              <div className="grid grid-cols-2 gap-3">
                {showThreshold && (
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground" htmlFor="threshold">
                      {t("alerts.modal.threshold")}
                    </Label>
                    <Input
                      id="threshold"
                      type="number"
                      value={threshold}
                      onChange={(e) => setThreshold(e.target.value)}
                      placeholder="e.g. 10000"
                    />
                  </div>
                )}
                {showPercent && (
                  <div className="space-y-1">
                    <Label className="text-xs text-muted-foreground" htmlFor="percent-change">
                      {t("alerts.modal.percentChange")}
                    </Label>
                    <Input
                      id="percent-change"
                      type="number"
                      value={percentChange}
                      onChange={(e) => setPercentChange(e.target.value)}
                      placeholder="e.g. 20"
                    />
                  </div>
                )}
              </div>
            </div>
          )}

          {/* ---- Delivery Channels ---- */}
          <div className="space-y-2">
            <Label>{t("alerts.modal.deliveryChannels")}</Label>
            <div className="flex gap-3">
              {["email", "in-app"].map((channel) => (
                <label
                  key={channel}
                  className="flex cursor-pointer items-center gap-2 text-sm"
                >
                  <input
                    type="checkbox"
                    checked={deliveryChannels.includes(channel)}
                    onChange={() => toggleChannel(channel)}
                    className="h-4 w-4 rounded border-border text-primary focus:ring-primary"
                  />
                  <span className="capitalize">{channel}</span>
                </label>
              ))}
            </div>
          </div>

          {/* ---- Check Frequency ---- */}
          <div className="space-y-2">
            <Label>{t("alerts.modal.checkFrequency")}</Label>
            <div className="flex gap-3">
              {FREQUENCY_OPTIONS.map((freq) => (
                <label
                  key={freq}
                  className="flex cursor-pointer items-center gap-2 text-sm"
                >
                  <input
                    type="radio"
                    name="check-frequency"
                    value={freq}
                    checked={checkFrequency === freq}
                    onChange={() => setCheckFrequency(freq)}
                    className="h-4 w-4 border-border text-primary focus:ring-primary"
                  />
                  <span className="capitalize">{freq}</span>
                </label>
              ))}
            </div>
          </div>
        </div>

        {/* ---- Footer ---- */}
        <DialogFooter>
          <Button variant="outline" onClick={onClose} disabled={isPending}>
            {t("alerts.cancel")}
          </Button>
          <Button
            onClick={handleSubmit}
            disabled={isPending || !alertName.trim()}
          >
            {isPending
              ? "..."
              : t("alerts.save")}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
