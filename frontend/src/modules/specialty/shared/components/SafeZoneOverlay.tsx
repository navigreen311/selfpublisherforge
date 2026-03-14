import React, { useState, useMemo } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface ZoneConfig {
  key: string;
  label: string;
  color: string;
  opacity: number;
  description: string;
}

interface ZoneRect {
  x: number;
  y: number;
  width: number;
  height: number;
}

interface SafeZoneOverlayProps {
  /** Total page width in pixels (including bleed). */
  pageWidth: number;
  /** Total page height in pixels (including bleed). */
  pageHeight: number;
  /** Bleed size in pixels. */
  bleedPx?: number;
  /** Safe margin inset from trim edge in pixels. */
  safeMarginPx?: number;
  /** Gutter width in pixels. */
  gutterPx?: number;
  /** Trim size label for the legend (e.g. "8.5 x 11 in"). */
  trimSizeLabel?: string;
  /** Child content (the page preview) rendered behind the overlay. */
  children?: React.ReactNode;
  className?: string;
}

// ---------------------------------------------------------------------------
// Zone definitions
// ---------------------------------------------------------------------------

const ZONES: ZoneConfig[] = [
  {
    key: 'bleed',
    label: 'Bleed',
    color: '#FF0000',
    opacity: 0.25,
    description: 'Area outside the trim that will be cut. Extend background images here.',
  },
  {
    key: 'trim',
    label: 'Trim',
    color: '#0000FF',
    opacity: 0.2,
    description: 'The cut line. Content here may be partially cut.',
  },
  {
    key: 'safe',
    label: 'Safe',
    color: '#00FF00',
    opacity: 0.15,
    description: 'Content in this zone is guaranteed to be visible after trimming.',
  },
  {
    key: 'gutter',
    label: 'Gutter',
    color: '#FFFF00',
    opacity: 0.25,
    description: 'Near-spine area. Content here may be hidden in the fold.',
  },
];

// ---------------------------------------------------------------------------
// Component
// ---------------------------------------------------------------------------

const SafeZoneOverlay: React.FC<SafeZoneOverlayProps> = ({
  pageWidth,
  pageHeight,
  bleedPx = 38, // ~0.125in at 300 DPI
  safeMarginPx = 113, // ~0.375in at 300 DPI
  gutterPx = 188, // ~0.625in at 300 DPI
  trimSizeLabel,
  children,
  className,
}) => {
  const [enabledZones, setEnabledZones] = useState<Record<string, boolean>>({
    bleed: true,
    trim: true,
    safe: true,
    gutter: true,
  });

  const toggleZone = (key: string) => {
    setEnabledZones((prev) => ({ ...prev, [key]: !prev[key] }));
  };

  // Compute zone rectangles
  const zoneRects = useMemo(() => {
    const trimX = bleedPx;
    const trimY = bleedPx;
    const trimW = pageWidth - 2 * bleedPx;
    const trimH = pageHeight - 2 * bleedPx;

    return {
      bleed: {
        // Four strips around the trim area
        rects: [
          // Top bleed strip
          { x: 0, y: 0, width: pageWidth, height: bleedPx },
          // Bottom bleed strip
          { x: 0, y: pageHeight - bleedPx, width: pageWidth, height: bleedPx },
          // Left bleed strip
          { x: 0, y: bleedPx, width: bleedPx, height: pageHeight - 2 * bleedPx },
          // Right bleed strip
          { x: pageWidth - bleedPx, y: bleedPx, width: bleedPx, height: pageHeight - 2 * bleedPx },
        ] as ZoneRect[],
      },
      trim: {
        // Trim line as a thin border (2px visual)
        rect: { x: trimX, y: trimY, width: trimW, height: trimH } as ZoneRect,
      },
      safe: {
        // The safe-zone boundary band between trim edge and safe interior
        rects: [
          // Top safe margin strip
          { x: trimX, y: trimY, width: trimW, height: safeMarginPx },
          // Bottom safe margin strip
          { x: trimX, y: trimY + trimH - safeMarginPx, width: trimW, height: safeMarginPx },
          // Left safe margin strip
          {
            x: trimX,
            y: trimY + safeMarginPx,
            width: safeMarginPx,
            height: trimH - 2 * safeMarginPx,
          },
          // Right safe margin strip
          {
            x: trimX + trimW - safeMarginPx,
            y: trimY + safeMarginPx,
            width: safeMarginPx,
            height: trimH - 2 * safeMarginPx,
          },
        ] as ZoneRect[],
      },
      gutter: {
        // Gutter zone (left side near spine)
        rect: { x: trimX, y: trimY, width: gutterPx, height: trimH } as ZoneRect,
      },
    };
  }, [pageWidth, pageHeight, bleedPx, safeMarginPx, gutterPx]);

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
      {/* Toggle buttons */}
      <div
        style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}
        role="group"
        aria-label="Toggle safe zone overlays"
      >
        {ZONES.map((zone) => (
          <button
            key={zone.key}
            onClick={() => toggleZone(zone.key)}
            aria-pressed={enabledZones[zone.key]}
            style={{
              display: 'flex',
              alignItems: 'center',
              gap: 6,
              padding: '6px 12px',
              borderRadius: 6,
              border: enabledZones[zone.key]
                ? `2px solid ${zone.color}`
                : '2px solid #E5E7EB',
              background: enabledZones[zone.key] ? `${zone.color}18` : '#FFFFFF',
              cursor: 'pointer',
              fontSize: 13,
              fontWeight: 500,
              color: '#374151',
              transition: 'all 0.15s',
            }}
          >
            {/* Color swatch */}
            <span
              style={{
                display: 'inline-block',
                width: 14,
                height: 14,
                borderRadius: 3,
                background: zone.color,
                opacity: enabledZones[zone.key] ? 1 : 0.4,
              }}
            />
            {zone.label}
          </button>
        ))}
      </div>

      {/* Overlay + page preview */}
      <div
        style={{
          position: 'relative',
          width: pageWidth,
          height: pageHeight,
          overflow: 'hidden',
          border: '1px solid #E5E7EB',
          borderRadius: 4,
          maxWidth: '100%',
        }}
      >
        {/* Page content behind overlays */}
        <div style={{ position: 'absolute', top: 0, left: 0, width: '100%', height: '100%' }}>
          {children}
        </div>

        {/* SVG overlay */}
        <svg
          width={pageWidth}
          height={pageHeight}
          style={{ position: 'absolute', top: 0, left: 0, pointerEvents: 'none' }}
          aria-hidden="true"
        >
          {/* Bleed zone */}
          {enabledZones.bleed &&
            zoneRects.bleed.rects.map((r, i) => (
              <rect
                key={`bleed-${i}`}
                x={r.x}
                y={r.y}
                width={r.width}
                height={r.height}
                fill={ZONES[0].color}
                opacity={ZONES[0].opacity}
              />
            ))}

          {/* Trim line */}
          {enabledZones.trim && (
            <rect
              x={zoneRects.trim.rect.x}
              y={zoneRects.trim.rect.y}
              width={zoneRects.trim.rect.width}
              height={zoneRects.trim.rect.height}
              fill="none"
              stroke={ZONES[1].color}
              strokeWidth={2}
              strokeDasharray="8,4"
              opacity={0.7}
            />
          )}

          {/* Safe zone margin band */}
          {enabledZones.safe &&
            zoneRects.safe.rects.map((r, i) => (
              <rect
                key={`safe-${i}`}
                x={r.x}
                y={r.y}
                width={r.width}
                height={r.height}
                fill={ZONES[2].color}
                opacity={ZONES[2].opacity}
              />
            ))}

          {/* Gutter zone */}
          {enabledZones.gutter && (
            <rect
              x={zoneRects.gutter.rect.x}
              y={zoneRects.gutter.rect.y}
              width={zoneRects.gutter.rect.width}
              height={zoneRects.gutter.rect.height}
              fill={ZONES[3].color}
              opacity={ZONES[3].opacity}
            />
          )}
        </svg>
      </div>

      {/* Legend */}
      <div
        style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
          gap: 8,
          padding: 12,
          background: '#F9FAFB',
          borderRadius: 8,
          border: '1px solid #E5E7EB',
        }}
        role="list"
        aria-label="Zone legend"
      >
        {ZONES.map((zone) => (
          <div
            key={zone.key}
            role="listitem"
            style={{
              display: 'flex',
              gap: 8,
              alignItems: 'flex-start',
              opacity: enabledZones[zone.key] ? 1 : 0.5,
            }}
          >
            <span
              style={{
                display: 'inline-block',
                width: 16,
                height: 16,
                borderRadius: 3,
                background: zone.color,
                opacity: zone.opacity + 0.3,
                flexShrink: 0,
                marginTop: 2,
              }}
            />
            <div>
              <div style={{ fontWeight: 600, fontSize: 13, color: '#1F2937' }}>{zone.label}</div>
              <div style={{ fontSize: 12, color: '#6B7280', lineHeight: 1.4 }}>
                {zone.description}
              </div>
            </div>
          </div>
        ))}
        {trimSizeLabel && (
          <div style={{ fontSize: 12, color: '#6B7280', gridColumn: '1 / -1', marginTop: 4 }}>
            Trim size: {trimSizeLabel} &middot; Bleed: 0.125 in &middot; Safe margin: 0.375 in
          </div>
        )}
      </div>
    </div>
  );
};

export default SafeZoneOverlay;
