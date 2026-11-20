import { useSupportConfig } from '@/components/shared/SupportConfigProvider';

export function HelpSection() {
  const { supportEmail } = useSupportConfig();

  return (
    <>
      <h1 data-qa="issues-header" className="govuk-heading-l">Data issues</h1>
      <p className="govuk-body">
        To report any issues found within the data please find the detail page for that data
        set/feed. This can easily be done using the data set/feed ID. Browse for that data and
        provide feedback to the data publisher. This will enable them to read your comments and
        response to your query. This way data quality can be iteratively improved within the
        service, and the transport ecosystem.
      </p>
      <p className="govuk-body">
        Contact <a className="govuk-link" href={`mailto:${supportEmail}`}>{supportEmail}</a> for
        any queries or questions you might have if it is not already answered within the
        developer documentation. We also welcome constructive feedback about the service.
      </p>
    </>
  );
}

