"use client";

import { useState, useCallback } from "react";
import { format, parseISO } from "date-fns";
import {
  Instagram,
  Twitter,
  Facebook,
  Copy,
  Pencil,
  Check,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";
import { toast } from "sonner";
import { useUpdateSocialPost } from "../hooks";
import type { SocialPost } from "../types";

interface SocialPostCardProps {
  post: SocialPost;
}

const platformConfig: Record<string, { icon: React.ElementType; label: string; color: string; charLimit: number }> = {
  twitter: { icon: Twitter, label: "X / Twitter", color: "bg-black text-white", charLimit: 280 },
  facebook: { icon: Facebook, label: "Facebook", color: "bg-blue-600 text-white", charLimit: 63206 },
  instagram: { icon: Instagram, label: "Instagram", color: "bg-gradient-to-r from-purple-500 to-pink-500 text-white", charLimit: 2200 },
  tiktok: { icon: Copy, label: "TikTok", color: "bg-gray-900 text-white", charLimit: 2200 },
};

const statusBadgeConfig: Record<string, { variant: "default" | "secondary" | "outline" | "destructive"; label: string }> = {
  draft: { variant: "secondary", label: "Draft" },
  scheduled: { variant: "outline", label: "Scheduled" },
  published: { variant: "default", label: "Published" },
  failed: { variant: "destructive", label: "Failed" },
};

export function SocialPostCard({ post }: SocialPostCardProps) {
  const [isEditing, setIsEditing] = useState(false);
  const [editContent, setEditContent] = useState(post.content);

  const updateMutation = useUpdateSocialPost();

  const config = platformConfig[post.platform] || platformConfig.twitter;
  const statusConfig = statusBadgeConfig[post.status] || statusBadgeConfig.draft;
  const PlatformIcon = config.icon;

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(post.content);
      toast.success("Copied to clipboard");
    } catch {
      toast.error("Failed to copy");
    }
  }, [post.content]);

  const handleSaveEdit = useCallback(() => {
    if (editContent.trim() === post.content) {
      setIsEditing(false);
      return;
    }
    updateMutation.mutate(
      { id: post.id, updates: { content: editContent.trim() } },
      {
        onSuccess: () => {
          setIsEditing(false);
          toast.success("Post updated");
        },
      }
    );
  }, [editContent, post.content, post.id, updateMutation]);

  const handleCancelEdit = useCallback(() => {
    setEditContent(post.content);
    setIsEditing(false);
  }, [post.content]);

  const handleMarkPosted = useCallback(() => {
    updateMutation.mutate(
      { id: post.id, updates: { status: "published" } as Partial<SocialPost> },
      {
        onSuccess: () => {
          toast.success("Marked as posted");
        },
      }
    );
  }, [post.id, updateMutation]);

  const charCount = isEditing ? editContent.length : post.content.length;
  const isOverLimit = charCount > config.charLimit;

  return (
    <div className="bg-card border rounded-lg p-4 space-y-3">
      {/* Top row: platform + status */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-2">
          <span
            className={cn(
              "inline-flex items-center gap-1 px-2 py-1 rounded text-xs font-bold",
              config.color
            )}
          >
            <PlatformIcon className="h-3 w-3" />
            {config.label}
          </span>
          <Badge variant={statusConfig.variant}>{statusConfig.label}</Badge>
        </div>
        {post.scheduled_at && (
          <span className="text-xs text-muted-foreground">
            {format(parseISO(post.scheduled_at), "MMM d, yyyy 'at' h:mm a")}
          </span>
        )}
      </div>

      {/* Content */}
      {isEditing ? (
        <div className="space-y-2">
          <Textarea
            value={editContent}
            onChange={(e) => setEditContent(e.target.value)}
            rows={4}
            className="text-sm"
          />
          <div className="flex items-center justify-between">
            <span
              className={cn(
                "text-xs",
                isOverLimit ? "text-destructive" : "text-muted-foreground"
              )}
            >
              {charCount} / {config.charLimit}
            </span>
            <div className="flex gap-2">
              <Button size="sm" variant="ghost" onClick={handleCancelEdit}>
                <X className="h-3 w-3 mr-1" />
                Cancel
              </Button>
              <Button
                size="sm"
                onClick={handleSaveEdit}
                disabled={updateMutation.isPending || isOverLimit}
              >
                <Check className="h-3 w-3 mr-1" />
                Save
              </Button>
            </div>
          </div>
        </div>
      ) : (
        <p className="text-sm whitespace-pre-wrap">{post.content}</p>
      )}

      {/* Hashtags */}
      {post.hashtags && post.hashtags.length > 0 && !isEditing && (
        <div className="flex flex-wrap gap-1">
          {post.hashtags.map((tag, i) => (
            <Badge key={i} variant="secondary" className="text-xs font-normal">
              {tag.startsWith("#") ? tag : `#${tag}`}
            </Badge>
          ))}
        </div>
      )}

      {/* Character count (non-editing) + Actions */}
      {!isEditing && (
        <div className="flex items-center justify-between pt-1 border-t">
          <span
            className={cn(
              "text-xs",
              isOverLimit ? "text-destructive" : "text-muted-foreground"
            )}
          >
            {charCount} / {config.charLimit} characters
          </span>
          <div className="flex gap-1">
            <Button size="sm" variant="ghost" onClick={() => setIsEditing(true)}>
              <Pencil className="h-3 w-3 mr-1" />
              Edit
            </Button>
            <Button size="sm" variant="ghost" onClick={handleCopy}>
              <Copy className="h-3 w-3 mr-1" />
              Copy
            </Button>
            {post.status !== "published" && (
              <Button size="sm" variant="ghost" onClick={handleMarkPosted}>
                <Check className="h-3 w-3 mr-1" />
                Mark Posted
              </Button>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
