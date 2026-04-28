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
    <div className="app-dataset-form">
      <h1>Choose data type</h1>
      <br></br>
      <h3>Please choose the type of data you would like to publish.</h3>

      {/* Each label wraps its radio input — clicking the label also selects the radio */}
      {/* onChange fires every time a new radio is clicked, updating 'selected' via setSelected */}

      <label className="app-dataset-form__option">
        <input
          type="radio"
          name="filter"
          value="timetables"
          checked={selected === 'timetables'}           // true only when 'selected' equals 'all'
          onChange={() => setSelected('timetables')}    // updates state when this radio is clicked
        />
        Timetables
      </label>

      <label className="app-dataset-form__option">
        <input
          type="radio"
          name="filter"
          value="avl"
          checked={selected === 'avl'}
          onChange={() => setSelected('avl')}
        />
        Automatic Vehicle Location (AVL)
      </label>

      <label className="app-dataset-form__option">
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
      <button onClick={handleSubmit} className="app-dataset-form__button">
        Submit
      </button>

      {/* Shows which option is currently selected — useful for debugging */}
      <p className="app-dataset-form__selected">
        Currently selected: <strong>{selected}</strong>
      </p>
    </div>
  )
}
