import React, { useState } from 'react';

// parameters
// customize appearance and scale
const GRID_UNITS = 50;
// pixels per 10mm unit
const CELL_PIXEL_SIZE = 15;

// color palette
const COLOR_BG = '#ffffff';
const COLOR_GRID_LINES = '#f0f0f0';
const COLOR_SELECTED = '#3498db';
const COLOR_SELECTED_OUTLINE = '#2980b9';

const UserInput = () => {
  // 1. form data storage
  const [items, setItems] = useState({
    pens: 0,
    standardSD: 0,
    microSD: 0,
  });

  // stores array of tray objects: { id, length, width, height }
  const [trays, setTrays] = useState([]);

  // 2. grid data storage
  const [selectedCoords, setSelectedCoords] = useState(new Set());
  const [isDragging, setIsDragging] = useState(false);
  const [dragMode, setDragMode] = useState(null);

  // prevent non-integer inputs (decimals, negative signs)
  const preventInvalidKeys = (e) => {
    if (['.', '-', 'e', 'E', '+'].includes(e.key)) {
      e.preventDefault();
    }
  };

  // handle simple item inputs with upper limits & positive integers
  const handleItemChange = (e) => {
    const { name, value } = e.target;

    // strip out any non-digit characters just in case
    const cleanValue = value.replace(/\D/g, '');
    let num = cleanValue === '' ? 0 : parseInt(cleanValue, 10);

    // enforce upper limits
    if (name === 'pens') num = Math.min(num, 25);
    if (name === 'standardSD') num = Math.min(num, 20);
    if (name === 'microSD') num = Math.min(num, 30);

    setItems((prev) => ({
      ...prev,
      [name]: num,
    }));
  };

  // handle tray count with upper limit (10)
  const handleTrayCountChange = (e) => {
    const cleanValue = e.target.value.replace(/\D/g, '');
    let count = cleanValue === '' ? 0 : parseInt(cleanValue, 10);
    count = Math.min(count, 10); // max 10 trays

    setTrays((prev) => {
      const newTrays = [...prev];
      if (count > prev.length) {
        // add new trays with default minimum values
        for (let i = prev.length; i < count; i++) {
          newTrays.push({
            id: Date.now() + i,
            length: 3,
            width: 3,
            height: 'short',
            divX: 0,
            divY: 0,
          });
        }
      } else {
        // remove extra trays
        newTrays.length = count;
      }
      return newTrays;
    });
  };

  // update specific tray dimension (only positive integers)
  const handleTrayDimChange = (index, field, value) => {
    setTrays((prev) => {
      const newTrays = [...prev];
      if (field === 'height') {
        newTrays[index][field] = value;
      } else {
        const cleanValue = value.replace(/\D/g, '');
        let num = cleanValue === '' ? 0 : parseInt(cleanValue, 10);
        // allow typing temporarily, strict enforcement on blur/export
        newTrays[index][field] = num;
      }
      return newTrays;
    });
  };

  // enforce min/max tray size and dynamic divider limits on blur
  const handleTrayDimBlur = (index, field, value) => {
    setTrays((prev) => {
      const newTrays = [...prev];
      let num = parseInt(value, 10) || 0;

      // length and width limits
      if (field === 'length' || field === 'width') {
        if (num < 3) num = 3;
        if (num > 20) num = 20;

        // ensure existing sections don't exceed the new smaller size.
        if (field === 'length' && newTrays[index].divX > num) {
          newTrays[index].divX = num;
        }
        if (field === 'width' && newTrays[index].divY > num) {
          newTrays[index].divY = num;
        }
      }
      // div limit
      else if (field === 'divX') {
        if (num < 0) num = 0;
        if (num > newTrays[index].length) num = newTrays[index].length;
      }
      else if (field === 'divY') {
        if (num < 0) num = 0;
        if (num > newTrays[index].width) num = newTrays[index].width;
      }

      newTrays[index][field] = num;
      return newTrays;
    });
  };

  // grid interaction logic
  const handleMouseDown = (row, col, e) => {
    setIsDragging(true);
    const mode = e.shiftKey ? 'remove' : 'add';
    setDragMode(mode);
    toggleCell(row, col, mode);
  };

  const handleMouseEnter = (row, col) => {
    if (isDragging && dragMode) toggleCell(row, col, dragMode);
  };

  const handleMouseUp = () => {
    setIsDragging(false);
    setDragMode(null);
  };

  const toggleCell = (row, col, mode) => {
    if (row >= 0 && row < GRID_UNITS && col >= 0 && col < GRID_UNITS) {
      const coordKey = `${row},${col}`;
      setSelectedCoords((prev) => {
        const next = new Set(prev);
        mode === 'add' ? next.add(coordKey) : next.delete(coordKey);
        return next;
      });
    }
  };

  const resetAll = () => {
    if (window.confirm('clear all inputs and selection?')) {
      setSelectedCoords(new Set());
      setItems({ pens: 0, standardSD: 0, microSD: 0 });
      setTrays([]);
    }
  };

// packages everything for the backend API
  const exportData = async () => {
    const coordList = Array.from(selectedCoords)
        .map((str) => str.split(',').map(Number))
        .sort((a, b) => a[0] - b[0] || a[1] - b[1]);

    const payload = {
      items: items,
      trays: trays.map(({ length, width, height, divX, divY }) => ({
        length: Math.max(3, length),
        width: Math.max(3, width),
        height,
        divX: Math.max(0, divX || 0),
        divY: Math.max(0, divY || 0)
      })),
      availableSpace: coordList
    };

    // backend fetch request
    try {
      const response = await fetch('http://localhost:8000/api/generate-organizer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(payload),
      });

      if (response.ok) {
        alert('success sent to backend');
      } else {
        alert('alert: backend error');
      }
    } catch (error) {
      console.error(error);
      alert('alert: could not connect to the backend');
    }

    return payload;
  };

  const gridStyle = {
    display: 'grid',
    gridTemplateColumns: `repeat(${GRID_UNITS}, ${CELL_PIXEL_SIZE}px)`,
    gridTemplateRows: `repeat(${GRID_UNITS}, ${CELL_PIXEL_SIZE}px)`,
    gap: '1px',
    backgroundColor: COLOR_GRID_LINES,
    border: `1px solid ${COLOR_GRID_LINES}`,
    width: 'fit-content',
    margin: '0 auto',
    userSelect: 'none',
    touchAction: 'none',
  };

  const inputStyle = { width: '50px', marginLeft: '10px', padding: '4px' };

  return (
      <div
          style={{
            padding: '20px',
            fontFamily: 'sans-serif',
            maxWidth: '900px',
            margin: '0 auto',
          }}
          onMouseUp={handleMouseUp}
          onMouseLeave={handleMouseUp}
      >
        <h2 style={{ textAlign: 'center', marginBottom: '30px' }}>
          Desk Organizer User Input
        </h2>

        <div
            style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '20px',
              marginBottom: '30px',
            }}
        >
          {/* 1. items section */}
          <div
              style={{
                flex: 1,
                backgroundColor: '#f8f9fa',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #ddd',
              }}
          >
            <h3 style={{ marginTop: 0, fontSize: '18px' }}>Item Quantities</h3>
            <div
                style={{ display: 'flex', flexDirection: 'column', gap: '15px' }}
            >
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                Pens (max 25):
                <input
                    type="number"
                    name="pens"
                    min="0"
                    max="25"
                    onKeyDown={preventInvalidKeys}
                    value={items.pens === 0 ? '' : items.pens}
                    placeholder="0"
                    onChange={handleItemChange}
                    style={inputStyle}
                />
              </label>
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                Standard SD (max 20):
                <input
                    type="number"
                    name="standardSD"
                    min="0"
                    max="20"
                    onKeyDown={preventInvalidKeys}
                    value={items.standardSD === 0 ? '' : items.standardSD}
                    placeholder="0"
                    onChange={handleItemChange}
                    style={inputStyle}
                />
              </label>
              <label style={{ display: 'flex', justifyContent: 'space-between' }}>
                MicroSD (max 30):
                <input
                    type="number"
                    name="microSD"
                    min="0"
                    max="30"
                    onKeyDown={preventInvalidKeys}
                    value={items.microSD === 0 ? '' : items.microSD}
                    placeholder="0"
                    onChange={handleItemChange}
                    style={inputStyle}
                />
              </label>
            </div>
          </div>

          {/* 2. trays section */}
          <div
              style={{
                flex: 1,
                backgroundColor: '#e9ecef',
                padding: '20px',
                borderRadius: '8px',
                border: '1px solid #ced4da',
              }}
          >
            <h3 style={{ marginTop: 0, fontSize: '18px' }}>Storage Trays</h3>
            <label
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                }}
            >
              Number of Trays (max 10):
              <input
                  type="number"
                  min="0"
                  max="10"
                  onKeyDown={preventInvalidKeys}
                  value={trays.length === 0 ? '' : trays.length}
                  placeholder="0"
                  onChange={handleTrayCountChange}
                  style={inputStyle}
              />
            </label>
          </div>
        </div>

        {/* dynamic tray dimensions section */}
        {trays.length > 0 && (
            <div
                style={{
                  marginBottom: '30px',
                  padding: '20px',
                  border: '1px dashed #bbb',
                  borderRadius: '8px',
                }}
            >
              <h4 style={{ marginTop: 0 }}>Tray Dimensions & Dividers</h4>
              <div
                  style={{
                    display: 'grid',
                    gridTemplateColumns: 'repeat(auto-fill, minmax(350px, 1fr))',
                    gap: '15px',
                  }}
              >
                {trays.map((tray, index) => (
                    <div
                        key={tray.id}
                        style={{
                          padding: '15px',
                          backgroundColor: '#fff',
                          border: '1px solid #eee',
                          borderRadius: '6px',
                          display: 'flex',
                          flexDirection: 'column',
                          gap: '12px',
                        }}
                    >
                      {/* Header & Height Row */}
                      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <strong>Tray {index + 1}</strong>
                        <select
                            value={tray.height}
                            onChange={(e) =>
                                handleTrayDimChange(index, 'height', e.target.value)
                            }
                            style={{ padding: '4px', cursor: 'pointer' }}
                        >
                          <option value="short">Short (30mm)</option>
                          <option value="high">High (80mm)</option>
                        </select>
                      </div>

                      {/* Length Binding Group */}
                      <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            backgroundColor: '#f8f9fa',
                            padding: '10px',
                            borderRadius: '4px',
                            border: '1px solid #e9ecef'
                          }}
                      >
                        <label style={{ display: 'flex', alignItems: 'center', fontWeight: '500' }}>
                          Length:{' '}
                          <input
                              type="number"
                              min="3"
                              max="20"
                              onKeyDown={preventInvalidKeys}
                              value={tray.length === 0 ? '' : tray.length}
                              onChange={(e) =>
                                  handleTrayDimChange(index, 'length', e.target.value)
                              }
                              onBlur={(e) =>
                                  handleTrayDimBlur(index, 'length', e.target.value)
                              }
                              style={{ width: '40px', padding: '4px', margin: '0 5px' }}
                          />{' '}
                          cm
                        </label>
                        <label style={{ fontSize: '14px', color: '#495057' }}>
                          Length Sections:{' '}
                          <input
                              type="number"
                              min="0"
                              max={tray.length}
                              onKeyDown={preventInvalidKeys}
                              value={tray.divX === 0 ? '' : tray.divX}
                              onChange={(e) =>
                                  handleTrayDimChange(index, 'divX', e.target.value)
                              }
                              onBlur={(e) =>
                                  handleTrayDimBlur(index, 'divX', e.target.value)
                              }
                              style={{ width: '40px', padding: '4px', marginLeft: '5px' }}
                          />
                        </label>
                      </div>

                      {/* Width Binding Group */}
                      <div
                          style={{
                            display: 'flex',
                            justifyContent: 'space-between',
                            alignItems: 'center',
                            backgroundColor: '#f8f9fa',
                            padding: '10px',
                            borderRadius: '4px',
                            border: '1px solid #e9ecef'
                          }}
                      >
                        <label style={{ display: 'flex', alignItems: 'center', fontWeight: '500' }}>
                          Width:{' '}
                          <input
                              type="number"
                              min="3"
                              max="20"
                              onKeyDown={preventInvalidKeys}
                              value={tray.width === 0 ? '' : tray.width}
                              onChange={(e) =>
                                  handleTrayDimChange(index, 'width', e.target.value)
                              }
                              onBlur={(e) =>
                                  handleTrayDimBlur(index, 'width', e.target.value)
                              }
                              style={{ width: '40px', padding: '4px', margin: '0 5px' }}
                          />{' '}
                          cm
                        </label>
                        <label style={{ fontSize: '14px', color: '#495057' }}>
                          Width Sections:{' '}
                          <input
                              type="number"
                              min="0"
                              max={tray.width}
                              onKeyDown={preventInvalidKeys}
                              value={tray.divY === 0 ? '' : tray.divY}
                              onChange={(e) =>
                                  handleTrayDimChange(index, 'divY', e.target.value)
                              }
                              onBlur={(e) =>
                                  handleTrayDimBlur(index, 'divY', e.target.value)
                              }
                              style={{ width: '40px', padding: '4px', marginLeft: '5px' }}
                          />
                        </label>
                      </div>
                    </div>
                ))}
              </div>
            </div>
        )}

        {/* 3. grid section */}
        <h3 style={{ textAlign: 'center' }}>Available Space (10mm grid)</h3>
        <div style={gridStyle}>
          {Array.from({ length: GRID_UNITS * GRID_UNITS }).map((_, index) => {
            const row = Math.floor(index / GRID_UNITS);
            const col = index % GRID_UNITS;
            const isSelected = selectedCoords.has(`${row},${col}`);

            return (
                <div
                    key={`${row}-${col}`}
                    onMouseDown={(e) => handleMouseDown(row, col, e)}
                    onMouseEnter={() => handleMouseEnter(row, col)}
                    style={{
                      width: CELL_PIXEL_SIZE,
                      height: CELL_PIXEL_SIZE,
                      backgroundColor: isSelected ? COLOR_SELECTED : COLOR_BG,
                      boxSizing: 'border-box',
                      border: isSelected
                          ? `1px solid ${COLOR_SELECTED_OUTLINE}`
                          : 'none',
                      cursor: 'crosshair',
                    }}
                />
            );
          })}
        </div>

        {/* 4. controls */}
        <div
            style={{
              display: 'flex',
              justifyContent: 'center',
              gap: '40px',
              marginTop: '20px',
            }}
        >
          <button
              onClick={resetAll}
              style={{ width: '120px', padding: '8px', cursor: 'pointer' }}
          >
            clear all
          </button>
          <button
              onClick={exportData}
              style={{
                width: '200px',
                padding: '8px',
                cursor: 'pointer',
              }}
          >
            export to backend
          </button>
        </div>
        <p
            style={{
              textAlign: 'center',
              color: '#666',
              fontSize: '14px',
              marginTop: '15px',
            }}
        >
          click to select | shift + click to remove
        </p>
      </div>
  );
};

export default UserInput;