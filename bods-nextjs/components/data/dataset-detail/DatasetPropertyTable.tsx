/**
 * Property table shared by the data-host dataset detail pages. The type
 * specific rows (e.g. TransXChange version, data quality, last updated) are
 * passed as children.
 *
 * Source: transit_odp/browse/templates/browse/base/property_table.html
 */

import type { ReactNode } from 'react';
import type { DatasetType } from '@/types';
import { DatasetStatusIndicator } from './DatasetStatusIndicator';

interface DatasetPropertyTableProps {
  id: number;
  name: string;
  /** "Timetables data", "Automatic Vehicle Locations data", ... */
  dataTypeLabel: string;
  datasetType: DatasetType;
  description: string;
  organisationName: string;
  /** The publisher's dataset search, Django `owner_search_link` */
  ownerHref: string;
  status: string;
  /** Type specific rows */
  children?: ReactNode;
}

export function DatasetPropertyTable({
  id,
  name,
  dataTypeLabel,
  datasetType,
  description,
  organisationName,
  ownerHref,
  status,
  children,
}: DatasetPropertyTableProps) {
  return (
    <table className="govuk-table consumer-property-table">
      <tbody className="govuk-table__body">
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Name
          </th>
          <td colSpan={2} className="govuk-table__cell dont-break-out">
            {name}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Data type
          </th>
          <td colSpan={2} className="govuk-table__cell dont-break-out">
            {dataTypeLabel}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            {datasetType === 'AVL' ? 'Data feed ID' : 'Data set ID'}
          </th>
          <td colSpan={2} className="govuk-table__cell dont-break-out">
            {id}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Description
          </th>
          <td colSpan={2} className="govuk-table__cell dont-break-out">
            {description}
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Owner
          </th>
          <td colSpan={2} className="govuk-table__cell dont-break-out">
            <div className="stacked">
              <a className="govuk-link" href={ownerHref}>
                {organisationName}
              </a>
              Access all data uploaded by this publisher
            </div>
          </td>
        </tr>
        <tr className="govuk-table__row">
          <th scope="row" className="govuk-table__header">
            Status
          </th>
          <td colSpan={2} className="govuk-table__cell">
            <div className="flex-between">
              <DatasetStatusIndicator status={status} datasetType={datasetType} />
            </div>
          </td>
        </tr>
        {children}
      </tbody>
    </table>
  );
}
