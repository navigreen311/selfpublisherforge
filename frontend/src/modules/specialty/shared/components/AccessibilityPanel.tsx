import React, { useState, useCallback } from 'react';

// ---------------------------------------------------------------------------
// Types
// ---------------------------------------------------------------------------

type VariantType = 'dyslexia_friendly' | 'large_print' | 'high_contrast';

interface VariantConfig {
  type: VariantType;
  title: string;
  description: string;
  settingsSummary: string[];
  beforePreview: React.CSSProperties;
  afterPreview: React.CSSProperties;
  beforeLabel: string;
  afterLabel: string;
}

interface GeneratedVariant {
  id: string;
  type: VariantType;
  title: string;
  createdAt: string;
  downloadUrl?: string;
  pageCount: number;
  status: 'generating' | 'ready' | 'error';
}

interface AccessibilityPanelProps {
  /** Book ID to generate variants for. */
  bookId: string;
  /** Book type (childrens, coloring, puzzle). */
  bookType: string;
  /** Callback when a variant generation is requested. */
  onGenerateVariant?: (bookId: string, variantType: VariantType) => Promise<GeneratedVariant>;
  /** Callback when a variant download is requested. */
  onDownloadVariant?: (variantId: string) => void;
  /** Pre-existing generated variants to display. */
  existingVariants?: GeneratedVariant[];
  className?: string;
}

// ---------------------------------------------------------------------------
// Variant configurations
// ---------------------------------------------------------------------------

const VARIANT_CONFIGS: VariantConfig[] = [
  {
    type: 'dyslexia_friendly',
    title: 'Dyslexia-Friendly',
    description:
      'Optimised for readers with dyslexia using specialised font, increased spacing, and a warm off-white background to reduce visual stress.',
    settingsSummary: [
      'OpenDyslexic font',
      '1.5x line spacing',
      '+15% letter spacing',
      'Left-aligned text',
      'Off-white background (#FFFDF5)',
      'No italics or all-caps',
    ],
    beforePreview: {
      fontFamily: 'serif',
      fontSize: 13,
      lineHeight: 1.2,
      textAlign: 'justify' as const,
      color: '#000',
      background: '#FFF',
      padding: 12,
      borderRadius: 6,
    },
    afterPreview: {
      fontFamily: 'OpenDyslexic, Comic Sans MS, sans-serif',
      fontSize: 13,
      lineHeight: 1.8,
      letterSpacing: '0.15em',
      textAlign: 'left' as const,
      color: '#333333',
      background: '#FFFDF5',
      padding: 12,
      borderRadius: 6,
    },
    beforeLabel: 'Standard',
    afterLabel: 'Dyslexia-Friendly',
  },
  {
    type: 'large_print',
    title: 'Large Print',
    description:
      'Meets APH (American Printing House) guidelines with 18pt minimum body text, WCAG AAA contrast, and generous margins.',
    settingsSummary: [
      '18pt body text minimum',
      '24pt heading minimum',
      '7:1 contrast ratio (WCAG AAA)',
      'APH-compliant font',
      '1.4x line spacing',
      '0.75in minimum margins',
    ],
    beforePreview: {
      fontFamily: 'serif',
      fontSize: 11,
      lineHeight: 1.2,
      color: '#555',
      background: '#F5F5F0',
      padding: 12,
      borderRadius: 6,
    },
    afterPreview: {
      fontFamily: 'Verdana, sans-serif',
      fontSize: 16,
      lineHeight: 1.5,
      color: '#000000',
      background: '#FFFFFF',
      padding: 16,
      borderRadius: 6,
      fontWeight: 500,
    },
    beforeLabel: 'Standard (12pt)',
    afterLabel: 'Large Print (18pt+)',
  },
  {
    type: 'high_contrast',
    title: 'High Contrast',
    description:
      'Pure black-on-white rendering with bold numbers and instructions, thicker grid lines, and no decorative elements.',
    settingsSummary: [
      'Pure black on white',
      '2px minimum grid lines',
      'Bold numbers and instructions',
      'Decorative elements removed',
      '3px borders',
      'Maximum contrast ratio',
    ],
    beforePreview: {
      fontFamily: 'sans-serif',
      fontSize: 13,
      color: '#666',
      background: '#F0EDE8',
      padding: 12,
      borderRadius: 6,
      border: '1px solid #DDD',
    },
    afterPreview: {
      fontFamily: 'sans-serif',
      fontSize: 13,
      color: '#000000',
      background: '#FFFFFF',
      padding: 12,
      borderRadius: 6,
      border: '3px solid #000000',
      fontWeight: 700,
    },
    beforeLabel: 'Standard',
    afterLabel: 'High Contrast',
  },
];

const SAMPLE_TEXT = 'The quick brown fox jumps over the lazy dog. Pack my box with five dozen liquor jugs.';

// ---------------------------------------------------------------------------
// Sub-components
// ---------------------------------------------------------------------------

interface VariantCardProps {
  config: VariantConfig;
  isGenerating: boolean;
  onGenerate: () => void;
}

const VariantCard: React.FC<VariantCardProps> = ({ config, isGenerating, onGenerate }) => {
  return (
    <div
      style={{
        border: '1px solid #E5E7EB',
        borderRadius: 12,
        padding: 20,
        background: '#FFFFFF',
        display: 'flex',
        flexDirection: 'column',
        gap: 14,
      }}
    >
      {/* Title + description */}
      <div>
        <h3 style={{ margin: 0, fontSize: 17, fontWeight: 600, color: '#1F2937' }}>
          {config.title}
        </h3>
        <p style={{ margin: '6px 0 0', fontSize: 13, color: '#6B7280', lineHeight: 1.5 }}>
          {config.description}
        </p>
      </div>

      {/* Before / After preview */}
      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#9CA3AF', marginBottom: 4 }}>
            {config.beforeLabel}
          </div>
          <div style={config.beforePreview}>{SAMPLE_TEXT}</div>
        </div>
        <div>
          <div style={{ fontSize: 11, fontWeight: 600, color: '#3B82F6', marginBottom: 4 }}>
            {config.afterLabel}
          </div>
          <div style={config.afterPreview}>{SAMPLE_TEXT}</div>
        </div>
      </div>

      {/* Settings summary */}
      <div>
        <div style={{ fontSize: 12, fontWeight: 600, color: '#4B5563', marginBottom: 4 }}>
          Settings
        </div>
        <ul style={{ margin: 0, padding: '0 0 0 18px', fontSize: 12, color: '#6B7280' }}>
          {config.settingsSummary.map((s, i) => (
            <li key={i} style={{ marginBottom: 2 }}>
              {s}
            </li>
          ))}
        </ul>
      </div>

      {/* Generate button */}
      <button
        onClick={onGenerate}
        disabled={isGenerating}
        style={{
          padding: '10px 20px',
          borderRadius: 8,
          border: 'none',
          background: isGenerating ? '#9CA3AF' : '#3B82F6',
          color: '#FFFFFF',
          fontSize: 14,
          fontWeight: 600,
          cursor: isGenerating ? 'not-allowed' : 'pointer',
          alignSelf: 'flex-start',
          transition: 'background 0.15s',
        }}
        aria-label={`Generate ${config.title} variant`}
      >
        {isGenerating ? 'Generating...' : 'Generate Variant'}
      </button>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Main component
// ---------------------------------------------------------------------------

const AccessibilityPanel: React.FC<AccessibilityPanelProps> = ({
  bookId,
  bookType,
  onGenerateVariant,
  onDownloadVariant,
  existingVariants: initialVariants = [],
  className,
}) => {
  const [generatingTypes, setGeneratingTypes] = useState<Set<VariantType>>(new Set());
  const [variants, setVariants] = useState<GeneratedVariant[]>(initialVariants);

  const handleGenerate = useCallback(
    async (variantType: VariantType) => {
      if (!onGenerateVariant) return;

      setGeneratingTypes((prev) => new Set(prev).add(variantType));

      try {
        const result = await onGenerateVariant(bookId, variantType);
        setVariants((prev) => [result, ...prev]);
      } catch {
        // Error handling -- the caller's onGenerateVariant should handle
        // toast / notification; we just stop the spinner.
      } finally {
        setGeneratingTypes((prev) => {
          const next = new Set(prev);
          next.delete(variantType);
          return next;
        });
      }
    },
    [bookId, onGenerateVariant],
  );

  const variantLabel = (type: VariantType): string => {
    switch (type) {
      case 'dyslexia_friendly':
        return 'Dyslexia-Friendly';
      case 'large_print':
        return 'Large Print';
      case 'high_contrast':
        return 'High Contrast';
      default:
        return type;
    }
  };

  return (
    <div className={className} style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700, color: '#111827' }}>
          Accessibility Variants
        </h2>
        <p style={{ margin: '4px 0 0', fontSize: 14, color: '#6B7280' }}>
          Generate accessible editions of your book to reach more readers and meet accessibility
          standards.
        </p>
      </div>

      {/* Variant cards */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>
        {VARIANT_CONFIGS.map((config) => (
          <VariantCard
            key={config.type}
            config={config}
            isGenerating={generatingTypes.has(config.type)}
            onGenerate={() => handleGenerate(config.type)}
          />
        ))}
      </div>

      {/* Generated variants list */}
      {variants.length > 0 && (
        <div>
          <h3 style={{ margin: '0 0 12px', fontSize: 16, fontWeight: 600, color: '#1F2937' }}>
            Generated Variants
          </h3>
          <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: 8,
              border: '1px solid #E5E7EB',
              borderRadius: 8,
              overflow: 'hidden',
            }}
          >
            {variants.map((v) => (
              <div
                key={v.id}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'space-between',
                  padding: '12px 16px',
                  borderBottom: '1px solid #F3F4F6',
                  background: '#FFFFFF',
                }}
              >
                <div style={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <span style={{ fontSize: 14, fontWeight: 500, color: '#1F2937' }}>
                    {v.title || variantLabel(v.type)}
                  </span>
                  <span style={{ fontSize: 12, color: '#9CA3AF' }}>
                    {v.pageCount} pages &middot; {v.createdAt}
                  </span>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
                  {/* Status badge */}
                  <span
                    style={{
                      fontSize: 11,
                      fontWeight: 600,
                      padding: '3px 8px',
                      borderRadius: 10,
                      background:
                        v.status === 'ready'
                          ? '#D1FAE5'
                          : v.status === 'generating'
                            ? '#FEF3C7'
                            : '#FEE2E2',
                      color:
                        v.status === 'ready'
                          ? '#065F46'
                          : v.status === 'generating'
                            ? '#92400E'
                            : '#991B1B',
                    }}
                  >
                    {v.status === 'ready'
                      ? 'Ready'
                      : v.status === 'generating'
                        ? 'Generating'
                        : 'Error'}
                  </span>

                  {/* Download button */}
                  {v.status === 'ready' && v.downloadUrl && (
                    <button
                      onClick={() => onDownloadVariant?.(v.id)}
                      style={{
                        padding: '5px 12px',
                        borderRadius: 6,
                        border: '1px solid #D1D5DB',
                        background: '#FFFFFF',
                        cursor: 'pointer',
                        fontSize: 12,
                        fontWeight: 500,
                        color: '#374151',
                      }}
                      aria-label={`Download ${variantLabel(v.type)} variant`}
                    >
                      Download
                    </button>
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
};

export default AccessibilityPanel;
