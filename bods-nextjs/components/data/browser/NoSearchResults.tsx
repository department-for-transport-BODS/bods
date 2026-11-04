/** Mirrors the `{% empty %}` block in Django's browse/snippets/search_list.html. */
export function NoSearchResults() {
  return (
    <div>
      <hr className="govuk-section-break govuk-section-break--m govuk-section-break" />
      <h4 className="govuk-heading-s">Having trouble finding what you want?</h4>
      <ul className="govuk-list govuk-list--bullet">
        <li>Check your spelling and try again</li>
      </ul>
    </div>
  );
}
