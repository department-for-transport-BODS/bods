/* Choose data type page */
'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';

export default function FilterForm() {
  const [selected, setSelected] = useState('');
  const router = useRouter();

  function handleSubmit() {
    if (selected) {
      router.push(`/${selected}`); // navigates to e.g. /published
    }
  }

  return (
    <div style={{ fontFamily: 'sans-serif', maxWidth: '400px', margin: '60px auto' }}>
      <h1>Choose data type</h1>
      <br></br>
      <h3>Please choose the type of data you would like to publish.</h3>

      {/* Each label wraps its radio input — clicking the label also selects the radio */}
      {/* onChange fires every time a new radio is clicked, updating 'selected' via setSelected */}

      <label style={optionStyle}>
        <input
          type="radio"
          name="filter"
          value="timetables"
          checked={selected === 'atimetablesl'}           // true only when 'selected' equals 'all'
          onChange={() => setSelected('timetables')}    // updates state when this radio is clicked
        />
        Timetables
      </label>

      <label style={optionStyle}>
        <input
          type="radio"
          name="filter"
          value="avl"
          checked={selected === 'avl'}
          onChange={() => setSelected('avl')}
        />
        Automatic Vehicle Location (AVL)
      </label>

      <label style={optionStyle}>
        <input
          type="radio"
          name="filter"
          value="fares"
          checked={selected === 'fares'}
          onChange={() => setSelected('fares')}
        />
        Fares
      </label>

      {/* onClick calls handleSubmit, which uses router.push() to navigate */}
      <button onClick={handleSubmit} style={buttonStyle}>
        Submit
      </button>

      {/* Shows which option is currently selected — useful for debugging */}
      <p style={{ marginTop: '16px', color: '#555' }}>
        Currently selected: <strong>{selected}</strong>
      </p>
    </div>
  )
}

// Styles written as JS objects because we are in TSX, not a plain HTML/CSS file
// In TSX, the style prop takes an object: style={{ property: 'value' }}
const optionStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  gap: '10px',
  marginBottom: '12px',
  cursor: 'pointer',
  fontSize: '1rem',
}

const buttonStyle: React.CSSProperties = {
  marginTop: '16px',
  padding: '8px 20px',
  fontSize: '1rem',
  cursor: 'pointer',
}
