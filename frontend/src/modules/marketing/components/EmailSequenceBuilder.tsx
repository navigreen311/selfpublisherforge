"use client";

import { useState } from "react";
import type { EmailTemplate, EmailSequence } from "../hooks";

interface EmailSequenceBuilderProps {
  sequence?: EmailSequence;
  onSave?: (data: {
    name: string;
    description?: string;
    emails: Partial<EmailTemplate>[];
  }) => void;
  onSend?: (recipientEmails: string[]) => void;
}

const templateTypeLabels: Record<string, string> = {
  welcome: "Welcome",
  launch_announcement: "Launch Announcement",
  follow_up: "Follow-Up",
  review_request: "Review Request",
  custom: "Custom",
};

const statusBadgeColors: Record<string, string> = {
  draft: "bg-gray-100 text-gray-800",
  active: "bg-green-100 text-green-800",
  paused: "bg-yellow-100 text-yellow-800",
  completed: "bg-blue-100 text-blue-800",
  archived: "bg-red-100 text-red-800",
};

export function EmailSequenceBuilder({ sequence, onSave, onSend }: EmailSequenceBuilderProps) {
  const [name, setName] = useState(sequence?.name || "");
  const [description, setDescription] = useState(sequence?.description || "");
  const [emails, setEmails] = useState<Partial<EmailTemplate>[]>(
    sequence?.emails || [
      {
        template_type: "welcome",
        subject: "",
        body_html: "",
        delay_days: 0,
        order_index: 0,
      },
    ]
  );
  const [recipientInput, setRecipientInput] = useState("");
  const [emailError, setEmailError] = useState("");

  const isValidEmail = (email: string): boolean => {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email.trim());
  };

  const validateEmails = (input: string): { valid: string[]; invalid: string[] } => {
    const emails = input.split(",").map(e => e.trim()).filter(Boolean);
    const valid = emails.filter(isValidEmail);
    const invalid = emails.filter(e => !isValidEmail(e));
    return { valid, invalid };
  };

  const handleRecipientsChange = (value: string) => {
    setRecipientInput(value);
    if (value) {
      const { invalid } = validateEmails(value);
      if (invalid.length > 0) {
        setEmailError(`Invalid email(s): ${invalid.join(", ")}`);
      } else {
        setEmailError("");
      }
    } else {
      setEmailError("");
    }
  };

  const addEmail = () => {
    setEmails((prev) => [
      ...prev,
      {
        template_type: "custom" as const,
        subject: "",
        body_html: "",
        delay_days: prev.length > 0 ? (prev[prev.length - 1].delay_days || 0) + 3 : 0,
        order_index: prev.length,
      },
    ]);
  };

  const removeEmail = (index: number) => {
    setEmails((prev) => prev.filter((_, i) => i !== index));
  };

  const updateEmail = (index: number, field: string, value: unknown) => {
    setEmails((prev) =>
      prev.map((email, i) => (i === index ? { ...email, [field]: value } : email))
    );
  };

  const handleSave = () => {
    onSave?.({
      name,
      description: description || undefined,
      emails,
    });
  };

  const handleSend = () => {
    const { valid, invalid } = validateEmails(recipientInput);
    if (invalid.length > 0) {
      setEmailError(`Invalid email(s): ${invalid.join(", ")}`);
      return;
    }
    if (valid.length > 0) {
      onSend?.(valid);
    }
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold">Email Sequence Builder</h2>
          {sequence && (
            <span
              className={`text-xs px-2 py-1 rounded-full ${
                statusBadgeColors[sequence.status] || ""
              }`}
              aria-current={sequence.status === "active" ? "step" : undefined}
            >
              {sequence.status}
            </span>
          )}
        </div>
        <div className="flex gap-2">
          <button
            onClick={handleSave}
            className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
          >
            Save Sequence
          </button>
        </div>
      </div>

      {/* Sequence Info */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Sequence Name
          </label>
          <input
            type="text"
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="e.g., Book Launch Sequence"
          />
        </div>
        <div>
          <label className="block text-sm font-medium text-gray-700 mb-1">
            Description
          </label>
          <input
            type="text"
            value={description}
            onChange={(e) => setDescription(e.target.value)}
            className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
            placeholder="Describe this email sequence..."
          />
        </div>
      </div>

      {/* Email List */}
      <div className="space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-semibold">Emails ({emails.length})</h3>
          <button
            onClick={addEmail}
            className="px-3 py-1.5 text-sm bg-gray-100 hover:bg-gray-200 rounded-lg"
          >
            + Add Email
          </button>
        </div>

        {emails.map((email, index) => (
          <div key={index} className="border rounded-lg p-4 space-y-3 bg-white">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <span className="text-sm font-bold text-gray-400">#{index + 1}</span>
                <span className="text-sm text-gray-500">
                  {templateTypeLabels[email.template_type || "custom"]}
                </span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-xs text-gray-400">
                  Delay: {email.delay_days || 0} days
                </span>
                {emails.length > 1 && (
                  <button
                    onClick={() => removeEmail(index)}
                    className="text-red-400 hover:text-red-600 text-sm"
                  >
                    Remove
                  </button>
                )}
              </div>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-3">
              <div className="md:col-span-2">
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Subject
                </label>
                <input
                  type="text"
                  value={email.subject || ""}
                  onChange={(e) => updateEmail(index, "subject", e.target.value)}
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 text-sm"
                  placeholder="Email subject line..."
                />
              </div>
              <div>
                <label className="block text-xs font-medium text-gray-500 mb-1">
                  Delay (days)
                </label>
                <input
                  type="number"
                  min={0}
                  value={email.delay_days || 0}
                  onChange={(e) =>
                    updateEmail(index, "delay_days", parseInt(e.target.value, 10) || 0)
                  }
                  className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 text-sm"
                />
              </div>
            </div>

            <div>
              <label className="block text-xs font-medium text-gray-500 mb-1">
                Body (HTML)
              </label>
              <textarea
                value={email.body_html || ""}
                onChange={(e) => updateEmail(index, "body_html", e.target.value)}
                rows={4}
                className="w-full px-3 py-2 border rounded focus:ring-2 focus:ring-blue-500 text-sm font-mono"
                placeholder="<p>Hello {reader_name}...</p>"
              />
            </div>
          </div>
        ))}
      </div>

      {/* Send Section */}
      {sequence && sequence.status === "draft" && (
        <div className="border-t pt-4">
          <h3 className="font-semibold mb-2">Send Sequence</h3>
          <div className="flex gap-2">
            <input
              type="text"
              value={recipientInput}
              onChange={(e) => handleRecipientsChange(e.target.value)}
              className="flex-1 px-3 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500"
              placeholder="Enter recipient emails, comma-separated"
            />
            <button
              onClick={handleSend}
              disabled={emailError.length > 0}
              className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed"
            >
              Send
            </button>
          </div>
          {emailError && (
            <p className="text-sm text-destructive mt-1">{emailError}</p>
          )}
        </div>
      )}

      {/* Stats */}
      {sequence && (
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 pt-4 border-t">
          <div className="text-center">
            <div className="text-2xl font-bold">{sequence.recipient_count}</div>
            <div className="text-xs text-gray-500">Recipients</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">{sequence.sent_count}</div>
            <div className="text-xs text-gray-500">Sent</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {sequence.open_rate ? `${(sequence.open_rate * 100).toFixed(1)}%` : "--"}
            </div>
            <div className="text-xs text-gray-500">Open Rate</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold">
              {sequence.click_rate ? `${(sequence.click_rate * 100).toFixed(1)}%` : "--"}
            </div>
            <div className="text-xs text-gray-500">Click Rate</div>
          </div>
        </div>
      )}
    </div>
  );
}
