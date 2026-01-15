/**
 * Registering / Using our account Section
 * Source: transit_odp/guidance/templates/guidance/bus_operators/register_bus_open_data.html
 */

import { TRAVELINE_NOC_URL } from '@/lib/config';
import { SupportEmailLink } from './SupportEmailLink';

export function RegisteringSection() {
  return (
    <>
      <h2 data-qa="registring-header" className="govuk-heading-l">Registering</h2>
      <p data-qa="registring-paragraph" className="govuk-body">
        Operators can create an account for the Bus Open Data Digital Service by emailing{' '}
        <SupportEmailLink />.
      </p>

      <h2 data-qa="my-account-header" className="govuk-heading-l">My account</h2>
      <p data-qa="my-account-paragraph" className="govuk-body">
        There are three account types: admin, standard and agent.
      </p>

      <h2 data-qa="org-profile-header" className="govuk-heading-l">Organisation profile</h2>
      
      <h2 data-qa="short-name-header" className="govuk-heading-l">Short name &amp; National Operator Codes</h2>
      <p data-qa="short-name-paragraph" className="govuk-body">
        Under organisation profile, users can edit the short name and National Operator
        Codes (NOC) of the operator. The Bus Open Data Service uses the NOC inputted here
        to cross reference against data supplied to the service. Please make sure that
        these are maintained.
      </p>
      <p data-qa="traveline-paragraph" className="govuk-body">
        The noc database can be found on the Traveline website:{' '}
        <a className="govuk-link" rel="noopener noreferrer" target="_blank" href={TRAVELINE_NOC_URL}>
          {TRAVELINE_NOC_URL}
        </a>.
      </p>
      <p data-qa="email-support-paragraph" className="govuk-body">
        To change the operator&apos;s long name on BODS, please contact{' '}
        <SupportEmailLink />.
      </p>

      <h2 data-qa="user-management-header" className="govuk-heading-l">User management</h2>
      <p data-qa="user-management-paragraph-1" className="govuk-body">
        Only admin users can add and remove other users from the operator&apos;s organisation.
        All users can publish data for the operator.
      </p>
      <p data-qa="user-management-paragraph-2" className="govuk-body">
        Types of users:
      </p>
      <p data-qa="user-management-paragraph-3" className="govuk-body">
        <strong>Admin</strong> users should be the key account holders of the operator.
        They can add and remove other users from the organisation.
      </p>
      <p data-qa="user-management-paragraph-4" className="govuk-body">
        <strong>Standard</strong> users should be the staff of the operator.
      </p>
      <p data-qa="user-management-paragraph-5" className="govuk-body">
        <strong>Agents</strong> are external to the operator&apos;s organisation and can publish an
        operator&apos;s data to the service. Agents must be invited to the service in the first
        instance by an operator. Please ensure external contracts are established prior
        to assigning agents.
      </p>

      <h3 data-qa="unable-create-header" className="govuk-heading-m">Unable to create a user?</h3>
      <p data-qa="user-management-paragraph-6" className="govuk-body">
        If you are having issues inviting a new user to your organisation, please contact{' '}
        <SupportEmailLink />.
      </p>
    </>
  );
}


