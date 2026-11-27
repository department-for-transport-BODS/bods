import Link from 'next/link';
import { dataPath } from '@/config/client';

export function CaseStudiesSection() {
  return (
    <>
      <h1 data-qa="case-studies-header" className="govuk-heading-l">Case studies</h1>
      <p className="govuk-body">
        The Bus Open Data Service (BODS) is an online service that provides access to UK bus
        company data.
      </p>
      <p className="govuk-body">
        All the data on the service has been published by the bus companies themselves. There are
        3 types of data available on the service:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Timetables data</li>
        <li>Bus location data</li>
        <li>Fares data</li>
      </ul>
      <p className="govuk-body">
        This guide has been created to show a simple example of how to use the BODS API. For
        this case study, we will demonstrate how to download an individual dataset from one of
        the operator companies on BODS via the API.
      </p>

      <h2 data-qa="setting-up-header" className="govuk-heading-m">Setting up</h2>
      <p className="govuk-body">To start using this guide, you will need:</p>
      <ol className="govuk-list govuk-list--number">
        <li>A Postman account</li>
        <li>An API key</li>
      </ol>

      <h3 data-qa="postman-account-header" className="govuk-heading-s">Postman account</h3>
      <p className="govuk-body">
        This guide uses Postman to download the data. Go to{' '}
        <a className="govuk-link" href="http://www.postman.com" target="_blank" rel="noopener noreferrer">
          Postman
        </a>{' '}
        and sign up (for free) if you don&apos;t already have an account.
      </p>

      <h3 data-qa="api-key-header" className="govuk-heading-s">API key</h3>
      <p className="govuk-body">
        Next you need an <b>API key</b> for BODS.
      </p>
      <p className="govuk-body">
        If you don&apos;t have an account on BODS, you can create one at{' '}
        <Link className="govuk-link" href="/account/signup">Create account</Link>.
      </p>
      <p className="govuk-body">
        Sign in to BODS at <Link className="govuk-link" href="/account/login">Sign in</Link>.
      </p>
      <p className="govuk-body">
        In the top right, click <span className="guidance-text-highlight">My account</span>{' '}
        <span className="govuk-!-padding-1">&gt;</span>{' '}
        <span className="guidance-text-highlight">Account settings</span>
      </p>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Account settings" src="/assets/images/case-study/account-settings.png" height="auto" width="auto" />
      </div>
      <p className="govuk-body">
        Your <b>API key</b> is shown in the settings. Make a note of it.
      </p>

      <h2 data-qa="download-dataset-header" className="govuk-heading-m">Download dataset</h2>
      <h3 data-qa="find-bods-datasets-header" className="govuk-heading-s">Find BODS datasets</h3>
      <p className="govuk-body">
        In order to download the dataset you&rsquo;re interested in, you need to find its{' '}
        <b>Dataset ID.</b>
      </p>
      <p className="govuk-body">The starting point for finding this is the data catalogue.</p>
      <p className="govuk-body">Here&rsquo;s how to download it.</p>
      <p className="govuk-body">
        Type the URL <span className="guidance-text-highlight">{dataPath('/catalogue')}</span>{' '}
        into the address bar of a web browser such as Google Chrome, hit Return and save the
        resulting <span className="guidance-text-highlight">.zip</span> file.
      </p>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Chrome address bar" src="/assets/images/case-study/chrome-address-bar.png" height="auto" width="auto" />
      </div>
      <p className="govuk-body">
        Unlock the <span className="guidance-text-highlight">.zip</span> file. The unzipped
        folder will contain a file called{' '}
        <span className="guidance-text-highlight">overall_data_catalogue.csv</span>.
      </p>
      <p className="govuk-body">
        Open this file in Excel (or equivalent) as a comma-separated file; be careful not to
        specify any other separators, such as semi-colon.
      </p>
      <p className="govuk-body">The spreadsheet that opens lists all the datasets for each operator.</p>
      <p className="govuk-body">
        The column called <span className="guidance-text-highlight">Operator</span> lists the
        name of the bus company that published the data.
      </p>
      <p className="govuk-body govuk-!-margin-bottom-2">
        The column <span className="guidance-text-highlight">Dataset Type</span> lists the type
        of data in each dataset, which will be one of:
      </p>
      <ul className="govuk-list govuk-list--bullet">
        <li>Timetables</li>
        <li>Automatic Vehicle Locations (i.e. bus location data)</li>
        <li>Fares</li>
      </ul>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Data catalogue" src="/assets/images/case-study/data-catalogue-operator.png" height="auto" width="auto" />
      </div>
      <p className="govuk-body">
        First, browse or search these two columns to find the data type from the operator
        you&apos;re interested in.
      </p>
      <p className="govuk-body">
        Then use the <span className="guidance-text-highlight">Data Set/Feed Name</span> column
        to find the name of the dataset you want to download.
      </p>
      <p className="govuk-body">
        Get the <b>Dataset ID</b> from the <span className="guidance-text-highlight">Dataset ID</span>{' '}
        column.
      </p>

      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Data catalogue" src="/assets/images/case-study/data-catalogue-dataset-id.png" height="auto" width="auto" />
      </div>
      <h3 data-qa="download-header" className="govuk-heading-s">Download</h3>
      <p className="govuk-body">
        Now that you have the <b>Dataset ID</b> you can download the dataset in Postman as
        follows.
      </p>
      <p className="govuk-body">Go to Postman and create a new request:</p>
      <ol className="govuk-list govuk-list--number">
        <li>
          Set the request type to <span className="guidance-text-highlight">GET</span>
        </li>
        <li>
          Set the URL according to data type:
          <ul className="govuk-list govuk-list--bullet">
            <li>
              For timetables data, use{' '}
              <span className="guidance-text-highlight">https://data.bus-data.dft.gov.uk/api/v1/dataset/{'{ID}'}/</span>
            </li>
            <li>
              For bus location data, use{' '}
              <span className="guidance-text-highlight">https://data.bus-data.dft.gov.uk/api/v1/datafeed/{'{ID}'}/</span>
            </li>
            <li>
              For fares data, use{' '}
              <span className="guidance-text-highlight">https://data.bus-data.dft.gov.uk/api/v1/fares/dataset/{'{ID}'}/</span>
            </li>
          </ul>
          where <span className="guidance-text-highlight">{'{ID}'}</span> is the <b>Dataset ID</b>
        </li>
        <li>
          Set a param with key <span className="guidance-text-highlight">api_key</span> and value
          equal to your <b>API key</b>
        </li>
        <li>Click Send</li>
      </ol>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Postman request" src="/assets/images/case-study/postman-timetables-request.png" height="auto" width="auto" />
      </div>
      <p className="govuk-body">
        The response is different for each of the three data types. The following section gives a
        synopsis for each type.
      </p>

      <h2 data-qa="setting-up-header" className="govuk-heading-m">Interpreting the response</h2>
      <h3 data-qa="setting-up-header" className="govuk-heading-s">Timetables and fares data</h3>
      <p className="govuk-body">
        For timetables and fares data, the response is a JSON text file that describes properties
        of the dataset pertinent to BODS.
      </p>
      <p className="govuk-body">
        To get more information, use the <span className="guidance-text-highlight">url</span>{' '}
        parameter to download the original dataset uploaded by the bus company.
      </p>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Postman response" src="/assets/images/case-study/postman-timetables-response.png" height="auto" width="auto" />
      </div>
      <ol className="govuk-list govuk-list--number">
        <li>
          Click on the value of <span className="guidance-text-highlight">url</span> in Postman
          <ul className="govuk-list govuk-list--bullet">
            <li>This creates a new Postman request</li>
          </ul>
        </li>
        <li>
          Set the request type to <span className="guidance-text-highlight">GET</span>
        </li>
        <li>Click &quot;Send and Download&quot; from the &quot;Send&quot; dropdown</li>
        <li>
          Save the file to disk
          <ul className="govuk-list govuk-list--bullet">
            <li>
              The file will either be a <span className="guidance-text-highlight">.zip</span> or
              a <span className="guidance-text-highlight">.xml</span> file
            </li>
          </ul>
        </li>
        <li>Open the file with an appropriate application</li>
      </ol>
      <h3 data-qa="setting-up-header" className="govuk-heading-s">Bus location data</h3>
      <p className="govuk-body">
        For bus location data, the response from the dataset query comprises a SIRI-VM XML file
        describing the data feed.
      </p>
      <div className="govuk-grid-row govuk-!-margin-top-7 govuk-!-margin-bottom-7">
        <img className="govuk-!-width-full" alt="Postman response" src="/assets/images/case-study/postman-avl-response.png" height="auto" width="auto" />
      </div>
    </>
  );
}

