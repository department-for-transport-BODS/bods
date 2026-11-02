'use client';

import { useEffect, useRef, useState, type FormEvent, type KeyboardEvent } from 'react';

interface BrowseSearchBannerProps {
  title: string;
  description: string;
  searchValue: string;
  placeholder: string;
  onSearchChange: (value: string) => void;
  /** Receives the chosen suggestion when one was clicked, otherwise nothing. */
  onSearchSubmit: (value?: string) => void;
  /**
   * Terms for prefix autocomplete (Django's `BODSFrontend.AutoCompleteSearch`):
   * from two typed characters, case-insensitive prefix matches are listed.
   */
  suggestions?: string[];
}

const MIN_AUTOCOMPLETE_LENGTH = 2;

export function BrowseSearchBanner({
  title,
  description,
  searchValue,
  placeholder,
  onSearchChange,
  onSearchSubmit,
  suggestions,
}: BrowseSearchBannerProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const [isListOpen, setIsListOpen] = useState(false);
  const [activeIndex, setActiveIndex] = useState(-1);

  const matches =
    suggestions && isListOpen && searchValue.length >= MIN_AUTOCOMPLETE_LENGTH
      ? suggestions.filter((term) => term.slice(0, searchValue.length).toUpperCase() === searchValue.toUpperCase())
      : [];

  useEffect(() => {
    if (!suggestions) return undefined;
    const closeOnOutsideClick = (event: MouseEvent) => {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsListOpen(false);
        setActiveIndex(-1);
      }
    };
    document.addEventListener('click', closeOnOutsideClick);
    return () => document.removeEventListener('click', closeOnOutsideClick);
  }, [suggestions]);

  const handleSubmit = (event: FormEvent) => {
    event.preventDefault();
    onSearchSubmit();
  };

  const chooseSuggestion = (term: string) => {
    onSearchChange(term);
    setIsListOpen(false);
    setActiveIndex(-1);
    onSearchSubmit(term);
  };

  const handleKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (matches.length === 0) return;
    if (event.key === 'ArrowDown') {
      event.preventDefault();
      setActiveIndex((index) => (index + 1 >= matches.length ? 0 : index + 1));
    } else if (event.key === 'ArrowUp') {
      event.preventDefault();
      setActiveIndex((index) => (index - 1 < 0 ? matches.length - 1 : index - 1));
    } else if (event.key === 'Enter' && activeIndex > -1) {
      event.preventDefault();
      chooseSuggestion(matches[activeIndex]);
    }
  };

  return (
    <div className="app-masthead">
      <div className="govuk-width-container">
        <div className="govuk-grid-row govuk-!-margin-top-5">
          <div className="govuk-grid-column-one-half">
            <h1 className="govuk-heading-xl app-masthead__title">{title}</h1>
            <p id="search-description" className="govuk-body app-data-browser__search-description">
              {description}
            </p>
            <form onSubmit={handleSubmit} autoComplete={suggestions ? 'off' : undefined}>
              <div
                ref={containerRef}
                className={`app-data-browser__searchbox${suggestions ? ' autocomplete' : ''}`}
              >
                <input
                  className="govuk-input app-data-browser__searchbox-input"
                  id="search"
                  name="q"
                  type="search"
                  value={searchValue}
                  onChange={(event) => {
                    onSearchChange(event.target.value);
                    setIsListOpen(true);
                    setActiveIndex(-1);
                  }}
                  onKeyDown={handleKeyDown}
                  placeholder={placeholder}
                  aria-labelledby="search-description"
                />
                <button className="app-data-browser__searchbox-button" type="submit" aria-label="submit search">
                  <svg width="21" height="22" viewBox="0 0 21 22" xmlns="http://www.w3.org/2000/svg">
                    <g transform="translate(-760 -316)" fill="none" fillRule="evenodd">
                      <path
                        d="M776.594 331.75a9.418 9.418 0 0 0 2.428-6.296c0-5.213-4.268-9.454-9.51-9.454-5.244 0-9.512 4.242-9.512 9.454 0 5.213 4.268 9.455 9.51 9.455a9.523 9.523 0 0 0 5.04-1.444l4.176 4.152c.25.248.59.383.931.383.34 0 .681-.136.931-.383a1.295 1.295 0 0 0 .023-1.873l-4.017-3.994zm-13.939-6.296c0-3.746 3.065-6.814 6.855-6.814 3.792 0 6.833 3.068 6.833 6.814s-3.064 6.815-6.832 6.815-6.856-3.047-6.856-6.815z"
                        fill="#FFF"
                        fillRule="nonzero"
                      />
                    </g>
                  </svg>
                </button>
                {matches.length > 0 && (
                  <div id="searchautocomplete-list" className="autocomplete-items">
                    {matches.map((term, index) => (
                      <div
                        key={term}
                        className={index === activeIndex ? 'autocomplete-active' : undefined}
                        onClick={() => chooseSuggestion(term)}
                      >
                        <strong>{term}</strong>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </form>
          </div>
        </div>
      </div>
    </div>
  );
}
