import { Fragment } from 'react';
import type { LineDetail } from './line-detail-types';

const NO_VALID_FILES = 'No currently valid files available in this dataset for this service';

// Source: the dataset-property-table in
// transit_odp/publish/templates/publish/revision_review/review_line_metadata.html and
// transit_odp/browse/templates/browse/timetables/dataset_detail/review_line_metadata.html
export function LinePropertyTable({
  line,
  firstHeaderClassName,
}: {
  line: LineDetail;
  firstHeaderClassName?: string;
}) {
  const isFlexible = line.serviceType === 'Flexible' || line.serviceType === 'Flexible/Standard';
  const methods = line.bookingMethods;

  return (
    <table className="govuk-table dataset-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className={`govuk-table__header${firstHeaderClassName ? ` ${firstHeaderClassName}` : ''}`}>
            Type of service
          </th>
          <td className="govuk-table__cell dont-break-out" colSpan={2}>
            {line.serviceType}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Registration Number
          </th>
          <td className="govuk-table__cell dont-break-out" colSpan={2}>
            {line.serviceCode}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Current valid file(s)
          </th>
          <td className="govuk-table__cell dont-break-out" colSpan={2}>
            {line.currentValidFiles.length
              ? line.currentValidFiles.map((file, index) => (
                  <Fragment key={`${file.filename}-${index}`}>
                    {index > 0 ? <br /> : null}
                    <div className="stacked">
                      {file.startDate || 'No Start Date'} - {file.endDate || 'No End Date'}
                      <br />
                      {file.filename}
                    </div>
                  </Fragment>
                ))
              : 'N/A'}
          </td>
        </tr>
        {isFlexible ? (
          <>
            <tr className="govuk-table__row">
              <th scope="row" className="govuk-table__header">
                Booking arrangements
              </th>
              <td className="govuk-table__cell dont-break-out" colSpan={2}>
                {line.bookingArrangements || NO_VALID_FILES}
              </td>
            </tr>
            <tr className="govuk-table__row">
              <th scope="row" className="govuk-table__header">
                Booking methods
              </th>
              <td className="govuk-table__cell dont-break-out" colSpan={2}>
                <div className="stacked">
                  {methods ? (
                    <>
                      {methods.phone ? `Phone - ${methods.phone}` : null}
                      <br />
                      {methods.email ? `Email - ${methods.email}` : null}
                      <br />
                      {methods.url ? `URL - ${methods.url}` : null}
                    </>
                  ) : (
                    NO_VALID_FILES
                  )}
                </div>
              </td>
            </tr>
          </>
        ) : null}
      </tbody>
    </table>
  );
}
