import { useSupportConfig } from '@/components/shared/SupportConfigProvider';

const timetableSuppliers = [
  ['Excel TransXChange Tool', 'N/A', '', ''],
  ['GRM Mapping', 'https://www.grmmapping.co.uk', 'enquiries@grmmapping.co.uk', 'Timetables'],
  ['Transmach TM 500 and TM 920', 'https://transmach.co.uk/tm500.html', 'sales@transmach.co.uk', 'Timetables / AVL'],
  ['Elydium', 'https://elydium.co.uk/bus-open-data/', 'busopendata@elydium.co.uk', 'Timetables / Fares'],
  ['Omnibus', 'https://omnibus.solutions/', 'support@omnibus.uk.com', 'Timetables'],
  ['Ticketer', 'https://www.ticketer.com/en/', 'support@ticketer.co.uk', 'Timetables / AVL / Fares'],
  ['Shuttle ID - BOD Package', 'https://shuttleid.uk/packages/', 'info@shuttleid.uk', 'AVL'],
  ['Create Fares Data Service', 'https://fares-data.dft.gov.uk/', '', 'Fares'],
  ['Mentz', 'https://www.mentz.net/en/', 'info@mentz.net', 'Timetables'],
  ['Optibus', 'https://www.optibus.com/', 'info@optibus.com', 'Timetables'],
  ['Trapeze', 'https://trapezegroup.co.uk/', 'ccuk@trapezegroup.com', 'Timetables'],
  ['Systra', 'https://www.systra.co.uk/en/', 'https://www.systra.co.uk/en/systra/contact', 'Timetables'],
  ['INIT', 'https://www.initse.com/ende/home/', 'pobszynski@init.co.uk', 'AVL'],
  ['Vix Technology', 'https://vixtechnology.com/', 'uk.sales@vixtechnology.com', 'Timetables / AVL'],
  ['InfoRox', 'https://www.inforox.com/', 'info@inforox.com', 'AVL'],
  ['R2P', 'https://www.r2p.com/', 'info@r2p.com', 'AVL'],
  ['Ticket Technology - Tixiom Handheld and Ezifare Handheld', 'http://www.ticket-technology.co.uk/products/tixiom-t1m', 'http://www.ticket-technology.co.uk/contact-us', 'AVL'],
  ['Go Swiftly - Monotrome', 'https://www.goswift.ly/metronome', 'https://www.goswift.ly/contact-us', 'AVL'],
  ['Rise DM - Next Stop Driver', 'http://www.nextstopapp.co.uk/', 'info@risedm.com', 'Timetables / AVL'],
  ['Vectare - VecTive', 'https://vectare.co.uk/', 'info@vectare.co.uk', 'AVL'],
  ['Parkeon Flowbird', 'https://www.flowbird.group/', 'contact@flowbird.group', 'AVL'],
  ['Rewire Security', 'https://www.rewiresecurity.co.uk/', 'info@rewiresecurity.co.uk', 'AVL'],
] as const;

const busLocationSuppliers = [
  ['INIT', 'https://www.initse.com/ende/home/', 'pobszynski@init.co.uk'],
  ['Parkeon Flowbird', 'https://www.flowbird.group/', 'contact@flowbird.group'],
  ['Ticketer', 'https://www.ticketer.com/en/', 'support@ticketer.co.uk'],
  ['Vix', 'https://vixtechnology.com/', 'uk.sales@vixtechnology.com'],
] as const;

function Contact({ value }: { value: string }) {
  if (!value) return null;
  if (value.startsWith('http')) return <a className="govuk-link" href={value} target="_blank" rel="noopener noreferrer">{value}</a>;
  return <a className="govuk-link" href={`mailto:${value}`}>{value}</a>;
}

function SupplierTable({ rows, includeDataType = false }: { rows: readonly (readonly string[])[]; includeDataType?: boolean }) {
  return (
    <table data-qa="requirements-table" className="govuk-table">
      <thead data-qa="requirements-table-header" className="govuk-table__head"><tr className="govuk-table__row"><th scope="col" className="govuk-table__header">Supplier</th><th scope="col" className="govuk-table__header">Website (URL)</th><th scope="col" className="govuk-table__header">Email address</th>{includeDataType && <th scope="col" className="govuk-table__header">Data type</th>}</tr></thead>
      <tbody className="govuk-table__body">
        {rows.map((row) => <tr className="govuk-table__row" key={row[0]}><td className="govuk-table__cell">{row[0]}</td><td className="govuk-table__cell"><Contact value={row[1]} /></td><td className="govuk-table__cell"><Contact value={row[2]} /></td>{includeDataType && <td className="govuk-table__cell">{row[3]}</td>}</tr>)}
      </tbody>
    </table>
  );
}

function AgentTable({ title, rows }: { title: string; rows: readonly (readonly string[])[] }) {
  return <><h3 className="govuk-heading-m">{title}</h3><table data-qa="requirements-table" className="govuk-table"><thead className="govuk-table__head"><tr className="govuk-table__row"><th scope="col" className="govuk-table__header">Agent</th><th scope="col" className="govuk-table__header">Email address</th></tr></thead><tbody className="govuk-table__body">{rows.map(([agent, email]) => <tr className="govuk-table__row" key={agent}><td className="govuk-table__cell">{agent}</td><td className="govuk-table__cell"><Contact value={email} /></td></tr>)}</tbody></table></>;
}

export function HelpSection() {
  const { supportEmail } = useSupportConfig();

  return (
    <>
      <h1 data-qa="help-header" className="govuk-heading-l">How to get help</h1>
      <h2 data-qa="timetable-header" className="govuk-heading-m">Timetables solution suppliers</h2>
      <SupplierTable rows={timetableSuppliers} includeDataType />
      <h3 data-qa="bus-location-header" className="govuk-heading-m">Bus location solution suppliers</h3>
      <SupplierTable rows={busLocationSuppliers} />
      <AgentTable title="Agents for timetables and fares support" rows={[['Elydium Limited', 'busopendata@elydium.co.uk'], ['MCI Transport Consultants Ltd', 'wayne@martlet.uk.com'], ["Charlton's Consultance", 'mark.fdr@outlook.com']]} />
      <AgentTable title="Agent for timetable support" rows={[['BODS', '']]} />
      <AgentTable title="Agent for AVL support" rows={[['ShuttleID', 'info@shuttleid.uk'], ['Trackaroo', 'info@trackaroo.co.uk']]} />
      <AgentTable title="Agents for timetables and AVL support" rows={[['Rise Digital Media', 'Scott.james@risedm.com'], ['Transmach', 'dhanraj@transmach.co.uk']]} />
      <h3 data-qa="timetable-header" className="govuk-heading-m">Fares solution suppliers</h3>
      <p className="govuk-body">Many ETM suppliers are developing NeTEx output solutions for their customers. Speak with your ETM supplier about their developments and how they align with your requirements.</p>
      <p className="govuk-body">Transport for the North (TfN) are developing the Fare Data Build Tool, that will allow operators to create their own NeTEx fares data, please contact <a className="govuk-link" href="mailto:fdbt-support@infinityworks.com">fdbt-support@infinityworks.com</a> for more information.</p>
      <h3 className="govuk-heading-m">Contact the Bus Open Data Service</h3>
      <p className="govuk-body">Contact <a className="govuk-link" href={`mailto:${supportEmail}`}>{supportEmail}</a> for:</p>
      <ul className="govuk-list govuk-list--bullet"><li>Request TxC tool support or creation from DfT</li><li>Support using the Fare Data Build tool</li><li>Technical and publishing issues on BODS</li><li>Create an operator account</li><li>Enquiries about the Bus Open Data Program</li><li>Feedback on the service</li></ul>
    </>
  );
}
