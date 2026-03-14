import React, { useState, useMemo, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

interface DeviceSpec {
  key: string;
  name: string;
  width: number;
  height: number;
  dpi: number;
  platform: 'kindle' | 'apple';
  frameColor: string;
  bezelWidth: number;
  grayscale?: boolean;
  hasNotch?: boolean;
}

interface PageData {
  pageNumber: number;
  imageUrl?: string;
  textContent?: string;
  layout?: string;
}

interface DevicePreviewProps {
  pages: PageData[];
  currentPage?: number;
  onPageChange?: (page: number) => void;
  className?: string;
}

// ---------------------------------------------------------------------------
// Device specifications
// ---------------------------------------------------------------------------

const DEVICES: DeviceSpec[] = [
  {
    key: 'kindle_fire_hd_10',
    name: 'Kindle Fire HD 10',
    width: 1920,
    height: 1200,
    dpi: 224,
    platform: 'kindle',
    frameColor: '#232F3E',
    bezelWidth: 24,
  },
  {
    key: 'kindle_fire_hd_8',
    name: 'Kindle Fire HD 8',
    width: 1280,
    height: 800,
    dpi: 189,
    platform: 'kindle',
    frameColor: '#232F3E',
    bezelWidth: 20,
  },
  {
    key: 'kindle_paperwhite',
    name: 'Kindle Paperwhite',
    width: 1236,
    height: 1648,
    dpi: 300,
    platform: 'kindle',
    frameColor: '#1A1A2E',
    bezelWidth: 16,
    grayscale: true,
  },
  {
    key: 'ipad_10_2',
    name: 'iPad 10.2"',
    width: 2160,
    height: 1620,
    dpi: 264,
    platform: 'apple',
    frameColor: '#C0C0C0',
    bezelWidth: 28,
  },
  {
    key: 'ipad_mini_8_3',
    name: 'iPad Mini 8.3"',
    width: 2266,
    height: 1488,
    dpi: 326,
    platform: 'apple',
    frameColor: '#E0E0E0',
    bezelWidth: 20,
  },
  {
    key: 'iphone_15',
    name: 'iPhone 15',
    width: 2556,
    height: 1179,
    dpi: 460,
    platform: 'apple',
    frameColor: '#1C1C1E',
    bezelWidth: 12,
    hasNotch: true,
  },
];

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface DeviceCardProps {
  device: DeviceSpec;
  selected: boolean;
  onSelect: () => void;
}

const DeviceCard: React.FC<DeviceCardProps> = ({ device, selected, onSelect }) => {
  // Compute a small visual representation of the device aspect ratio
  const maxThumbH = 48;
  const aspect = device.width / device.height;
  const thumbW = aspect >= 1 ? maxThumbH : Math.round(maxThumbH * aspect);
  const thumbH = aspect >= 1 ? Math.round(maxThumbH / aspect) : maxThumbH;

  return (
    <button
      onClick={onSelect}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        gap: 6,
        padding: '10px 14px',
        border: selected ? '2px solid #3B82F6' : '2px solid #E5E7EB',
        borderRadius: 10,
        background: selected ? '#EFF6FF' : '#FFFFFF',
        cursor: 'pointer',
        minWidth: 110,
        transition: 'border-color 0.15s, background 0.15s',
      }}
      aria-pressed={selected}
      aria-label={`Preview on ${device.name}`}
    >
      {/* Mini device frame */}
      <div
        style={{
          width: thumbW + 8,
          height: thumbH + 8,
          borderRadius: 4,
          background: device.frameColor,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
        }}
      >
        <div
          style={{
            width: thumbW,
            height: thumbH,
            borderRadius: 2,
            background: device.grayscale ? '#E0E0E0' : '#FFFFFF',
          }}
        />
      </div>
      <span style={{ fontSize: 11, fontWeight: selected ? 600 : 400, color: '#374151', textAlign: 'center' }}>
        {device.name}
      </span>
      <span style={{ fontSize: 10, color: '#9CA3AF' }}>
        {device.width}x{device.height} &middot; {device.dpi} DPI
      </span>
    </button>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const DevicePreview: React.FC<DevicePreviewProps> = ({
  pages,
  currentPage: controlledPage,
  onPageChange,
  className,
}) => {
  const [selectedDeviceKey, setSelectedDeviceKey] = useState<string>(DEVICES[0].key);
  const [internalPage, setInternalPage] = useState(0);
  const [zoomMode, setZoomMode] = useState<'fit' | 'actual'>('fit');

  const currentPageIndex = controlledPage ?? internalPage;

  const selectedDevice = useMemo(
    () => DEVICES.find((d) => d.key === selectedDeviceKey) ?? DEVICES[0],
    [selectedDeviceKey],
  );

  const page = pages[currentPageIndex] as PageData | undefined;

  // ---- Navigation ----

  const goToPage = useCallback(
    (idx: number) => {
      const clamped = Math.max(0, Math.min(idx, pages.length - 1));
      if (onPageChange) {
        onPageChange(clamped);
      } else {
        setInternalPage(clamped);
      }
    },
    [pages.length, onPageChange],
  );

  const goPrev = useCallback(() => goToPage(currentPageIndex - 1), [currentPageIndex, goToPage]);
  const goNext = useCallback(() => goToPage(currentPageIndex + 1), [currentPageIndex, goToPage]);

  // ---- Compute preview area dimensions ----
  // Scale the device resolution down to fit within a max preview box
  const MAX_PREVIEW_W = 640;
  const MAX_PREVIEW_H = 520;

  const previewScale = useMemo(() => {
    if (zoomMode === 'actual') return 1;
    const sW = MAX_PREVIEW_W / selectedDevice.width;
    const sH = MAX_PREVIEW_H / selectedDevice.height;
    return Math.min(sW, sH);
  }, [selectedDevice, zoomMode]);

  const previewW = Math.round(selectedDevice.width * previewScale);
  const previewH = Math.round(selectedDevice.height * previewScale);
  const bezel = Math.round(selectedDevice.bezelWidth * previewScale);

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
      {/* Device selector row */}
      <div
        style={{
          display: 'flex',
          gap: 8,
          overflowX: 'auto',
          paddingBottom: 4,
        }}
        role="radiogroup"
        aria-label="Select preview device"
      >
        {DEVICES.map((device) => (
          <DeviceCard
            key={device.key}
            device={device}
            selected={device.key === selectedDeviceKey}
            onSelect={() => setSelectedDeviceKey(device.key)}
          />
        ))}
      </div>

      {/* Preview area */}
      <div
        style={{
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          gap: 12,
          overflow: zoomMode === 'actual' ? 'auto' : 'hidden',
          maxHeight: zoomMode === 'actual' ? 600 : undefined,
        }}
      >
        {/* Device frame */}
        <div
          style={{
            width: previewW + bezel * 2,
            height: previewH + bezel * 2,
            borderRadius: bezel,
            background: selectedDevice.frameColor,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            position: 'relative',
            boxShadow: '0 4px 20px rgba(0,0,0,0.25)',
          }}
          role="img"
          aria-label={`${selectedDevice.name} device frame showing page ${currentPageIndex + 1}`}
        >
          {/* Notch (iPhone) */}
          {selectedDevice.hasNotch && (
            <div
              style={{
                position: 'absolute',
                top: 0,
                left: '50%',
                transform: 'translateX(-50%)',
                width: Math.round(previewW * 0.3),
                height: Math.round(bezel * 0.8),
                borderRadius: '0 0 12px 12px',
                background: '#000',
                zIndex: 2,
              }}
            />
          )}

          {/* Screen area */}
          <div
            style={{
              width: previewW,
              height: previewH,
              background: selectedDevice.grayscale ? '#F5F5F5' : '#FFFFFF',
              borderRadius: Math.max(2, bezel - 4),
              overflow: 'hidden',
              position: 'relative',
              filter: selectedDevice.grayscale ? 'grayscale(100%)' : undefined,
            }}
          >
            {page ? (
              <>
                {page.imageUrl && (
                  <img
                    src={page.imageUrl}
                    alt={`Page ${currentPageIndex + 1}`}
                    style={{
                      width: '100%',
                      height: '100%',
                      objectFit: 'contain',
                      position: 'absolute',
                      top: 0,
                      left: 0,
                    }}
                  />
                )}
                {page.textContent && (
                  <div
                    style={{
                      position: 'absolute',
                      bottom: '10%',
                      left: '5%',
                      right: '5%',
                      textAlign: 'center',
                      fontSize: Math.max(10, Math.round(14 * previewScale)),
                      color: '#1F2937',
                      background: 'rgba(255,255,255,0.85)',
                      padding: '4px 8px',
                      borderRadius: 4,
                    }}
                  >
                    {page.textContent}
                  </div>
                )}
              </>
            ) : (
              <div
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  height: '100%',
                  color: '#9CA3AF',
                  fontSize: 14,
                }}
              >
                No page data
              </div>
            )}
          </div>
        </div>
      </div>

      {/* Controls: navigation + zoom */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 16,
        }}
      >
        {/* Prev */}
        <button
          onClick={goPrev}
          disabled={currentPageIndex <= 0}
          aria-label="Previous page"
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid #D1D5DB',
            background: currentPageIndex <= 0 ? '#F3F4F6' : '#FFFFFF',
            cursor: currentPageIndex <= 0 ? 'not-allowed' : 'pointer',
            fontSize: 18,
          }}
        >
          &#8592;
        </button>

        {/* Page indicator */}
        <span style={{ fontSize: 14, color: '#4B5563' }}>
          Page {currentPageIndex + 1} of {pages.length}
        </span>

        {/* Next */}
        <button
          onClick={goNext}
          disabled={currentPageIndex >= pages.length - 1}
          aria-label="Next page"
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid #D1D5DB',
            background: currentPageIndex >= pages.length - 1 ? '#F3F4F6' : '#FFFFFF',
            cursor: currentPageIndex >= pages.length - 1 ? 'not-allowed' : 'pointer',
            fontSize: 18,
          }}
        >
          &#8594;
        </button>

        {/* Zoom toggle */}
        <button
          onClick={() => setZoomMode((m) => (m === 'fit' ? 'actual' : 'fit'))}
          aria-label={zoomMode === 'fit' ? 'Switch to actual size' : 'Switch to fit to screen'}
          style={{
            padding: '6px 14px',
            borderRadius: 6,
            border: '1px solid #D1D5DB',
            background: zoomMode === 'actual' ? '#DBEAFE' : '#FFFFFF',
            cursor: 'pointer',
            fontSize: 13,
            fontWeight: 500,
          }}
        >
          {zoomMode === 'fit' ? 'Actual Size' : 'Fit to Screen'}
        </button>
      </div>
    </div>
  );
};

export default DevicePreview;
