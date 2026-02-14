"use client";

import { useState } from "react";
import { Loader2, Smartphone } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { useMobileCheckMutation } from "../hooks";
import type { MobileCheckResult } from "../types";

export interface MobileCheckFormData {
  title: string;
  author: string;
  price?: number;
}

interface MobileCheckFormProps {
  onCheckComplete?: (result: MobileCheckResult, formData: MobileCheckFormData) => void;
  className?: string;
}

interface FormErrors {
  title?: string;
  author?: string;
  blurb?: string;
}

export function MobileCheckForm({ onCheckComplete, className }: MobileCheckFormProps) {
  const [title, setTitle] = useState("");
  const [author, setAuthor] = useState("");
  const [subtitle, setSubtitle] = useState("");
  const [price, setPrice] = useState("");
  const [blurb, setBlurb] = useState("");
  const [errors, setErrors] = useState<FormErrors>({});

  const mobileMutation = useMobileCheckMutation();

  const validate = (): boolean => {
    const newErrors: FormErrors = {};
    if (!title.trim()) newErrors.title = "Title is required.";
    if (!author.trim()) newErrors.author = "Author is required.";
    if (!blurb.trim()) newErrors.blurb = "Blurb is required.";
    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleCheck = () => {
    if (!validate()) return;

    mobileMutation.mutate(
      {
        title: title.trim(),
        subtitle: subtitle.trim() || undefined,
        blurb: blurb.trim(),
        author_name: author.trim(),
        price: price ? parseFloat(price) : undefined,
      },
      {
        onSuccess: (result) => {
          onCheckComplete?.(result, {
            title: title.trim(),
            author: author.trim(),
            price: price ? parseFloat(price) : undefined,
          });
        },
      }
    );
  };

  return (
    <Card className={className}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Smartphone className="h-5 w-5" />
          Mobile Display Check
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="mobile-title">
              Title <span className="text-destructive">*</span>
            </Label>
            <Input
              id="mobile-title"
              value={title}
              onChange={(e) => {
                setTitle(e.target.value);
                if (errors.title) setErrors((p) => ({ ...p, title: undefined }));
              }}
              placeholder="Book title"
            />
            {errors.title && (
              <p className="text-xs text-destructive">{errors.title}</p>
            )}
          </div>
          <div className="space-y-2">
            <Label htmlFor="mobile-author">
              Author <span className="text-destructive">*</span>
            </Label>
            <Input
              id="mobile-author"
              value={author}
              onChange={(e) => {
                setAuthor(e.target.value);
                if (errors.author) setErrors((p) => ({ ...p, author: undefined }));
              }}
              placeholder="Author name"
            />
            {errors.author && (
              <p className="text-xs text-destructive">{errors.author}</p>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2">
          <div className="space-y-2">
            <Label htmlFor="mobile-subtitle">Subtitle (optional)</Label>
            <Input
              id="mobile-subtitle"
              value={subtitle}
              onChange={(e) => setSubtitle(e.target.value)}
              placeholder="Subtitle"
            />
          </div>
          <div className="space-y-2">
            <Label htmlFor="mobile-price">Price (optional)</Label>
            <Input
              id="mobile-price"
              type="number"
              step="0.01"
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="3.99"
            />
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="mobile-blurb">
            Blurb <span className="text-destructive">*</span>
          </Label>
          <Textarea
            id="mobile-blurb"
            value={blurb}
            onChange={(e) => {
              setBlurb(e.target.value);
              if (errors.blurb) setErrors((p) => ({ ...p, blurb: undefined }));
            }}
            rows={5}
            placeholder="Book description / blurb"
          />
          {errors.blurb && (
            <p className="text-xs text-destructive">{errors.blurb}</p>
          )}
        </div>

        <Button onClick={handleCheck} disabled={mobileMutation.isPending}>
          {mobileMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Checking...
            </>
          ) : (
            <>
              <Smartphone className="mr-2 h-4 w-4" />
              Check Mobile Display
            </>
          )}
        </Button>

        {mobileMutation.isError && (
          <Alert variant="destructive">
            <AlertDescription>
              Failed to check mobile display. Please try again.
            </AlertDescription>
          </Alert>
        )}
      </CardContent>
    </Card>
  );
}
