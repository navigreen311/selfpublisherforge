"use client";

import { useState, useEffect } from "react";
import {
  Download,
  Edit,
  RefreshCw,
  Star,
  Settings,
  FileImage,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Progress } from "@/components/ui/progress";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import type { Cover } from "@/modules/cover-design/types";

interface CoverResultsProps {
  jobId: string;
  bookTitle: string;
  onBack: () => void;
}

interface CoverVariation extends Cover {
  variation_index: number;
}
