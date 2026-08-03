import { config } from '@/config';

export function HelpSectionTables() {
  const supportEmailHref = `mailto:${config.supportEmail}`;
  return (
    <>
      <h2 className="govuk-heading-m">Timetables solution suppliers</h2>
      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Supplier</th>
            <th scope="col" className="govuk-table__header">Website (URL)</th>
            <th scope="col" className="govuk-table__header">Email address</th>
            <th scope="col" className="govuk-table__header">Data type</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Excel TransXChange Tool</td>
            <td className="govuk-table__cell">N/A</td>
            <td className="govuk-table__cell"><a className="govuk-link" href={supportEmailHref}>{config.supportEmail}</a></td>
            <td className="govuk-table__cell"></td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">GRM Mapping</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.grmmapping.co.uk" target="_blank" rel="noopener noreferrer">www.grmmapping.co.uk</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:enquiries@grmmapping.co.uk">enquiries@grmmapping.co.uk</a></td>
            <td className="govuk-table__cell">Timetables</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Transmach TM 500 and TM 920</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://transmach.co.uk/tm500.html" target="_blank" rel="noopener noreferrer">https://transmach.co.uk/tm500.html</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:sales@transmach.co.uk">sales@transmach.co.uk</a></td>
            <td className="govuk-table__cell">Timetables / AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Elydium</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://elydium.co.uk/bus-open-data/" target="_blank" rel="noopener noreferrer">https://elydium.co.uk/bus-open-data/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:busopendata@elydium.co.uk">busopendata@elydium.co.uk</a></td>
            <td className="govuk-table__cell">Timetables / Fares</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Ticketer</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.ticketer.com/en/" target="_blank" rel="noopener noreferrer">https://www.ticketer.com/en/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:support@ticketer.co.uk">support@ticketer.co.uk</a></td>
            <td className="govuk-table__cell">Timetables / AVL / Fares</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Shuttle ID - BOD Package</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://shuttleid.uk/packages/" target="_blank" rel="noopener noreferrer">https://shuttleid.uk/packages/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@shuttleid.uk">info@shuttleid.uk</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Create Fares Data Service</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://fares-data.dft.gov.uk/" target="_blank" rel="noopener noreferrer">https://fares-data.dft.gov.uk/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href={supportEmailHref}>{config.supportEmail}</a></td>
            <td className="govuk-table__cell">Fares</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Mentz</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.mentz.net/en/" target="_blank" rel="noopener noreferrer">https://www.mentz.net/en/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@mentz.net">info@mentz.net</a></td>
            <td className="govuk-table__cell">Timetables</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Optibus</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.optibus.com/" target="_blank" rel="noopener noreferrer">https://www.optibus.com/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@optibus.com">info@optibus.com</a></td>
            <td className="govuk-table__cell">Timetables</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Trapeze</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://trapezegroup.co.uk/" target="_blank" rel="noopener noreferrer">https://trapezegroup.co.uk/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:ccuk@trapezegroup.com">ccuk@trapezegroup.com</a></td>
            <td className="govuk-table__cell">Timetables</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Systra</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.systra.co.uk/en/" target="_blank" rel="noopener noreferrer">https://www.systra.co.uk/en/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.systra.co.uk/en/systra/contact" target="_blank" rel="noopener noreferrer">https://www.systra.co.uk/en/systra/contact</a></td>
            <td className="govuk-table__cell">Timetables</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">INIT</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.initse.com/ende/home/" target="_blank" rel="noopener noreferrer">https://www.initse.com/ende/home/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:pobszynski@init.co.uk">pobszynski@init.co.uk</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vix Technology</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://vixtechnology.com/" target="_blank" rel="noopener noreferrer">https://vixtechnology.com/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:uk.sales@vixtechnology.com">uk.sales@vixtechnology.com</a></td>
            <td className="govuk-table__cell">Timetables / AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">InfoRox</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.inforox.com/" target="_blank" rel="noopener noreferrer">https://www.inforox.com/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@inforox.com">info@inforox.com</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">R2P</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.r2p.com/" target="_blank" rel="noopener noreferrer">https://www.r2p.com/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@r2p.com">info@r2p.com</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Ticket Technology - Tixiom Handheld and Ezifare Handheld</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="http://www.ticket-technology.co.uk/products/tixiom-t1m" target="_blank" rel="noopener noreferrer">http://www.ticket-technology.co.uk/products/tixiom-t1m</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="http://www.ticket-technology.co.uk/contact-us" target="_blank" rel="noopener noreferrer">http://www.ticket-technology.co.uk/contact-us</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Go Swiftly - Monotrome</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.goswift.ly/metronome" target="_blank" rel="noopener noreferrer">https://www.goswift.ly/metronome</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.goswift.ly/contact-us" target="_blank" rel="noopener noreferrer">https://www.goswift.ly/contact-us</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Rise DM - Next Stop Driver</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="http://www.nextstopapp.co.uk/" target="_blank" rel="noopener noreferrer">http://www.nextstopapp.co.uk/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@risedm.com">info@risedm.com</a></td>
            <td className="govuk-table__cell">Timetables / AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vectare - VecTive</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://vectare.co.uk/" target="_blank" rel="noopener noreferrer">https://vectare.co.uk/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@vectare.co.uk">info@vectare.co.uk</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Parkeon Flowbird</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.flowbird.group/" target="_blank" rel="noopener noreferrer">https://www.flowbird.group/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:contact@flowbird.group">contact@flowbird.group</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Rewire Security</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.rewiresecurity.co.uk/" target="_blank" rel="noopener noreferrer">https://www.rewiresecurity.co.uk/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:info@rewiresecurity.co.uk">info@rewiresecurity.co.uk</a></td>
            <td className="govuk-table__cell">AVL</td>
          </tr>
        </tbody>
      </table>

      <h3 className="govuk-heading-m">Bus location solution suppliers</h3>
      <table className="govuk-table">
        <thead className="govuk-table__head">
          <tr className="govuk-table__row">
            <th scope="col" className="govuk-table__header">Supplier</th>
            <th scope="col" className="govuk-table__header">Website (URL)</th>
            <th scope="col" className="govuk-table__header">Email address</th>
          </tr>
        </thead>
        <tbody className="govuk-table__body">
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">INIT</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.initse.com/ende/home/" target="_blank" rel="noopener noreferrer">https://www.initse.com/ende/home/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:pobszynski@init.co.uk">pobszynski@init.co.uk</a></td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Parkeon Flowbird</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.flowbird.group/" target="_blank" rel="noopener noreferrer">https://www.flowbird.group/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:contact@flowbird.group">contact@flowbird.group</a></td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Ticketer</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://www.ticketer.com/en/" target="_blank" rel="noopener noreferrer">https://www.ticketer.com/en/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:support@ticketer.co.uk">support@ticketer.co.uk</a></td>
          </tr>
          <tr className="govuk-table__row">
            <td className="govuk-table__cell">Vix</td>
            <td className="govuk-table__cell"><a className="govuk-link" href="https://vixtechnology.com/" target="_blank" rel="noopener noreferrer">https://vixtechnology.com/</a></td>
            <td className="govuk-table__cell"><a className="govuk-link" href="mailto:uk.sales@vixtechnology.com">uk.sales@vixtechnology.com</a></td>
          </tr>
        </tbody>
      </table>

      <h3 className="govuk-heading-m">Fares solution suppliers</h3>
      <p className="govuk-body">
        Many ETM suppliers are developing NeTEx output solutions for their customers. Speak with
        your ETM supplier about their developments and how they align with your requirements.
      </p>
      <p className="govuk-body">
        Transport for the North (TfN) are developing the Fare Data Build Tool, that will allow
        operators to create their own NeTEx fares data, please contact{' '}
        <a className="govuk-link" href="mailto:fdbt-support@infinityworks.com">
          fdbt-support@infinityworks.com
        </a>{' '}
        for more information.
      </p>
    </>
  );
}

