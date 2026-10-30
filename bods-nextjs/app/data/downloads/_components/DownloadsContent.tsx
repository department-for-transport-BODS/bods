import type { ReactNode } from 'react';
import Link from 'next/link';
import { Breadcrumbs } from '@/components/shared/Breadcrumbs';
import { dataPath, wwwPath } from '@/config/client';
import { hostBreadcrumbs } from '@/lib/host-breadcrumbs';
import { DownloadHelpModal } from './DownloadHelpModal';

/**
 * Source: transit_odp/browse/templates/browse/downloads.html
 * View: transit_odp/browse/views/base_views.py - DownloadsView
 * Help modals: transit_odp/browse/templates/browse/snippets/help_modals/*.html
 */

interface DownloadsContentProps {
  isGtfsServiceAlertsLive: boolean;
  ptiPdfUrl: string;
}

function TxcHelp({ ptiPdfUrl }: { ptiPdfUrl: string }) {
  return (
    <DownloadHelpModal heading="TransXChange">
      <p className="govuk-body">
        TransXChange is the UK nationwide standard for exchanging bus schedules and related data. It
        is used for:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>The electronic registration of bus routes</li>
        <li>The Traffic Area Network</li>
        <li>
          The exchange of bus routes with other computer systems such as journey planners and
          vehicle real-time tracking systems
        </li>
      </ul>
      <p className="govuk-body">
        TransXChange is part of a family of coherent transport related XML standards that follow
        GovTalk guidelines. The latest transxchange profile used on BODS can be{' '}
        <a className="govuk-link" href={ptiPdfUrl} target="_blank">
          found here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

function GtfsHelp() {
  return (
    <DownloadHelpModal heading="GTFS">
      <p className="govuk-body">
        The General Transit Feed Specification (GTFS) is a data specification that allows public
        transit agencies to publish their transit data in a format that can be consumed by a wide
        variety of software applications. Today, the GTFS data format is used by thousands of public
        transport providers.
      </p>
      <p className="govuk-body">
        More information on this can be{' '}
        <a className="govuk-link" href="https://gtfs.org/" target="_blank">
          found here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

const SIRI_INTRO =
  'The Service Interface for Real-time Information (SIRI) specifies a European interface standard for exchanging information about the planned, current or projected performance of real-time public transport operations between different computer systems. The latest UK profile of SIRI can be found';

function SiriVmHelp() {
  return (
    <DownloadHelpModal heading="SIRI-VM">
      <p className="govuk-body">
        {SIRI_INTRO}{' '}
        <a
          className="govuk-link"
          rel="noopener noreferrer"
          target="_blank"
          href="https://www.gov.uk/government/publications/technical-guidance-publishing-location-data-using-the-bus-open-data-service-siri-vm/technical-guidance-siri-vm"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

function SiriSxHelp() {
  return (
    <DownloadHelpModal heading="SIRI-SX">
      <p className="govuk-body">
        {SIRI_INTRO}{' '}
        <a
          className="govuk-link"
          rel="noopener noreferrer"
          target="_blank"
          href="http://siri.org.uk/schema/schemas.htm"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

function GtfsRtHelp() {
  return (
    <DownloadHelpModal heading="GTFS-RT">
      <p className="govuk-body">
        GTFS Realtime is a feed specification that allows public transportation agencies to provide
        realtime updates about their fleet to application developers. It is an extension to GTFS
        (General Transit Feed Specification), an open data format for public transportation
        schedules and associated geographic information.
      </p>
      <p className="govuk-body">
        To learn more about GTFS-RT please visit{' '}
        <a
          className="govuk-link"
          href="https://developers.google.com/transit/gtfs-realtime"
          target="_blank"
          rel="noopener noreferrer"
        >
          here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

function NetexHelp() {
  return (
    <DownloadHelpModal heading="NeTEx">
      <p className="govuk-body">
        NeTEx provides a means to exchange data for passenger information such as stops, routes
        timetables and fares, among different computer systems, together with related operational
        data. It can be used to collect and integrate data from many different stakeholders, and to
        reintegrate it as it evolves through successive versions.
      </p>
      <p className="govuk-body">
        More information on this can be{' '}
        <a className="govuk-link" href="http://netex.uk/netex/schema.htm" target="_blank">
          found here
        </a>
        .
      </p>
    </DownloadHelpModal>
  );
}

function DownloadSection({ children }: { children: ReactNode }) {
  return (
    <div className="govuk-grid-row govuk-!-margin-top-5">
      <div className="govuk-grid-column-two-thirds">{children}</div>
    </div>
  );
}

function Attribute({ label, children }: { label: string; children: ReactNode }) {
  return (
    <li>
      <b>{label}:</b> {children}
    </li>
  );
}

export function DownloadsContent({ isGtfsServiceAlertsLive, ptiPdfUrl }: DownloadsContentProps) {
  return (
    <div className="govuk-width-container">
      <Breadcrumbs
        items={hostBreadcrumbs('data', {
          label: 'Download All Data',
          href: dataPath('/downloads'),
        })}
      />

      <div className="govuk-main-wrapper app-main-class">
        <div className="govuk-grid-row">
          <div className="govuk-grid-column-two-thirds">
            <h1 className="govuk-heading-xl dont-break-out" aria-label="Heading Title">
              Download all data
            </h1>
            <p className="govuk-body">
              <a className="govuk-link" href={dataPath('/catalogue')}>
                Download the data catalogue
              </a>
            </p>
            <p className="govuk-body">
              Data catalogue will provide you with a comprehensive view of all data published on BODS
              and provide matching information between different dataset types.
            </p>
          </div>
          <div className="govuk-grid-column-one-third">
            <h3 className="govuk-heading-m">Need further help?</h3>
            <ul className="govuk-list">
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={dataPath('/guide-me')}>
                  Guide me
                </Link>
              </li>
              <li className="govuk-!-margin-bottom-3">
                <Link className="govuk-link" href={wwwPath('/contact')}>
                  Contact us for technical issues
                </Link>
              </li>
            </ul>
          </div>
        </div>

        <DownloadSection>
          <p className="govuk-body">
            <a className="govuk-link" href={dataPath('/timetable/download/')}>
              Timetables data
            </a>
          </p>
          <p className="govuk-body">
            Timetables data provides details of a specific number, day, date,
            <br />
            route and time. You can download all the timetables data cached
            <br />
            on the service.
          </p>
          <ul className="govuk-list">
            <li>
              <b>Format:</b> TransXChange <TxcHelp ptiPdfUrl={ptiPdfUrl} /> GTFS <GtfsHelp />
            </li>
            <Attribute label="TXC profile">TXC 2.4 PTI v1.1</Attribute>
            <Attribute label="Mode">Bus</Attribute>
            <Attribute label="File type">ZIP file</Attribute>
            <Attribute label="Update frequency">Daily 6:00 am and 6:00 pm GMT</Attribute>
          </ul>
        </DownloadSection>

        <DownloadSection>
          <p className="govuk-body">
            <a className="govuk-link" href={dataPath('/avl/download/')}>
              Location data
            </a>
          </p>
          <p className="govuk-body">
            Location data provides the most recent real time vehicle
            <br />
            position cached on the service. You can download all current
            <br />
            bus location data.
          </p>
          <ul className="govuk-list">
            <li>
              <b>Format:</b> SIRI-VM <SiriVmHelp /> GTFS-RT <GtfsRtHelp />
            </li>
            <Attribute label="Mode">Bus</Attribute>
            <Attribute label="File type">ZIP file</Attribute>
            <li>
              <b>Update frequency :</b> Every 10 seconds
            </li>
          </ul>
        </DownloadSection>

        <DownloadSection>
          <p className="govuk-body">
            <a className="govuk-link" href={dataPath('/fares/download/')}>
              Fares data
            </a>
          </p>
          <p className="govuk-body">You can download all fares data cached on the service.</p>
          <ul className="govuk-list">
            <li>
              <b>Format:</b> NeTEx <NetexHelp />
            </li>
            <Attribute label="NeTEx profile">v1.1</Attribute>
            <Attribute label="Mode">Bus</Attribute>
            <Attribute label="File type">ZIP file</Attribute>
            <Attribute label="Update frequency">Daily 6:00 am and 6:00 pm GMT</Attribute>
          </ul>
        </DownloadSection>

        <DownloadSection>
          <p className="govuk-body">
            <a className="govuk-link" href={dataPath('/disruptions/download/')}>
              Disruptions data
            </a>
          </p>
          <p className="govuk-body">
            {isGtfsServiceAlertsLive
              ? 'Download disruptions data for selected regions in SIRI-SX and GTFS-RT formats.'
              : 'Download disruptions data for selected regions in SIRI-SX format.'}
          </p>
          <ul className="govuk-list">
            <li>
              <b>Format:</b> SIRI-SX <SiriSxHelp />
              {isGtfsServiceAlertsLive && (
                <>
                  {' '}
                  GTFS-RT <GtfsRtHelp />
                </>
              )}
            </li>
            <Attribute label="Mode">Bus, Ferry, Light Rail</Attribute>
            <Attribute label="File type">ZIP file</Attribute>
            <Attribute label="Update frequency">Every minute</Attribute>
            <Attribute label="Source">Local authorities</Attribute>
          </ul>
        </DownloadSection>

        <DownloadSection>
          <p className="govuk-body">
            <a className="govuk-link" href={dataPath('/coach/download')}>
              Coach data
            </a>
          </p>
          <p className="govuk-body">Download coach data in ATCO-CIF or TxC 2.4 PTI.</p>
          <ul className="govuk-list">
            <Attribute label="Format">TxC2.4 PTI/ATCO.CIF</Attribute>
            <Attribute label="Mode">Coach</Attribute>
            <Attribute label="File type">ZIP file</Attribute>
            <Attribute label="Update frequency">Every Friday</Attribute>
            <Attribute label="Source">Operator</Attribute>
          </ul>
        </DownloadSection>
      </div>
    </div>
  );
}
