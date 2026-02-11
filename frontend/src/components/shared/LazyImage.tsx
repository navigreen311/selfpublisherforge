"use client";

import Image from "next/image";
import { useState } from "react";
import { cn } from "@/lib/utils";

interface LazyImageProps {
  src: string;
  alt: string;
  width?: number;
  height?: number;
  fill?: boolean;
  className?: string;
  objectFit?: "cover" | "contain" | "fill" | "none" | "scale-down";
  priority?: boolean;
  sizes?: string;
  quality?: number;
  placeholder?: "blur" | "empty";
  blurDataURL?: string;
  onLoad?: () => void;
}

/**
 * Optimized image component with lazy loading, blur placeholder, and responsive sizing
 * Uses Next.js Image component for automatic optimization
 */
export function LazyImage({
  src,
  alt,
  width,
  height,
  fill = false,
  className,
  objectFit = "cover",
  priority = false,
  sizes,
  quality = 75,
  placeholder = "blur",
  blurDataURL,
  onLoad,
}: LazyImageProps) {
  const [isLoading, setIsLoading] = useState(true);
  const [hasError, setHasError] = useState(false);

  // Generate a simple blur data URL if none provided
  const defaultBlurDataURL =
    blurDataURL ||
    "data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj48cmVjdCB3aWR0aD0iNDAwIiBoZWlnaHQ9IjQwMCIgZmlsbD0iI2YzZjRmNiIvPjwvc3ZnPg==";

  const handleLoadingComplete = () => {
    setIsLoading(false);
    onLoad?.();
  };

  const handleError = () => {
    setIsLoading(false);
    setHasError(true);
  };

  if (hasError) {
    return (
      <div
        className={cn(
          "flex items-center justify-center bg-muted text-muted-foreground",
          className
        )}
        style={{ width: width || "100%", height: height || "100%" }}
      >
        <div className="text-center p-4">
          <p className="text-sm">Failed to load image</p>
        </div>
      </div>
    );
  }

  return (
    <div className={cn("relative overflow-hidden", className)}>
      <Image
        src={src}
        alt={alt}
        width={fill ? undefined : width}
        height={fill ? undefined : height}
        fill={fill}
        className={cn(
          "transition-opacity duration-300",
          isLoading ? "opacity-0" : "opacity-100",
          className
        )}
        style={{ objectFit }}
        loading={priority ? undefined : "lazy"}
        priority={priority}
        sizes={
          sizes ||
          "(max-width: 640px) 100vw, (max-width: 1024px) 50vw, 33vw"
        }
        quality={quality}
        placeholder={placeholder}
        blurDataURL={placeholder === "blur" ? defaultBlurDataURL : undefined}
        onLoad={handleLoadingComplete}
        onError={handleError}
      />
      {isLoading && (
        <div className="absolute inset-0 bg-muted animate-pulse" />
      )}
    </div>
  );
}
