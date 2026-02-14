import React, { useState, useEffect } from 'react';
import { Canvas, FabricObject, Shadow } from 'fabric';

interface PropertiesPanelProps {
  canvas: Canvas | null;
  selectedObject: FabricObject | null;
}

const BOOK_FONTS = [
  'Playfair Display', 'Merriweather', 'Lora', 'Oswald', 'Montserrat', 'Roboto', 'Raleway',
  'Open Sans', 'Noto Serif', 'PT Serif', 'Crimson Text', 'Libre Baskerville', 'EB Garamond',
  'Georgia', 'Times New Roman', 'Cormorant Garamond', 'Bitter', 'Arvo', 'Slabo 27px',
  'Vollkorn', 'Alegreya', 'Spectral', 'Cardo', 'Libre Franklin', 'Work Sans', 'Poppins',
  'Inter', 'Rubik', 'Nunito', 'Karla', 'Source Sans Pro', 'Fira Sans', 'Cabin',
  'Quicksand', 'Barlow', 'Josefin Sans', 'Bebas Neue', 'Anton', 'Righteous', 'Cinzel',
];

export const PropertiesPanel: React.FC<PropertiesPanelProps> = ({ canvas, selectedObject }) => {
  const [properties, setProperties] = useState<any>({});
  const [showShadow, setShowShadow] = useState(false);
  const [showStroke, setShowStroke] = useState(false);

  const isTextObject = selectedObject?.type === 'i-text' || selectedObject?.type === 'text' || selectedObject?.type === 'textbox';

  useEffect(() => {
    if (selectedObject) {
      const obj = selectedObject as any;
      setProperties({
        left: Math.round(obj.left || 0),
        top: Math.round(obj.top || 0),
        width: Math.round(obj.width * (obj.scaleX || 1)),
        height: Math.round(obj.height * (obj.scaleY || 1)),
        opacity: (obj.opacity || 1) * 100,
        fontFamily: obj.fontFamily || 'Arial',
        fontSize: obj.fontSize || 16,
        fill: obj.fill || '#000000',
        fontWeight: obj.fontWeight || 'normal',
        fontStyle: obj.fontStyle || 'normal',
        textAlign: obj.textAlign || 'left',
        charSpacing: obj.charSpacing || 0,
        lineHeight: obj.lineHeight || 1.16,
        shadowColor: obj.shadow?.color || '#000000',
        shadowOffsetX: obj.shadow?.offsetX || 0,
        shadowOffsetY: obj.shadow?.offsetY || 0,
        shadowBlur: obj.shadow?.blur || 0,
        stroke: obj.stroke || '#000000',
        strokeWidth: obj.strokeWidth || 0,
      });
      setShowShadow(!!obj.shadow);
      setShowStroke(!!(obj.stroke && obj.strokeWidth > 0));
    }
  }, [selectedObject]);

  const updateProperty = (key: string, value: any) => {
    if (!selectedObject || !canvas) return;
    const obj = selectedObject as any;
    if (key === 'width') {
      obj.set('scaleX', value / obj.width);
    } else if (key === 'height') {
      obj.set('scaleY', value / obj.height);
    } else if (key === 'opacity') {
      obj.set('opacity', value / 100);
    } else {
      obj.set(key, value);
    }
    setProperties({ ...properties, [key]: value });
    canvas.renderAll();
  };

  const toggleShadow = () => {
    if (!selectedObject || !canvas) return;
    const obj = selectedObject as any;
    const newShowShadow = !showShadow;
    setShowShadow(newShowShadow);
    if (newShowShadow) {
      obj.set('shadow', new Shadow({
        color: properties.shadowColor || '#000000',
        offsetX: properties.shadowOffsetX || 5,
        offsetY: properties.shadowOffsetY || 5,
        blur: properties.shadowBlur || 10,
      }));
    } else {
      obj.set('shadow', null);
    }
    canvas.renderAll();
  };

  const updateShadow = (key: string, value: any) => {
    if (!selectedObject || !canvas) return;
    const obj = selectedObject as any;
    const shadow = obj.shadow || new Shadow({ color: '#000000', offsetX: 0, offsetY: 0, blur: 0 });
    shadow[key] = value;
    obj.set('shadow', shadow);
    const propKey = 'shadow' + key.charAt(0).toUpperCase() + key.slice(1);
    setProperties({ ...properties, [propKey]: value });
    canvas.renderAll();
  };

  const toggleStroke = () => {
    if (!selectedObject || !canvas) return;
    const obj = selectedObject as any;
    const newShowStroke = !showStroke;
    setShowStroke(newShowStroke);
    if (newShowStroke) {
      obj.set('stroke', properties.stroke || '#000000');
      obj.set('strokeWidth', properties.strokeWidth || 2);
    } else {
      obj.set('stroke', '');
      obj.set('strokeWidth', 0);
    }
    canvas.renderAll();
  };

  const deleteElement = () => {
    if (!selectedObject || !canvas) return;
    canvas.remove(selectedObject);
    canvas.discardActiveObject();
    canvas.renderAll();
  };

  if (!selectedObject) {
    return (
      <div className="w-80 bg-white border-l border-gray-200 p-6 flex items-center justify-center">
        <p className="text-gray-500 text-center">
          Select an element on the canvas to edit its properties
        </p>
      </div>
    );
  }

  return (
    <div className="w-80 bg-white border-l border-gray-200 overflow-y-auto">
      <div className="p-6 space-y-6">
        {isTextObject && (
          <>
            <div>
              <h3 className="text-sm font-semibold text-gray-900 mb-4">Text Properties</h3>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Font Family</label>
                <select
                  value={properties.fontFamily}
                  onChange={(e) => updateProperty('fontFamily', e.target.value)}
                  className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 focus:border-blue-500 text-sm"
                >
                  {BOOK_FONTS.map((font) => (
                    <option key={font} value={font}>{font}</option>
                  ))}
                </select>
              </div>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Font Size: {properties.fontSize}pt</label>
                <div className="flex gap-2">
                  <input type="range" min="8" max="120" value={properties.fontSize} onChange={(e) => updateProperty('fontSize', parseInt(e.target.value))} className="flex-1" />
                  <input type="number" min="8" max="120" value={properties.fontSize} onChange={(e) => updateProperty('fontSize', parseInt(e.target.value))} className="w-16 px-2 py-1 border border-gray-300 rounded text-sm" />
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Color</label>
                <div className="flex gap-2">
                  <input type="color" value={properties.fill} onChange={(e) => updateProperty('fill', e.target.value)} className="w-12 h-10 rounded border border-gray-300 cursor-pointer" />
                  <input type="text" value={properties.fill} onChange={(e) => updateProperty('fill', e.target.value)} className="flex-1 px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" placeholder="#000000" />
                </div>
              </div>
              <div className="mb-4 grid grid-cols-2 gap-2">
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Weight</label>
                  <select value={properties.fontWeight} onChange={(e) => updateProperty('fontWeight', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                    <option value="normal">Regular</option>
                    <option value="bold">Bold</option>
                  </select>
                </div>
                <div>
                  <label className="block text-xs font-medium text-gray-700 mb-1">Style</label>
                  <select value={properties.fontStyle} onChange={(e) => updateProperty('fontStyle', e.target.value)} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm">
                    <option value="normal">Normal</option>
                    <option value="italic">Italic</option>
                  </select>
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Alignment</label>
                <div className="flex gap-2">
                  <button onClick={() => updateProperty('textAlign', 'left')} className={'flex-1 px-3 py-2 border rounded-md text-sm font-medium ' + (properties.textAlign === 'left' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50')}>Left</button>
                  <button onClick={() => updateProperty('textAlign', 'center')} className={'flex-1 px-3 py-2 border rounded-md text-sm font-medium ' + (properties.textAlign === 'center' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50')}>Center</button>
                  <button onClick={() => updateProperty('textAlign', 'right')} className={'flex-1 px-3 py-2 border rounded-md text-sm font-medium ' + (properties.textAlign === 'right' ? 'bg-blue-500 text-white border-blue-500' : 'bg-white text-gray-700 border-gray-300 hover:bg-gray-50')}>Right</button>
                </div>
              </div>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Letter Spacing: {properties.charSpacing}px</label>
                <input type="range" min="-5" max="20" step="0.1" value={properties.charSpacing} onChange={(e) => updateProperty('charSpacing', parseFloat(e.target.value))} className="w-full" />
              </div>
              <div className="mb-4">
                <label className="block text-xs font-medium text-gray-700 mb-1">Line Height: {properties.lineHeight ? properties.lineHeight.toFixed(2) : '1.16'}</label>
                <input type="range" min="1.0" max="3.0" step="0.05" value={properties.lineHeight} onChange={(e) => updateProperty('lineHeight', parseFloat(e.target.value))} className="w-full" />
              </div>
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-700">Drop Shadow</label>
                  <button onClick={toggleShadow} className={'px-3 py-1 rounded text-xs font-medium ' + (showShadow ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700')}>{showShadow ? 'ON' : 'OFF'}</button>
                </div>
                {showShadow && (
                  <div className="space-y-3 pl-3 border-l-2 border-gray-200">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Color</label>
                      <div className="flex gap-2">
                        <input type="color" value={properties.shadowColor} onChange={(e) => updateShadow('color', e.target.value)} className="w-10 h-8 rounded border border-gray-300 cursor-pointer" />
                        <input type="text" value={properties.shadowColor} onChange={(e) => updateShadow('color', e.target.value)} className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Offset X: {properties.shadowOffsetX}px</label>
                      <input type="range" min="-50" max="50" value={properties.shadowOffsetX} onChange={(e) => updateShadow('offsetX', parseInt(e.target.value))} className="w-full" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Offset Y: {properties.shadowOffsetY}px</label>
                      <input type="range" min="-50" max="50" value={properties.shadowOffsetY} onChange={(e) => updateShadow('offsetY', parseInt(e.target.value))} className="w-full" />
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Blur: {properties.shadowBlur}px</label>
                      <input type="range" min="0" max="50" value={properties.shadowBlur} onChange={(e) => updateShadow('blur', parseInt(e.target.value))} className="w-full" />
                    </div>
                  </div>
                )}
              </div>
              <div className="mb-4">
                <div className="flex items-center justify-between mb-2">
                  <label className="text-xs font-medium text-gray-700">Text Outline</label>
                  <button onClick={toggleStroke} className={'px-3 py-1 rounded text-xs font-medium ' + (showStroke ? 'bg-blue-500 text-white' : 'bg-gray-200 text-gray-700')}>{showStroke ? 'ON' : 'OFF'}</button>
                </div>
                {showStroke && (
                  <div className="space-y-3 pl-3 border-l-2 border-gray-200">
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Color</label>
                      <div className="flex gap-2">
                        <input type="color" value={properties.stroke} onChange={(e) => updateProperty('stroke', e.target.value)} className="w-10 h-8 rounded border border-gray-300 cursor-pointer" />
                        <input type="text" value={properties.stroke} onChange={(e) => updateProperty('stroke', e.target.value)} className="flex-1 px-2 py-1 border border-gray-300 rounded text-sm" />
                      </div>
                    </div>
                    <div>
                      <label className="block text-xs text-gray-600 mb-1">Width: {properties.strokeWidth}px</label>
                      <input type="range" min="1" max="10" value={properties.strokeWidth} onChange={(e) => updateProperty('strokeWidth', parseInt(e.target.value))} className="w-full" />
                    </div>
                  </div>
                )}
              </div>
            </div>
            <hr className="border-gray-200" />
          </>
        )}
        <div>
          <h3 className="text-sm font-semibold text-gray-900 mb-4">Position & Size</h3>
          <div className="grid grid-cols-2 gap-3 mb-3">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">X Position</label>
              <input type="number" value={properties.left} onChange={(e) => updateProperty('left', parseInt(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Y Position</label>
              <input type="number" value={properties.top} onChange={(e) => updateProperty('top', parseInt(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
            </div>
          </div>
          <div className="grid grid-cols-2 gap-3 mb-4">
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Width</label>
              <input type="number" value={properties.width} onChange={(e) => updateProperty('width', parseInt(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
            </div>
            <div>
              <label className="block text-xs font-medium text-gray-700 mb-1">Height</label>
              <input type="number" value={properties.height} onChange={(e) => updateProperty('height', parseInt(e.target.value))} className="w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-2 focus:ring-blue-500 text-sm" />
            </div>
          </div>
          <div className="mb-4">
            <label className="block text-xs font-medium text-gray-700 mb-1">Opacity: {Math.round(properties.opacity)}%</label>
            <input type="range" min="0" max="100" value={properties.opacity} onChange={(e) => updateProperty('opacity', parseInt(e.target.value))} className="w-full" />
          </div>
        </div>
        <hr className="border-gray-200" />
        <div>
          <button onClick={deleteElement} className="w-full px-4 py-2 bg-red-500 text-white rounded-md hover:bg-red-600 focus:outline-none focus:ring-2 focus:ring-red-500 focus:ring-offset-2 font-medium text-sm">Delete Element</button>
        </div>
      </div>
    </div>
  );
};
