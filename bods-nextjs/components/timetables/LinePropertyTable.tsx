import { Fragment } from 'react';
import type { LineDetail, ValidFile } from './line-detail-types';

const NO_VALID_FILES = 'No currently valid files available in this dataset for this service';

type LinePropertyTableLine = Pick<LineDetail, 'serviceType' | 'serviceCode' | 'bookingArrangements' | 'bookingMethods'> &
  Partial<Pick<LineDetail, 'currentValidFiles'>>;

/**
 * Source: transit_odp/publish/templates/publish/snippets/dataset_detail_files.html
 * Start - end dates, then the file name, one block per file ("N/A" when there are none).
 */
export function FileList({ files }: { files: ValidFile[] }) {
  if (!files.length) return <>N/A</>;
  return (
    <>
      {files.map((file, index) => (
        <Fragment key={`${file.filename}-${index}`}>
          {index > 0 ? <br /> : null}
          <div className="stacked">
            {file.startDate || 'No Start Date'} - {file.endDate || 'No End Date'}
            <br />
            {file.filename}
          </div>
        </Fragment>
      ))}
    </>
  );
}

// Source: the dataset-property-table in
// transit_odp/publish/templates/publish/revision_review/review_line_metadata.html and
// transit_odp/browse/templates/browse/timetables/dataset_detail/review_line_metadata.html
//
// The operator licence line page (licence_review_line_metadata.html) shares the table but has no
// "Current valid file(s)" row (it lists files per data type further down) and, on its passenger
// facing variant (`?pf=`), drops the registration number and flexible booking rows. Those pages
// turn the optional rows off.
export function LinePropertyTable({
  line,
  firstHeaderClassName,
  showRegistrationNumber = true,
  showValidFiles = true,
  showBookingDetails = true,
}: {
  line: LinePropertyTableLine;
  firstHeaderClassName?: string;
  showRegistrationNumber?: boolean;
  showValidFiles?: boolean;
  showBookingDetails?: boolean;
}) {
  const isFlexible =
    showBookingDetails && (line.serviceType === 'Flexible' || line.serviceType === 'Flexible/Standard');
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
        {showRegistrationNumber ? (
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Registration Number
            </th>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              {line.serviceCode}
            </td>
          </tr>
        ) : null}
        {showValidFiles ? (
          <tr className="govuk-table__row">
            <th scope="row" className="govuk-table__header">
              Current valid file(s)
            </th>
            <td className="govuk-table__cell dont-break-out" colSpan={2}>
              <FileList files={line.currentValidFiles ?? []} />
            </td>
          </tr>
        ) : null}
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
