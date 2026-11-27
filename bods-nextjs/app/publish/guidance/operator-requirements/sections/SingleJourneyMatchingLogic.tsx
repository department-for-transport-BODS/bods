export function SingleJourneyMatchingLogic() {
  return (
    <>
      <p className="govuk-body"><b>Single journey matching logic</b></p>
      <p className="govuk-body">
        To be able to compare data for any given journey it is necessary to first identify a single
        journey in both the SIRI and TxC datasets. The SIRI delivery is the starting point for the
        process.{' '}
        <a className="govuk-link" href="https://pti.org.uk/system/files/files/SIRI_VM_PTI_Data_Matching_v1-1.pdf" target="_blank" rel="noopener noreferrer">
          Read more information on SIRI-VM PTI and Data matching
        </a>.
      </p>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 1</b></p>
      <p className="govuk-body govuk-!-margin-bottom-0">1.1: Using OperatorRef and LineRef from the SIRI data locate the TxC files that contain data for the operator and line. There may be multiple files.</p>
      <p className="govuk-body govuk-!-margin-bottom-0">1.2: Check which files contain data valid for the date of the SIRI data. This requires checking the OperatingPeriod to find data valid for the date being tested.</p>
      <p className="govuk-body">1.3: If more than one data set has a TXC file containing the OperatorRef and LineRef, stop processing.</p>
      <ul className="govuk-list govuk-list--number">
        <li>If files are found in more than one dataset, stop processing.</li>
        <li>If files are found, continue to Step 2.</li>
        <li>
          If no file is found, mark the vehicle journey as failed to be analysed.
          <ul className="govuk-list govuk-list--bullet">
            <li>1.1: &ldquo;No published TXC files found matching NOC {'{noc}'} and line name {'{line_name}'}&rdquo;</li>
            <li>1.2: &ldquo;No timetables found with VehicleActivity date in OperatingPeriod&rdquo;</li>
            <li>1.3: &ldquo;Matched OperatorRef and LineRef in more than one dataset&rdquo;</li>
          </ul>
        </li>
      </ul>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 2</b></p>
      <p className="govuk-body">2.1: From the Step 1 subset of TxC files, search each file for a JourneyCode that matches the DatedVehicleJourneyRef from the SIRI journey.</p>
      <ul className="govuk-list govuk-list--number">
        <li>If files are found with matching JourneyCodes, continue to Step 3.</li>
        <li>
          If no file is found, mark the vehicle journey as failed to be analysed.
          <ul className="govuk-list govuk-list--bullet">
            <li>2.1: &ldquo;No vehicle journeys found with JourneyCode {'{vehicle_journey_ref}'}&rdquo;</li>
          </ul>
        </li>
      </ul>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 3</b></p>
      <p className="govuk-body">3.1: From the Step 2 subset of TxC files, search each file for an OperatingProfile appropriate for the date and type of day of the SIRI data being tested.</p>
      <ul className="govuk-list govuk-list--number">
        <li>If files are found with a matching OperatingProfile, continue to Step 4.</li>
        <li>
          If no matching OperatingProfile is found, mark the vehicle journey as failed to be analysed.
          <ul className="govuk-list govuk-list--bullet">
            <li>3.1: &ldquo;No vehicle journeys found with OperatingProfile applicable to VehicleActivity date&rdquo;</li>
          </ul>
        </li>
      </ul>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 4</b></p>
      <p className="govuk-body">From the Step 3 subset of TxC files, use the file with the highest RevisionNumber that is valid for the date of the SIRI data.</p>
      <ul className="govuk-list govuk-list--alpha">
        <li>If only one file remains after filtering by RevisionNumber, move to Step 5.</li>
        <li>If more than one file remains after reading the RevisionNumber, mark the vehicle journey as failed to be analysed.</li>
      </ul>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 5</b></p>
      <p className="govuk-body">There may be more than one matching JourneyCode within a TxC, for example for weekday and weekend journeys or journeys relating to a serviced organisation.</p>
      <p className="govuk-body">5.1: Search within the file for JourneyCodes with an OperatingProfile valid for the date being tested. For journeys referencing a serviced organisation, establish whether that organisation is working on the day of the SIRI journey.</p>
      <p className="govuk-body">If the serviced organisation is working that day, there should be one JourneyCode with the combination of OperatingProfile, ServicedOrganisation and DaysOfOperation.</p>
      <p className="govuk-body">5.2: If the serviced organisation is not working that day, there should be one JourneyCode with the combination of OperatingProfile, ServicedOrganisation and DaysOfNonOperation.</p>
      <p className="govuk-body">5.3: If there is no serviced organisation data for the JourneyCode with an appropriate OperatingProfile, there should be only one JourneyCode.</p>
      <ul className="govuk-list govuk-list--number">
        <li>If a single JourneyCode is identified, move to Step 6.</li>
        <li>
          If more than one valid JourneyCode is found:
          <ul className="govuk-list govuk-list--alpha">
            <li>If only one TxC is found, mark the vehicle journey as failed to be analysed: &ldquo;Found more than one matching vehicle journey in a single timetables file belonging to a single service code&rdquo;.</li>
            <li>If more than one TxC is found and each has the same service code, mark the vehicle journey as failed to be analysed: &ldquo;Found more than one matching vehicle journey in timetables belonging to a single service code&rdquo;.</li>
            <li>If more than one TxC and more than one service code remain, exclude the journey from the operator score and remove it from the uncounted vehicle activity report. There is no error for this case.</li>
          </ul>
        </li>
      </ul>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 6</b></p>
      <p className="govuk-body">Once a single JourneyCode with an appropriate OperatingPeriod and OperatingProfile is identified, testing can progress to the remaining matching values.</p>
      <p className="govuk-body">If DatedVehicleJourneyRef from the selected SIRI delivery cannot be matched to a single JourneyCode in a TxC file, analysis fails for all data types.</p>

      <p className="govuk-body govuk-!-margin-bottom-0"><b>Step 7</b></p>
      <p className="govuk-body">It is necessary to identify the correct direction, destination and origin information for the full journey being tested.</p>
      <p className="govuk-body">Start by identifying the JourneyPattern for the journey&rsquo;s direction. The JourneyPattern identifies its JourneyPatternSections, allowing the first and last sections to be identified for the origin and destination.</p>
      <p className="govuk-body">OriginRef is the StopPointRef in the From element of the first JourneyPatternSection.</p>
      <p className="govuk-body">DestinationRef is the StopPointRef in the To element of the last JourneyPatternSection.</p>
      <p className="govuk-body">To identify the direction, find the direction associated with the JourneyPattern referenced in the isolated JourneyCode.</p>
      <p className="govuk-body">To identify the block, find the BlockNumber associated with the isolated JourneyCode.</p>
    </>
  );
}
