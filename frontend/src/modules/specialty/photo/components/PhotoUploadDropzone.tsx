"use client";
import { Upload } from "lucide-react";
import { Button } from "@/components/ui/button";
interface Props { bookType?: string; bookId?: string; onUploaded?: () => void; }
export function PhotoUploadDropzone({ onUploaded }: Props) { return (<div className="border-2 border-dashed rounded-lg p-8 text-center"><Upload className="mx-auto mb-2 h-8 w-8 text-muted-foreground" /><p className="text-sm">Drop photos here</p><Button variant="outline" size="sm" className="mt-3" onClick={onUploaded}>Browse Files</Button></div>); }
