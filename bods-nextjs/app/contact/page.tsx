/**
 * Contact Page
 * 
 * Source: transit_odp/templates/pages/contact.html
 * 
 * Note: SUPPORT_PHONE and SUPPORT_EMAIL should be set via environment variables
 * to match the Django configuration. The defaults here match the current deployed values.
 */

import Link from 'next/link';
import { SUPPORT_EMAIL, SUPPORT_PHONE } from '@/lib/config';

export default function ContactPage() {
  return (
    <div className="govuk-width-container">
      <div className="govuk-main-wrapper">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds govuk-!-padding-right-9">
            <h1 className="govuk-heading-l">
              Contact the Bus Open Data Service
            </h1>
            
            <h2 className="govuk-heading-s">
              Feedback and support
            </h2>
            <div>
              <p className="govuk-body-m">
                If you require support or are experiencing issues, please contact the Bus Open
                Data Service Help Desk.
              </p>
              <p className="govuk-body-m">
                The Help Desk is available Monday to Friday, 9am to 5pm (excluding Bank Holidays
                in England and Wales, and the 24th December).
              </p>
              <p className="govuk-body-m">
                The Help Desk can be contacted by telephone or email as follows.
              </p>
              <ul className="govuk-list">
                <li>
                  Telephone: {SUPPORT_PHONE}
                </li>
                <li>
                  Email: <a className="govuk-link" href={`mailto:${SUPPORT_EMAIL}`}>{SUPPORT_EMAIL}</a>
                </li>
              </ul>
            </div>
            
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
            
            <div>
              <h2 className="govuk-heading-s">
                Share your stories
              </h2>
              <ul className="govuk-list">
                <li>
                  Please share your bus open data stories via Twitter, using the{' '}
                  <a className="govuk-link" href="https://twitter.com/busopendata" target="_blank" rel="noopener noreferrer">@busopendata</a>
                  {' '}account and{' '}
                  <a className="govuk-link" href="https://twitter.com/hashtag/BusOpenData" target="_blank" rel="noopener noreferrer">#BusOpenData</a>
                  {' '}hashtag.
                </li>
              </ul>
            </div>
            
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
            
            <div>
              <h2 className="govuk-heading-s">
                Media enquiries
              </h2>
              <p className="govuk-body">
                <a 
                  className="govuk-link"
                  target="_blank"
                  rel="noopener noreferrer"
                  href="https://www.gov.uk/government/organisations/department-for-transport/about/media-enquiries"
                >
                  https://www.gov.uk/government/organisations/department-for-transport/about/media-enquiries
                </a>
              </p>
              <p className="govuk-body">
                The Department for Transport press office only deals with enquiries from the media.
              </p>
            </div>
          </div>
          
          <div className="govuk-grid-column-one-third">
            <h2 className="govuk-heading-m">
              Bus Open Data Service
            </h2>
            <div>
              <p className="govuk-body-m">
                The Bus Open Data Service enables local bus operators in England to publish
                higher quality data about timetables, fares and real time data.
              </p>
              <ul className="govuk-list app-list--nav govuk-!-font-size-19">
                <li>
                  <a 
                    className="govuk-link"
                    href="https://www.gov.uk/government/consultations/bus-services-act-2017-bus-open-data"
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Find out more about Bus Open Data Service
                  </a>
                </li>
                <li>
                  <a 
                    className="govuk-link" 
                    href="https://www.gov.uk/government/organisations/department-for-transport" 
                    target="_blank"
                    rel="noopener noreferrer"
                  >
                    Department for Transport
                  </a>
                </li>
              </ul>
            </div>
            
            <hr className="govuk-section-break govuk-section-break--l govuk-section-break--visible" />
            
            <h2 className="govuk-heading-s">
              Follow us
            </h2>
            <div>
              <p className="govuk-body-m">
                <a 
                  href="https://twitter.com/busopendata?ref_src=twsrc%5Etfw"
                  className="govuk-link"
                  target="_blank"
                  rel="noopener noreferrer"
                  style={{ display: 'flex', flexDirection: 'column' }}
                >
                  <svg 
                    viewBox="0 0 1200 1227"
                    xmlns="http://www.w3.org/2000/svg"
                    width="120"
                    height="120"
                    aria-hidden="true"
                    focusable="false"
                    style={{ color: '#0b0c0c' }}
                  >
                    <path 
                      fill="currentColor" 
                      d="M714.163 519.284L1160.89 0H1055.03L667.137 450.887L357.328 0H0L468.492 681.821L0 1226.37H105.866L515.491 750.218L842.672 1226.37H1200L714.137 519.284H714.163ZM569.165 687.828L521.697 619.934L144.011 79.6944H306.615L611.412 515.685L658.88 583.579L1055.08 1150.3H892.476L569.165 687.854V687.828Z"
                    />
                  </svg>
                  <span className="govuk-!-padding-top-3">Bus open data service Twitter</span>
                </a>
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
