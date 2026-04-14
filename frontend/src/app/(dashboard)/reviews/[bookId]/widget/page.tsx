"use client";

import { use } from "react";

import { WidgetGenerator } from "@/modules/review-widget/components/WidgetGenerator";

export default function ReviewWidgetPage({
  params,
}: {
  params: Promise<{ bookId: string }>;
}) {
  const { bookId } = use(params);
  return <WidgetGenerator bookId={bookId} />;
}
