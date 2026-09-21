'use client';

import Link from 'next/link';
import { useParams, useRouter, useSearchParams } from 'next/navigation';

type TimetableCancelContentProps = {
  formUrl: string;
  confirmUrl: string;
  heading: string;
};

export function TimetableCancelContent({ formUrl, confirmUrl, heading }: TimetableCancelContentProps) {
  const router = useRouter();

  const goBackOrFallback = () => {
    router.push(formUrl, { scroll: true });
  };

  return (
    <div className="govuk-width-container">
      <Link type="button" className="govuk-back-link govuk-button-back-link" href={formUrl}>
        Back
      </Link>
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl">{heading}</h1>
            <p className="govuk-body">Any changes you have made so far will not be saved.</p>

            <div className="govuk-button-group">
              <Link role="button" className="govuk-button" href={confirmUrl}>
                Confirm
              </Link>
              <button type="button" className="govuk-button govuk-button--secondary" onClick={goBackOrFallback}>
                Cancel
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}

export function TimetableCreateCancelContent() {
  const params = useParams();
  const searchParams = useSearchParams();
  const orgId = params.orgId as string;

  const step = searchParams.get('step') === 'provide-data' ? '?step=provide-data' : '';
  const formUrl = `/publish/org/${orgId}/dataset/timetable/new${step}`;
  const listUrl = `/publish/org/${orgId}/dataset/timetable`;

  return (
    <TimetableCancelContent
      formUrl={formUrl}
      confirmUrl={listUrl}
      heading="Would you like to cancel publishing this data set?"
    />
  );
}